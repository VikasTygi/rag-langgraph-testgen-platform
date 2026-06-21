from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    planner_node,
    retriever_node,
    controlled_context_node,
    should_generate_or_stop,
    generator_node,
    validator_node,
    fixer_node,
    should_fix_or_finish,
    final_output_node,
)

from app.graph.state import TestGenerationState


def build_test_generation_graph():
    graph = StateGraph(TestGenerationState)

    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("controlled_context", controlled_context_node)
    graph.add_node("generator", generator_node)
    graph.add_node("validator", validator_node)
    graph.add_node("fixer", fixer_node)
    graph.add_node("final_output", final_output_node)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "controlled_context")

    graph.add_conditional_edges(
        "controlled_context",
        should_generate_or_stop,
        {
            "generator": "generator",
            "final_output": "final_output",
        },
    )

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

    def run(
        self,
        user_prompt: str,
        framework: str,
        top_k: int = 4,
        user: dict | None = None,
    ) -> dict:
        safe_top_k = min(top_k, 5)

        initial_state: TestGenerationState = {
            "user_prompt": user_prompt,
            "framework": framework,
            "top_k": safe_top_k,
            "user": user or {},

            "status": "started",
            "message": "",
            "missing": [],

            "plan": "",
            "retrieved_docs": [],
            "generated_code": "",
            "valid": False,
            "errors": [],
            "validation_summary": "",
            "validation_result": None,
            "fix_attempts": 0,
            "stop_generation": False,
        }

        final_state = self.workflow.invoke(initial_state)

        return {
            "status": final_state.get("status", "success"),
            "message": final_state.get("message", ""),
            "missing": final_state.get("missing", []),

            "framework": final_state["framework"],
            "user_prompt": final_state["user_prompt"],
            "plan": final_state.get("plan", ""),
            "retrieved_context_count": len(final_state.get("retrieved_docs", [])),
            "generated_code": final_state.get("generated_code"),

            "valid": final_state.get("valid", False),
            "errors": final_state.get("errors", []),
            "fix_attempts": final_state.get("fix_attempts", 0),
            "validation_summary": final_state.get("validation_summary", ""),
            "validation_result": final_state.get("validation_result"),
        }