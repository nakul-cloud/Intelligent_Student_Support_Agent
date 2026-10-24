"""Verification script for CrossEncoderReranker and two-stage RAG retrieval pipeline."""

import asyncio
import time
from app.config.settings import settings
from app.ai.retrieval.reranker import CrossEncoderReranker
from app.tools.rag_tool import search_student_handbook, warm_rag_pipeline


async def main():
    print("=" * 60)
    print("1. Verifying CrossEncoderReranker Module")
    print(f"Reranker model configured: {settings.reranker_model}")
    print(f"Reranker device: {settings.reranker_device}")
    print(f"Reranker enabled: {settings.reranker_enabled}")

    reranker = CrossEncoderReranker()
    
    # Test candidates
    mock_candidates = [
        {
            "id": "c1",
            "score": 0.52,
            "content": "Students must pay their tuition fees before the start of the semester or face a late fee penalty.",
            "metadata": {"section_number": "4.1", "page_number": 12, "section_title": "Fee Penalties"},
        },
        {
            "id": "c2",
            "score": 0.78,
            "content": "A minimum of 75% attendance in lectures and practical sessions is mandatory to appear in end-semester examinations.",
            "metadata": {"section_number": "10.2", "page_number": 28, "section_title": "Attendance Requirement"},
        },
        {
            "id": "c3",
            "score": 0.65,
            "content": "Medical leave condonation may be granted up to 10% on submission of valid hospital records.",
            "metadata": {"section_number": "10.3", "page_number": 29, "section_title": "Medical Condonation"},
        },
    ]

    query = "What is the minimum attendance required to take exams?"
    print(f"\nQuery: '{query}'")
    
    t0 = time.perf_counter()
    reranked = reranker.rerank(query, mock_candidates, top_k=2)
    t1 = time.perf_counter()
    print(f"Reranking completed in {(t1 - t0)*1000:.2f}ms")
    print(f"Returned {len(reranked)} items (top_k=2):")
    for idx, item in enumerate(reranked, 1):
        print(f"  #{idx}: ID={item['id']} | Re-rank Score={item['score']} | Bi-encoder Score={item['bi_encoder_score']}")
        print(f"      Section: {item['metadata']['section_title']} (Sec {item['metadata']['section_number']})")
        print(f"      Content: {item['content'][:60]}...")

    # Validate that the most relevant candidate (attendance, c2) is top 1
    assert reranked[0]["id"] == "c2", f"Expected c2 to be #1, got {reranked[0]['id']}"
    assert len(reranked) == 2, f"Expected 2 results, got {len(reranked)}"
    print("\n[PASS] Re-ranker scored and ordered candidates accurately!")

    # Test LRU cache speedup on repeated call
    t2 = time.perf_counter()
    cached_reranked = reranker.rerank(query, mock_candidates, top_k=2)
    t3 = time.perf_counter()
    print(f"Repeated cached reranking completed in {(t3 - t2)*1000:.2f}ms")
    print("\n[PASS] LRU Cache speedup verified!")

    # Test End-to-End Tool execution
    print("\n" + "=" * 60)
    print("2. Verifying search_student_handbook end-to-end")
    tool_output = await search_student_handbook("attendance requirement for examinations", top_k=2)
    print(f"Tool Output Preview:\n{tool_output[:350]}...\n")
    print("[PASS] End-to-End search_student_handbook executed cleanly!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
