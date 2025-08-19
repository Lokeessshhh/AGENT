from collections import Counter

def compute_field_confidence(field_name, ocr_token_confs, llm_run_values, validator_ok, return_breakdown=False):
    """
    - ocr_token_confs: list of OCR token confidences involved (0..1)
    - llm_run_values: list of values returned across N LLM runs
    - validator_ok: bool or 0/1
    - return_breakdown: if True, return (score, details dict)
    """
    ocr_score = (sum(ocr_token_confs) / len(ocr_token_confs)) if ocr_token_confs else 0.0
    c = Counter([str(v).strip().lower() for v in llm_run_values if v is not None])
    if len(c) == 0:
        llm_agreement = 0.0
    else:
        most_common_count = c.most_common(1)[0][1]
        llm_agreement = most_common_count / len(llm_run_values)
    validator_score = 1.0 if validator_ok else 0.0

    score = 0.45 * ocr_score + 0.45 * llm_agreement + 0.10 * validator_score
    score = max(0.0, min(1.0, score))

    if return_breakdown:
        return score, {
            "ocr_score": round(ocr_score, 2),
            "llm_agreement": round(llm_agreement, 2),
            "validator_score": round(validator_score, 2),
            "formula": "0.45*OCR + 0.45*LLM agreement + 0.10*Validator"
        }
    return score


def overall_confidence(per_field_scores):
    """
    Compute overall confidence as the simple average of all per-field scores.
    """
    if not per_field_scores:
        return 0.0
    return sum(per_field_scores) / len(per_field_scores)
