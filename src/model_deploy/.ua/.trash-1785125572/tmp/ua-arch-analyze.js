#!/usr/bin/env node
/*
 * Understand-Anything Architecture Analyzer - Phase 1 structural analysis.
 *
 * Usage: node ua-arch-analyze.js <input.json> <output.json>
 *
 * Computes directory grouping, node-type grouping, import adjacency,
 * cross-category dependency analysis, inter/intra-group import patterns,
 * directory + file pattern matching, deployment topology, data pipeline,
 * doc coverage and dependency direction. Writes a single JSON object to the
 * output path and exits 0 on success.
 */
'use strict';

const fs = require('fs');

function fail(msg) {
  console.error('FATAL: ' + msg);
  process.exit(1);
}

const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  fail('usage: node ua-arch-analyze.js <input.json> <output.json>');
}

let data;
try {
  data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
} catch (e) {
  fail('cannot read/parse input JSON: ' + e.message);
}

const fileNodes = Array.isArray(data.fileNodes) ? data.fileNodes : [];
const importEdges = Array.isArray(data.importEdges) ? data.importEdges : [];
const allEdges = Array.isArray(data.allEdges) ? data.allEdges : [];

// ---- node id sets & lookup -------------------------------------------------
const nodeIdSet = new Set(fileNodes.map((n) => n.id));
const nodeById = new Map();
for (const n of fileNodes) nodeById.set(n.id, n);

// ---- A. directory grouping -------------------------------------------------
// Compute common path prefix shared by all files (directory-level).
function dirSegments(p) {
  // normalize, strip trailing slashes, split on '/'
  const clean = p.replace(/\\/g, '/').replace(/\/+$/, '');
  const i = clean.lastIndexOf('/');
  return i === -1 ? '' : clean.slice(0, i);
}

const allDirs = fileNodes.map((n) => dirSegments(n.filePath)).filter(Boolean);
function commonDirPrefix(dirs) {
  if (dirs.length === 0) return '';
  const split = dirs.map((d) => d.split('/'));
  let prefix = [];
  const first = split[0];
  for (let i = 0; i < first.length; i++) {
    const seg = first[i];
    if (split.every((s) => s[i] === seg)) prefix.push(seg);
    else break;
  }
  return prefix.length === 0 ? '' : prefix.join('/') + '/';
}
const prefix = commonDirPrefix(allDirs);

// group by the first directory segment after the prefix
function firstSegmentAfterPrefix(filePath) {
  const clean = filePath.replace(/\\/g, '/');
  let rest = clean;
  if (prefix && clean.startsWith(prefix)) rest = clean.slice(prefix.length);
  else {
    // fall back: first directory segment of the whole path
    const i = clean.indexOf('/');
    return i === -1 ? '__root__' : clean.slice(0, i);
  }
  // rest is relative to the common prefix
  if (rest.indexOf('/') === -1) {
    // file directly under prefix (no subdir) -> root
    return '__root__';
  }
  return rest.slice(0, rest.indexOf('/'));
}

// To capture the multi-package workspace structure (act/, elephant_gripper/,
// rm65_dual_arm/ ...) we should group by the TOP-LEVEL directory rather than
// by the segment after a deep common prefix. The common prefix for this repo
// is empty (files span many top-level packages), so firstSegmentAfterPrefix
// already yields the top-level package. We keep the generic helper for safety
// but expose the real grouping below.
const directoryGroups = {};
for (const n of fileNodes) {
  const seg = firstSegmentAfterPrefix(n.filePath) || '__root__';
  if (!directoryGroups[seg]) directoryGroups[seg] = [];
  directoryGroups[seg].push(n.id);
}

// ---- B. node type grouping -------------------------------------------------
const nodeTypeGroups = {};
for (const n of fileNodes) {
  const t = n.type || 'file';
  if (!nodeTypeGroups[t]) nodeTypeGroups[t] = [];
  nodeTypeGroups[t].push(n.id);
}

// ---- C. import adjacency (fan-in / fan-out) -------------------------------
const fanOut = {};
const fanIn = {};
for (const n of fileNodes) {
  fanOut[n.id] = 0;
  fanIn[n.id] = 0;
}
for (const e of importEdges) {
  if (nodeIdSet.has(e.source) && nodeIdSet.has(e.target)) {
    fanOut[e.source] = (fanOut[e.source] || 0) + 1;
    fanIn[e.target] = (fanIn[e.target] || 0) + 1;
  }
}

