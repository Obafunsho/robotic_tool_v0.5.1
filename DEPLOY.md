# Putting the tool online

This folder is a complete web application. The website, the calculations and the Word business case all run from the same Python code; nothing else is needed.

## 1. Run it on your own computer (10 minutes)

1. Install Python 3.11 or later.
2. Unzip this folder, open a terminal in it and run:

   ```
   pip install -r requirements.txt
   python -m pytest -q
   streamlit run app.py
   ```

3. A browser opens at http://localhost:8501. Choose the configuration in the left panel, check the inputs, read the results, then open the "Business case" tab and press "Generate Word business case" to download the document.

All 681 tests should pass before anything is put online. Package versions are pinned in `requirements.txt`; change them deliberately and re-run the tests.

## 2. Put it online

Three routes, from quickest to most controlled.

### Route A: Streamlit Community Cloud (free, minutes, good for a pilot)

1. Create a private GitHub repository and upload this folder.
2. Sign in at share.streamlit.io with the same GitHub account, choose "New app", select the repository and `app.py`, and deploy.
3. Restrict access to named email addresses in the app settings.

Hosting is outside the NHS and outside the UK. Use it for demonstration with placeholder prices only, not for confidential supplier quotes.

### Route B: Docker on UK cloud or a university server (recommended for trusts)

The included `Dockerfile` builds a container that runs the tests and then starts the app on port 8501.

```
docker build -t robotic-tool .
docker run -p 8501:8501 robotic-tool
```

The same container can be deployed to Azure App Service (UK South), AWS (London) or a University of Birmingham server. Put it behind the organisation's single sign-on and HTTPS.

### Route C: inside an NHS network

Give the container to the trust or ICS digital team. Because nothing is stored and no patient data is used, the information governance requirement is light, but commercially sensitive prices are entered, so hosting inside the network is the safest option for live use.

## 3. Data and security

- No patient-identifiable data is used or requested.
- Nothing entered is saved on the server. Users download an inputs file (.json) and can reload it from the sidebar to reproduce a case.
- Supplier prices may be commercially confidential. Do not hard-code real quotes into `defaults.py` in a shared repository.

## 4. For the Python developer

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit web interface. Reads inputs, calls the engine, offers the Word download. |
| `engine.py` | All calculations, one function per step. No interface code. |
| `defaults.py` | Every placeholder input: specialties, platforms, prices, unit costs, presets. |
| `business_case.py` | Builds the Five Case Model content from engine results. |
| `docx_render.py` | Renders that content to Word with python-docx. |
| `benchmark.py`, `sensitivity.py`, `register.py` | Benchmark programme, tornado analysis, assumptions register. |
| `charts.py`, `inputs_io.py` | Charts for Word; saving and reloading cases. |
| `templates.py` | The two-week theatre template (main input). |
| `.streamlit/config.toml`, `static/` | Theme and favicon. Keep both when deploying. |
| `show_the_maths.py` | Prints a step-by-step worked example. |
| `test_engine.py`, `test_app.py` | Test suite: hand-calculated cases, invariants, independent re-calculation, document and app smoke tests. |
| `.github/workflows/tests.yml` | Runs the tests on every change in GitHub. |

Planned for v2: business case template redo (clinician-led principles), staffing for new theatre lists, surgeon capacity limit, national allocation view, 12-month review screen, capital accounting refinements (VAT, impairment), and Surgical Data and Policy Lab branding.

Any change to `engine.py` or `defaults.py` should come with a test, and the full test suite must pass before deployment.
