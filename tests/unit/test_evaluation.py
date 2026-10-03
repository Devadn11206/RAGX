from app.evaluation.retrieval_metrics import calculate_hit_at_k, calculate_recall_at_k, calculate_mrr

def test_retrieval_metrics_golden():
    expected = ["A", "B"]
    retrieved = ["X", "Y", "A", "Z", "B"]
    
    assert calculate_hit_at_k(expected, retrieved, 1) == 0.0
    assert calculate_hit_at_k(expected, retrieved, 3) == 1.0
    assert calculate_hit_at_k(expected, retrieved, 5) == 1.0
    
    assert calculate_recall_at_k(expected, retrieved, 5) == 1.0
    assert calculate_recall_at_k(expected, retrieved, 3) == 0.5
    
    # First match is at index 2 (rank 3), RR = 1/3
    assert abs(calculate_mrr(expected, retrieved) - 0.3333333333333333) < 1e-6
