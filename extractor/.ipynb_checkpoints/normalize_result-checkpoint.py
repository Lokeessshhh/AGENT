# extractor/normalize_result.py
from typing import Dict, Any, List
from extractor.confidence import compute_field_confidence, overall_confidence
from extractor.validator import validate_fields

def normalize_extraction(raw: Dict[str, Any], all_tokens: List[Dict]) -> Dict[str, Any]:
    """
    Take raw llm_raw output + OCR tokens and enforce the required schema.
    """
    doc_type = raw.get("doc_type", "unknown")
    fields = []
    per_field_scores = []

    # LLM run values for self-consistency
    llm_runs = raw.get("_llm_runs", [])

    for f in raw.get("fields", []):
        name = f.get("name")
        value = f.get("value")
        src = f.get("source", {})

        # OCR tokens overlapping bbox
        token_confs = []
        if src and "bbox" in src and "page" in src:
            bbox = src["bbox"]
            page = src["page"]
            token_confs = [
                t["conf"]
                for t in all_tokens
                if t.get("page") == page
                and t["bbox"][0] >= bbox[0]-5
                and t["bbox"][2] <= bbox[2]+5
            ]
        else:
            token_confs = [t["conf"] for t in all_tokens]

        # Collect values for this field across runs
        run_vals = []
        for run in llm_runs:
            val = None
            for ff in run.get("fields", []):
                if ff.get("name") == name:
                    val = ff.get("value")
            run_vals.append(val)

        # Compute confidence (for now validator_ok=True, since validation is handled separately)
        conf, breakdown = compute_field_confidence(
            name, token_confs, run_vals, validator_ok=True, return_breakdown=True
        )
        per_field_scores.append(conf)

        fields.append({
            "name": name,
            "value": value,
            "confidence": round(conf, 2),
            "source": src if src else None,
            "confidence_breakdown": breakdown,
        })


    # Run type-specific validation
    qa = validate_fields(
        doc_type,
        {f["name"]: f["value"] for f in fields},
        raw.get("line_items", [])
    )

    return {
        "doc_type": doc_type,
        "fields": fields,
        "overall_confidence": round(overall_confidence(per_field_scores), 2),
        "qa": qa,
    }
