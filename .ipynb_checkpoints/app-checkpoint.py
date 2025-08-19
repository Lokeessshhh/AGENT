# app.py
import streamlit as st
from extractor.ocr import pdf_bytes_to_images, image_to_ocr_data
from extractor.llm_extract import extract_with_llm
from extractor.router import detect_doc_type
from extractor.normalize_result import normalize_extraction
from extractor.confidence import overall_confidence
import json

st.set_page_config(page_title="Agentic Doc Extractor", layout="wide")
st.title("Agentic Document Extraction")

uploaded = st.file_uploader("Upload PDF / Image", type=["pdf","png","jpg","jpeg"])
expected_fields_text = st.text_area("Optional: comma-separated fields to extract (e.g. InvoiceNumber,TotalAmount)")

if uploaded and st.button("Run extraction"):
    try:
        pdf_bytes = uploaded.read()
        images = pdf_bytes_to_images(pdf_bytes)
        if not images:
            st.error("❌ OCR failed to convert PDF/image.")
            st.stop()

        all_tokens, full_text = [], ""
        for p, img in enumerate(images, start=1):
            tok = image_to_ocr_data(img)
            for t in tok:
                t['page'] = p
            all_tokens.extend(tok)
            full_text += " " + " ".join([t['text'] for t in tok])

        if not all_tokens:
            st.error("❌ OCR produced no tokens.")
            st.stop()

        # ... continue with doc_type, LLM, normalization

    except Exception as e:
        st.error(f"❌ Extraction failed: {e}")
        st.stop()

    st.info(f"Found {len(all_tokens)} OCR tokens across {len(images)} pages")

    # Doc type detection
    doc_type, route_scores = detect_doc_type(full_text, all_tokens)
    st.success(f"Detected document type: {doc_type}")
    with st.expander("Routing scores"):
        st.json(route_scores)

    # Expected fields
    expected_fields = [f.strip() for f in expected_fields_text.split(",") if f.strip()]
    if not expected_fields:
        if doc_type == "invoice":
            expected_fields = ["InvoiceNumber","InvoiceDate","VendorName","TotalAmount","LineItems"]
        elif doc_type == "medical_bill":
            expected_fields = [
                "PatientName","PatientID","HospitalName","BillNumber",
                "AdmissionDate","DischargeDate","TotalAmount","LineItems"
            ]
        else:  # prescription
            expected_fields = ["PatientName","DoctorName","PrescriptionDate","Medications"]

    # LLM extraction
    llm_raw = extract_with_llm(
        full_text,
        all_tokens,
        expected_fields,
        n_consistency=3,
        doc_type=doc_type,
    )

    # Normalize into schema
    normalized = normalize_extraction(llm_raw, all_tokens)

    st.subheader("Final normalized output (schema-compliant)")
    st.code(json.dumps(normalized, indent=2))

    # Confidence scoring explanation
    st.subheader("Confidence scoring explanation")
    st.markdown(
        "Each field's confidence = **0.45 * OCR_score + 0.45 * LLM_agreement + 0.10 * Validator_score**"
    )

    for f in normalized["fields"]:
        with st.expander(f"Confidence breakdown: {f['name']}"):
            st.write(f"**Value:** {f['value']}")
            st.write(f"**Final Confidence:** {f['confidence']:.2f}")

            breakdown = f.get("confidence_breakdown", {})
            if breakdown:
                st.write("**Components:**")
                st.write(f"OCR Score: {breakdown['ocr_score']}")
                st.progress(int(breakdown['ocr_score'] * 100))

                st.write(f"LLM Agreement: {breakdown['llm_agreement']}")
                st.progress(int(breakdown['llm_agreement'] * 100))

                st.write(f"Validator Score: {breakdown['validator_score']}")
                st.progress(int(breakdown['validator_score'] * 100))

    st.success(f"Overall confidence: {normalized['overall_confidence']:.2f}")

    # Download button should export normalized JSON
    st.download_button("Download JSON", json.dumps(normalized, indent=2), file_name="extraction.json")
