<p align="center">
  <img src="https://img.shields.io/badge/Figma-F24E1E?style=for-the-badge&logo=figma&logoColor=white" alt="Figma" />
  <img src="https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white" alt="Angular" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/MCP-VS_Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white" alt="MCP" />
</p>

<h1 align="center">🔥 FigmaForge</h1>

<p align="center">
  <strong>Forge production-ready Angular components from Figma designs</strong>
</p>

<p align="center">
  <em>AI-powered code generation via VS Code Copilot Chat + CLI</em>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-examples">Examples</a>
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Pixel-Perfect** | Exact positioning, colors, typography from your designs |
| 🤖 **AI-Driven** | Generate via VS Code Copilot Chat with natural language |
| ⌨️ **CLI Support** | Command-line interface for scripting and CI/CD |
| 🎨 **Design Tokens** | Extract colors, fonts, spacing as SCSS variables |
| 📦 **Asset Export** | Automatic SVG/PNG extraction |
| 🔄 **Non-Destructive** | Regenerate without losing custom code |

## 🚀 Quick Start

```bash
# Clone & install
git clone https://github.com/aspect-developer/FigmaForge.git
cd FigmaForge

# Setup
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt

# Configure
cp .env.template .env
# Add your FIGMA_TOKEN to .env
```

> 💡 Get your Figma token at [figma.com/settings](https://www.figma.com/settings)

## 🎮 Usage

### 🤖 AI-Driven (VS Code Copilot Chat)

1. Open project in VS Code
2. Reload window (`Ctrl+Shift+P` → "Developer: Reload Window")
3. Open Copilot Chat (`Ctrl+Shift+I`)
4. Chat naturally:

```
📝 "List all components in file ABC123XYZ"

🔥 "Generate hero-section from node 1:23 in file ABC123XYZ"

🎯 "Extract design tokens from file ABC123XYZ"
```

### ⌨️ CLI

```bash
# Sync & extract tokens
python cli.py sync -f ABC123XYZ

# Generate component
python cli.py generate -f ABC123XYZ -n 1:23 -m my-button

# Initialize new project
python cli.py init
```

## 📁 Generated Output

```
src/app/components/my-button/
├── my-button.component.ts      # TypeScript with @Input()
├── my-button.component.html    # Semantic HTML
└── my-button.component.scss    # BEM-style SCSS
```

## 🔍 Finding Figma IDs

| ID | Location | Example |
|----|----------|---------|
| **File Key** | URL: `figma.com/file/ABC123XYZ/...` | `ABC123XYZ` |
| **Node ID** | Right-click → Copy link → `?node-id=1-23` | `1:23` |

## 📂 Project Structure

```
FigmaForge/
├── 🎯 cli.py                 # CLI commands
├── 🤖 mcp_stdio_server.py    # Copilot Chat MCP server
├── 📁 .vscode/mcp.json       # VS Code MCP config
├── 📁 src/
│   ├── figma/                # API client
│   ├── generators/           # Code generators
│   └── extractors/           # Token extraction
└── 📁 docs/                  # Documentation
```

## ⚙️ Configuration

| Variable | Description |
|----------|-------------|
| `FIGMA_TOKEN` | Your Figma personal access token |
| `ANGULAR_OUTPUT_PATH` | Where to generate components |
| `ASSETS_OUTPUT_PATH` | Where to save extracted assets |

## 🛠️ MCP Tools

| Tool | Description |
|------|-------------|
| `sync_figma` | Sync file & extract tokens |
| `generate_component` | Generate Angular component |
| `list_components` | List all components |
| `preview` | Get raw design JSON |
| `extract_tokens` | Export SCSS variables |

## 📄 License

MIT © 2024

---

<p align="center">
  <strong>🔥 FigmaForge</strong> — Forging code from designs
</p>
