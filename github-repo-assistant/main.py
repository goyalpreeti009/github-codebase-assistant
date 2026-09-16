import os
import sys
from dotenv import load_dotenv
import github
from github import Github
from google import genai
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()
console = Console()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GITHUB_TOKEN or not GEMINI_KEY:
    console.print(
        "[bold red]Error: GITHUB_TOKEN or GEMINI_API_KEY is missing from your .env file![/bold red]"
    )
    sys.exit(1)

# Clean authentication without deprecation warning
auth = github.Auth.Token(GITHUB_TOKEN)
gh = Github(auth=auth)
ai = genai.Client(api_key=GEMINI_KEY)

# Fallback chain in case one model is overloaded (503)
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-3.6-flash"]

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".md",
    ".json",
    ".html",
    ".css",
    ".cpp",
    ".c",
    ".java",
)


def extract_repo_context(repo_name: str, max_files: int = 10) -> str:
    """Recursively walks repository files and builds a concatenated code context string."""
    console.print(f"[cyan]Connecting to repository: {repo_name}...[/cyan]")
    repo = gh.get_repo(repo_name)
    contents = repo.get_contents("")

    code_context = (
        f"Repository: {repo.full_name}\n"
        f"Description: {repo.description or 'No description provided'}\n\n"
    )
    files_processed = 0

    with console.status("[yellow]Fetching repository files...[/yellow]"):
        while contents and files_processed < max_files:
            file_item = contents.pop(0)

            if file_item.type == "dir":
                if file_item.name not in IGNORED_DIRECTORIES:
                    contents.extend(repo.get_contents(file_item.path))
            else:
                if file_item.name.endswith(SUPPORTED_EXTENSIONS):
                    try:
                        decoded_text = file_item.decoded_content.decode("utf-8")
                        code_context += (
                            f"--- File: {file_item.path} ---\n"
                            f"{decoded_text[:1500]}\n\n"
                        )
                        files_processed += 1
                    except Exception:
                        continue

    return code_context


def generate_with_fallback(prompt: str) -> str:
    """Attempts generation across a fallback list of models if high traffic (503) occurs."""
    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            response = ai.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            last_error = e
            console.print(f"[dim yellow]Model {model_name} busy or unavailable. Trying fallback...[/dim yellow]")
            continue
    raise last_error


def main():
    console.rule("[bold green]GitHub Codebase Assistant[/bold green]")
    repo_input = console.input(
        "[yellow]Enter target repository (e.g., goyalpreeti009/asl-hand-sign-detection): [/yellow]"
    ).strip()

    try:
        context = extract_repo_context(repo_input)
        console.print("[green]Context successfully loaded![/green]\n")
    except Exception as exc:
        console.print(f"[bold red]Failed to load repository: {exc}[/bold red]")
        return

    console.print("[dim]Type your questions below. Enter 'exit' or 'q' to quit.[/dim]\n")

    while True:
        query = console.input("[bold blue]Ask a question: [/bold blue]").strip()
        if query.lower() in {"exit", "q"}:
            console.print("[yellow]Exiting assistant. Goodbye![/yellow]")
            break

        if not query:
            continue

        with console.status("[bold yellow]Analyzing codebase and generating answer...[/bold yellow]"):
            prompt = f"""
You are an expert software developer and technical code assistant.
Analyze the following codebase context:

{context}

User Question: {query}

Instructions:
- Provide an accurate, concise answer based directly on the provided code context.
- Cite specific files or directories when referencing architecture.
- Include brief code snippets where relevant.
"""
            try:
                answer = generate_with_fallback(prompt)
                console.print("\n")
                console.print(Markdown(answer))
                console.print("\n" + "-" * 60 + "\n")
            except Exception as e:
                console.print(f"[bold red]Error generating response: {e}[/bold red]")


if __name__ == "__main__":
    main()