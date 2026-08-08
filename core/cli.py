"""
CyberGhost OSINT (Community Edition)
Zero Configuration Passive Reconnaissance & Threat Intelligence
"""
import sys
import asyncio
import time
import argparse
import platform
import re
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

console = Console() if HAS_RICH else None

from core.orchestrator import OsintOrchestrator
from core.report import generate_json_report, generate_html_report, generate_stix_report

VERSION = "1.0.0"

# ANSI Colors
C = "\033[1;36m"
G = "\033[1;32m"
R = "\033[1;31m"
Y = "\033[1;33m"
NC = "\033[0m"


def validate_target(target: str) -> str:
    """Validate and sanitize the target input."""
    target = target.strip()
    target = target.replace('https://', '').replace('http://', '').split('/')[0]

    if not target:
        print(f"{R}Error: Empty target.{NC}")
        sys.exit(1)

    if re.search(r'[;&|\\$><`\n\r\t]', target):
        print(f"{R}Error: Target contains invalid or dangerous characters.{NC}")
        sys.exit(1)

    if not re.match(r'^[a-zA-Z0-9._:-]+$', target):
        print(f"{R}Error: Target contains invalid characters. Use a domain (example.com) or IP.{NC}")
        sys.exit(1)

    return target


def print_logo():
    """Print a clean, professional banner."""
    if HAS_RICH:
        banner = Panel(
            "[bold cyan]CyberGhost OSINT[/bold cyan] [dim]Community Edition v{ver}[/dim]\n"
            "[dim]Zero-Config Passive Reconnaissance & Intelligence[/dim]".format(ver=VERSION),
            border_style="cyan",
            expand=False,
            padding=(1, 4),
        )
        console.print(banner)
    else:
        print(f"\n{C}╔══════════════════════════════════════════════════════╗{NC}")
        print(f"{C}║  CyberGhost OSINT Community Edition v{VERSION}          ║{NC}")
        print(f"{C}║  Zero-Config Passive Reconnaissance & Intelligence   ║{NC}")
        print(f"{C}╚══════════════════════════════════════════════════════╝{NC}\n")


def display_results(summary: dict):
    """Display scan results using Rich or ANSI fallback."""
    score = summary.get('security_score', 0)
    score_color = "red" if score < 50 else "yellow" if score < 80 else "green"
    
    if HAS_RICH:
        console.print(f"\n[bold white]Target:[/bold white] [bold cyan]{summary['target']}[/bold cyan]")
        console.print(f"[bold white]Security Posture Score:[/bold white] [bold {score_color}]{score}/100[/bold {score_color}]\n")
        
        console.print("[bold white]Module Execution Status:[/bold white]")
        for finding in summary.get('findings', []):
            source = finding['source']
            status = finding['status'].upper()
            if status == "SUCCESS":
                console.print(f"  [bold green][+][/bold green] {source.ljust(25)} [bold green]SUCCESS[/bold green]")
            elif status in ["WARNING", "PARTIAL"]:
                console.print(f"  [bold yellow][!][/bold yellow] {source.ljust(25)} [bold yellow]{status}[/bold yellow]")
            else:
                console.print(f"  [bold red][x][/bold red] {source.ljust(25)} [bold red]FAILED[/bold red]")
        console.print("")
        
        for finding in summary.get('findings', []):
            if finding['status'] != 'success' or not finding['data']:
                continue

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Data", style="white")

            if isinstance(finding['data'], dict):
                for k, v in finding['data'].items():
                    if isinstance(v, list):
                        table.add_row(f"[bold]{k}:[/bold]")
                        for item in v:
                            table.add_row(f"  • {item}")
                    else:
                        table.add_row(f"[bold]{k}:[/bold] {v}")

            panel = Panel(table, title=f"[bold cyan]{finding['source']} ({finding['category']})[/]", border_style="cyan", expand=False)
            console.print(panel)
    else:
        print(f"\n  Target: {summary['target']}")
        print(f"  Security Posture Score: {score}/100\n")
        
        print(f"  {C}Module Execution Status:{NC}")
        for finding in summary.get('findings', []):
            source = finding['source']
            status = finding['status'].upper()
            if status == "SUCCESS":
                print(f"  {G}[+]{NC} {source.ljust(25)} {G}SUCCESS{NC}")
            elif status in ["WARNING", "PARTIAL"]:
                print(f"  {Y}[!]{NC} {source.ljust(25)} {Y}{status}{NC}")
            else:
                print(f"  {R}[x]{NC} {source.ljust(25)} {R}FAILED{NC}")
        print("")
        
        for finding in summary.get('findings', []):
            if finding['status'] != 'success' or not finding['data']:
                continue
                
            print(f"\n{C}═══ {finding['source']} ({finding['category']}) ═══{NC}")
            if isinstance(finding['data'], dict):
                for k, v in finding['data'].items():
                    if isinstance(v, list):
                        print(f"  {k}:")
                        for item in v:
                            print(f"    • {item}")
                    else:
                        print(f"  {k}: {v}")


def main():
    if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(
        description=f"CyberGhost OSINT v{VERSION} — Community Edition (Zero-Config)",
        epilog="Example: cyberghost example.com --html --stix"
    )
    parser.add_argument("target", nargs='?', help="Target domain or IP (e.g., example.com)")
    parser.add_argument("--json", action="store_true", help="Export results as JSON")
    parser.add_argument("--html", action="store_true", help="Export results as HTML report")
    parser.add_argument("--stix", action="store_true", help="Export results as STIX 2.1 bundle")
    parser.add_argument("--version", action="version", version=f"CyberGhost OSINT v{VERSION}")

    args = parser.parse_args()

    if not args.target:
        parser.print_help()
        print(f"\n{R}Error: Please specify a target. Example: cyberghost example.com{NC}")
        sys.exit(1)

    target = validate_target(args.target)
    print_logo()
    
    start_time = time.time()
    orchestrator = OsintOrchestrator(target)

    # Run scan
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if HAS_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task_id = progress.add_task("[cyan]Scanning target...", total=None)
            asyncio.run(orchestrator.run_all())
            progress.update(task_id, completed=100, description="[green]Scan complete")
    else:
        print(f"  Scanning {target}...")
        asyncio.run(orchestrator.run_all())

    summary = orchestrator.get_summary()
    display_results(summary)

    # Exports
    if args.json:
        path = generate_json_report(target, summary)
        print(f"\n✅ JSON report saved: {path}")
    if args.html:
        path = generate_html_report(target, summary)
        print(f"✅ HTML report saved: {path}")
    if args.stix:
        path = generate_stix_report(target, summary)
        print(f"✅ STIX report saved: {path}")

    elapsed = time.time() - start_time
    if HAS_RICH:
        console.print(f"\n[bold cyan]Investigation completed in {elapsed:.2f}s[/bold cyan]")
    else:
        print(f"\n{C}Investigation completed in {elapsed:.2f}s{NC}")


if __name__ == "__main__":
    main()
