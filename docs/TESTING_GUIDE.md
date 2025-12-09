# FigmaForge - Testing Guide

This guide covers testing all FigmaForge features via CLI and MCP (Copilot Chat).

---

## Prerequisites

1. **Activate virtual environment**
   ```bash
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # Mac/Linux
   ```

2. **Verify Figma token**
   ```bash
   echo %FIGMA_TOKEN%           # Windows
   echo $FIGMA_TOKEN            # Mac/Linux
   ```

3. **Get your Figma file key and node ID**
   - **File Key:** From URL `figma.com/design/{FILE_KEY}/...`
   - **Node ID:** Right-click element → "Copy link" → extract `node-id={NODE_ID}`

---

## CLI Commands

### Help
```bash
python cli.py --help
python cli.py generate --help
```

### Generate Components

```bash
# Angular (default)
python cli.py generate -f FILE_KEY -n "NODE_ID" -m my-button

# React
python cli.py generate -f FILE_KEY -n "NODE_ID" -m my-button --framework react

# Vue 3
python cli.py generate -f FILE_KEY -n "NODE_ID" -m my-button --framework vue

# Web Components
python cli.py generate -f FILE_KEY -n "NODE_ID" -m my-button --framework webcomponent
```

### Style Options

```bash
# SCSS (default)
python cli.py generate -f FILE_KEY -n "NODE_ID" -m component --style scss

# Tailwind CSS
python cli.py generate -f FILE_KEY -n "NODE_ID" -m component --style tailwind
```

### Layout Options

```bash
# Absolute positioning (default)
python cli.py generate -f FILE_KEY -n "NODE_ID" -m component

# Responsive flexbox
python cli.py generate -f FILE_KEY -n "NODE_ID" -m component --responsive
```

### Additional Options

```bash
# Dry run (preview without writing files)
python cli.py generate -f FILE_KEY -n "NODE_ID" -m component --dry-run

# Bypass cache (fresh API fetch)
python cli.py generate -f FILE_KEY -n "NODE_ID" -m component --no-cache
```

### Cache Management

```bash
python cli.py cache          # View cache statistics
python cli.py cache --clear  # Clear all cached data
```

### Watch Mode

```bash
# Auto-regenerate on Figma file changes
python cli.py watch -f FILE_KEY -n "NODE_ID" -m component --interval 30
```

### Sync & Initialize

```bash
python cli.py sync -f FILE_KEY    # Sync file and extract tokens
python cli.py init                # Initialize project directories
```

---

## MCP Testing (Copilot Chat)

### Verify MCP Server
1. Open VS Code in FigmaForge directory
2. `Ctrl+Shift+P` → "Developer: Reload Window"
3. `Ctrl+Shift+P` → "MCP: List Servers" → Verify "figmaforge" appears

### Test in Copilot Chat
```
List all components in Figma file YOUR_FILE_KEY

Generate "button" from node NODE_ID in file YOUR_FILE_KEY

Generate a React component called "card" from node NODE_ID in file YOUR_FILE_KEY
```

---

## Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## Feature Verification

| Feature | Command | Expected Output |
|---------|---------|-----------------|
| Angular | `--framework angular` | `.ts`, `.html`, `.scss` files |
| React | `--framework react` | `.tsx`, `.module.css` files |
| Vue | `--framework vue` | `.vue` file |
| Web Components | `--framework webcomponent` | `.js` file |
| Tailwind | `--style tailwind` | `.tailwind.json` file |
| Responsive | `--responsive` | Flexbox CSS properties |
| Dry Run | `--dry-run` | Console preview, no files |
| Caching | Run generate twice | "⚡ Cache hit" message |
| Watch Mode | `watch` command | "👀 Watch Mode" output |

---

## Troubleshooting

### FIGMA_TOKEN not set
```bash
cp .env.template .env
# Edit .env and add your token
```

### Rate limit hit
- Wait 60 seconds (auto-retry enabled)
- Use caching to reduce API calls

### MCP server not found
1. Reload VS Code window
2. Check `.vscode/mcp.json` exists
3. Run `pip install -r requirements.txt`
