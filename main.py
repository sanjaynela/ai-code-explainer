"""
AI Code Explainer - GitHub Repository Analyzer
==============================================

This script uses LangChain and Ollama to:
1. Fetch code files from a GitHub repository
2. Summarize each file using a local LLM (Llama via Ollama)
3. Generate a comprehensive repository summary
4. Optionally push the summary back to GitHub as SUMMARY.md

Author: Based on Medium article about AI-powered code review
"""

import os
import requests
import base64
from typing import List, Dict, Optional
from dotenv import load_dotenv

# LangChain imports for LLM integration (using modern API)
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# Load environment variables from .env file
load_dotenv()

# Configuration constants
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional: for private repos or pushing summaries


def fetch_files(repo_path: str, file_extensions: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Fetches code files from a GitHub repository using the GitHub API.
    
    This function recursively fetches all files from the repository and filters
    them based on file extensions (e.g., .py, .js, .ts).
    
    Args:
        repo_path: Full GitHub API path to the repository contents
                  (e.g., "https://api.github.com/repos/owner/repo/contents")
        file_extensions: Optional list of file extensions to filter by
                        (e.g., ['.py', '.js', '.ts']). If None, fetches all files.
    
    Returns:
        List of dictionaries, each containing:
        - 'name': filename
        - 'path': relative path in repo
        - 'content': file content as string
    """
    files = []
    
    # Prepare headers for GitHub API (token optional but recommended)
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    def fetch_recursive(path: str):
        """
        Recursively fetch files from GitHub repository.
        Handles both files and directories.
        """
        try:
            response = requests.get(path, headers=headers)
            response.raise_for_status()  # Raise error for bad status codes
            data = response.json()
            
            # Handle case where API returns a single file object
            if isinstance(data, dict) and data.get('type') == 'file':
                data = [data]
            
            for item in data:
                if item['type'] == 'file':
                    # Filter by file extension if specified
                    if file_extensions:
                        file_ext = os.path.splitext(item['name'])[1]
                        if file_ext not in file_extensions:
                            continue
                    
                    # Fetch file content
                    if 'download_url' in item:
                        # For text files, use download_url
                        content_response = requests.get(item['download_url'], headers=headers)
                        content = content_response.text
                    elif 'content' in item:
                        # For base64 encoded content, decode it
                        content = base64.b64decode(item['content']).decode('utf-8')
                    else:
                        content = ""
                    
                    files.append({
                        'name': item['name'],
                        'path': item['path'],
                        'content': content
                    })
                    
                elif item['type'] == 'dir':
                    # Recursively fetch files from subdirectories
                    fetch_recursive(item['url'])
                    
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from {path}: {e}")
    
    # Start fetching from the root directory
    fetch_recursive(repo_path)
    
    return files


def summarize_file(filename: str, code: str, llm: OllamaLLM) -> str:
    """
    Uses LangChain to summarize a single code file using the LLM.
    
    This function creates a prompt that asks the LLM to act as a senior
    software engineer and explain what the file does, its main functions,
    logic, and purpose.
    
    Args:
        filename: Name of the file being summarized
        code: Content of the code file
        llm: Initialized Ollama LLM instance
    
    Returns:
        String summary of the file
    """
    # Create a prompt template for file summarization
    # The template uses {filename} and {code} as input variables
    summary_prompt = PromptTemplate(
        input_variables=["filename", "code"],
        template="""
You are a senior software engineer. Summarize what the file `{filename}` does.

Explain its main functions, logic, and purpose in clear language.

Code:

```python
{code}
```

Provide a concise but comprehensive summary.
"""
    )
    
    # Use modern LangChain API: create a chain using the pipe operator
    # This combines the prompt with the LLM: prompt | llm
    chain = summary_prompt | llm
    
    # Invoke the chain with the filename and code as inputs
    # Using invoke() instead of deprecated run()
    result = chain.invoke({"filename": filename, "code": code})
    
    # Extract the content if it's a message object, otherwise return as string
    if hasattr(result, 'content'):
        return result.content
    return str(result)


def generate_repo_summary(summaries: List[Dict[str, str]], llm: OllamaLLM) -> str:
    """
    Generates a high-level summary of the entire repository by combining
    individual file summaries.
    
    This function takes all file summaries and asks the LLM to synthesize
    them into a cohesive explanation of the repository's architecture,
    purpose, and how components fit together.
    
    Args:
        summaries: List of dictionaries with 'filename' and 'summary' keys
        llm: Initialized Ollama LLM instance
    
    Returns:
        String containing the comprehensive repository summary
    """
    # Format the file summaries for the prompt
    # Each summary is formatted as "filename: summary"
    file_summaries_text = "\n\n".join([
        f"**{s['filename']}**\n{s['summary']}" 
        for s in summaries
    ])
    
    # Create a prompt template for repository-level summarization
    merge_prompt = PromptTemplate(
        input_variables=["file_summaries"],
        template="""
You are an AI technical writer. Combine these file summaries into a single, high-level explanation
of what the entire repository does, how its components fit together, and what could be improved.

Summaries:

{file_summaries}

Provide a well-structured summary that includes:
1. Overall purpose of the repository
2. Architecture and how components interact
3. Key technologies and patterns used
4. Potential improvements or areas of concern
"""
    )
    
    # Use modern LangChain API: create a chain using the pipe operator
    merge_chain = merge_prompt | llm
    
    # Invoke the chain with file summaries as input
    result = merge_chain.invoke({"file_summaries": file_summaries_text})
    
    # Extract the content if it's a message object, otherwise return as string
    if hasattr(result, 'content'):
        return result.content
    return str(result)


def push_summary_to_github(repo: str, summary_text: str, token: str) -> bool:
    """
    Pushes the generated summary to GitHub as a SUMMARY.md file.
    
    This function uses the GitHub API to create or update a SUMMARY.md file
    in the repository. It requires a GitHub personal access token with
    appropriate permissions.
    
    Args:
        repo: Repository in format "owner/repo" (e.g., "sanjaynela/personalRepoNextJs")
        summary_text: The summary text to push
        token: GitHub personal access token
    
    Returns:
        True if successful, False otherwise
    """
    # Encode the summary text to base64 (required by GitHub API)
    content_encoded = base64.b64encode(summary_text.encode('utf-8')).decode('utf-8')
    
    # GitHub API endpoint for creating/updating a file
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/SUMMARY.md"
    
    # Prepare the request payload
    data = {
        "message": "Add AI-generated summary",
        "content": content_encoded,
        "branch": "main"  # Adjust if your default branch is different
    }
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        # Check if file already exists (to update instead of create)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # File exists, we need to include the SHA for update
            existing_file = response.json()
            data["sha"] = existing_file["sha"]
        
        # Create or update the file
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        
        print(f"[SUCCESS] Successfully pushed SUMMARY.md to {repo}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error pushing summary to GitHub: {e}")
        return False


def main():
    """
    Main function that orchestrates the entire code explanation workflow.
    
    Steps:
    1. Fetch files from GitHub repository
    2. Initialize Ollama LLM
    3. Summarize each file
    4. Generate repository-level summary
    5. Save summary to local file
    6. Optionally push to GitHub
    """
    # Configuration: Update these values for your repository
    REPO_OWNER = "sanjaynela"
    REPO_NAME = "personalRepoNextJs"
    GITHUB_API = f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/contents"
    
    # File extensions to analyze (None = all files)
    # Common options: ['.py'], ['.js', '.ts', '.tsx'], ['.py', '.js'], etc.
    FILE_EXTENSIONS = None  # Set to ['.py'] to only analyze Python files
    
    # Ollama model to use (make sure you've run: ollama pull llama3)
    OLLAMA_MODEL = "llama3"
    
    # Whether to push summary back to GitHub
    PUSH_TO_GITHUB = False  # Set to True if you want to push SUMMARY.md
    
    print("=" * 60)
    print("AI Code Explainer - GitHub Repository Analyzer")
    print("=" * 60)
    print(f"\nRepository: {REPO_OWNER}/{REPO_NAME}")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"File extensions: {FILE_EXTENSIONS or 'All files'}")
    print("\n" + "-" * 60)
    
    # Step 1: Fetch files from GitHub
    print("\n[1/5] Fetching files from GitHub repository...")
    repo_files = fetch_files(GITHUB_API, file_extensions=FILE_EXTENSIONS)
    print(f"[SUCCESS] Fetched {len(repo_files)} files.")
    
    if not repo_files:
        print("[ERROR] No files found. Exiting.")
        return
    
    # Step 2: Initialize Ollama LLM
    print("\n[2/5] Initializing Ollama LLM...")
    try:
        # Initialize Ollama with the specified model
        # temperature=0 makes responses more deterministic
        llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0)
        print(f"[SUCCESS] LLM initialized with model: {OLLAMA_MODEL}")
    except Exception as e:
        print(f"[ERROR] Error initializing Ollama: {e}")
        print("Make sure Ollama is running and you've pulled the model:")
        print(f"  ollama pull {OLLAMA_MODEL}")
        return
    
    # Step 3: Summarize each file
    print("\n[3/5] Summarizing individual files...")
    summaries = []
    for i, file in enumerate(repo_files, 1):
        print(f"  Processing {i}/{len(repo_files)}: {file['name']}...")
        try:
            summary = summarize_file(file['name'], file['content'], llm)
            summaries.append({
                "filename": file['name'],
                "path": file['path'],
                "summary": summary
            })
        except Exception as e:
            print(f"  [ERROR] Error summarizing {file['name']}: {e}")
            # Continue with other files even if one fails
            continue
    
    print(f"[SUCCESS] Summarized {len(summaries)} files.")
    
    # Step 4: Generate repository-level summary
    print("\n[4/5] Generating repository-level summary...")
    try:
        repo_summary = generate_repo_summary(summaries, llm)
        print("[SUCCESS] Repository summary generated.")
    except Exception as e:
        print(f"[ERROR] Error generating repository summary: {e}")
        return
    
    # Step 5: Save summary to local file
    print("\n[5/5] Saving summary to SUMMARY.md...")
    output_content = f"""# Repository Summary: {REPO_OWNER}/{REPO_NAME}

Generated by AI Code Explainer using LangChain and Ollama

---

## Overall Summary

{repo_summary}

---

## File-by-File Breakdown

"""
    
    # Add individual file summaries
    for summary in summaries:
        output_content += f"### {summary['filename']}\n\n"
        output_content += f"{summary['summary']}\n\n"
        output_content += "---\n\n"
    
    # Write to local file
    with open("SUMMARY.md", "w", encoding="utf-8") as f:
        f.write(output_content)
    
    print("[SUCCESS] Summary saved to SUMMARY.md")
    
    # Step 6 (Optional): Push summary to GitHub
    if PUSH_TO_GITHUB:
        if not GITHUB_TOKEN:
            print("\n[WARNING] GITHUB_TOKEN not set. Skipping GitHub push.")
        else:
            print("\n[6/6] Pushing summary to GitHub...")
            push_summary_to_github(
                f"{REPO_OWNER}/{REPO_NAME}",
                output_content,
                GITHUB_TOKEN
            )
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

