from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

# 1. Update State to handle RAG flow
class State(TypedDict):
    query: str      # The user's original question
    content: str    # The retrieved context or generated answer
    compliant: bool

# 2. Retrieval Node
def retrieve_docs_node(state: State):
    # Using your specific endpoint
    search_client = SearchClient(
        endpoint="https://project-test-005.search.windows.net",
        index_name="compliance-index",
        credential=AzureKeyCredential("I3tuAyTzm1WuAf6MPzXrGT9ZLh0XbH9ycIR7MmjH6tAzSeCHjCIi") # Note: Move to .env later!
    )
    
    # Search using the user's query
    results = search_client.search(search_text=state["query"])
    
    # Extract content from documents
    docs = [doc.get('content', '') for doc in results]
    context = "\n".join(docs)
    
    print(f"--- Retrieved {len(docs)} documents from Azure ---")
    return {"content": context}

# 3. Compliance Node
def check_compliance(state: State):
    # Logic: If retrieved content is empty or contains "restricted", it fails
    is_compliant = len(state["content"]) > 0 and "restricted" not in state["content"].lower()
    print(f"--- Compliance Check: {'Passed' if is_compliant else 'Failed'} ---")
    return {"compliant": is_compliant}

# 4. Rewrite/Fallback Node
def rewrite_node(state: State):
    print("--- Cleaning/Redacting content ---")
    return {"content": "Information redacted due to compliance policy.", "compliant": True}

# 5. Router
def router(state: State) -> Literal["end", "rewrite"]:
    return "end" if state["compliant"] else "rewrite"

# Build the Graph
workflow = StateGraph(State)

workflow.add_node("retrieve", retrieve_docs_node)
workflow.add_node("check", check_compliance)
workflow.add_node("rewrite", rewrite_node)

# Set the flow: Retrieve -> Check -> (End or Rewrite)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "check")

workflow.add_conditional_edges(
    "check",
    router,
    {
        "end": END,
        "rewrite": "rewrite"
    }
)
workflow.add_edge("rewrite", END)

app = workflow.compile()

# Test the RAG flow
print("Starting Compliance RAG Test:")
app.invoke({"query": "compliance guidelines", "content": ""})