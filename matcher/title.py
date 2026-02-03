from rapidfuzz import fuzz

def title_similarity(t1: str, t2: str) -> float:
    if not t1 or not t2:
        return 0.0
    return fuzz.token_set_ratio(t1, t2) / 100.0
