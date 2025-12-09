"""FigmaForge - Forge Angular components from Figma designs."""

import os
import sys
import click
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from src.figma.client import FigmaClient
from src.figma.normalizer import FigmaNormalizer
from src.extractors.tokens import TokenExtractor
from src.extractors.token_scss import TokenSCSSGenerator
from src.generators.component_generator import ComponentGenerator
from src.exceptions import FigmaAPIError, FigmaForgeError
from src.cache import get_cache

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
        TokenSCSSGenerator().save_scss(tokens, scss_output)
        
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
        
    except FigmaForgeError as e:
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
@click.option("--framework", "-w", type=click.Choice(["angular", "react", "vue", "webcomponent"]), default="angular", help="Target framework")
@click.option("--regenerate", is_flag=True, help="Non-destructive update")
@click.option("--responsive", "-r", is_flag=True, help="Use flexbox/responsive layout instead of absolute positioning")
@click.option("--dry-run", "-d", is_flag=True, help="Preview generated code without writing files")
@click.option("--no-cache", is_flag=True, help="Bypass cache and fetch fresh data from Figma")
def generate(file_key: str, node_id: str, name: str, output: str, style: str, framework: str, regenerate: bool, responsive: bool, dry_run: bool, no_cache: bool):
    """Generate component from Figma node (Angular, React, Vue, Web Components)."""
    from rich.syntax import Syntax
    from rich.panel import Panel
    
    try:
        mode_label = f" [{framework}]"
        mode_label += " (responsive)" if responsive else ""
        mode_label += " [preview]" if dry_run else ""
        if no_cache:
            mode_label += " [no-cache]"
        console.print(f"\n[bold cyan]⚙️  Generating: {name}{mode_label}[/bold cyan]\n")
        
        client = FigmaClient(use_cache=not no_cache)
        output_path = output or os.getenv("ANGULAR_OUTPUT_PATH", "./src/app/components")
        assets_path = os.getenv("ASSETS_OUTPUT_PATH", "./src/assets/figma")
        
        generator = ComponentGenerator(
            figma_client=client,
            output_path=output_path,
            assets_output_path=assets_path,
            style_format=style,
            responsive_mode=responsive,
            framework=framework
        )
        
        result = generator.generate_component(
            file_key=file_key,
            node_id=node_id,
            component_name=name,
            regenerate=regenerate,
            dry_run=dry_run
        )
        
        if dry_run:
            # Display code preview with syntax highlighting
            console.print("\n[bold cyan]📋 Code Preview (no files written)[/bold cyan]\n")
            
            content = result.get("generated_content", {})
            
            if "html" in content:
                console.print(Panel(
                    Syntax(content["html"]["content"], "html", theme="monokai", line_numbers=True),
                    title=f"[green]{Path(content['html']['file']).name}[/green]",
                    border_style="green"
                ))
            
            if "ts" in content:
                console.print(Panel(
                    Syntax(content["ts"]["content"], "typescript", theme="monokai", line_numbers=True),
                    title=f"[blue]{Path(content['ts']['file']).name}[/blue]",
                    border_style="blue"
                ))
            
            if "scss" in content:
                console.print(Panel(
                    Syntax(content["scss"]["content"], "scss", theme="monokai", line_numbers=True),
                    title=f"[magenta]{Path(content['scss']['file']).name}[/magenta]",
                    border_style="magenta"
                ))
            
            console.print("\n[yellow]ℹ️  Dry run - no files were written[/yellow]")
            console.print(f"[dim]Run without --dry-run to generate files[/dim]\n")
        else:
            console.print(f"\n[bold green]✅ Generated![/bold green]")
            console.print(f"[dim]{result['component_path']}[/dim]\n")
            
            for path in result["files"]:
                console.print(f"  [green]✓[/green] {Path(path).name}")
            
            if result["assets"]:
                console.print(f"\n[dim]Assets: {len(result['assets'])}[/dim]")
            console.print()
        
    except FigmaForgeError as e:
        console.print(f"\n[red]✗ {e}[/red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]✗ {e}[/red]\n")
        sys.exit(1)


