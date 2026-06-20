# ISP Burnpur Contract Assistant

This version is designed for free GitHub + Streamlit Cloud hosting.

It uses a prebuilt JSON contract index, retrieves evidence with BM25-style scoring plus contract-specific routing, and calls Gemini through the REST API. It avoids Qdrant, Torch, sentence-transformers, and other heavy packages so it stays within free Streamlit Cloud constraints.

## Streamlit Cloud Deploy

1. Push this folder to a GitHub repository.
2. In Streamlit Cloud, create a new app from the repository.
3. Set the main file to:

```text
streamlit_app.py
```

4. Add this in Streamlit Cloud secrets:

```toml
GEMINI_API_KEY = "your_google_gemini_key"
```

## Run Locally With Streamlit

```powershell
cd "C:\Users\INP\Documents\Codex\2026-06-20\https-chatgpt-com-share-6a361319-a3d8\outputs\isp_burnpur_contract_assistant_runnable"
$env:GEMINI_API_KEY="your_key"
streamlit run streamlit_app.py
```

## Rebuild The Index Locally

```powershell
cd "C:\Users\INP\Documents\Codex\2026-06-20\https-chatgpt-com-share-6a361319-a3d8\outputs\isp_burnpur_contract_assistant_runnable"
python local_contract_server.py build --source-dir "C:\Users\INP\Downloads"
```

Commit the generated `index/contract_index.json` and `index/summary.json` with the app.

## Lightweight Local Test Server

```powershell
$env:GEMINI_API_KEY="your_key"
python local_contract_server.py serve
```

Open:

```text
http://127.0.0.1:7860
```

## Ask From Terminal

```powershell
$env:GEMINI_API_KEY="your_key"
python local_contract_server.py ask --question "what safety should be followed in the furnace area?"
```

If the key is not set, the app still returns retrieved evidence so you can verify whether the correct contract text is being found.