// helper: which directory group does a node belong to?
function groupOf(nodeId) {
  const n = nodeById.get(nodeId);
  if (!n) return null;
  return firstSegmentAfterPrefix(n.filePath) || '__root__';
}

// ---- E. inter-group import frequency --------------------------------------
const interGroupMap = {}; // "from->to" -> count
for (const e of importEdges) {
  if (!nodeIdSet.has(e.source) || !nodeIdSet.has(e.target)) continue;
  const a = groupOf(e.source);
  const b = groupOf(e.target);
  if (a === null || b === null || a === b) continue;
  const key = a + '\u0001' + b;
  interGroupMap[key] = (interGroupMap[key] || 0) + 1;
}
const interGroupImports = Object.entries(interGroupMap).map(([k, c]) => {
  const [from, to] = k.split('\u0001');
  return { from, to, count: c };
}).sort((x, y) => y.count - x.count);

// ---- F. intra-group import density ----------------------------------------
const groupInternal = {};
const groupTotal = {};
for (const g of Object.keys(directoryGroups)) {
  groupInternal[g] = 0;
  groupTotal[g] = 0;
}
for (const e of importEdges) {
  if (!nodeIdSet.has(e.source) || !nodeIdSet.has(e.target)) continue;
  const a = groupOf(e.source);
  const b = groupOf(e.target);
  if (a === null || b === null) continue;
  if (a === b) groupInternal[a] += 1;
  groupTotal[a] += 1;
  if (a !== b) groupTotal[b] += 1;
}
const intraGroupDensity = {};
for (const g of Object.keys(directoryGroups)) {
  const total = groupInternal[g] + groupTotal[g]; // avoid divide-by-zero confusion
  const denom = groupTotal[g] || 0;
  intraGroupDensity[g] = {
    internalEdges: groupInternal[g],
    totalEdges: groupTotal[g],
    density: denom === 0 ? 0 : Number((groupInternal[g] / denom).toFixed(3)),
  };
}

// ---- D. cross-category dependency analysis --------------------------------
// Count edges of each type between node-type groups (using allEdges).
const crossMap = {}; // "fromType\u0001toType\u0001edgeType" -> count
function typeOf(nodeId) {
  const n = nodeById.get(nodeId);
  return n ? n.type || 'file' : null;
}
for (const e of allEdges) {
  const ft = typeOf(e.source);
  const tt = typeOf(e.target);
  if (!ft || !tt) continue;
  const et = e.type || 'related';
  const key = ft + '\u0001' + tt + '\u0001' + et;
  crossMap[key] = (crossMap[key] || 0) + 1;
}
const crossCategoryEdges = Object.entries(crossMap).map(([k, c]) => {
  const [fromType, toType, edgeType] = k.split('\u0001');
  return { fromType, toType, edgeType, count: c };
}).sort((x, y) => y.count - x.count);

// ---- G. directory pattern matching ----------------------------------------
const DIR_PATTERNS = [
  [/^(routes|api|controllers|endpoints|handlers|routers|controller|serializers|blueprints)$/, 'api'],
  [/^(services|core|lib|domain|logic|internal|signals|composables|mailers|jobs|channels)$/, 'service'],
  [/^(models|db|data|persistence|repository|entities|entity|migrations|migration|sql|database)$/, 'data'],
  [/^(components|views|pages|ui|layouts|screens)$/, 'ui'],
  [/^(middleware|plugins|interceptors|guards)$/, 'middleware'],
  [/^(utils|helpers|common|shared|tools|templatetags|pkg)$/, 'utility'],
  [/^(config|constants|env|settings|management|commands)$/, 'config'],
  [/^(__tests__|test|tests|spec|specs|fixtures)$/, 'test'],
  [/^(types|interfaces|schemas|contracts|dtos|dto|request|response)$/, 'types'],
  [/^(hooks)$/, 'hooks'],
  [/^(store|state|reducers|actions|slices)$/, 'state'],
  [/^(assets|static|public)$/, 'assets'],
  [/^(cmd|bin)$/, 'entry'],
  [/^(src)$/, 'service'],
  [/^(docs|documentation|wiki)$/, 'documentation'],
  [/^(deploy|deployment|infra|infrastructure|k8s|kubernetes|helm|charts|terraform|tf|docker)$/, 'infrastructure'],
  [/^(\.github|\.gitlab|\.circleci)$/, 'ci-cd'],
  [/^(runtime|repo|service|scripts|launch|include|src|msg|lib)$/, null], // generic - classify per file
];

