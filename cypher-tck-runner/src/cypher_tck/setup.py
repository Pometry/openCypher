"""Builds TCK setup graphs from CREATE-only Cypher through the Raphtory API.

clam refuses Cypher writes, so `Given having executed: CREATE ...` is translated here instead.
Nodes and edges are added at time 0; several labels become one `A:B` node type, as the old
CREATE did. Setups that use anything but CREATE patterns of literals return False.
"""

from __future__ import annotations

import itertools
import re
from typing import Any

_TOKEN = re.compile(
    r"""\s*(?:
      (?P<str>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
    | (?P<num>-?(?:\d+\.\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?|\d+[eE][-+]?\d+|0x[0-9a-fA-F]+|\d+))
    | (?P<name>`[^`]*`|[A-Za-z_][A-Za-z0-9_]*)
    | (?P<skip>//[^\n]*|;)
    | (?P<sym><-|->|[-()\[\]{}:,])
    )""",
    re.X,
)
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "\\": "\\", "'": "'", '"': '"'}


class Unsupported(Exception):
    pass


def _tokens(text: str) -> list[tuple[str, str]]:
    out, pos, text = [], 0, text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise Unsupported(text[pos : pos + 20])
        kind = m.lastgroup
        if kind != "skip":
            out.append((kind, m.group(kind)))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return out


class _Parser:
    def __init__(self, text: str) -> None:
        self.toks = _tokens(text)
        self.i = 0

    def peek(self, value: str | None = None) -> bool:
        if self.i >= len(self.toks):
            return False
        return value is None or self.toks[self.i][1] == value

    def take(self, value: str | None = None) -> tuple[str, str]:
        if not self.peek(value):
            raise Unsupported(f"expected {value}")
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def name(self) -> str:
        kind, text = self.take()
        if kind != "name":
            raise Unsupported(text)
        return text.strip("`")

    def value(self) -> Any:
        kind, text = self.take()
        if kind == "str":
            return re.sub(r"\\(u[0-9a-fA-F]{4}|.)", _unescape, text[1:-1])
        if kind == "num":
            if text.lower().lstrip("-").startswith("0x"):
                return int(text, 16)
            return float(text) if any(c in text for c in ".eE") else int(text)
        if kind == "name" and text.lower() in ("true", "false", "null"):
            return {"true": True, "false": False, "null": None}[text.lower()]
        if text == "[":
            items = []
            while not self.peek("]"):
                items.append(self.value())
                if not self.peek("]"):
                    self.take(",")
            self.take("]")
            return items
        raise Unsupported(text)

    def props(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if not self.peek("{"):
            return out
        self.take("{")
        while not self.peek("}"):
            key = self.name()
            self.take(":")
            out[key] = self.value()
            if not self.peek("}"):
                self.take(",")
        self.take("}")
        return {k: v for k, v in out.items() if v is not None}

    def node(self) -> tuple[str | None, list[str], dict[str, Any]]:
        self.take("(")
        var = self.name() if self.peek() and self.toks[self.i][0] == "name" else None
        labels = []
        while self.peek(":"):
            self.take(":")
            labels.append(self.name())
        props = self.props()
        self.take(")")
        return var, labels, props

    def rel(self) -> tuple[bool, str, dict[str, Any]]:
        incoming = self.peek("<-")
        self.take("<-" if incoming else "-")
        self.take("[")
        if self.peek() and self.toks[self.i][0] == "name":
            self.name()
        self.take(":")
        rel_type = self.name()
        props = self.props()
        self.take("]")
        self.take("-" if incoming else "->")
        return incoming, rel_type, props


def _unescape(m: re.Match[str]) -> str:
    esc = m.group(1)
    return chr(int(esc[1:], 16)) if esc.startswith("u") else _ESCAPES.get(esc, esc)


def create_graph(graph: Any, query: str) -> bool:
    """Apply a CREATE-only setup query to `graph`; False if it uses anything else."""
    try:
        parser = _Parser(query)
        ops: list[tuple] = []
        bound: dict[str, str] = {}
        ids = (f"n{i}" for i in itertools.count(graph.count_nodes()))

        def node_id() -> str:
            var, labels, props = parser.node()
            if var in bound:
                if labels or props:
                    raise Unsupported("rebinding a bound node")
                return bound[var]
            nid = next(ids)
            if var:
                bound[var] = nid
            ops.append(("node", nid, props, ":".join(labels) or None))
            return nid

        while parser.peek():
            kind, word = parser.take()
            if kind != "name" or word.upper() != "CREATE":
                raise Unsupported(word)
            while True:
                left = node_id()
                while parser.peek("-") or parser.peek("<-"):
                    incoming, rel_type, props = parser.rel()
                    right = node_id()
                    src, dst = (right, left) if incoming else (left, right)
                    ops.append(("edge", src, dst, props, rel_type))
                    left = right
                if not parser.peek(","):
                    break
                parser.take(",")
    except Unsupported:
        return False
    for op in ops:
        if op[0] == "node":
            graph.add_node(0, op[1], properties=op[2], node_type=op[3])
        else:
            graph.add_edge(0, op[1], op[2], properties=op[3], layer=op[4])
    return True
