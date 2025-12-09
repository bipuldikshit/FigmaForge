# FigmaForge - MCP Integration Guide

Use FigmaForge with VS Code GitHub Copilot Chat via the Model Context Protocol (MCP).

---

## Setup

The project includes `.vscode/mcp.json` which auto-configures the MCP server.

1. Open the FigmaForge project in VS Code
2. Reload window (`Ctrl+Shift+P` → "Developer: Reload Window")
3. Verify: Command Palette → "MCP: List Servers" → Look for `figmaforge`

---

## Available Tools

| Tool | Description |
|------|-------------|
| `generate_component` | Generate component for Angular, React, Vue, or Web Components |
| `sync_figma` | Sync Figma file and extract design tokens |
| `list_components` | List all components in a Figma file |
| `preview` | Get raw design JSON for a node |
| `extract_tokens` | Export design tokens as SCSS variables |

---

## generate_component Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `fileKey` | string | ✅ | - | Figma file key from URL |
| `nodeId` | string | ✅ | - | Node ID (format: `1:23`) |
| `componentName` | string | ✅ | - | Component name (kebab-case) |
| `framework` | string | ❌ | `angular` | `angular`, `react`, `vue`, `webcomponent` |
| `styleFormat` | string | ❌ | `scss` | `scss`, `tailwind` |
| `responsive` | boolean | ❌ | `false` | Use flexbox layouts |
| `dryRun` | boolean | ❌ | `false` | Preview without writing files |
| `noCache` | boolean | ❌ | `false` | Bypass API cache |
| `outputPath` | string | ❌ | - | Custom output directory |

---

## Usage Examples

Open Copilot Chat (`Ctrl+Shift+I`) and use natural language:

### List Components
```
List all components in Figma file ABC123XYZ
```

### Generate Angular Component
```
Generate "primary-button" from node 1:23 in file ABC123XYZ
```

### Generate React Component
```
Generate a React component called "user-card" from node 5:67 in file ABC123XYZ
```

### Generate Vue Component
```
Generate a Vue component called "nav-bar" from node 2:34 using vue framework in file ABC123XYZ
```

### Generate Web Component
```
Generate a Web Component called "custom-modal" from node 3:45 with webcomponent framework in file ABC123XYZ
```

### With Tailwind Styling
```
Generate "hero-section" from node 4:56 in file ABC123XYZ using tailwind styling
```

### Responsive Layout
```
Generate "dashboard" from node 1:23 in file ABC123XYZ with responsive layout
```

### Dry Run Preview
```
Preview what would be generated for node 1:23 in file ABC123XYZ without writing files
```

### Bypass Cache
```
Generate "settings-panel" from node 2:34 in file ABC123XYZ with fresh data (no cache)
```

---

## Troubleshooting

### Server not found
1. Reload VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window")
2. Verify `.vscode/mcp.json` exists
3. Ensure virtual environment has all dependencies: `pip install -r requirements.txt`

### Token error
1. Verify `FIGMA_TOKEN` is set in `.env` file
2. Check token validity at https://www.figma.com/settings

### Encoding issues (Windows)
Ensure `mcp.json` includes:
```json
{
  "env": {
    "PYTHONIOENCODING": "utf-8"
  }
}
```

### Rate limit errors
- FigmaForge auto-retries after 60 seconds
- Caching reduces API calls on repeat generations
- Avoid `noCache: true` for repeated requests
