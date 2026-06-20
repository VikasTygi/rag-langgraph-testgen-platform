from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    final_output_node,
    fixer_node,
    generator_node,
    planner_node,
    retriever_node,
    should_fix_or_finish,
    validator_node,
)
from app.graph.state import TestGenerationState


def build_test_generation_graph():
    graph = StateGraph(TestGenerationState)

    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("generator", generator_node)
    graph.add_node("validator", validator_node)
    graph.add_node("fixer", fixer_node)
    graph.add_node("final_output", final_output_node)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "generator")
    graph.add_edge("generator", "validator")

    graph.add_conditional_edges(
        "validator",
        should_fix_or_finish,
        {
            "fixer": "fixer",
            "final_output": "final_output",
        },
    )

    graph.add_edge("fixer", "validator")
    graph.add_edge("final_output", END)

    return graph.compile()


class TestGenerationWorkflow:
    def __init__(self):
        self.workflow = build_test_generation_graph()

    def run(self, user_prompt: str, framework: str, top_k: int = 4) -> dict:
        initial_state: TestGenerationState = {
            "user_prompt": user_prompt,
            "framework": framework,
            "top_k": top_k,
            "plan": "",
            "retrieved_docs": [],
            "generated_code": "",
            "valid": False,
            "errors": [],
            "validation_summary": "",
            "fix_attempts": 0,
        }

        final_state = self.workflow.invoke(initial_state)

        return {
            "framework": final_state["framework"],
            "user_prompt": final_state["user_prompt"],
            "plan": final_state["plan"],
            "retrieved_context_count": len(final_state["retrieved_docs"]),
            "generated_code": final_state["generated_code"],
            "valid": final_state["valid"],
            "errors": final_state["errors"],
            "fix_attempts": final_state["fix_attempts"],
            "validation_summary": final_state["validation_summary"],
        }