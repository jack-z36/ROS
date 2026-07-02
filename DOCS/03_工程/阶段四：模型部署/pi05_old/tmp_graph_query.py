import json
from networkx.readwrite import json_graph
from pathlib import Path
G = json_graph.node_link_graph(json.loads(Path('01-doing/pi05_test/graphify-out/graph.json').read_text(encoding='utf-8')))
terms = ['Action encoding', 'ObservationSnapshot', 'DeployConfig', 'Pi05VlaDeployNode', 'SafetyGuard', 'ObservationCollector', 'state codec', 'action codec']
for term in terms:
    scored=[]
    words=term.lower().split()
    for nid,d in G.nodes(data=True):
        label=(d.get('label') or '').lower(); src=(d.get('source_file') or '').lower()
        score=sum(1 for w in words if w in label or w in src)
        if term.lower() in label: score+=4
        if score: scored.append((score,G.degree(nid),d.get('label'),d.get('source_file'),d.get('source_location')))
    scored.sort(reverse=True)
    print('\n==',term,'==')
    for row in scored[:5]:
        print(row)
