def final_match_score(
    attribute_score: float,
    title_score: float,
    brand_match: bool
) -> float:
    return (
        0.6 * attribute_score +
        0.3 * title_score +
        0.1 * (1.0 if brand_match else 0.0)
    )
