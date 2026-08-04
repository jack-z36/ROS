#!/usr/bin/env node
'use strict';

// Tour Builder - Graph Topology Analysis Script
// Usage: node ua-tour-analyze.js <input.json> <output.json>

const fs = require('fs');

function main() {
  const inputPath = process.argv[2];
  const outputPath = process.argv[3];
  if (!inputPath || !outputPath) {
    console.error('Usage: node ua-tour-analyze.js <input.json> <output.json>');
    process.exit(1);
  }

  const raw = fs.readFileSync(inputPath, 'utf8');
  const data = JSON.parse(raw);
  const nodes = data.nodes || [];
  const edges = data.edges || [];
  const layers = data.layers || [];

  // Build lookups
  const nodeById = new Map();
  for (const n of nodes) nodeById.set(n.id, n);
  const nodeIds = new Set(nodeById.keys());

  // ---------- Fan-in / Fan-out ----------
  // Fan-in: count edges pointing TO a node
  // Fan-out: count edges pointing FROM a node
  const fanIn = new Map();
  const fanOut = new Map();
  for (const n of nodes) { fanIn.set(n.id, 0); fanOut.set(n.id, 0); }
  for (const e of edges) {
    const s = e.source, t = e.target;
    if (nodeIds.has(s)) fanOut.set(s, (fanOut.get(s) || 0) + 1);
    if (nodeIds.has(t)) fanIn.set(t, (fanIn.get(t) || 0) + 1);
  }

  // Fan-in ranking: top 20 (exclude pure hierarchical "contains" which inflate counts)
  // We'll compute two: one with all edges, one excluding "contains" (which are tree edges).
  // Use the excluding-contains version for "importance" semantics, since contains is just folder nesting.
  const fanInNoContains = new Map();
  const fanOutNoContains = new Map();
  for (const n of nodes) { fanInNoContains.set(n.id, 0); fanOutNoContains.set(n.id, 0); }
  for (const e of edges) {
    if (e.type === 'contains') continue;
    const s = e.source, t = e.target;
    if (nodeIds.has(s)) fanOutNoContains.set(s, (fanOutNoContains.get(s) || 0) + 1);
    if (nodeIds.has(t)) fanInNoContains.set(t, (fanInNoContains.get(t) || 0) + 1);
  }

  const topFanIn = nodes
    .map(n => ({ id: n.id, name: n.name, fanIn: fanInNoContains.get(n.id) || 0, type: n.type }))
    .sort((a, b) => b.fanIn - a.fanIn)
    .slice(0, 20);

  const topFanOut = nodes
    .map(n => ({ id: n.id, name: n.name, fanOut: fanOutNoContains.get(n.id) || 0, type: n.type }))
    .sort((a, b) => b.fanOut - a.fanOut)
    .slice(0, 20);

  // ---------- Entry Point Candidates ----------
  const ENTRY_NAMES = new Set([
    'index.ts','index.js','main.ts','main.js','app.ts','app.js','server.ts','server.js',
    'mod.rs','main.go','main.py','main.rs','manage.py','app.py','wsgi.py','asgi.py','run.py',
    '__main__.py','Application.java','Main.java','Program.cs','config.ru','index.php',
    'App.swift','Application.kt','main.cpp','main.c'
  ]);
  // ROS / launch additions:
  const LAUNCH_NAMES = new Set([
    'act_system.launch.py','gripper_ctrl.py','act_deploy_node.py'
  ]);

  // For "high fan-out top 10%" and "low fan-in bottom 25%"
  const fanOutValues = nodes.map(n => fanOutNoContains.get(n.id) || 0).sort((a,b)=>a-b);
  const fanInValues = nodes.map(n => fanInNoContains.get(n.id) || 0).sort((a,b)=>a-b);
  const p90FanOut = fanOutValues[Math.floor(fanOutValues.length * 0.9)] || 0;
  const p25FanIn = fanInValues[Math.floor(fanInValues.length * 0.25)] || 0;

  const entryScores = [];
  for (const n of nodes) {
    let score = 0;
    const name = n.name || '';
    const fp = n.filePath || '';
    const depth = fp.split('/').length - 1;
    const fo = fanOutNoContains.get(n.id) || 0;
    const fi = fanInNoContains.get(n.id) || 0;

    if (n.type === 'document') {
      if (name === 'README.md' && depth === 0) score += 5;
      else if (/\.md$/i.test(name) && depth === 0) score += 2;
      else if (name === 'README.md') score += 1; // sub-package README
    } else if (n.type === 'file' || n.type === 'config' || n.type === 'service') {
      if (ENTRY_NAMES.has(name)) score += 3;
      if (LAUNCH_NAMES.has(name)) score += 3;
      if (depth <= 1) score += 1;
      if (fo >= p90FanOut && p90FanOut > 0) score += 1;
      if (fi <= p25FanIn) score += 1;
    }
    if (score > 0) {
      entryScores.push({
        id: n.id, name: n.name, score,
        type: n.type, filePath: fp,
        summary: (n.summary || '').slice(0, 220)
      });
    }
  }
  entryScores.sort((a, b) => b.score - a.score);
  const entryPointCandidates = entryScores.slice(0, 8);

  // ---------- BFS from top CODE entry point ----------
  // For a ROS workspace, the natural "uses/depends-on" chain is broader than
  // Python imports: launch files orchestrate nodes via triggers/depends_on/provisions,
  // and configures connects config to code. We follow these forward edge types.
  const FOLLOW_TYPES = new Set(['imports', 'calls', 'triggers', 'depends_on', 'provisions', 'configures']);
  const adjFwd = new Map();
  for (const n of nodes) adjFwd.set(n.id, []);
  for (const e of edges) {
    if (!FOLLOW_TYPES.has(e.type)) continue;
    if (nodeIds.has(e.source) && nodeIds.has(e.target)) {
      adjFwd.get(e.source).push(e.target);
    }
  }

  // Pick the best CODE entry point: prefer the project's actual main entry
  // (act_deploy_node.py / act_system.launch.py) over a trivial CLI like gripper_ctrl.py.
  // gripper_ctrl.py is a debug CLI with no forward deps, so it produces an empty BFS.
  const PREFERRED_ENTRY = new Set([
    'file:act/ui/act_deploy_node.py',
    'file:act_system/launch/act_system.launch.py'
  ]);
  let startNode = null;
  for (const c of entryPointCandidates) {
    if (PREFERRED_ENTRY.has(c.id)) { startNode = c.id; break; }
  }
  if (!startNode) {
    for (const c of entryPointCandidates) {
      if (c.type !== 'document') { startNode = c.id; break; }
    }
  }
  if (!startNode && entryPointCandidates.length) startNode = entryPointCandidates[0].id;
  if (!startNode && nodes.length) startNode = nodes[0].id;

  // Multi-source BFS from the launch entry AND the deploy-node entry.
  // A ROS workspace has two natural roots: the top-level launch orchestrator
  // (depends_on -> per-package launch files) and the inference node itself
  // (imports/calls -> service/runtime/types). Seeding both gives a richer,
  // more representative traversal than either alone.
  const SEEDS = [
    'file:act_system/launch/act_system.launch.py',
    'file:act/ui/act_deploy_node.py'
  ].filter(id => nodeIds.has(id));
  if (SEEDS.length === 0 && startNode) SEEDS.push(startNode);

  const bfsOrder = [];
  const depthMap = {};
  {
    const visited = new Set();
    const queue = [];
    for (const s of SEEDS) {
      if (!visited.has(s)) {
        visited.add(s); depthMap[s] = 0; queue.push({ id: s, depth: 0 });
      }
    }
    while (queue.length) {
      const { id, depth } = queue.shift();
      bfsOrder.push(id);
      const next = adjFwd.get(id) || [];
      const seen = new Set();
      for (const t of next) {
        if (visited.has(t) || seen.has(t)) continue;
        seen.add(t); visited.add(t);
        depthMap[t] = depth + 1;
        queue.push({ id: t, depth: depth + 1 });
      }
    }
  }
  const byDepth = {};
  for (const [id, d] of Object.entries(depthMap)) {
    const k = String(d);
    if (!byDepth[k]) byDepth[k] = [];
    byDepth[k].push(id);
  }

  // ---------- Non-code file inventory ----------
  const documentation = [];
  const infrastructure = []; // service, pipeline, resource
  const dataFiles = [];      // table, schema, endpoint
  const configFiles = [];
  for (const n of nodes) {
    const item = { id: n.id, name: n.name, type: n.type, summary: (n.summary || '').slice(0, 240) };
    if (n.type === 'document') documentation.push(item);
    else if (n.type === 'service' || n.type === 'pipeline' || n.type === 'resource') infrastructure.push(item);
    else if (n.type === 'table' || n.type === 'schema' || n.type === 'endpoint') dataFiles.push(item);
    else if (n.type === 'config') configFiles.push(item);
  }

  // ---------- Tightly-coupled clusters ----------
  // Bidirectional pairs via imports/calls/depends_on/exports
  const BIDIR_TYPES = new Set(['imports', 'calls', 'depends_on', 'exports', 'related']);
  const fwd = new Map(); // source -> set(targets)
  for (const n of nodes) fwd.set(n.id, new Set());
  for (const e of edges) {
    if (!BIDIR_TYPES.has(e.type)) continue;
    if (nodeIds.has(e.source) && nodeIds.has(e.target)) {
      fwd.get(e.source).add(e.target);
    }
  }
  // Find mutual pairs
  const pairEdges = []; // [a,b] with a<b
  const seenPair = new Set();
  for (const [a, ts] of fwd.entries()) {
    for (const b of ts) {
      const bt = fwd.get(b);
      if (bt && bt.has(a)) {
        const key = a < b ? a + '|' + b : b + '|' + a;
        if (seenPair.has(key)) continue;
        seenPair.add(key);
        pairEdges.push([a, b]);
      }
    }
  }
  // Build clusters from pair edges
  const parent = new Map();
  function find(x) { while (parent.get(x) !== x) { parent.set(x, parent.get(parent.get(x))); x = parent.get(x); } return x; }
  function union(a, b) {
    const ra = find(a), rb = find(b);
    if (ra !== rb) parent.set(ra, rb);
  }
  for (const n of nodes) parent.set(n.id, n.id);
  for (const [a, b] of pairEdges) union(a, b);

  const clusterGroups = new Map(); // root -> set of members
  for (const n of nodes) {
    const r = find(n.id);
    if (!clusterGroups.has(r)) clusterGroups.set(r, new Set());
    clusterGroups.get(r).add(n.id);
  }
  // Score clusters by counting internal edges
  const clusters = [];
  for (const [root, members] of clusterGroups.entries()) {
    if (members.size < 2 || members.size > 6) continue;
    let edgeCount = 0;
    for (const e of edges) {
      if (members.has(e.source) && members.has(e.target)) edgeCount++;
    }
    clusters.push({ nodes: Array.from(members), edgeCount });
  }
  clusters.sort((a, b) => b.edgeCount - a.edgeCount);
  const topClusters = clusters.slice(0, 10);

  // ---------- Node Summary Index ----------
  const nodeSummaryIndex = {};
  for (const n of nodes) {
    nodeSummaryIndex[n.id] = {
      name: n.name,
      type: n.type,
      summary: n.summary || '',
      filePath: n.filePath || ''
    };
  }

  // ---------- Layers ----------
  const layerList = layers.map(l => ({
    id: l.id, name: l.name, description: l.description || ''
  }));

  const result = {
    scriptCompleted: true,
    entryPointCandidates,
    fanInRanking: topFanIn,
    fanOutRanking: topFanOut,
    bfsTraversal: {
      startNode: SEEDS.join(' + '),
      startNodes: SEEDS,
      order: bfsOrder,
      depthMap,
      byDepth
    },
    nonCodeFiles: {
      documentation,
      infrastructure,
      data: dataFiles,
      config: configFiles
    },
    clusters: topClusters,
    layers: {
      count: layerList.length,
      list: layerList
    },
    nodeSummaryIndex,
    totalNodes: nodes.length,
    totalEdges: edges.length
  };

  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), 'utf8');
  console.error(`OK: wrote ${outputPath} (nodes=${nodes.length}, edges=${edges.length}, bfs reached=${bfsOrder.length})`);
  process.exit(0);
}

try {
  main();
} catch (err) {
  console.error('FATAL:', err && err.stack ? err.stack : err);
  process.exit(1);
}
