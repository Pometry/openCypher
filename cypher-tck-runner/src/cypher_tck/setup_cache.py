"""Setup graphs recorded on a build that runs Cypher writes, replayed on one that refuses them.

A setup the CREATE translator cannot handle (UNWIND, MATCH ... CREATE, date() values) runs through the
engine. On a build with writes, `record` saves what the step added or changed; on a build without,
`replay` re-adds it with add_node/add_edge. Entries are keyed by the scenario's setup queries so far.
"""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any

CACHE = Path(__file__).resolve().parents[2] / "setup-cache"


def _key(queries: list[str]) -> Path:
    return CACHE / (hashlib.sha1("\x00".join(queries).encode()).hexdigest() + ".pickle")


def snapshot(graph: Any) -> tuple[dict, dict]:
    """Nodes `{id: (type, props)}` and edges `{(src, dst, layer): props}` of `graph`."""
    nodes = {n.id: (n.node_type, n.properties.as_dict()) for n in graph.nodes}
    edges = {
        (e.src.id, e.dst.id, layer): e.layer(layer).properties.as_dict()
        for e in graph.edges
        for layer in e.layer_names
    }
    return nodes, edges


def record(queries: list[str], before: tuple[dict, dict], graph: Any) -> None:
    """Save what the setup step changed; nothing when it deleted anything."""
    (nodes0, edges0), (nodes1, edges1) = before, snapshot(graph)
    if nodes0.keys() - nodes1.keys() or edges0.keys() - edges1.keys():
        return
    delta = (
        {k: v for k, v in nodes1.items() if nodes0.get(k) != v},
        {k: v for k, v in edges1.items() if edges0.get(k) != v},
    )
    try:
        data = pickle.dumps(delta)
    except Exception:  # noqa: BLE001 - a value the engine returns that pickle cannot hold
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    _key(queries).write_bytes(data)


def replay(queries: list[str], graph: Any) -> bool:
    """Re-add a recorded setup step to `graph`; False when none was recorded."""
    path = _key(queries)
    if not path.exists():
        return False
    nodes, edges = pickle.loads(path.read_bytes())
    for nid, (node_type, props) in nodes.items():
        graph.add_node(0, nid, properties=props, node_type=node_type)
    for (src, dst, layer), props in edges.items():
        graph.add_edge(0, src, dst, properties=props, layer=layer)
    return True
