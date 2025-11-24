import asyncio
import ollama
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

# Initialize the server
server = Server("ollama-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_completion",
            description="Generate text using Ollama",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to generate text for",
                    },
                    "model": {
                        "type": "string",
                        "description": "The model to use (default: llama3)",
                    },
                },
                "required": ["prompt"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "generate_completion":
        if not arguments:
            raise ValueError("Arguments are required")
            
        prompt = arguments.get("prompt")
        model = arguments.get("model", "llama3")
        
        if not prompt:
            raise ValueError("Prompt is required")

        try:
            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
            )
            
            return [
                types.TextContent(
                    type="text",
                    text=response['message']['content']
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
            
    raise ValueError(f"Tool {name} not found")

async def main():
    # Run the server using stdin/stdout
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ollama-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
