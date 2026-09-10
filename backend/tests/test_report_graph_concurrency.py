"""Deterministic regression test for the LangGraph concurrent-state-update fix in
agents/report_generator.py (see commit "Fix LangGraph concurrent-state-update crash in
multi-agent report sections"). Needs only langgraph + pytest -- no langchain, no LLM
provider packages, no API keys, no network calls.

Deliberately does NOT import agents.report_generator: that module's top-level imports
cascade into every real agent (exploration/sql/roi/budget/kpi/market/compiler), which
pull in langchain-groq, langchain-google-genai, tavily-python etc -- none of which this
test needs, and none of which should be a precondition for verifying a LangGraph state-
merge property. Instead, section_agent_mapping is extracted directly from the source
file via `ast`, so this test is checking the real, current mapping (not a hand-copied
duplicate that could silently drift) without executing any of report_generator.py.

The two node patterns below (buggy: return the whole mutated state; fixed: return only
the owned key) are reproductions of report_generator.py's actual before/after code
(compare against `git show <fix commit>^:backend/agents/report_generator.py` and the
current file) -- reproduced here rather than imported so the test doesn't depend on the
heavy agent import chain.

Run (from backend/, with pytest and langgraph installed):
    python -m pytest tests/test_report_graph_concurrency.py -v
"""
import ast
import os
from typing import Annotated, Any, Dict, List, TypedDict

import pytest
from langgraph.errors import InvalidUpdateError
from langgraph.graph import END, StateGraph

REPORT_GENERATOR_SOURCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agents", "report_generator.py"
)

AGENT_KEYS = ["exploration_agent", "sql_agent", "roi_agent", "budget_agent", "kpi_agent", "market_agent"]
NODE_NAME = {
    "exploration_agent": "exploration", "sql_agent": "sql", "roi_agent": "roi",
    "budget_agent": "budget", "kpi_agent": "kpi", "market_agent": "market",
}
RESULT_KEY = {
    "exploration_agent": "exploration_results", "sql_agent": "sql_results", "roi_agent": "roi_results",
    "budget_agent": "budget_results", "kpi_agent": "kpi_results", "market_agent": "market_results",
}


def load_section_agent_mapping() -> Dict[str, List[str]]:
    """Extract the literal dict assigned to self.section_agent_mapping inside
    SupervisorAgent.__init__, straight from the source file, via ast -- so this test
    can never silently drift from the mapping report_generator.py actually uses."""
    tree = ast.parse(open(REPORT_GENERATOR_SOURCE, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr == "section_agent_mapping"
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    return ast.literal_eval(node.value)
    raise AssertionError(f"self.section_agent_mapping assignment not found in {REPORT_GENERATOR_SOURCE}")


# Structurally mirrors agents.report_generator.AgentState (same field names/shape) --
# redefined locally rather than imported to avoid that module's import chain.
class AgentState(TypedDict):
    messages: Annotated[List[Any], "Chat messages"]
    current_section: str
    current_question: str
    exploration_results: Dict
    sql_results: Dict
    roi_results: Dict
    budget_results: Dict
    kpi_results: Dict
    market_results: Dict
    final_answer: str


def make_state(section, question="test question"):
    return AgentState(
        messages=[], current_section=section, current_question=question,
        exploration_results={}, sql_results={}, roi_results={}, budget_results={},
        kpi_results={}, market_results={}, final_answer="",
    )


def build_workflow(mapping: Dict[str, List[str]], buggy: bool) -> StateGraph:
    workflow = StateGraph(AgentState)

    def supervisor(state):
        return state

    def make_buggy_node(agent_key, result_key):
        def node(state):
            if agent_key in mapping[state["current_section"]]:
                # Pre-fix pattern: mutate and return the WHOLE shared state.
                state[result_key] = f"stub-result:{agent_key}"
                return state
            # Matches the real pre-fix code exactly: inactive branches fell through
            # with no explicit return (implicit None), rather than returning state.
            return None
        return node

    def make_fixed_node(agent_key, result_key):
        def node(state):
            if agent_key in mapping[state["current_section"]]:
                # Current pattern: return only the single key this node owns.
                return {result_key: f"stub-result:{agent_key}"}
            return {}
        return node

    def compile_buggy(state):
        state["final_answer"] = "compiled"
        return state

    def compile_fixed(state):
        return {"final_answer": "compiled"}

    workflow.set_entry_point("supervisor")
    workflow.add_node("supervisor", supervisor)
    for agent_key in AGENT_KEYS:
        node_name = NODE_NAME[agent_key]
        node_fn = make_buggy_node(agent_key, RESULT_KEY[agent_key]) if buggy else make_fixed_node(agent_key, RESULT_KEY[agent_key])
        workflow.add_node(node_name, node_fn)
        workflow.add_edge("supervisor", node_name)
        workflow.add_edge(node_name, "compiler")
    workflow.add_node("compiler", compile_buggy if buggy else compile_fixed)
    workflow.add_edge("compiler", END)

    return workflow


def multi_agent_sections(mapping):
    return {s: agents for s, agents in mapping.items() if len(agents) >= 2}


def test_section_agent_mapping_has_four_multi_agent_sections():
    """The real number behind the "N of 7 sections" claim in the fix's commit message."""
    mapping = load_section_agent_mapping()
    multi = multi_agent_sections(mapping)
    assert len(mapping) == 7
    assert set(multi) == {"business_context", "marketing_performance", "performance_drivers", "marketing_roi"}
    assert len(multi) == 4


def test_pre_fix_pattern_raises_concurrent_update_error():
    mapping = load_section_agent_mapping()
    chain = build_workflow(mapping, buggy=True).compile()

    for section in multi_agent_sections(mapping):
        with pytest.raises(InvalidUpdateError, match="Can receive only one value per step"):
            chain.invoke(make_state(section))


def test_pre_fix_pattern_does_not_raise_for_single_agent_sections():
    """Sanity check that the bug is specifically about concurrent writers -- sections
    with exactly one active agent never had this crash."""
    mapping = load_section_agent_mapping()
    chain = build_workflow(mapping, buggy=True).compile()

    single_agent_sections = {s: a for s, a in mapping.items() if len(a) < 2}
    assert len(single_agent_sections) == 3
    for section in single_agent_sections:
        result = chain.invoke(make_state(section))
        assert result["final_answer"] == "compiled"


def test_current_pattern_merges_cleanly_for_all_seven_sections():
    mapping = load_section_agent_mapping()
    chain = build_workflow(mapping, buggy=False).compile()

    for section in mapping:
        result = chain.invoke(make_state(section))
        assert result["final_answer"] == "compiled"
