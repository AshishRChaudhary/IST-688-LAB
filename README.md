# IST 688 - Lab Application

A multipage Streamlit app for "Building Human-Centered AI Applications." All labs live as
sibling `.py` files at the repo root, added as pages via `st.navigation` in `streamlit_app.py`.
New labs get added the same way: drop in a `LabX.py` and add it to the navigation list.

- **Lab 1** (`Lab1.py`) - Document question answering: upload a `.txt`/`.md` file, ask a
  question about it, and get an answer from GPT (user supplies and validates their own
  API key via a text input).
- **Lab 2** (`Lab2.py`, default page) - Document summarizer: upload a PDF and get a
  summary, with sidebar options for language and summary format, and a choice between
  models via a checkbox.

Assignment instruction PDFs are kept locally under `Instructions/` and are gitignored
(not part of the repo).

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Add your OpenAI API key to `.streamlit/secrets.toml`:

   ```
   OPENAI_API_KEY = "your-key-here"
   ```

3. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

### Deploying to Streamlit Community Cloud

`.streamlit/secrets.toml` is gitignored and never pushed to GitHub. After deploying,
add the same key under the app's **Settings > Secrets** in the Streamlit Community Cloud
dashboard — it's stored separately from the repo and injected into `st.secrets` at runtime.
