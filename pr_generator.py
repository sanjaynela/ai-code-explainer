#!/usr/bin/env python3
"""
PR Generator via MCP
====================

This script generates a Pull Request description based on your local git diff
using an MCP (Model Context Protocol) server.

Usage:
    python pr_generator.py [server_command] [server_args...]

Example:
    python pr_generator.py npx -y @modelcontextprotocol/server-ollama
    
    # Or set via environment variables:
    export MCP_SERVER_COMMAND="npx"
    export MCP_SERVER_ARGS="-y @modelcontextprotocol/server-ollama"
    python pr_generator.py
"""

import asyncio
import os
import subprocess
import sys
from typing import Optional, List, Dict, Any

# Check if mcp is installed
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Error: 'mcp' package not found. Please run: pip install mcp")
    sys.exit(1)


def get_git_diff() -> str:
    """
    Retrieves the git diff of the current repository.
    """
    try:
        # Get staged changes
        staged = subprocess.check_output(
            ["git", "diff", "--cached"], text=True
        )
        
        # Get unstaged changes
        unstaged = subprocess.check_output(
            ["git", "diff"], text=True
        )
        
        full_diff = staged + "\n" + unstaged
        
        if not full_diff.strip():
            print("No changes detected in git repository.")
            sys.exit(0)
            
        return full_diff
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or git is not installed.")
        sys.exit(1)


async def generate_pr_description(diff: str, server_params: StdioServerParameters):
    """
    Connects to the MCP server and requests a PR description.
    """
    print(f"Connecting to MCP server: {server_params.command} {' '.join(server_params.args)}")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools_result = await session.list_tools()
            tools = tools_result.tools
            
            if not tools:
                print("No tools found on the MCP server.")
                return

            print(f"Found {len(tools)} tools: {', '.join(t.name for t in tools)}")
            
            # Look for a suitable tool
            # We look for tools that might generate text or chat
            target_tool = None
            for tool in tools:
                if tool.name in ["chat", "generate", "summarize", "completion"]:
                    target_tool = tool
                    break
            
            if not target_tool:
                # Fallback: use the first tool if it looks promising or just try 'chat'
                # Some servers might have specific names.
                # For now, we'll try to find one with "chat" or "generate" in the name
                for tool in tools:
                    if "chat" in tool.name.lower() or "generate" in tool.name.lower():
                        target_tool = tool
                        break
            
            if not target_tool:
                print("Could not find a suitable tool for generation. Available tools:", [t.name for t in tools])
                return

            print(f"Using tool: {target_tool.name}")
            
            # Construct the prompt
            prompt = f"""
You are an expert software engineer. Please generate a comprehensive Pull Request description for the following code changes.
Include:
1. A clear title.
2. A summary of changes.
3. A list of modified files and key changes in each.
4. Any potential risks or things to note.

Git Diff:
{diff[:10000]}  # Truncate if too long to avoid context limits
"""
            
            # Call the tool
            # Note: The arguments depend on the specific tool's schema.
            # Most 'chat' tools take 'messages' or 'prompt'.
            # We will try to guess or use a standard format.
            
            arguments = {}
            input_schema = target_tool.inputSchema
            properties = input_schema.get("properties", {})
            
            if "messages" in properties:
                arguments["messages"] = [{"role": "user", "content": prompt}]
            elif "prompt" in properties:
                arguments["prompt"] = prompt
            elif "text" in properties:
                arguments["text"] = prompt
            else:
                # Fallback: try to pass it as the first argument found
                keys = list(properties.keys())
                if keys:
                    arguments[keys[0]] = prompt
            
            try:
                result = await session.call_tool(target_tool.name, arguments=arguments)
                
                # Print the result
                # The result is a list of content items (TextContent or ImageContent)
                print("\n" + "="*40)
                print("GENERATED PR DESCRIPTION")
                print("="*40 + "\n")
                
                for content in result.content:
                    if content.type == "text":
                        print(content.text)
                    else:
                        print(f"[{content.type} content]")
                        
            except Exception as e:
                print(f"Error calling tool: {e}")


def main():
    # Determine server command
    command = os.environ.get("MCP_SERVER_COMMAND")
    args = os.environ.get("MCP_SERVER_ARGS", "").split()
    
    # Override with CLI args if provided
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = sys.argv[2:]
    
    if not command:
        # Default suggestion
        print("Usage: python pr_generator.py <server_command> [args...]")
        print("\nNo server specified. Using local python server: python ollama_server.py")
        command = "/Users/sanjay/personalProjects/aiCodeExplainer/.venv/bin/python"
        args = ["ollama_server.py"]
    
    # Get git diff
    diff = get_git_diff()
    
    # Run async main
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=os.environ.copy()
    )
    
    try:
        asyncio.run(generate_pr_description(diff, server_params))
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
