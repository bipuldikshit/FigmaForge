"""FigmaForge - Forge Angular components from Figma designs."""

import os
import sys
import click
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from src.figma.client import FigmaClient, FigmaAPIError
from src.figma.normalizer import FigmaNormalizer
from src.extractors.tokens import TokenExtractor
from src.extractors.scss_generator import SCSSGenerator
from src.generators.component_generator import ComponentGenerator

load_dotenv()
console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """🔥 FigmaForge - Forge Angular components from Figma"""
    if not os.getenv("FIGMA_TOKEN"):
        console.print("[yellow]⚠ FIGMA_TOKEN not set. Get one at: https://www.figma.com/settings[/yellow]\n")


@cli.command()
@click.option("--file-key", "-f", required=True, help="Figma file key from URL")
@click.option("--output", "-o", default="./design-tokens.json", help="Output file")
def sync(file_key: str, output: str):
    """Sync Figma file and extract design tokens."""
    try:
        console.print(f"\n[bold cyan]🔄 Syncing: {file_key}[/bold cyan]\n")
        
        client = FigmaClient()
        file_data = client.get_file(file_key)
        
        normalizer = FigmaNormalizer()
        normalized = normalizer.normalize_file(file_data)
        
        token_extractor = TokenExtractor()
        tokens = token_extractor.extract_tokens(normalized["nodes"])
        token_extractor.save_tokens(tokens, output)
        
        scss_output = output.replace(".json", ".scss")
        SCSSGenerator().save_scss(tokens, scss_output)
        
        console.print(f"\n[bold green]✅ Done![/bold green]")
        console.print(f"[dim]File: {normalized['file_name']} | Components: {len(normalized['components'])}[/dim]\n")
        
        if normalized["components"]:
            table = Table(title="Components")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Assets", justify="right")
            
            for comp in normalized["components"][:10]:
                table.add_row(comp["name"], comp["id"], str(len(comp["assets"])))
            
            console.print(table)
            if len(normalized["components"]) > 10:
                console.print(f"[dim]...and {len(normalized['components']) - 10} more[/dim]")
        
    except FigmaAPIError as e:
        console.print(f"\n[red]✗ {e}[/red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ {e}[/red]\n")
        sys.exit(1)


@cli.command()
@click.option("--file-key", "-f", required=True, help="Figma file key")
@click.option("--node-id", "-n", required=True, help="Node ID (e.g., '1:23')")
@click.option("--name", "-m", required=True, help="Component name (kebab-case)")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--style", "-s", type=click.Choice(["scss", "tailwind"]), default="scss")
@click.option("--regenerate", is_flag=True, help="Non-destructive update")
def generate(file_key: str, node_id: str, name: str, output: str, style: str, regenerate: bool):
    """Generate Angular component from Figma node."""
    try:
        console.print(f"\n[bold cyan]⚙️  Generating: {name}[/bold cyan]\n")
        
        client = FigmaClient()
        output_path = output or os.getenv("ANGULAR_OUTPUT_PATH", "./src/app/components")
        assets_path = os.getenv("ASSETS_OUTPUT_PATH", "./src/assets/figma")
        
        generator = ComponentGenerator(
            figma_client=client,
            output_path=output_path,
            assets_output_path=assets_path,
            style_format=style
        )
        
        result = generator.generate_component(
            file_key=file_key,
            node_id=node_id,
            component_name=name,
            regenerate=regenerate
        )
        
        console.print(f"\n[bold green]✅ Generated![/bold green]")
        console.print(f"[dim]{result['component_path']}[/dim]\n")
        
        for path in result["files"]:
            console.print(f"  [green]✓[/green] {Path(path).name}")
        
        if result["assets"]:
            console.print(f"\n[dim]Assets: {len(result['assets'])}[/dim]")
        console.print()
        
    except FigmaAPIError as e:
        console.print(f"\n[red]✗ {e}[/red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ {e}[/red]\n")
        sys.exit(1)


@cli.command()
@click.option("--file-key", "-f", required=True, help="Figma file key")
@click.option("--interval", "-i", default=30, help="Check interval (seconds)")
def watch(file_key: str, interval: int):
    """Watch Figma file for changes (not yet implemented)."""
    console.print(f"\n[bold cyan]👀 Watching: {file_key}[/bold cyan]")
    console.print(f"[dim]Interval: {interval}s[/dim]")
    console.print("[yellow]⚠ Watch mode coming soon[/yellow]\n")


@cli.command()
def init():
    """Initialize project directories and config."""
    console.print("\n[bold cyan]🎨 Initializing project[/bold cyan]\n")
    
    for dir_path in ["./src/app/components", "./src/assets/figma", "./src/styles"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        console.print(f"  [green]✓[/green] {dir_path}")
    
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write("FIGMA_TOKEN=your_token_here\n")
            f.write("ANGULAR_OUTPUT_PATH=./src/app/components\n")
            f.write("ASSETS_OUTPUT_PATH=./src/assets/figma\n")
        console.print("  [green]✓[/green] .env (add your FIGMA_TOKEN)")
    else:
        console.print("  [yellow]•[/yellow] .env exists")
    
    console.print("\n[green]✅ Done![/green]")
    console.print("[dim]Next: add FIGMA_TOKEN to .env, then run 'python cli.py sync -f <key>'[/dim]\n")


if __name__ == "__main__":
    cli()
