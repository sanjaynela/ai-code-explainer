# AI Code Explainer

An AI-powered tool that reads your GitHub repository and explains the code using LangChain and Ollama (Meta's Llama models running locally).

## What It Does

This tool:
- Fetches code files from any GitHub repository
- Summarizes each file using a local LLM (Llama via Ollama)
- Generates a comprehensive repository-level summary
- Optionally pushes the summary back to GitHub as `SUMMARY.md`

## Features

- **100% Local**: Uses Ollama to run Meta's Llama models locally - no API keys or costs
- **Comprehensive Analysis**: Analyzes individual files and the entire repository architecture
- **Flexible**: Configure which file types to analyze
- **GitHub Integration**: Optionally push summaries back to your repo
- **PR Template Generator**: Automatically generates a detailed Pull Request description based on your git diff using MCP

## Prerequisites

1. **Ollama** - Download from [https://ollama.com/download](https://ollama.com/download)
2. **Python 3.8+**
3. **GitHub Personal Access Token** (optional, only for private repos or pushing summaries)

## Setup

### 1. Install Ollama and Pull a Model

```bash
# Download and install Ollama from https://ollama.com/download

# Pull a Llama model (llama3 is recommended)
ollama pull llama3
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)

If you want to access private repositories or push summaries to GitHub:

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your GitHub token
# GITHUB_TOKEN=your_github_token_here
```

Generate a GitHub token at: [https://github.com/settings/tokens](https://github.com/settings/tokens)

## Usage

### Basic Usage

1. Edit `main.py` and update the repository configuration:

```python
REPO_OWNER = "sanjaynela"
REPO_NAME = "personalRepoNextJs"
```

2. Run the script:

```bash
python main.py
```

### Configuration Options

In `main.py`, you can customize:

- **Repository**: Change `REPO_OWNER` and `REPO_NAME`
- **File Extensions**: Set `FILE_EXTENSIONS` to filter files (e.g., `['.py']` for Python only)
- **Ollama Model**: Change `OLLAMA_MODEL` (default: `"llama3"`)
- **Push to GitHub**: Set `PUSH_TO_GITHUB = True` to automatically push `SUMMARY.md`

### Example: Analyze Only Python Files

```python
FILE_EXTENSIONS = ['.py']  # Only analyze .py files
```

### Example: Use Different Model

```python
OLLAMA_MODEL = "llama3.1"  # Make sure to pull it first: ollama pull llama3.1
```

## Pull Request Generator

The project includes a tool to generate Pull Request descriptions automatically using the Model Context Protocol (MCP).

### Usage

1. Stage your changes:
```bash
git add .
```

2. Run the generator:
```bash
python pr_generator.py
```

This will:
1. Read your staged and unstaged git changes
2. Connect to the local Ollama MCP server (`ollama_server.py`)
3. Generate a comprehensive PR description including title, summary, and file breakdown

### Custom MCP Server

You can also use any other MCP server (like the official Ollama server via npx):

```bash
python pr_generator.py npx -y @modelcontextprotocol/server-ollama
```

## Output

The script generates a `SUMMARY.md` file containing:

1. **Overall Summary**: High-level explanation of the repository
2. **Architecture**: How components fit together
3. **File-by-File Breakdown**: Individual summaries for each file

## How It Works

1. **Fetch Files**: Uses GitHub API to recursively fetch all files from the repository
2. **Summarize Files**: Uses LangChain + Ollama to summarize each file individually
3. **Generate Summary**: Combines all file summaries into a repository-level overview
4. **Save Output**: Writes `SUMMARY.md` locally (and optionally pushes to GitHub)

## Technology Stack

- **LangChain**: Framework for building AI applications with LLMs
- **Ollama**: Local LLM runtime for running Llama models
- **Meta Llama**: Open-source language models (llama3, llama3.1, etc.)
- **GitHub API**: For fetching repository contents

## Why LangChain?

LangChain provides:
- **Modularity**: Reusable chains and prompt templates
- **Composability**: Easy to extend with new features
- **Structure**: Prevents prompt chaos as your use case grows

Instead of one-off prompt hacks, you build maintainable AI workflows.

## Notes

- First run may be slow as Ollama downloads/initializes the model
- Large repositories may take time to process
- Make sure Ollama is running before executing the script
- For private repos, you need a GitHub token with `repo` scope

## Contributing

Feel free to open issues or submit pull requests!

## License

This project is open source and available for personal and commercial use.

## Acknowledgments

Based on the Medium article: "I Built an AI That Reads My GitHub Repo and Explains the Code (Using LangChain)"

---

**Happy Coding!**

