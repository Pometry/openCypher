"""Behave environment configuration and hooks.

This module sets up the test environment for each scenario, including
initializing the graph database and storing scenario context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from raphtory import Graph

if TYPE_CHECKING:
    from behave.model import Scenario
    from behave.runner import Context

# ── ReportPortal integration ──────────────────────────────────────────────────
# behave-reportportal streams live results to a local RP instance.
# The agent is created lazily so tests run normally when RP is not configured.
try:
    from behave_reportportal.behave_agent import BehaveAgent, create_rp_service
    from behave_reportportal.config import Config
    _RP_AVAILABLE = True
except ImportError:
    _RP_AVAILABLE = False


def _get_agent(context: "Context") -> "BehaveAgent | None":
    """Return the BehaveAgent stored on the context, or None if RP is disabled."""
    return getattr(context, "rp_agent", None)


def _load_rp_config() -> "Config | None":
    """Read [report_portal] from behave.ini next to this file and return a Config."""
    import os
    from configparser import ConfigParser

    ini_path = os.path.join(os.path.dirname(__file__), "behave.ini")
    cp = ConfigParser()
    if not cp.read(ini_path):
        return None
    if not cp.has_section("report_portal"):
        return None
    rp_cfg = dict(cp["report_portal"])
    api_key = rp_cfg.get("api_key", "")
    if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE":
        return None
    return Config(**rp_cfg)


def before_all(context: Context) -> None:
    """Initialize the test environment before any scenarios run."""
    context.graph_db = Graph()

    # Start a ReportPortal launch (no-op if RP is not configured)
    context.rp_agent = None
    if _RP_AVAILABLE:
        try:
            cfg = _load_rp_config()
            if cfg:
                rp_service = create_rp_service(cfg)
                context.rp_agent = BehaveAgent(cfg, rp_service)
                context.rp_agent.start_launch(context)
                print("[RP] Streaming results to ReportPortal")
        except Exception as exc:
            print(f"[RP] Could not connect to ReportPortal, skipping: {exc}")


def before_scenario(context: Context, scenario: Scenario) -> None:
    """Set up state before each scenario."""
    # Start each scenario with a fresh graph
    context.graph_db = Graph()

    # Initialize scenario-specific state
    context.query_result = None
    context.last_query = None
    context.expected_error = None
    context.actual_error = None

    agent = _get_agent(context)
    if agent:
        agent.start_scenario(context, scenario)


def after_scenario(context: Context, scenario: Scenario) -> None:
    """Clean up after each scenario."""
    agent = _get_agent(context)
    if agent:
        agent.finish_scenario(context, scenario)



def before_step(context: Context, step: Any) -> None:
    """Hook called before each step."""
    agent = _get_agent(context)
    if agent:
        agent.start_step(context, step)


def after_step(context: Context, step: Any) -> None:
    """Hook called after each step."""
    agent = _get_agent(context)
    if agent:
        agent.finish_step(context, step)


def after_all(context: Context) -> None:
    """Finish the ReportPortal launch after all scenarios complete."""
    agent = _get_agent(context)
    if agent:
        agent.finish_launch(context)
