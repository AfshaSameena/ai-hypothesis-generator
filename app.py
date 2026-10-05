# app.py — Streamlit MVP (drop-in replacement)
import streamlit as st
import io
import pdfplumber
import json
from pathlib import Path
import re

st.set_page_config(page_title="AI Hypothesis Generator", layout="wide")
st.title("AI Hypothesis Generator — MVP")
st.caption("Uploads PDFs, extracts claims, detects conflicts, and proposes AI-generated hypotheses. Review required.")

# Sidebar upload
with st.sidebar:
    st.header("Upload")
    uploaded_files = st.file_uploader("Upload one or more research papers (PDF)", type=[
                                      "pdf"], accept_multiple_files=True)
    run_button = st.button("Generate hypotheses",
                           help="Run the prototype pipeline on uploaded files")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# -------------------------
# Extraction utilities
# -------------------------


def extract_from_uploaded_file(uploaded_file, ocr_fallback=False):
    """
    Extract paragraphs and tables from an uploaded Streamlit file (in-memory).
    Returns list of pages: {page, paragraphs(list), tables(list-of-lists)}
    """
    try:
        bytes_data = uploaded_file.read()
        with pdfplumber.open(io.BytesIO(bytes_data)) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if not text and ocr_fallback:
                    # Optional OCR path (requires pytesseract and Tesseract binary)
                    try:
                        from PIL import Image
                        import pytesseract
                        pil_image = page.to_image(resolution=200).original
                        if pil_image.mode != "RGB":
                            pil_image = pil_image.convert("RGB")
                        text = pytesseract.image_to_string(pil_image)
                    except Exception as e:
                        # OCR not available; continue
                        pass
                # simple paragraph split
                paragraphs = [p.strip() for p in text.replace(
                    "\r\n", "\n").split("\n\n") if p.strip()]
                tables = page.extract_tables() or []
                pages.append(
                    {"page": i, "paragraphs": paragraphs, "tables": tables})
        return pages
    except Exception as e:
        st.error(
            f"Error extracting PDF '{getattr(uploaded_file, 'name', 'uploaded')}': {e}")
        return []


def paragraphs_to_claims(paragraphs, paper_name):
    """
    Heuristic conversion of paragraphs to structured claims.
    Replace this with an IE model or LLM prompt for production.
    """
    claims = []
    for idx, p in enumerate(paragraphs, start=1):
        pval = None
        m = re.search(r"p\s*[=:<]\s*([0-9]*\.?[0-9]+)", p, flags=re.I)
        if m:
            try:
                pval = float(m.group(1))
            except:
                pval = None
        direction = None
        if re.search(r"\bincrease(s|d)?\b", p, flags=re.I):
            direction = "+"
        elif re.search(r"\bdecrease(s|d)?\b", p, flags=re.I):
            direction = "-"
        elif re.search(r"\bno significant\b|\bno statistically significant\b|\bns\b", p, flags=re.I):
            direction = "0"
        claim = {
            "id": f"{paper_name}_para{idx}",
            "paper": paper_name,
            "claim": p[:800],
            "direction": direction,
            "pvalue": pval,
            "context": p
        }
        claims.append(claim)
    return claims

# -------------------------
# Prototype conflict detector & generator (stubs)
# -------------------------


def detect_conflicts_stub(claims):
    """
    Very small clustering / conflict detector:
    If there are at least two claims with same variable (heuristic) but different directions,
    return a single conflict object. This is a placeholder — replace with real logic/KG.
    """
    conflicts = []
    if len(claims) >= 2:
        # For prototype, just take first two claims as conflicting if directions differ or one is '0'
        c1 = claims[0]
        c2 = claims[1]
        # Build conflict observations
        observations = [c1, c2]
        conflict_type = "direction / cohort / assay mismatch"
        conflicts.append(
            {"id": "conflict_1", "observations": observations, "conflict_type": conflict_type})
    return conflicts


def generate_hypotheses_stub(conflict):
    """
    Return a small list of stub hypotheses for a detected conflict.
    Replace with LLM prompt chain + KG reasoning for production.
    """
    return [
        {
            "id": "H1",
            "hypothesis": "The effect depends on disease stage.",
            "rationale": "One study sampled intermediate-stage patients while the other pooled mixed stages, which could dilute an effect.",
            "prediction": "Biomarker X elevated only in intermediate-stage patients after treatment Y.",
            "suggested_experiment": "Stratified analysis across early/intermediate/advanced stages using a consistent assay (ELISA)."
        },
        {
            "id": "H2",
            "hypothesis": "Assay sensitivity differences explain the discrepancy.",
            "rationale": "ELISA and multiplex differ in dynamic range and sensitivity.",
            "prediction": "Using ELISA on Study B samples will reproduce Study A's increase.",
            "suggested_experiment": "Re-run measurements with matched assay across cohorts."
        }
    ]

