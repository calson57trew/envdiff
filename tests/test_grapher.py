"""Tests for envdiff.grapher."""
from __future__ import annotations

import pytest

from envdiff.grapher import EnvGraph, GraphNode, build_graph, _extract_refs


@pytest.fixture
def simple_env() -> dict:
    return {
        "HOST": "localhost",
        "PORT": "5432",
        "DSN": "postgres://${HOST}:${PORT}/db",
        "REPLICA_DSN": "${DSN}?sslmode=require",
        "UNRELATED": "hello",
    }


def test_extract_refs_braced():
    assert _extract_refs("${FOO} and ${BAR}") == {"FOO", "BAR"}


def test_extract_refs_unbraced():
    assert _extract_refs("$FOO/$BAR") == {"FOO", "BAR"}


def test_extract_refs_none_returns_empty():
    assert _extract_refs(None) == set()


def test_extract_refs_no_refs():
    assert _extract_refs("plain value") == set()


def test_build_graph_node_count(simple_env):
    graph = build_graph(simple_env)
    assert set(graph.nodes.keys()) == set(simple_env.keys())


def test_build_graph_dsn_depends_on_host_and_port(simple_env):
    graph = build_graph(simple_env)
    assert graph.nodes["DSN"].depends_on == frozenset({"HOST", "PORT"})


def test_build_graph_replica_depends_on_dsn(simple_env):
    graph = build_graph(simple_env)
    assert graph.nodes["REPLICA_DSN"].depends_on == frozenset({"DSN"})


def test_build_graph_host_depended_by_dsn(simple_env):
    graph = build_graph(simple_env)
    assert "DSN" in graph.nodes["HOST"].depended_by


def test_build_graph_roots(simple_env):
    graph = build_graph(simple_env)
    roots = graph.roots()
    assert "HOST" in roots
    assert "PORT" in roots
    assert "UNRELATED" in roots
    assert "DSN" not in roots


def test_build_graph_leaves(simple_env):
    graph = build_graph(simple_env)
    leaves = graph.leaves()
    # REPLICA_DSN is not depended on by anyone
    assert "REPLICA_DSN" in leaves
    assert "UNRELATED" in leaves


def test_build_graph_ignores_external_refs():
    env = {"A": "${EXTERNAL_VAR}", "B": "hello"}
    graph = build_graph(env)
    # EXTERNAL_VAR is not in env, so A has no recorded deps
    assert graph.nodes["A"].depends_on == frozenset()


def test_graph_as_dict_structure(simple_env):
    graph = build_graph(simple_env)
    d = graph.as_dict()
    assert "DSN" in d
    assert "depends_on" in d["DSN"]
    assert "HOST" in d["DSN"]["depends_on"]


def test_graph_get_returns_node(simple_env):
    graph = build_graph(simple_env)
    node = graph.get("HOST")
    assert isinstance(node, GraphNode)
    assert node.key == "HOST"


def test_graph_get_missing_returns_none(simple_env):
    graph = build_graph(simple_env)
    assert graph.get("NONEXISTENT") is None


def test_build_graph_empty_env():
    graph = build_graph({})
    assert graph.nodes == {}
    assert graph.roots() == []
    assert graph.leaves() == []
