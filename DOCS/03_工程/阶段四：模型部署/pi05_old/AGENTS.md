# AGENTS.md

## This project: pi05 (Pi0.5 VLA deploy + train)

Pi05 is a Pi0.5 Vision-Language-Action (VLA) robotics package, including:
- **`pi05/common/`** — shared library (action codec, state codec, image preprocess, config schema, bundle, ros topics)
- **`pi05/deploy/`** — ROS2 deployment runtime (CLI / config / model loader / 3 ROS nodes / inference worker / observation collector / control loop / safety guard / shared buffer)
- **`pi05/train/`** — Pi0.5 LoRA fine-tuning (CLI / engine / dataset / batches / checkpoints / builders / utils)
- **`tools/mcap_to_lerobot_v3.py`** — Octopus ROS2 .mcap → LeRobot v3 dataset converter (action 14D, state 26D, inspire_hand_v1 tactile)
- **`third_party/lerobot/`** — vendored LeRobot reference: docs, examples (teleop lifecycles, training tutorials, HIL, RTC, async inference, DROID porting)

## ⛔ Mandatory: read the knowledge graph first

This project has a pre-built knowledge graph at `graphify-out/`. **Before answering any question about how this program works, querying an API, debugging, or proposing changes, you must consult the graph.** Skipping the graph is a workflow violation.

### Why

The graph is the result of `/graphify` running over the entire `pi05/` + `tools/` + `third_party/lerobot/docs` + `third_party/lerobot/examples` corpus (122 files, 146k words, 1067 nodes, 1880 edges, 69 communities). It costs ~945 tokens per query versus ~195k tokens to re-read the codebase — a **206× reduction** — and surfaces cross-file relationships you would miss by reading one file at a time.

### What to read, in order

1. **`graphify-out/GRAPH_REPORT.md`** — plain-language audit report. Top 5 communities are usually enough to orient.
2. **`graphify-out/graph.html`** — interactive browser visualization. Communities are color-coded. Useful when debugging "where does X live?".
3. **`graphify-out/graph.json`** — raw graph data (NetworkX node-link JSON). Use this for programmatic queries.

## How to query the graph

The graphify Python package is already installed. Use the scripts in the snippets below (they're part of the graphify skill — copy-paste, don't reinvent).

### `query` — "What is X connected to?" (BFS, broad context)

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from networkx.readwrite import json_graph
import networkx as nx
from pathlib import Path

data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')

question = 'YOUR QUESTION HERE'
terms = [t.lower() for t in question.split() if len(t) > 3]

scored = []
for nid, ndata in G.nodes(data=True):
    label = ndata.get('label', '').lower()
    score = sum(1 for t in terms if t in label)
    if score > 0:
        scored.append((score, nid))
scored.sort(reverse=True)
start_nodes = [nid for _, nid in scored[:3]]

frontier = set(start_nodes)
subgraph_nodes = set(start_nodes)
subgraph_edges = []
for _ in range(3):
    next_frontier = set()
    for n in frontier:
        for neighbor in G.neighbors(n):
            if neighbor not in subgraph_nodes:
                next_frontier.add(neighbor)
                subgraph_edges.append((n, neighbor))
    subgraph_nodes.update(next_frontier)
    frontier = next_frontier

for nid in sorted(subgraph_nodes, key=lambda n: G.degree(n), reverse=True)[:20]:
    d = G.nodes[nid]
    print(f'NODE {d.get(\"label\", nid)} [src={d.get(\"source_file\",\"\")} loc={d.get(\"source_location\",\"\")}]')
for u, v in subgraph_edges[:30]:
    d = G.edges[u, v]
    print(f'EDGE {G.nodes[u].get(\"label\",u)} --{d.get(\"relation\",\"\")}--> {G.nodes[v].get(\"label\",v)}')
"
```

### `path` — shortest path between two concepts

```bash
$(cat graphify-out/.graphify_python) -c "
import json, networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path
data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')
src, tgt = 'CONCEPT_A', 'CONCEPT_B'
def find(t):
    t = t.lower()
    return max(((sum(1 for w in t.split() if w in G.nodes[n].get('label','').lower()), n) for n in G.nodes()), default=(0,None))[1]
a, b = find(src), find(tgt)
if a and b:
    p = nx.shortest_path(G, a, b)
    print(f'Path ({len(p)-1} hops):')
    for i, n in enumerate(p):
        print(f'  {G.nodes[n].get(\"label\", n)}')
"
```

### `explain` — plain-language explanation of a single node

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from networkx.readwrite import json_graph
from pathlib import Path
data = json.loads(Path('graphify-out/graph.json').read_text())
G = json_graph.node_link_graph(data, edges='links')
term = 'NODE_NAME'
nid = max(G.nodes(), key=lambda n: sum(1 for w in term.lower().split() if w in G.nodes[n].get('label','').lower()))
d = G.nodes[nid]
print(f'NODE: {d.get(\"label\", nid)}')
print(f'  source: {d.get(\"source_file\",\"\")}')
print(f'  degree: {G.degree(nid)}')
print('CONNECTIONS:')
for nb in G.neighbors(nid):
    e = G.edges[nid, nb]
    print(f'  --{e.get(\"relation\",\"\")}--> {G.nodes[nb].get(\"label\", nb)} [{e.get(\"confidence\",\"\")}]')
"
```

