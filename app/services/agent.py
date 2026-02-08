from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, trim_messages
from app.core.config import settings
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode, tools_condition

# 1. Define the State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    # We keep these for frontend tracking
    current_task: str
    status: str

# 2. Define and Bind Tools
# Tavily is excellent for high-quality, AI-ready search results
search_tool = TavilySearch(max_results=3, tavily_api_key=settings.TAVILY_API_KEY)
tools = [search_tool]

# Initialize LLM and "bind" the tools to it
# temperature=0 is recommended for tool use to ensure precision
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0 
).bind_tools(tools)

# 3. Define the Nodes
async def researcher_node(state: AgentState):
    """
    The agent node: It decides whether to use a tool or provide a final answer.
    """
    # Trim to keep within token limits and maintain performance
    selected_messages = trim_messages(
        state["messages"], 
        max_tokens=1000,
        strategy="last",
        token_counter=len # Simple counter, or use a proper tokenizer
    )
    
    response = await llm.ainvoke(selected_messages)
    
    # We return the AI response. 
    # If it contains tool_calls, the conditional edge will handle it.
    return {
        "messages": [response],
        "status": "researching" if response.tool_calls else "answering"
    }

# 4. Build the Graph
workflow = StateGraph(AgentState)

# Add our custom researcher node
workflow.add_node("researcher", researcher_node)

# Add the prebuilt ToolNode (it automatically executes the tools in tools list)
workflow.add_node("tools", ToolNode(tools))

# --- Define the Logic Flow ---

# Start at the researcher
workflow.add_edge(START, "researcher")

# After the researcher node, we check:
# 1. Does the AI want to call a tool? -> Route to "tools" node
# 2. Does the AI have a final answer? -> Route to END
workflow.add_conditional_edges(
    "researcher",
    tools_condition, # This is a helper function that reads tool_calls
)

# After the tools run, they MUST loop back to the researcher 
# so the AI can read the search results and summarize.
workflow.add_edge("tools", "researcher")

# Compile
agent_app = workflow.compile()