function classifyDirSegment(seg) {
  for (const [re, label] of DIR_PATTERNS) {
    if (re.test(seg)) return label;
  }
  return null;
}

function classifyFile(filePath, name) {
  const lower = name.toLowerCase();
  const path = filePath.replace(/\\/g, '/');
  // test files
  if (/^(test_|.*_test\.|.*\.test\.|.*\.spec\.|.*_spec\.|.*test\.(py|go|java)|.*test\.(cs|php))/.test(lower) ||
      /^(test_.+\.py)$/.test(lower) ||
      /tests\//.test(path)) {
    if (/\.(test|spec)\./.test(lower) || /^test_/.test(lower) || /_test\.(go|c|cpp)$/.test(lower) ||
        /test\d*\.cpp$/.test(lower) || /Test\.java$/.test(lower) || /Tests\.cs$/.test(lower)) {
      return 'test';
    }
  }
  if (/\.(d\.ts)$/.test(lower)) return 'types';
  // entry / package roots
  if (lower === '__init__.py') return 'entry';
  if (lower === '__main__.py') return 'entry';
  if ((lower === 'index.ts' || lower === 'index.js') && /\/[^/]+\/index\.(ts|js)$/.test(path)) return 'entry';
  if (lower === 'manage.py') return 'entry';
  if (lower === 'wsgi.py' || lower === 'asgi.py') return 'config';
  if (lower === 'main.go' && /\/cmd\/[^/]+\/main\.go$/.test(path)) return 'entry';
  if ((lower === 'main.rs' || lower === 'lib.rs') && /\/src\/(main|lib)\.rs$/.test(path)) return 'entry';
  if (/Application\.java$/.test(name) || /Program\.cs$/.test(name)) return 'entry';
  if (lower === 'config.ru') return 'entry';
  // language-level project config
  if (['cargo.toml', 'go.mod', 'gemfile', 'pom.xml', 'build.gradle', 'composer.json', 'package.json', 'tsconfig.json', 'pyproject.toml', 'setup.py', 'setup.cfg', 'package.xml'].includes(lower)) return 'config';
  if (/^dockerfile/i.test(lower) || /^docker-compose\./.test(lower)) return 'infrastructure';
  if (/\.(tf|tfvars)$/.test(lower)) return 'infrastructure';
  if (lower === 'makefile') return 'infrastructure';
  if (/^\.github\/workflows\//.test(path) || lower === '.gitlab-ci.yml' || lower === 'jenkinsfile') return 'ci-cd';
  if (/\.(sql)$/.test(lower)) return 'data';
  if (/\.(graphql|gql|proto)$/.test(lower)) return 'types';
  if (/\.(msg)$/.test(lower)) return 'types'; // ROS message definitions -> schema/types
  if (/\.(md|rst)$/.test(lower)) return 'documentation';
  if (/\.(yaml|yml)$/.test(lower)) return 'config';
  if (lower.endsWith('.hpp') || lower.endsWith('.h') || lower.endsWith('.hxx')) return 'entry'; // header decl
  return null;
}

const patternMatches = {};
for (const g of Object.keys(directoryGroups)) {
  // try classifying the group name itself
  let label = classifyDirSegment(g);
  if (label) {
    patternMatches[g] = label;
    continue;
  }
  // otherwise vote across the group's files
  const votes = {};
  for (const id of directoryGroups[g]) {
    const n = nodeById.get(id);
    if (!n) continue;
    const fl = classifyFile(n.filePath, n.name);
    if (!fl) continue;
    votes[fl] = (votes[fl] || 0) + 1;
  }
  const entries = Object.entries(votes).sort((x, y) => y[1] - x[1]);
  patternMatches[g] = entries.length ? entries[0][0] : null;
}

// ---- H. deployment topology detection -------------------------------------
const infraFiles = [];
let hasDockerfile = false,
  hasCompose = false,
  hasK8s = false,
  hasTerraform = false,
  hasCI = false;
for (const n of fileNodes) {
  const name = n.name.toLowerCase();
  const path = n.filePath.replace(/\\/g, '/');
  if (/^dockerfile/i.test(name) || /^dockerfile\./.test(name)) {
    hasDockerfile = true;
    infraFiles.push(n.filePath);
  }
  if (/^docker-compose\./.test(name)) {
    hasCompose = true;
    infraFiles.push(n.filePath);
  }
  if (/(^|\/)k8s\//.test(path) || /\.(k8s\.yaml|kubernetes)$/.test(name)) {
    hasK8s = true;
    infraFiles.push(n.filePath);
  }
  if (/\.(tf|tfvars)$/.test(name)) {
    hasTerraform = true;
    infraFiles.push(n.filePath);
  }
  if (/^\.github\/workflows\//.test(path) || name === '.gitlab-ci.yml' || name === 'jenkinsfile') {
    hasCI = true;
    infraFiles.push(n.filePath);
  }
}
const deploymentTopology = {
  hasDockerfile,
  hasCompose,
  hasK8s,
  hasTerraform,
  hasCI,
  infraFiles,
};

// ---- I. data pipeline detection -------------------------------------------
const schemaFiles = [];
const migrationFiles = [];
const dataModelFiles = [];
const apiHandlerFiles = [];
for (const n of fileNodes) {
  const name = n.name.toLowerCase();
  if (/\.(sql|graphql|gql|proto|prisma)$/.test(name) || /schema\.(sql|graphql|json)/.test(name)) {
    schemaFiles.push(n.filePath);
  }
  if (/(^|\/)migrations?\//.test(n.filePath) || /^(\d+_)?migration.*\.sql$/.test(name)) {
    migrationFiles.push(n.filePath);
  }
  const tags = (n.tags || []).join('|').toLowerCase();
  if (tags.includes('data-model') || /models?\//.test(n.filePath)) {
    dataModelFiles.push(n.filePath);
  }
  if (tags.includes('api-handler') || /\/(routes|controllers|endpoints|handlers)\//.test(n.filePath)) {
    apiHandlerFiles.push(n.filePath);
  }
}
const dataPipeline = { schemaFiles, migrationFiles, dataModelFiles, apiHandlerFiles };

// ---- J. documentation coverage --------------------------------------------
const groupsWithDocs = [];
const undocumentedGroups = [];
for (const g of Object.keys(directoryGroups)) {
  const hasDoc = directoryGroups[g].some((id) => {
    const n = nodeById.get(id);
    return n && (n.type === 'document' || /\.(md|rst)$/i.test(n.name));
  });
  if (hasDoc) groupsWithDocs.push(g);
  else undocumentedGroups.push(g);
}
const docCoverage = {
  groupsWithDocs: groupsWithDocs.length,
  totalGroups: Object.keys(directoryGroups).length,
  coverageRatio: Object.keys(directoryGroups).length === 0 ? 0 :
    Number((groupsWithDocs.length / Object.keys(directoryGroups).length).toFixed(3)),
  undocumentedGroups,
};

// ---- K. dependency direction ----------------------------------------------
// For every pair of groups with imports between them, mark the dominant
// dependent. We dedupe by unordered pair.
const pairMap = {}; // "A\u0001B" -> {ab, ba}
for (const { from, to, count } of interGroupImports) {
  const key = from < to ? from + '\u0001' + to : to + '\u0001' + from;
  if (!pairMap[key]) pairMap[key] = { ab: 0, ba: 0, a: from < to ? from : to, b: from < to ? to : from };
  if (from < to) pairMap[key].ab += count;
  else pairMap[key].ba += count;
}
const dependencyDirection = [];
for (const key of Object.keys(pairMap)) {
  const { ab, ba, a, b } = pairMap[key];
  if (ab === 0 && ba === 0) continue;
  if (ab > ba) dependencyDirection.push({ dependent: a, dependsOn: b, count: ab - ba });
  else if (ba > ab) dependencyDirection.push({ dependent: b, dependsOn: a, count: ba - ab });
}
dependencyDirection.sort((x, y) => y.count - x.count);

// ---- file stats -----------------------------------------------------------
const filesPerGroup = {};
for (const g of Object.keys(directoryGroups)) filesPerGroup[g] = directoryGroups[g].length;
const nodeTypeCounts = {};
for (const t of Object.keys(nodeTypeGroups)) nodeTypeCounts[t] = nodeTypeGroups[t].length;

// ---- assemble output ------------------------------------------------------
const output = {
  scriptCompleted: true,
  commonPrefix: prefix,
  directoryGroups,
  nodeTypeGroups,
  crossCategoryEdges,
  interGroupImports,
  intraGroupDensity,
  patternMatches,
  deploymentTopology,
  dataPipeline,
  docCoverage,
  dependencyDirection,
  fileStats: {
    totalFileNodes: fileNodes.length,
    filesPerGroup,
    nodeTypeCounts,
  },
  fileFanIn: fanIn,
  fileFanOut: fanOut,
};

try {
  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf8');
} catch (e) {
  fail('cannot write output JSON: ' + e.message);
}

process.exit(0);