## Top 10 god nodes (read these first when orienting)

These are the most-connected abstractions in the codebase — touching them affects the most other code:

1. `Pi05CommandTopics` (32 edges) — ROS2 topic constants for VLA command stream
2. `Pi05ObservationTopics` (32 edges) — ROS2 topic constants for observation stream
3. `SharedBuffer` (31 edges) — thread-safe handoff between observation collector and inference worker
4. `_convert_one_mcap_into_dataset()` (30 edges) — heart of the MCAP → LeRobot v3 converter
5. `_deploy_from_mapping()` (25 edges) — bundle→runtime loader
6. `Pi05VlaDeployNode` (24 edges) — main ROS2 node that runs the VLA inference loop
7. `ControlLoop` (24 edges) — real-time control loop driver
8. `ObservationSnapshot` (24 edges) — frozen observation struct passed through the pipeline
9. `from_mapping()` (23 edges) — generic typed-config-from-dict factory
10. `CommandMuxNode` (22 edges) — teleop/VLA command multiplexer

## Most surprising cross-file connections

The graph surfaced these relationships that wouldn't be obvious from reading files linearly:

- `CommandMuxNode` and the bridge node both reach into `DeployConfig` (typed schema in `pi05/common/`) — the deploy config is the actual contract between ROS2 nodes and the CLI, not just an init parameter.
- `trainer.py` reaches into `pi05/common/config/schema.py`'s `ExperimentConfig` from at least 4 different call sites (training loop, builders, utils, checks) — `ExperimentConfig` is genuinely the train-side counterpart of `DeployConfig`.
- The MCAP converter's `_convert_one_mcap_into_dataset()` (the keystone 30-edge node) sits in a community that bridges `pi05/train/data/` (where the resulting dataset is consumed) and `pi05/common/data/normalization.py` (where the q99.5 fixed-scale norm stats are written) — **the converter is the only bridge between the deploy-side data shape and the train-side data shape**.

## Community structure (69 clusters)

Top communities by size (from `graphify-out/GRAPH_REPORT.md`):

| ID | Size | Label |
|----|------|-------|
| 0 | 116 | Action encoding (Pi0.5 common) |
| 1 | 97 | Training engine builders (optimizer/lr/dataloader) |
| 2 | 80 | MCAP to LeRobot v3 conversion |
| 3 | 62 | LeRobot hardware and contribution docs |
| 4 | 57 | Pi0.5 model builder with LoRA |
| 5 | 53 | HIL data collection orchestration |
| 6 | 51 | Deploy bundle and safety modes |
| 7 | 44 | Bundle I/O (manifest, normalizers, tactile preprocess) |
| 8 | 43 | DROID TFDS to LeRobot porting pipeline |
| 9 | 42 | Deploy CLI and ROS2 config schemas |
| 11 | 36 | LeRobot platform concepts (policies, robots, hub) |
| 12 | 32 | RTC offline dataset evaluation |
| 13 | 27 | RTC real-robot evaluation |
| 14 | 26 | LeRobot training tutorials |

Full community list in `graphify-out/GRAPH_REPORT.md` §Communities.

## Refresh the graph when

- New files added under `pi05_test/pi05/`, `pi05_test/tools/`, or `pi05_test/third_party/lerobot/{docs,examples}/`
- A god node changes (e.g., `Pi05VlaDeployNode`, `SharedBuffer`, `_convert_one_mcap_into_dataset`)
- The action/state schema changes (currently action=14D, state=26D, tactile layout=inspire_hand_v1)
- A new deploy CLI or ROS2 node is added
- The training loop's interface to the dataset changes

### Incremental refresh (recommended)

```bash
/graphify --update
```

This re-extracts only changed files and merges into `graphify-out/graph.json`. Code-only changes skip the LLM subagents.

### Full rebuild

```bash
/graphify
```

Required if you change the scope (e.g., add a new top-level directory).

## Graph location & cost

- **Corpus**: 122 files · 146,352 words · scope = `pi05/` + `tools/` + `third_party/lerobot/{docs,examples,*.md}`
- **Graph**: 1067 nodes · 1880 edges · 69 communities · 21 hyperedges
- **Token reduction**: 206.5× per query (945 vs 195,136 tokens naive)
- **Outputs** (all in `graphify-out/`):
  - `GRAPH_REPORT.md` — audit report (the one to read first)
  - `graph.html` — interactive browser viz (945 KB)
  - `graph.json` — raw NetworkX node-link JSON (1.2 MB)
  - `cost.json` — cumulative token cost
  - `manifest.json` — file manifest for `--update`
  - `cache/` — semantic extraction cache (per-file)
- **Edge confidence distribution**: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS (avg INFERRED confidence 0.5 — treat as architectural hints, not facts)

## Honesty rules for graph use

- The graph is a **map, not the territory**. When answering, always cite the `source_file` and `source_location` from the edge's evidence field. If the graph lacks the answer, say so — do not hallucinate edges.
- INFERRED edges (14% of total) are architectural hints, not facts. The graph's source says they "reason about each edge individually" with confidence scores 0.4–0.9. Be explicit when citing one.
- The semantic subagent chunks are bound to the source files as of the last `/graphify` run. If a file has been heavily edited since, the edge evidence may point to outdated line numbers.
