# matcher.py
import re
from title_processing import process_title


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def extract_model_tokens(text: str):
    """
    Extract model-like tokens:
    15R, V60e, A5, etc.
    Ignore pure numbers (storage sizes).
    """
    text = normalize(text)
    tokens = re.findall(r"\b[a-z]{0,3}\d{1,3}[a-z]{0,2}\b", text)
    return {t for t in tokens if not t.isdigit()}


def brand_in_text(brand: str, text: str) -> bool:
    if not brand or not text:
        return False
    return normalize(brand) in normalize(text)


def compute_confidence(amazon, candidate, debug=False) -> float:
    """
    amazon & candidate MUST already contain:
      - brand
      - clean_title
      - attributes
    """

    score = 0.0
    reasons = []

    amz_brand = amazon.get("brand")
    cand_brand = candidate.get("brand")

    amz_title = amazon.get("clean_title", "")
    cand_title = candidate.get("clean_title", "")

    # ---------------------------------------------------
    # 1. BRAND CHECK (30%)
    # ---------------------------------------------------

    if amz_brand:
        if cand_brand:
            if normalize(amz_brand) == normalize(cand_brand):
                score += 0.15 
                reasons.append("brand_match")
            else:
                if debug:
                    print("❌ BRAND MISMATCH")
                return 0.0
        else:
            if brand_in_text(amz_brand, cand_title):
                score += 0.15
                reasons.append("brand_found_in_title")
            else:
                reasons.append("brand_missing_allowed")
    else:
        reasons.append("amazon_brand_missing")

    # ---------------------------------------------------
    # 2. MODEL TOKEN MATCH (40%)
    # ---------------------------------------------------

    amz_tokens = extract_model_tokens(amz_title)
    cand_tokens = extract_model_tokens(cand_title)

    overlap = amz_tokens & cand_tokens
    if overlap:
        score += 0.5
        reasons.append(f"model_match={list(overlap)}")
    else:
        reasons.append("model_no_overlap")

    # ---------------------------------------------------
    # 3. ATTRIBUTE MATCH (30%)
    # ---------------------------------------------------

    amz_attr = amazon.get("attributes") or {}
    cand_attr = candidate.get("attributes") or {}

    hits = 0
    checks = 0

    for key in ("ram", "storage"):
        if key in amz_attr and key in cand_attr:
            checks += 1
            if str(amz_attr[key]) == str(cand_attr[key]):
                hits += 1

    if checks > 0:
        score += 0.35 * (hits / checks)
        reasons.append(f"attr_match={hits}/{checks}")
    else:
        score += 0.15
        reasons.append("attr_missing")

    score = round(score, 2)

    if debug:
        print("---- COMPARISON ----")
        print("Amazon clean :", amz_title)
        print("Candidate    :", cand_title)
        print("Brands       :", amz_brand, cand_brand)
        print("Model tokens :", amz_tokens, cand_tokens)
        print("Reasons      :", reasons)
        print("Score        :", score)
        print("--------------------")

    return score














# # matcher.py
# import re

# def normalize(text: str) -> str:
#     return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


# def extract_model_tokens(text: str):
#     """
#     Extract tokens like: 15R, V60e, A5, etc.
#     """
#     text = normalize(text)
#     return set(re.findall(r"[a-z]*\d+[a-z]*", text))


# def compute_confidence(amazon, candidate) -> float:
#     """
#     amazon: dict with keys -> brand, clean_title, attributes
#     candidate: dict with keys -> brand, clean_title, attributes
#     """

#     score = 0.0
#     max_score = 1.0

#     # ---------------- 1. Brand match (30%) ----------------
#     if amazon.get("brand") and candidate.get("brand"):
#         if normalize(amazon["brand"]) == normalize(candidate["brand"]):
#             score += 0.3
#         else:
#             return 0.0  # hard reject

#     # ---------------- 2. Model / clean title tokens (40%) ----------------
#     amz_tokens = extract_model_tokens(amazon.get("clean_title", ""))
#     cand_tokens = extract_model_tokens(candidate.get("clean_title", ""))

#     if amz_tokens and cand_tokens:
#         overlap = amz_tokens & cand_tokens
#         if overlap:
#             score += 0.4
#         else:
#             return 0.0  # wrong model

#     # ---------------- 3. Attribute agreement (30%) ----------------
#     amz_attr = amazon.get("attributes") or {}
#     cand_attr = candidate.get("attributes") or {}

#     attr_matches = 0
#     attr_checks = 0

#     for key in ("ram", "storage"):
#         if key in amz_attr and key in cand_attr:
#             attr_checks += 1
#             if str(amz_attr[key]) == str(cand_attr[key]):
#                 attr_matches += 1

#     if attr_checks > 0:
#         score += 0.3 * (attr_matches / attr_checks)
#     else:
#         # No attributes to compare → partial confidence
#         score += 0.15

#     return round(score, 2)