# -------------------------
# Main pipeline: process uploaded files, persist claims, run stubs
# -------------------------


def process_uploaded_files_and_generate(uploaded_files, ocr_fallback=False, persist=True):
    all_claims = []
    provenance = {}
    for f in uploaded_files:
        paper_name = getattr(f, "name", "uploaded_pdf")
        pages = extract_from_uploaded_file(f, ocr_fallback=ocr_fallback)
        # flatten paragraphs across pages
        paragraphs = []
        for p in pages:
            paragraphs.extend(p["paragraphs"])
        claims = paragraphs_to_claims(paragraphs, paper_name)
        all_claims.extend(claims)
        provenance[paper_name] = {"pages": len(pages)}
    # persist
    if persist:
        out_file = DATA_DIR / "extracted_claims.jsonl"
        with open(out_file, "a", encoding="utf-8") as fh:
            for c in all_claims:
                fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    # detect conflicts and generate hypotheses
    conflicts = detect_conflicts_stub(all_claims)
    hypotheses = []
    for c in conflicts:
        hyps = generate_hypotheses_stub(c)
        hypotheses.append({"conflict_id": c["id"], "hypotheses": hyps})
    return {"claims": all_claims, "conflicts": conflicts, "hypotheses": hypotheses, "provenance": provenance}


# -------------------------
# UI actions
# -------------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    st.header("Pipeline output")
    if run_button:
        if not uploaded_files:
            st.warning("Please upload at least one PDF to run the pipeline.")
        else:
            with st.spinner("Processing uploaded PDFs..."):
                try:
                    results = process_uploaded_files_and_generate(
                        uploaded_files, ocr_fallback=False, persist=True)
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
                    results = None
            if not results:
                st.info("No results.")
            else:
                claims = results["claims"]
                conflicts = results["conflicts"]
                if not conflicts:
                    st.success("No conflicts detected (prototype).")
                else:
                    for c in conflicts:
                        st.subheader(f"Conflict: {c['id']}")
                        st.markdown("**OBSERVATIONS**")
                        for obs in c["observations"]:
                            st.write(
                                f"- **{obs['paper']}**: {obs.get('claim', '(no text)')[:400]}  ")
                            st.write(
                                f"  - p-value: {obs.get('pvalue')}  - direction: {obs.get('direction')}  ")
                        st.markdown(f"**CONFLICT TYPE:** {c['conflict_type']}")
                        # hypotheses
                        hyps = next(
                            (h["hypotheses"] for h in results["hypotheses"] if h["conflict_id"] == c["id"]), [])
                        st.markdown("**AI-generated hypotheses (for review)**")
                        for h in hyps:
                            with st.expander(f"{h['id']}: {h['hypothesis']}"):
                                st.write("**Rationale:**", h['rationale'])
                                st.write("**Prediction:**", h['prediction'])
                                st.write("**Suggested experiment:**",
                                         h['suggested_experiment'])
                                st.write("---")

with col_right:
    st.header("Actions & provenance")
    if uploaded_files:
        st.write("Uploaded files:")
        for f in uploaded_files:
            st.write("-", getattr(f, "name", "uploaded_pdf"))
    st.write("- Download extracted claims (data/extracted_claims.jsonl)")
    st.write("- Human reviewer: approve / edit extractions")
    st.write(
        "- For real extraction, replace `paragraphs_to_claims` with an IE model or LLM prompt.")
    st.markdown("---")
    st.write("Tip: If text extraction fails (scanned PDF), reinstall Tesseract and enable OCR fallback in code.")

# Default help area (kept for reference)
st.markdown("---")
st.subheader("Example output format")
st.markdown("""
**OBSERVATION**

Study A → Biomarker X increases  
Study B → Biomarker X shows no significant change

**CONFLICT DETECTED**

**Top AI-generated hypothesis (H1)** — *Effect depends on disease stage.*

**Suggested experiment:** Cross-sectional comparison of early/intermediate/advanced stages (n=40 each), measure Biomarker X with ELISA.
""")
