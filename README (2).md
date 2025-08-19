# 📝 Agentic Document Extraction Challenge

This project implements an **Agentic Document Extraction System** for invoices, medical bills, and prescriptions.  
It uses OCR + LLM extraction + validation + confidence scoring, with a Streamlit interface.

---

## 🚀 Features
- 📤 **Upload** PDF or image (PNG/JPG)
- 🧠 **Doc type detection** (invoice / medical_bill / prescription)
- 🔍 **OCR** with bounding boxes & confidence (Tesseract + pdf2image/PIL)
- 🤖 **LLM extraction** (via OpenRouter/OpenAI) with self-consistency (multiple runs)
- ✅ **Validation rules**:
  - Invoices: totals, date, amount, invoice number format
  - Medical bills: patient ID, admission/discharge dates, totals
  - Prescriptions: doctor/patient names, prescription date, medications + dosage format
- 📊 **Confidence scoring**:
  ```
  confidence = 0.45 * OCR_score + 0.45 * LLM_agreement + 0.10 * Validator_score
  ```
- 🎛️ **Streamlit UI**:
  - Upload file
  - Auto-detect document type
  - JSON output (copy/download)
  - Confidence breakdown per field (progress bars + explanation)
  - Overall confidence score

---

## 🛠️ Tech Stack
- Python 3.9+
- [Streamlit](https://streamlit.io/) – interactive UI
- [pytesseract](https://github.com/madmaze/pytesseract) – OCR
- [pdf2image](https://github.com/Belval/pdf2image) – PDF page rendering
- [OpenRouter/OpenAI](https://openrouter.ai) – LLM for structured extraction
- [Pydantic](https://pydantic.dev) – schema validation

---

## 📂 Project Structure
```
agentic-document-extraction/
│
├── app.py                       # Streamlit UI
├── extractor/
│   ├── ocr.py                   # OCR pipeline
│   ├── llm_extract.py           # LLM extraction (self-consistency, JSON parsing)
│   ├── confidence.py            # Confidence scoring
│   ├── validator.py             # Validation rules (per doc_type)
│   ├── router.py                # Doc type detection
│   ├── schema.py                # Pydantic schema definitions
│   ├── normalize_result.py      # Normalize output → schema-compliant
│
├── requirements.txt             # Python dependencies
├── README.md                    # Documentation
```

---

## ⚙️ Setup

1. **Clone repo**
   ```bash
   git clone <your-repo-url>
   cd agentic-document-extraction
   ```

2. **Create environment**
   ```bash
   conda create -n doc-extract python=3.9 -y
   conda activate doc-extract
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract**
   - Windows: download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux/macOS:  
     ```bash
     sudo apt install tesseract-ocr
     ```

5. **Set API key**
   - Create a `.env` file:
     ```
     OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxx
     ```

---

## ▶️ Run the App
```bash
streamlit run app.py
```

Open browser at http://localhost:8501  

---

## 📊 Example Output

```json
{
  "doc_type": "invoice",
  "fields": [
    {"name": "InvoiceNumber", "value": "INV-12345", "confidence": 0.91,
     "source": {"page": 1, "bbox": [120, 80, 250, 110]},
     "confidence_breakdown": {
       "ocr_score": 0.92,
       "llm_agreement": 0.89,
       "validator_score": 1.0,
       "formula": "0.45*OCR + 0.45*LLM agreement + 0.10*Validator"
     }
    }
  ],
  "overall_confidence": 0.88,
  "qa": {"passed_rules":["totals_match"],"failed_rules":[],"notes":""}
}
```

---

## 🌍 Deployment
- The app can be deployed on **Streamlit Cloud**:
  1. Push code to GitHub.
  2. Go to https://share.streamlit.io
  3. Connect repo + branch → select `app.py`.
  4. Add `OPENROUTER_API_KEY` as a **secret** in Streamlit Cloud.
- Alternatively, deploy on **Render / Heroku / AWS**.

---

## 🏆 Deliverables
- ✅ Code repo (with commits & clean structure)
- ✅ Deployed Streamlit link
- ✅ README.md (this file)
- ✅ Confidence score explanation
