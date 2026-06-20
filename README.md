# ISP Burnpur Contract Assistant

A professional AI-powered contract Q&A assistant for the ISP Burnpur Hot Strip Mill project.
Runs free on GitHub + Streamlit Cloud. No paid subscriptions required.

## Features

- **Factual & descriptive answers** — two separate prompts tuned for each question type
- **Automatic neighbor-chunk retrieval** — adjacent contract passages fetched for richer context
- **Source references** — every answer links to exact contract excerpts for verification
- **BM25 + route-boosted search** — domain-aware retrieval for safety, scope, payment, etc.
- **Professional UI** — dark gradient header, quick-question buttons, Reference tab

## Deploy to Streamlit Cloud (Free)

### Step 1 — GitHub repository
1. Go to [github.com](https://github.com) and sign in.
2. Click **+** → **New repository** → name it `isp-burnpur-contract-assistant`.
3. Choose **Private**.
4. Click **Create repository**.

### Step 2 — Upload files
Upload these files/folders to the root of your repository:
```
streamlit_app.py
local_contract_server.py
requirements.txt
README.md
.gitignore
index/
  contract_index.json
  summary.json
```

### Step 3 — Gemini API key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create an API key. **Do not upload it to GitHub.**

### Step 4 — Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **Create app**.
3. Select your repository, branch `main`, main file `streamlit_app.py`.
4. Click **Advanced settings** → **Secrets**, paste:
   ```toml
   GEMINI_API_KEY = "paste_your_key_here"
   ```
5. Click **Deploy**.

## Run Locally

```powershell
pip install streamlit python-docx openpyxl pypdf
$env:GEMINI_API_KEY = "your_key"
streamlit run streamlit_app.py
```

## Rebuild the Index (after adding new contract files)

```powershell
python local_contract_server.py build --source-dir "C:\Users\INP\Desktop\ISP Burnpur contract"
```

Commit the updated `index/contract_index.json` and `index/summary.json` and redeploy.

## Local HTTP Server (no Streamlit)

```powershell
$env:GEMINI_API_KEY = "your_key"
python local_contract_server.py serve
# Open http://127.0.0.1:7860
```
