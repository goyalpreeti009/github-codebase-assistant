# 💬 GitHub Codebase Assistant

I built this project because whenever I dive into someone else's open-source repository (or even revisit my own projects from months ago), I spend way too much time hopping between random files, trying to trace functions and figure out how everything connects. 

Instead of manually digging through lines of code, I wanted a simple terminal tool where I could just drop a repo link, ask a question in plain English, and get an immediate, contextual answer.

---

## 💡 What it Does

You give it a GitHub repository (`username/repository-name`), and the tool:
1. Talks to the GitHub API to fetch the directory structure and read through the key source files.
2. Filters out noise like `node_modules`, virtual environments, and build artifacts.
3. Feeds that codebase context into Google's Gemini model.
4. Lets you have a real back-and-forth chat in your terminal about how the code works, where specific features live, or how to fix a bug.

---

## 🛠️ Built With

* **Python**
* **PyGithub** – To fetch file trees and source code via GitHub's API
* **Google Gemini API (`google-genai`)** – The reasoning engine behind the code answers
* **Rich** – To make the terminal interface clean, readable, and nicely formatted
* **Python-dotenv** – To keep secret tokens strictly local and safe

---

