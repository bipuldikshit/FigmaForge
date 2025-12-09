# FigmaForge — Architecture Overview

> **Audience:** Senior Engineers, Staff Engineers, System Architects

---

## 1. What FigmaForge Does

FigmaForge is a **Figma-to-code generator** that transforms Figma designs into production-ready components for **Angular, React, Vue, and Web Components**. It bridges the gap between design and development by:

1. **Fetching** design data from Figma's REST API with intelligent caching
2. **Normalizing** the JSON tree into a structured component model
3. **Extracting** design tokens, component variants, and interaction states
4. **Generating** framework-specific component files with pixel-perfect fidelity
5. **Downloading** SVG/PNG assets with inline optimization

---

## 2. System Architecture

### 2.1 High-Level Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│   Figma File    │────▶│  FigmaForge      │────▶│ Component Files         │
│  (Design)       │     │  (Python)        │     │ (.ts/.tsx/.vue/.js)     │
└─────────────────┘     └──────────────────┘     └─────────────────────────┘
                               │
                               ├── CLI (`cli.py`)
                               └── MCP Server (`mcp_stdio_server.py`)
                                   └── VS Code Copilot Chat
```

### 2.2 Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              ENTRY POINTS                                 │
├────────────────────────────────┬─────────────────────────────────────────┤
│  cli.py (Click CLI)            │  mcp_stdio_server.py (MCP Protocol)     │
│  - generate, sync, init        │  - 5 tools exposed to Copilot Chat      │
│  - watch, cache                │  - Full feature parity with CLI         │
└────────────────────────────────┴─────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           src/figma/ (API Layer)                          │
├─────────────────────┬───────────────────────┬────────────────────────────┤
│ client.py           │ normalizer.py         │ types.py                   │
│ - HTTP with caching │ - Tree traversal      │ - TypedDict definitions   │
│ - Rate limiting     │ - Component detection │ - FigmaNode, DesignTokens │
│ - ETag support      │ - Name sanitization   │                            │
└─────────────────────┴───────────────────────┴────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        src/extractors/ (Data Extraction)                  │
├────────────────┬────────────────┬─────────────────┬──────────────────────┤
│ tokens.py      │ variants.py    │ figma_variables │ interaction_states   │
│ - Colors       │ - COMPONENT_SET│ - Variables API │ - Hover/Focus/Active │
│ - Typography   │ - @Input types │ - Design tokens │ - CSS pseudo-classes │
│ - Spacing      │ - Union types  │ - Multi-mode    │                      │
└────────────────┴────────────────┴─────────────────┴──────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        src/generators/ (Code Generation)                  │
├──────────────────┬──────────────────┬──────────────────┬─────────────────┤
│ Angular          │ React            │ Vue              │ Web Components  │
│ - TypeScript     │ - TSX            │ - SFC            │ - Shadow DOM    │
│ - HTML template  │ - CSS Modules    │ - Composition API│ - Custom Elem   │
│ - SCSS/Tailwind  │                  │ - Scoped styles  │                 │
└──────────────────┴──────────────────┴──────────────────┴─────────────────┘
```

---

## 3. Core Capabilities

### 3.1 Multi-Framework Code Generation

| Framework | Generator | Output Files |
|-----------|-----------|--------------|
| Angular | `typescript_generator.py`, `html_generator.py`, `scss_generator.py` | `.component.ts`, `.component.html`, `.component.scss` |
| React | `react_generator.py` | `.tsx`, `.module.css` |
| Vue 3 | `vue_generator.py` | `.vue` (SFC with Composition API) |
| Web Components | `webcomponent_generator.py` | `.js` (Custom Element with Shadow DOM) |

### 3.2 Style Output Options

| Format | Generator | Description |
|--------|-----------|-------------|
| SCSS | `scss_generator.py` | BEM-style classes with variables |
| Tailwind | `tailwind_generator.py` | Utility class mappings |

