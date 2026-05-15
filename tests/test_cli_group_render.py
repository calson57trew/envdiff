"""Unit tests for cli_group rendering helpers."""
from __future__ import annotations

from envdiff.cli_group import _render_text
from envdiff.grouper import GroupReport, KeyGroup


def _make_report(**groups) -> GroupReport:
    report = GroupReport()
    for prefix, keys in groups.items():
        report.groups[prefix] = KeyGroup(prefix=prefix, keys=list(keys))
    return report


def test_render_text_shows_prefix_header():
    report = _make_report(DB=["DB_HOST", "DB_PORT"])
    text = _render_text(report)
    assert "[DB]" in text
    assert "(2 keys)" in text


def test_render_text_keys_indented():
    report = _make_report(DB=["DB_HOST"])
    text = _render_text(report)
    assert "  DB_HOST" in text


def test_render_text_ungrouped_section():
    report = GroupReport(ungrouped=["PORT", "DEBUG"])
    text = _render_text(report)
    assert "[ungrouped]" in text
    assert "  PORT" in text
    assert "  DEBUG" in text


def test_render_text_empty_report():
    report = GroupReport()
    text = _render_text(report)
    assert "No keys found" in text


def test_render_text_multiple_groups_sorted():
    report = _make_report(ZZ=["ZZ_A"], AA=["AA_B"])
    text = _render_text(report)
    aa_pos = text.index("[AA]")
    zz_pos = text.index("[ZZ]")
    assert aa_pos < zz_pos


def test_render_text_keys_within_group_sorted():
    report = _make_report(DB=["DB_PORT", "DB_HOST", "DB_NAME"])
    text = _render_text(report)
    host_pos = text.index("DB_HOST")
    name_pos = text.index("DB_NAME")
    port_pos = text.index("DB_PORT")
    assert host_pos < name_pos < port_pos
