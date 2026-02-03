from matcher.brand import normalize_brand
from matcher.rules import get_mandatory_attrs
from matcher.attributes import attribute_match_score
from matcher.title import title_similarity
from matcher.scoring import final_match_score
from matcher.db import fetch_candidates


def match_product(cur, source_product):
    """
    source_product = {
        id, platform, brand, category, title, attributes
    }
    """

    source_brand = normalize_brand(source_product["brand"])
    if not source_brand:
        return []

    mandatory_keys = get_mandatory_attrs(source_product["category"])
    candidates = fetch_candidates(cur, source_product)

    matches = []

    for c in candidates:
        candidate = {
            "id": c[0],
            "asin": c[1],
            "platform": c[2],
            "brand": normalize_brand(c[3]),
            "category": c[4],
            "title": c[5],
            "attributes": c[6] or {},
        }

        # BRAND CHECK
        if candidate["brand"] != source_brand:
            continue

        attr_score = attribute_match_score(
            source_product["attributes"],
            candidate["attributes"],
            mandatory_keys,
        )

        if attr_score == 0.0:
            continue

        title_score = title_similarity(
            source_product["title"],
            candidate["title"],
        )

        score = final_match_score(
            attr_score,
            title_score,
            brand_match=True,
        )

        if score >= 0.7:
            matches.append({
                "source_id": source_product["id"],
                "target_id": candidate["id"],
                "target_platform": candidate["platform"],
                "score": round(score, 3),
            })

    return sorted(matches, key=lambda x: x["score"], reverse=True)

