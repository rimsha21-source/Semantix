# SEMANTIX — Semantic Interpretation Lab

A Streamlit application demonstrating five explainable NLP modules:

1. Semantic Role Analyzer
2. Word Sense Disambiguation (simplified Lesk-style keyword overlap)
3. Negation Analyzer
4. Intent Detector
5. Semantic Relationship Map

JSON export is available for each analysis.

## Run locally

Python 3.10–3.12 is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload `app.py` and `requirements.txt` (README is optional).
3. In Streamlit Community Cloud, choose **New app**.
4. Select the repository, branch, and `app.py`.
5. Deploy. The spaCy English model is installed from the pinned model wheel in `requirements.txt`.

## Technical notes and honest limitations

- Semantic role extraction uses spaCy's `en_core_web_sm` dependency parser and maps syntactic dependencies to simplified semantic labels. This is not a full semantic role labeling model. If the model is unavailable, a lightweight fallback parser is used and identified in the output.
- Word sense disambiguation uses a small built-in lexicon and a simplified Lesk-style keyword-overlap score. It supports the words shown in the module's lexicon selector; it is not an unrestricted dictionary.
- Negation detection uses a list of common markers and a short local window. It does not fully resolve syntactic negation scope, double negation, or all contractions.
- Intent detection is rule-based and educational. It is not a trained intent classifier.
- The relationship map visualizes the roles extracted by the role analyzer. Its quality therefore depends on the parser output.

These limitations are deliberately disclosed so that the application remains explainable and suitable for an academic demonstration.
