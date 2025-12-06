"""MCP Stdio Server for VS Code Copilot Chat integration.

Exposes Figma-to-Angular tools via the Model Context Protocol (MCP).
"""

import os
import sys
import json
import asyncio
from typing import Any
from dotenv import load_dotenv

# Windows UTF-8 fix (must be set before MCP wraps stdio)
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.figma.client import FigmaClient, FigmaAPIError
from src.figma.normalizer import FigmaNormalizer
from src.extractors.tokens import TokenExtractor
from src.extractors.scss_generator import SCSSGenerator
from src.generators.component_generator import ComponentGenerator

load_dotenv()

mcp = Server("figmaforge")

_figma_client: FigmaClient | None = None
_component_generator: ComponentGenerator | None = None


def get_figma_client() -> FigmaClient:
    global _figma_client
    if _figma_client is None:
        _figma_client = FigmaClient()
    return _figma_client


def get_component_generator() -> ComponentGenerator:
    global _component_generator
    if _component_generator is None:
        output_path = os.getenv("ANGULAR_OUTPUT_PATH", "./src/app/components")
        assets_path = os.getenv("ASSETS_OUTPUT_PATH", "./src/assets/figma")
        _component_generator = ComponentGenerator(
            figma_client=get_figma_client(),
            output_path=output_path,
            assets_output_path=assets_path
        )
    return _component_generator


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """Register available MCP tools."""
    return [
        Tool(
            name="sync_figma",
            description="""Sync a Figma file and extract design information.

Fetches the file structure, normalizes components, and extracts design tokens.
Use this to explore available components before generating code.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fileKey": {
                        "type": "string",
                        "description": "Figma file key from URL"
                    },
                    "nodeIds": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: specific node IDs to sync"
                    }
                },
                "required": ["fileKey"]
            }
        ),
        Tool(
            name="generate_component",
            description="""Generate an Angular component from a Figma node.

Creates TypeScript, HTML, and SCSS files for a standalone Angular component.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fileKey": {"type": "string", "description": "Figma file key"},
                    "nodeId": {"type": "string", "description": "Node ID (format: '1:23')"},
                    "componentName": {"type": "string", "description": "Component name in kebab-case"},
                    "styleFormat": {"type": "string", "enum": ["scss", "tailwind"]},
                    "outputPath": {"type": "string", "description": "Custom output path"}
                },
                "required": ["fileKey", "nodeId", "componentName"]
            }
        ),
        Tool(
            name="preview",
            description="""Get raw design JSON and tokens for a Figma node.

Useful for inspecting design details before generating a component.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fileKey": {"type": "string", "description": "Figma file key"},
                    "nodeId": {"type": "string", "description": "Node ID"}
                },
                "required": ["fileKey", "nodeId"]
            }
        ),
        Tool(
            name="list_components",
            description="""List all components and frames in a Figma file.

Scans the file and returns available components for code generation.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fileKey": {"type": "string", "description": "Figma file key"}
                },
                "required": ["fileKey"]
            }
        ),
        Tool(
            name="extract_tokens",
            description="""Extract design tokens from a Figma file.

Extracts colors, typography, spacing, radii, and shadows as SCSS variables.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "fileKey": {"type": "string", "description": "Figma file key"},
                    "outputPath": {"type": "string", "description": "Output path for SCSS"}
                },
                "required": ["fileKey"]
            }
        )
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route tool calls to handlers."""
    try:
        handlers = {
            "sync_figma": handle_sync_figma,
            "generate_component": handle_generate_component,
            "preview": handle_preview,
            "list_components": handle_list_components,
            "extract_tokens": handle_extract_tokens,
        }
        handler = handlers.get(name)
        if handler:
            return await handler(arguments)
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except FigmaAPIError as e:
        return [TextContent(type="text", text=f"Figma API Error: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


async def handle_sync_figma(args: dict[str, Any]) -> list[TextContent]:
    client = get_figma_client()
    file_data = client.get_file(args["fileKey"], args.get("nodeIds"))
    
    normalizer = FigmaNormalizer()
    normalized = normalizer.normalize_file(file_data)
    
    token_extractor = TokenExtractor()
    tokens = token_extractor.extract_tokens(normalized["nodes"])
    
    result = {
        "success": True,
        "fileName": normalized["file_name"],
        "lastModified": normalized["last_modified"],
        "componentCount": len(normalized["components"]),
        "components": [
            {"id": c["id"], "name": c["name"], "hasAssets": len(c["assets"]) > 0}
            for c in normalized["components"][:20]
        ],
        "tokenSummary": {
            "colors": len(tokens.get("colors", {})),
            "typography": len(tokens.get("typography", {})),
            "spacing": len(tokens.get("spacing", {}))
        }
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def handle_generate_component(args: dict[str, Any]) -> list[TextContent]:
    generator = get_component_generator()
    
    if args.get("outputPath"):
        generator.output_path = args["outputPath"]
    
    result = generator.generate_component(
        file_key=args["fileKey"],
        node_id=args["nodeId"],
        component_name=args["componentName"],
        regenerate=False
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def handle_preview(args: dict[str, Any]) -> list[TextContent]:
    client = get_figma_client()
    nodes_data = client.get_file_nodes(args["fileKey"], [args["nodeId"]])
    
    if not nodes_data or args["nodeId"] not in nodes_data:
        return [TextContent(type="text", text=f"Node {args['nodeId']} not found")]
    
    node_wrapper = nodes_data[args["nodeId"]]
    node = node_wrapper.get("document") or node_wrapper
    
    token_extractor = TokenExtractor()
    tokens = token_extractor.extract_tokens({args["nodeId"]: node})
    
    result = {
        "success": True,
        "nodeType": node.get("type"),
        "nodeName": node.get("name"),
        "tokens": tokens
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def handle_list_components(args: dict[str, Any]) -> list[TextContent]:
    client = get_figma_client()
    file_data = client.get_file(args["fileKey"])
    
    normalizer = FigmaNormalizer()
    normalized = normalizer.normalize_file(file_data)
    
    result = {
        "success": True,
        "fileName": normalized["file_name"],
        "totalComponents": len(normalized["components"]),
        "components": [
            {"id": c["id"], "name": c["name"], "type": c.get("type", "COMPONENT"), "hasAssets": len(c["assets"]) > 0}
            for c in normalized["components"]
        ]
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def handle_extract_tokens(args: dict[str, Any]) -> list[TextContent]:
    output_path = args.get("outputPath", "./design-tokens.scss")
    
    client = get_figma_client()
    file_data = client.get_file(args["fileKey"])
    
    normalizer = FigmaNormalizer()
    normalized = normalizer.normalize_file(file_data)
    
    token_extractor = TokenExtractor()
    tokens = token_extractor.extract_tokens(normalized["nodes"])
    
    scss_generator = SCSSGenerator()
    scss_content = scss_generator.generate_scss(tokens)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(scss_content)
    
    result = {
        "success": True,
        "outputPath": output_path,
        "tokenCounts": {
            "colors": len(tokens.get("colors", {})),
            "typography": len(tokens.get("typography", {})),
            "spacing": len(tokens.get("spacing", {})),
            "radii": len(tokens.get("radii", {})),
            "shadows": len(tokens.get("shadows", {}))
        }
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream, mcp.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
