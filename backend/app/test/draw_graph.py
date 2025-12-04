import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph.graph import StateGraph, END
from app.models.state import AgentState

def build_graph_for_visualization() -> StateGraph:
    """Build the graph structure for visualization without initializing agents"""
    workflow = StateGraph(AgentState)
    
    # Add nodes (using placeholder functions)
    workflow.add_node("fetch_market_data", lambda state: state)
    workflow.add_node("bull_argues", lambda state: state)
    workflow.add_node("bear_argues", lambda state: state)
    workflow.add_node("check_debate_rounds", lambda state: state)
    workflow.add_node("referee_decides", lambda state: state)
    workflow.add_node("execute_hedera", lambda state: state)
    
    # Set entry point
    workflow.set_entry_point("fetch_market_data")
    
    # Add edges
    workflow.add_edge("fetch_market_data", "bull_argues")
    workflow.add_edge("bull_argues", "bear_argues")
    workflow.add_edge("bear_argues", "check_debate_rounds")
    
    # Conditional edge for debate rounds
    workflow.add_conditional_edges(
        "check_debate_rounds",
        lambda state: "continue" if state.get('current_round', 0) < state.get('max_rounds', 2) else "conclude",
        {
            "continue": "bull_argues",
            "conclude": "referee_decides"
        }
    )
    
    workflow.add_edge("referee_decides", "execute_hedera")
    workflow.add_edge("execute_hedera", END)
    
    return workflow.compile()

# Build the graph for visualization
compiled_graph = build_graph_for_visualization()

# Get the graph representation and generate PNG
png_data = compiled_graph.get_graph().draw_mermaid_png()

output_path = os.path.join(os.path.dirname(__file__), "agent_graph.png")
with open(output_path, "wb") as f:
    f.write(png_data)

print(f"Graph saved to {output_path}")