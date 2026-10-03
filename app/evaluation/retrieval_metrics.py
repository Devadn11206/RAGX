from typing import List

def calculate_hit_at_k(expected: List[str], retrieved: List[str], k: int) -> float:
    retrieved_k = retrieved[:k]
    for expected_id in expected:
        if expected_id in retrieved_k:
            return 1.0
    return 0.0

def calculate_recall_at_k(expected: List[str], retrieved: List[str], k: int) -> float:
    if not expected:
        return 0.0
    retrieved_k = retrieved[:k]
    hits = sum(1 for e in expected if e in retrieved_k)
    return float(hits) / len(expected)

def calculate_mrr(expected: List[str], retrieved: List[str]) -> float:
    for i, ret_id in enumerate(retrieved):
        if ret_id in expected:
            return 1.0 / (i + 1)
    return 0.0
