"""
RAG Test Suite — run from ai-engine/ directory:
    python tests/test_rag.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pinecone_client import index
from app.embeddings import embeddings
from services.retriever import retrieve_context
from services.ingest import store_text
from langchain_core.messages import HumanMessage


# ── Test 1: Pinecone connection & index stats ─────────────────────────────────
def test_pinecone_connection():
    print("\n[1] Pinecone Index Stats")
    stats = index.describe_index_stats()
    print(f"    Total vectors: {stats['total_vector_count']}")
    assert stats['total_vector_count'] >= 0, "Could not reach Pinecone"
    print("    ✓ Pinecone connected")


# ── Test 2: Embedding works ───────────────────────────────────────────────────
def test_embedding():
    print("\n[2] Embedding Test")
    vector = embeddings.embed_query("test query")
    print(f"    Vector dimensions: {len(vector)}")
    assert len(vector) > 0, "Embedding returned empty vector"
    print("    ✓ Embeddings working")


# ── Test 3: Ingest + retrieve round-trip ─────────────────────────────────────
def test_ingest_and_retrieve():
    print("\n[3] Ingest → Retrieve Round-trip")
    store_text("The Eiffel Tower is located in Paris, France.", "test_doc_eiffel")
    import time; time.sleep(2)  # wait for Pinecone to index

    context = retrieve_context("Where is the Eiffel Tower?")
    print(f"    Retrieved context: {context[:100] if context else 'None'}")
    assert context is not None, "Retriever returned None — score threshold may be too high or ingest failed"
    assert "Eiffel" in context or "Paris" in context, "Retrieved wrong context"
    print("    ✓ Ingest and retrieval working")


# ── Test 4: Retriever returns None for irrelevant query ───────────────────────
def test_retriever_filters_irrelevant():
    print("\n[4] Score Filtering Test")
    context = retrieve_context("xkqzwpfm gibberish query 12345")
    print(f"    Context for gibberish query: {context}")
    assert context is None, "Retriever should return None for irrelevant queries"
    print("    ✓ Score filtering works — irrelevant queries return None")


# ── Test 5: Full research agent response ─────────────────────────────────────
def test_research_agent():
    print("\n[5] Research Agent End-to-End")
    from agents.research_agent import research_agent
    state = {"messages": [HumanMessage(content="Where is the Eiffel Tower?")]}
    result = research_agent(state)
    response = result["messages"][-1][1] if isinstance(result["messages"][-1], tuple) else result["messages"][-1].content
    print(f"    Agent response: {response[:150]}")
    assert len(response) > 10, "Agent returned empty response"
    print("    ✓ Research agent responding")


# ── Test 6: Research agent fallback when no context ──────────────────────────
def test_research_agent_fallback():
    print("\n[6] Research Agent Fallback (no context)")
    from agents.research_agent import research_agent
    state = {"messages": [HumanMessage(content="xkqzwpfm gibberish query 12345")]}
    result = research_agent(state)
    response = result["messages"][-1][1] if isinstance(result["messages"][-1], tuple) else result["messages"][-1].content
    print(f"    Fallback response: {response[:150]}")
    assert len(response) > 10, "Fallback returned empty response"
    print("    ✓ Fallback to LLM working")


if __name__ == "__main__":
    tests = [
        test_pinecone_connection,
        test_embedding,
        test_ingest_and_retrieve,
        test_retriever_filters_irrelevant,
        test_research_agent,
        test_research_agent_fallback,
    ]

    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"    ✗ FAILED: {e}")
            failed.append(t.__name__)

    print(f"\n{'='*40}")
    print(f"Results: {passed}/{len(tests)} passed")
    if failed:
        print(f"Failed:  {', '.join(failed)}")
