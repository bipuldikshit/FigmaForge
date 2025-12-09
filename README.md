<p align="center">
  <img src="https://img.shields.io/badge/Figma-F24E1E?style=for-the-badge&logo=figma&logoColor=white" alt="Figma" />
  <img src="https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white" alt="Angular" />
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Vue-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/MCP-VS_Code-007ACC?style=for-the-badge&logo=visual-studio-code&logoColor=white" alt="MCP" />
</p>

<h1 align="center">🔥 FigmaForge</h1>

<p align="center">
  <strong>Forge production-ready components from Figma designs</strong>
</p>

<p align="center">
  <em>Multi-framework code generation (Angular, React, Vue, Web Components) via CLI & Copilot Chat</em>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-frameworks">Frameworks</a> •
  <a href="#-documentation">Docs</a>
</p>

---

## ✨ Features

### Core Features
| Feature | Description |
|---------|-------------|
| 🎯 **Pixel-Perfect** | Exact positioning, colors, typography from your designs |
| 🤖 **AI-Driven** | Generate via VS Code Copilot Chat with natural language |
| ⌨️ **CLI Support** | Command-line interface for scripting and CI/CD |
| 🎨 **Design Tokens** | Extract colors, fonts, spacing as SCSS variables |
| 📦 **Asset Export** | Automatic SVG/PNG extraction with inline optimization |
| 🔄 **Non-Destructive** | Regenerate without losing custom code |

### Multi-Framework Support
| Framework | Output Files | Flag |
|-----------|--------------|------|
| **Angular** | `.ts`, `.html`, `.scss` | `--framework angular` |
| **React** | `.tsx`, `.module.css` | `--framework react` |
| **Vue 3** | `.vue` (SFC) | `--framework vue` |
| **Web Components** | `.js` (Custom Elements) | `--framework webcomponent` |

### Advanced Features
| Feature | Description |
|---------|-------------|
| ⚡ **API Caching** | Local cache with ETag support for faster regeneration |
| 🌐 **Responsive Mode** | Flexbox layouts instead of absolute positioning |
| 🎨 **Tailwind CSS** | Generate Tailwind utility classes instead of SCSS |
| 👀 **Watch Mode** | Auto-regenerate components when Figma file changes |
| 🔀 **Component Variants** | Detect Figma variants → typed `@Input()` properties |
| 🎭 **Interaction States** | Map hover/focus/disabled variants to CSS pseudo-classes |
| 📐 **Figma Variables** | Extract design tokens from Figma Variables API |

---

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

---

## 🎮 Usage

### 🤖 AI-Driven (VS Code Copilot Chat)

1. Open project in VS Code
2. Reload window (`Ctrl+Shift+P` → "Developer: Reload Window")
3. Open Copilot Chat (`Ctrl+Shift+I`)
4. Chat naturally:

```
📝 "List all components in file ABC123XYZ"

🔥 "Generate a React component called hero-section from node 1:23 in file ABC123XYZ"

🎯 "Generate button from node 2:45 in file ABC123XYZ with tailwind styling and responsive layout"
```

### ⌨️ CLI Commands

```bash
# Generate Angular component (default)
python cli.py generate -f FILE_KEY -n "1:23" -m my-button

# Generate React component
python cli.py generate -f FILE_KEY -n "1:23" -m my-button --framework react

# Generate Vue component
python cli.py generate -f FILE_KEY -n "1:23" -m my-button --framework vue

# Generate Web Component
python cli.py generate -f FILE_KEY -n "1:23" -m my-button --framework webcomponent

# With Tailwind CSS
python cli.py generate -f FILE_KEY -n "1:23" -m my-button --style tailwind

# Responsive flexbox layout
python cli.py generate -f FILE_KEY -n "1:23" -m my-button --responsive

# Dry run (preview without writing)
python cli.py generate -f FILE_KEY -n "1:23" -m my-button --dry-run

# Bypass cache
python cli.py generate -f FILE_KEY -n "1:23" -m my-button --no-cache

# Cache management
python cli.py cache          # View cache stats
python cli.py cache --clear  # Clear all cached data

# Watch mode (auto-regenerate on changes)
python cli.py watch -f FILE_KEY -n "1:23" -m my-button --interval 30

# Sync file and extract design tokens
python cli.py sync -f FILE_KEY

# Initialize project directories
python cli.py init
```

---

## 🔧 Frameworks

### Angular (Default)
```bash
python cli.py generate -f FILE -n NODE -m button
```
Generates: `button.component.ts`, `button.component.html`, `button.component.scss`

### React
```bash
python cli.py generate -f FILE -n NODE -m button --framework react
```
Generates: `Button.tsx`, `Button.module.css`

### Vue 3
```bash
python cli.py generate -f FILE -n NODE -m button --framework vue
```
Generates: `Button.vue` (Single File Component with Composition API)

### Web Components
```bash
python cli.py generate -f FILE -n NODE -m button --framework webcomponent
```
Generates: `Button.js` (Custom Element with Shadow DOM)

---

## 🔍 Finding Figma IDs

| ID | Location | Example |
|----|----------|---------|
| **File Key** | URL: `figma.com/design/ABC123XYZ/...` | `ABC123XYZ` |
| **Node ID** | Right-click → "Copy link" → `?node-id=1-23` | `1:23` |

---

## 📂 Project Structure

```
FigmaForge/
├── cli.py                    # CLI entry point
├── mcp_stdio_server.py       # MCP server for Copilot Chat
├── .vscode/mcp.json          # VS Code MCP configuration
├── src/
│   ├── figma/                # Figma API client & normalizer
│   ├── generators/           # Angular, React, Vue, WebComponent generators
│   ├── extractors/           # Tokens, variants, assets, interaction states
│   └── utils/                # CSS utilities, console output
├── tests/                    # Unit tests (33+ tests)
└── docs/                     # Documentation
```

---

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FIGMA_TOKEN` | Your Figma personal access token | Required |
| `ANGULAR_OUTPUT_PATH` | Component output directory | `./src/app/components` |
| `ASSETS_OUTPUT_PATH` | Asset output directory | `./src/assets/figma` |

---

## 🛠️ MCP Tools (Copilot Chat)

| Tool | Description |
|------|-------------|
| `generate_component` | Generate component (any framework) |
| `sync_figma` | Sync file & extract tokens |
| `list_components` | List all components in file |
| `preview` | Get raw design JSON |
| `extract_tokens` | Export SCSS variables |

### MCP Parameters
| Parameter | Values | Description |
|-----------|--------|-------------|
| `framework` | angular, react, vue, webcomponent | Target framework |
| `styleFormat` | scss, tailwind | Style output format |
| `responsive` | true/false | Use flexbox layouts |
| `dryRun` | true/false | Preview without writing |
| `noCache` | true/false | Bypass API cache |

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## 📚 Documentation

- [Testing Guide](docs/TESTING_GUIDE.md) - Complete testing instructions
- [MCP Integration](docs/MCP_INTEGRATION.md) - Copilot Chat setup
- [Architecture](docs/ARCHITECTURE.md) - System design overview

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>🔥 FigmaForge</strong> — Forging code from designs
</p>
