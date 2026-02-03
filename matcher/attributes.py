def attribute_match_score(a: dict, b: dict, mandatory_keys: list[str]) -> float:
    """
    Returns 0.0 → reject
    Returns 0–1 → match strength
    """

    if not a or not b:
        return 0.0

    # HARD REJECT if mandatory mismatch
    for key in mandatory_keys:
        if key in a and key in b:
            if a[key] != b[key]:
                return 0.0
        else:
            return 0.0  # mandatory missing

    # Soft scoring for remaining attributes
    common_keys = set(a.keys()) & set(b.keys())
    if not common_keys:
        return 0.0

    matched = sum(1 for k in common_keys if a[k] == b[k])
    return matched / len(common_keys)
