import os
import streamlit as st
from dotenv import load_dotenv
import github
from github import Github
from google import genai

load_dotenv()

# Page configuration
st.set_page_config(page_title="GitHub Codebase Assistant", page_icon="💬", layout="wide")
st.title("💬 GitHub Codebase Assistant")
st.caption("Chat with any public GitHub repository using Google Gemini")

# Initialize API clients
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GITHUB_TOKEN or not GEMINI_KEY:
    st.error("Missing GITHUB_TOKEN or GEMINI_API_KEY in your .env file.")
    st.stop()

auth = github.Auth.Token(GITHUB_TOKEN)
gh = Github(auth=auth)
ai = genai.Client(api_key=GEMINI_KEY)

MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-3.6-flash"]
IGNORED_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
SUPPORTED_EXTS = (".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".json", ".html", ".css", ".cpp", ".c", ".java")

# Helper function to load repository files
def extract_repo_context(repo_name: str, max_files: int = 10) -> str:
    repo = gh.get_repo(repo_name)
    contents = repo.get_contents("")
    code_context = f"Repository: {repo.full_name}\nDescription: {repo.description or 'None'}\n\n"
    files_processed = 0

    while contents and files_processed < max_files:
        file_item = contents.pop(0)
        if file_item.type == "dir":
            if file_item.name not in IGNORED_DIRS:
                contents.extend(repo.get_contents(file_item.path))
        else:
            if file_item.name.endswith(SUPPORTED_EXTS):
                try:
                    text = file_item.decoded_content.decode("utf-8")
                    code_context += f"--- File: {file_item.path} ---\n{text[:1500]}\n\n"
                    files_processed += 1
                except Exception:
                    continue
    return code_context

# Helper function to handle model fallback
def ask_gemini(prompt: str) -> str:
    for model_name in MODELS_TO_TRY:
        try:
            res = ai.models.generate_content(model=model_name, contents=prompt)
            return res.text
        except Exception:
            continue
    raise RuntimeError("All Gemini models are currently busy. Please try again in a few seconds.")

# Sidebar for repository indexing
with st.sidebar:
    st.header("Configuration")
    repo_input = st.text_input("Target Repository", value="goyalpreeti009/asl-hand-sign-detection")
    index_btn = st.button("Index Repository", type="primary")

# Initialize session state for memory
if "context" not in st.session_state:
    st.session_state.context = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle repository indexing
if index_btn:
    with st.spinner("Extracting repository code via GitHub API..."):
        try:
            st.session_state.context = extract_repo_context(repo_input.strip())
            st.session_state.messages = []
            st.sidebar.success("Repository loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Failed to load repo: {e}")

# Display prior chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input and response generation
if user_prompt := st.chat_input("Ask a question about this repository..."):
    if not st.session_state.context:
        st.warning("Please click 'Index Repository' in the sidebar first.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing codebase..."):
                prompt = f"""
You are an expert developer assistant. Use the codebase context below to answer the user's question.

Context:
{st.session_state.context}

Question: {user_prompt}
"""
                try:
                    reply = ask_gemini(prompt)
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as err:
                    st.error(str(err))