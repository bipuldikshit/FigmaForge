# FigmaForge - MCP Integration Guide

Use FigmaForge with VS Code Copilot Chat via the Model Context Protocol (MCP).

## Setup

The project includes `.vscode/mcp.json` which auto-configures the MCP server.

1. Open project in VS Code
2. Reload window (`Ctrl+Shift+P` → "Developer: Reload Window")
3. Verify: Command Palette → "MCP: List Servers" → Look for `figmaforge`

## Available Tools

| Tool | Description |
|------|-------------|
| `sync_figma` | Sync file and extract tokens |
| `generate_component` | Generate Angular component |
| `list_components` | List all components in file |
| `preview` | Get raw design JSON |
| `extract_tokens` | Export SCSS variables |

## Usage

Open Copilot Chat (`Ctrl+Shift+I`) and use natural language:

```
🔍 List components in file ABC123XYZ
```

```
🔥 Generate "primary-button" from node 1:23 in file ABC123XYZ
```

```
🎨 Extract design tokens from file ABC123XYZ
```

## Troubleshooting

**Server not found?**
- Reload VS Code window
- Check `.vscode/mcp.json` exists
- Ensure `.venv` has dependencies installed

**Token error?**
- Verify `FIGMA_TOKEN` in `.env`
- Check token at https://www.figma.com/settings
