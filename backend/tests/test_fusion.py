"""
Unit tests for Reciprocal Rank Fusion (RRF).
"""
import pytest
from app.retrieval.fusion import FusedCandidate, reciprocal_rank_fusion


def test_rrf_single_list_scoring():
    """Verify RRF formula RRF(d) = 1 / (k + rank) for dense-only results."""
    dense_results = [
        {"chunk_id": "chunk_A", "similarity_score": 0.95, "content": "Log text A"},
        {"chunk_id": "chunk_B", "similarity_score": 0.85, "content": "Log text B"},
    ]
    sparse_results = []

    fused = reciprocal_rank_fusion(dense_results, sparse_results, k=60)

    assert len(fused) == 2
    # Rank 1: 1 / (60 + 1) = 1 / 61 = 0.016393
    assert fused[0].chunk_id == "chunk_A"
    assert fused[0].dense_rank == 1
    assert fused[0].bm25_rank is None
    assert fused[0].retrieval_methods == ["dense"]
    assert pytest.approx(fused[0].rrf_score, abs=1e-5) == round(1.0 / 61.0, 6)

    # Rank 2: 1 / (60 + 2) = 1 / 62 = 0.016129
    assert fused[1].chunk_id == "chunk_B"
    assert fused[1].dense_rank == 2
    assert fused[1].bm25_rank is None
    assert pytest.approx(fused[1].rrf_score, abs=1e-5) == round(1.0 / 62.0, 6)


def test_rrf_duplicate_merging_and_combined_score():
    """Verify chunk appearing in both dense and sparse has its reciprocal ranks summed."""
    dense_results = [
        {"chunk_id": "chunk_shared", "similarity_score": 0.92, "content": "Shared content"},
        {"chunk_id": "chunk_dense_only", "similarity_score": 0.80, "content": "Dense only"},
    ]
    sparse_results = [
        {"chunk_id": "chunk_sparse_only", "bm25_score": 12.5, "content": "Sparse only"},
        {"chunk_id": "chunk_shared", "bm25_score": 8.0, "content": "Shared content"},
    ]

    fused = reciprocal_rank_fusion(dense_results, sparse_results, k=60)

    assert len(fused) == 3
    top = fused[0]
    assert top.chunk_id == "chunk_shared"
    assert top.retrieval_methods == ["dense", "bm25"]
    assert top.dense_rank == 1
    assert top.bm25_rank == 2
    assert top.dense_score == 0.92
    assert top.bm25_score == 8.0

    # chunk_shared score = 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.032522
    expected_score = round(1.0 / 61.0 + 1.0 / 62.0, 6)
    assert pytest.approx(top.rrf_score, abs=1e-5) == expected_score


def test_rrf_custom_k_parameter():
    """Verify custom k constant modifies reciprocal rank scaling."""
    dense_results = [{"chunk_id": "c1", "similarity_score": 0.9}]
    sparse_results = []

    fused = reciprocal_rank_fusion(dense_results, sparse_results, k=20)
    assert len(fused) == 1
    # 1 / (20 + 1) = 1 / 21 = 0.047619
    assert pytest.approx(fused[0].rrf_score, abs=1e-5) == round(1.0 / 21.0, 6)


def test_rrf_empty_inputs_return_empty():
    """Verify empty result sets return empty list."""
    assert reciprocal_rank_fusion([], [], k=60) == []