@cli.command()
@click.option("--file-key", "-f", required=True, help="Figma file key")
@click.option("--node-id", "-n", multiple=True, help="Node IDs to watch (can specify multiple)")
@click.option("--name", "-m", multiple=True, help="Component names (must match node-id count)")
@click.option("--interval", "-i", default=30, help="Check interval in seconds (default: 30)")
@click.option("--responsive", "-r", is_flag=True, help="Use responsive layout mode")
def watch(file_key: str, node_id: tuple, name: tuple, interval: int, responsive: bool):
    """Watch Figma file for changes and auto-regenerate components.
    
    Example:
        figmaforge watch -f FILE_KEY -n 1:23 -m my-button -n 4:56 -m my-card
    """
    import time
    import signal
    
    if node_id and len(node_id) != len(name):
        console.print("[red]✗ Number of --node-id and --name options must match[/red]")
        sys.exit(1)
    
    # Build component list
    components = list(zip(node_id, name)) if node_id else []
    
    console.print(f"\n[bold cyan]👀 Watch Mode[/bold cyan]")
    console.print(f"[dim]File: {file_key}[/dim]")
    console.print(f"[dim]Interval: {interval}s[/dim]")
    
    if components:
        console.print(f"\n[cyan]Components to regenerate:[/cyan]")
        for nid, cname in components:
            console.print(f"  • {cname} ({nid})")
    else:
        console.print("\n[yellow]⚠ No components specified. Watching for changes only.[/yellow]")
        console.print("[dim]Use -n NODE_ID -m NAME to specify components to regenerate[/dim]")
    
    console.print(f"\n[dim]Press Ctrl+C to stop watching[/dim]\n")
    
    client = FigmaClient()
    output_path = os.getenv("ANGULAR_OUTPUT_PATH", "./src/app/components")
    assets_path = os.getenv("ASSETS_OUTPUT_PATH", "./src/assets/figma")
    
    last_modified = None
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        console.print("\n\n[yellow]⏹ Stopping watch...[/yellow]")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while running:
            try:
                # Get file metadata to check lastModified
                file_data = client.get_file(file_key, geometry="")
                current_modified = file_data.get("lastModified", "")
                
                if last_modified is None:
                    last_modified = current_modified
                    console.print(f"[green]✓[/green] Initial sync complete")
                    console.print(f"[dim]Last modified: {current_modified}[/dim]")
                elif current_modified != last_modified:
                    console.print(f"\n[bold yellow]🔄 Change detected![/bold yellow]")
                    console.print(f"[dim]New timestamp: {current_modified}[/dim]\n")
                    
                    last_modified = current_modified
                    
                    # Regenerate components
                    if components:
                        generator = ComponentGenerator(
                            figma_client=client,
                            output_path=output_path,
                            assets_output_path=assets_path,
                            style_format="scss",
                            responsive_mode=responsive
                        )
                        
                        for nid, cname in components:
                            try:
                                console.print(f"[cyan]📝 Regenerating: {cname}[/cyan]")
                                generator.generate_component(
                                    file_key=file_key,
                                    node_id=nid,
                                    component_name=cname,
                                    regenerate=True
                                )
                                console.print(f"[green]✓[/green] {cname} updated")
                            except Exception as e:
                                console.print(f"[red]✗ {cname}: {e}[/red]")
                    else:
                        console.print("[dim]No components configured for regeneration[/dim]")
                else:
                    # No changes - show heartbeat
                    console.print(f"[dim]• Checked at {time.strftime('%H:%M:%S')} - no changes[/dim]")
                
                # Wait for next check
                for _ in range(interval):
                    if not running:
                        break
                    time.sleep(1)
                    
            except FigmaAPIError as e:
                console.print(f"[yellow]⚠ API error, retrying: {e}[/yellow]")
                time.sleep(5)
            except Exception as e:
                console.print(f"[red]✗ Error: {e}[/red]")
                time.sleep(5)
    
    except KeyboardInterrupt:
        pass
    
    console.print("[green]✅ Watch stopped[/green]\n")


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


@cli.command()
@click.option("--clear", "-c", is_flag=True, help="Clear all cached entries")
@click.option("--stats", "-s", is_flag=True, default=True, help="Show cache statistics")
def cache(clear: bool, stats: bool):
    """Manage Figma API response cache.
    
    The cache speeds up repeated operations by storing Figma API responses
    locally in ~/.figmaforge/cache/
    
    Examples:
        python cli.py cache           # Show stats
        python cli.py cache --clear   # Clear all cache
    """
    cache_instance = get_cache()
    
    if clear:
        count = cache_instance.clear()
        console.print(f"\n[yellow]🗑 Cleared {count} cached entries[/yellow]\n")
        return
    
    # Always show stats by default
    cache_stats = cache_instance.stats()
    
    console.print("\n[bold cyan]📦 Cache Statistics[/bold cyan]\n")
    
    table = Table(show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Entries", justify="right")
    table.add_column("Size", justify="right")
    
    for category, data in cache_stats["categories"].items():
        size_kb = data["size_bytes"] / 1024
        table.add_row(category, str(data["entries"]), f"{size_kb:.1f} KB")
    
    total_kb = cache_stats["total_size_bytes"] / 1024
    table.add_row("─" * 10, "─" * 5, "─" * 8, style="dim")
    table.add_row("Total", str(cache_stats["total_entries"]), f"{total_kb:.1f} KB", style="bold")
    
    console.print(table)
    console.print(f"\n[dim]Location: {cache_instance.CACHE_DIR}[/dim]")
    console.print("[dim]Use --clear to delete all cached entries[/dim]\n")


if __name__ == "__main__":
    cli()