### 3.3 Layout Modes

| Mode | Flag | Description |
|------|------|-------------|
| Absolute | default | Pixel-perfect positioning |
| Responsive | `--responsive` | Flexbox layouts from auto-layout |

### 3.4 API Caching

- **Location:** `~/.figmaforge/cache/`
- **TTL:** 24 hours with ETag validation
- **Bypass:** `--no-cache` flag
- **Management:** `cache` CLI command

### 3.5 Watch Mode

Auto-regenerate components when Figma file changes:
```bash
python cli.py watch -f FILE_KEY -n NODE_ID -m component-name --interval 30
```

### 3.6 Design Token Extraction

| Extractor | Purpose |
|-----------|---------|
| `tokens.py` | Colors, typography, spacing, shadows |
| `variants.py` | Component variants → typed @Input properties |
| `figma_variables.py` | Figma Variables API → SCSS/CSS tokens |
| `interaction_states.py` | Hover/focus/disabled → CSS pseudo-classes |

---

## 4. Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| CLI Framework | Click |
| HTTP Client | Requests |
| MCP Protocol | `mcp` SDK |
| Console Output | Rich |
| Configuration | python-dotenv |
| Caching | Disk-based with ETag |
| Testing | pytest |

---

## 5. Project Structure

```
FigmaForge/
├── cli.py                          # CLI entry point
├── mcp_stdio_server.py             # MCP server for Copilot Chat
├── src/
│   ├── cache.py                    # API response caching
│   ├── config.py                   # Configuration management
│   ├── exceptions.py               # Custom exception types
│   ├── figma/
│   │   ├── client.py               # Figma API client
│   │   ├── normalizer.py           # JSON tree normalizer
│   │   └── types.py                # TypedDict definitions
│   ├── generators/
│   │   ├── component_generator.py  # Orchestrator
│   │   ├── typescript_generator.py # Angular TypeScript
│   │   ├── html_generator.py       # Angular HTML
│   │   ├── scss_generator.py       # SCSS with BEM
│   │   ├── tailwind_generator.py   # Tailwind utilities
│   │   ├── react_generator.py      # React TSX + CSS Modules
│   │   ├── vue_generator.py        # Vue 3 SFC
│   │   ├── webcomponent_generator.py # Custom Elements
│   │   ├── responsive_layout.py    # Flexbox conversion
│   │   └── framework_selector.py   # Framework routing
│   ├── extractors/
│   │   ├── tokens.py               # Design token extraction
│   │   ├── variants.py             # Component variant detection
│   │   ├── figma_variables.py      # Figma Variables API
│   │   ├── interaction_states.py   # State extraction
│   │   └── assets.py               # SVG/PNG download
│   └── utils/
│       ├── css.py                  # CSS utilities
│       ├── colors.py               # Color conversion
│       └── console.py              # Rich console output
├── tests/                          # Unit tests
└── docs/                           # Documentation
```

---

## 6. Design Decisions

### Caching Strategy
Disk-based cache with 24-hour TTL and ETag support. Image URLs are excluded (short-lived). Cache can be bypassed with `--no-cache` or cleared with `cache --clear`.

### Framework Abstraction
The `ComponentGenerator` orchestrates generation. The `framework` parameter routes to the appropriate generator. All generators share common asset extraction and variant detection.

### MCP Integration
STDIO transport with UTF-8 encoding for Windows compatibility. Rich console output redirected to stderr to preserve JSON protocol on stdout. All CLI parameters exposed as tool arguments.

### Non-Destructive Regeneration
Generated code is wrapped in `AUTO-GEN-START` / `AUTO-GEN-END` markers. Custom code outside these markers is preserved on regeneration.

---

## 7. Testing

```bash
python -m pytest tests/ -v
```

Test coverage includes:
- CSS utilities (camelCase, PascalCase, BEM naming)
- Token extraction
- Generator output
- Asset handling
