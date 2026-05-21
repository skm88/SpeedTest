"""SpeedTerm - Internet speed test in your terminal."""
import time
import sys
import statistics
import argparse

try:
    import requests
except ImportError:
    print("Erreur: 'requests' n'est pas installé. Lancez: pip install requests")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.align import Align
except ImportError:
    print("Erreur: 'rich' n'est pas installé. Lancez: pip install rich")
    sys.exit(1)

__version__ = "1.0.0"

console = Console()

DOWNLOAD_BASE = "https://speed.cloudflare.com/__down"
UPLOAD_URL = "https://speed.cloudflare.com/__up"
META_URL = "https://speed.cloudflare.com/meta"


def get_connection_info():
    """Récupère les informations sur la connexion (ISP, IP, localisation)."""
    try:
        r = requests.get(META_URL, timeout=5)
        return r.json()
    except Exception:
        return {}


def measure_ping(samples=10):
    """Mesure le ping en envoyant plusieurs requêtes HEAD."""
    times = []
    for _ in range(samples):
        try:
            start = time.perf_counter()
            requests.get(f"{DOWNLOAD_BASE}?bytes=0", timeout=5)
            times.append((time.perf_counter() - start) * 1000)
        except Exception:
            pass
    if not times:
        return None
    return {
        "min": min(times),
        "avg": statistics.mean(times),
        "max": max(times),
        "jitter": statistics.stdev(times) if len(times) > 1 else 0,
    }


def measure_download(size_mb=25, progress_callback=None):
    """Mesure le débit de téléchargement (download)."""
    size = size_mb * 1_000_000
    start = time.perf_counter()
    downloaded = 0
    try:
        response = requests.get(
            f"{DOWNLOAD_BASE}?bytes={size}", stream=True, timeout=60
        )
        for chunk in response.iter_content(chunk_size=65536):
            downloaded += len(chunk)
            if progress_callback:
                progress_callback(downloaded, size)
    except Exception as e:
        console.print(f"[red]Erreur download: {e}[/red]")
        return 0
    elapsed = time.perf_counter() - start
    if elapsed == 0:
        return 0
    return (downloaded * 8) / (elapsed * 1_000_000)  # Mbps


def measure_upload(size_mb=10, progress_callback=None):
    """Mesure le débit d'envoi (upload)."""
    size = size_mb * 1_000_000
    data = b"\x00" * size
    start = time.perf_counter()
    try:
        requests.post(UPLOAD_URL, data=data, timeout=60)
    except Exception as e:
        console.print(f"[red]Erreur upload: {e}[/red]")
        return 0
    elapsed = time.perf_counter() - start
    if elapsed == 0:
        return 0
    return (size * 8) / (elapsed * 1_000_000)  # Mbps


def quality_label(mbps):
    """Retourne une étiquette qualitative pour un débit en Mbps."""
    if mbps >= 100:
        return "[bold green]Excellent[/bold green]"
    if mbps >= 50:
        return "[bold cyan]Très bon[/bold cyan]"
    if mbps >= 25:
        return "[bold yellow]Bon[/bold yellow]"
    if mbps >= 10:
        return "[yellow]Moyen[/yellow]"
    return "[red]Faible[/red]"


def ping_quality(ms):
    if ms < 20:
        return "[bold green]Excellent[/bold green]"
    if ms < 50:
        return "[bold cyan]Bon[/bold cyan]"
    if ms < 100:
        return "[yellow]Moyen[/yellow]"
    return "[red]Élevé[/red]"


def print_banner():
    banner = """[bold cyan]
  ╔═══════════════════════════════════════════╗
  ║   🌐  S P E E D T E R M   v{version}            ║
  ║   Test de vitesse Internet — Terminal     ║
  ╚═══════════════════════════════════════════╝[/bold cyan]""".format(
        version=__version__
    )
    console.print(banner)


def print_info(info):
    if not info:
        console.print("[dim]Impossible de récupérer les infos de connexion[/dim]\n")
        return
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="bold white")
    table.add_row("ISP", info.get("asOrganization", "N/A"))
    table.add_row(
        "Localisation",
        f"{info.get('city', 'N/A')}, {info.get('country', 'N/A')}",
    )
    table.add_row("IP", info.get("clientIp", "N/A"))
    table.add_row("Serveur", info.get("colo", "N/A"))
    console.print(Panel(table, title="[cyan]Connexion[/cyan]", border_style="cyan"))


def run_test(download_size=25, upload_size=10, ping_samples=10):
    print_banner()
    console.print()

    info = get_connection_info()
    print_info(info)
    console.print()

    results = {}

    # Ping
    with console.status("[cyan]⏱  Mesure du ping...[/cyan]", spinner="dots"):
        ping = measure_ping(samples=ping_samples)
    results["ping"] = ping
    if ping:
        console.print(
            f"[green]✓[/green] Ping: [bold]{ping['avg']:.1f} ms[/bold] "
            f"(min {ping['min']:.1f} / max {ping['max']:.1f} / "
            f"jitter {ping['jitter']:.1f})"
        )
    else:
        console.print("[red]✗ Échec du ping[/red]")

    # Download
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]⬇  Téléchargement...[/cyan]"),
        BarColumn(),
        TextColumn("[bold]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("download", total=download_size * 1_000_000)

        def update_download(current, total):
            progress.update(task, completed=current)

        download = measure_download(
            size_mb=download_size, progress_callback=update_download
        )
    results["download"] = download
    console.print(f"[green]✓[/green] Download: [bold]{download:.2f} Mbps[/bold]")

    # Upload
    with console.status("[cyan]⬆  Envoi (upload)...[/cyan]", spinner="dots"):
        upload = measure_upload(size_mb=upload_size)
    results["upload"] = upload
    console.print(f"[green]✓[/green] Upload: [bold]{upload:.2f} Mbps[/bold]")

    console.print()

    # Tableau final
    table = Table(title="📊 Résultats", border_style="cyan", title_style="bold cyan")
    table.add_column("Mesure", style="cyan", no_wrap=True)
    table.add_column("Valeur", justify="right", style="bold white")
    table.add_column("Qualité", justify="center")

    if ping:
        table.add_row("Ping moyen", f"{ping['avg']:.1f} ms", ping_quality(ping["avg"]))
        table.add_row("Jitter", f"{ping['jitter']:.1f} ms", "")
    table.add_row("⬇  Download", f"{download:.2f} Mbps", quality_label(download))
    table.add_row("⬆  Upload", f"{upload:.2f} Mbps", quality_label(upload))

    console.print(table)
    console.print()
    return results


def main():
    parser = argparse.ArgumentParser(
        prog="speedterm",
        description="Test de vitesse Internet dans le terminal.",
    )
    parser.add_argument(
        "--download-size",
        type=int,
        default=25,
        help="Taille du fichier de test download en Mo (défaut: 25)",
    )
    parser.add_argument(
        "--upload-size",
        type=int,
        default=10,
        help="Taille du fichier de test upload en Mo (défaut: 10)",
    )
    parser.add_argument(
        "--ping-samples",
        type=int,
        default=10,
        help="Nombre d'échantillons de ping (défaut: 10)",
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Sortie simplifiée (Ping/Download/Upload sur 3 lignes)",
    )
    parser.add_argument(
        "--version", action="version", version=f"speedterm {__version__}"
    )
    args = parser.parse_args()

    try:
        if args.simple:
            ping = measure_ping(samples=args.ping_samples)
            download = measure_download(size_mb=args.download_size)
            upload = measure_upload(size_mb=args.upload_size)
            print(f"Ping:     {ping['avg']:.1f} ms" if ping else "Ping:     N/A")
            print(f"Download: {download:.2f} Mbps")
            print(f"Upload:   {upload:.2f} Mbps")
        else:
            run_test(
                download_size=args.download_size,
                upload_size=args.upload_size,
                ping_samples=args.ping_samples,
            )
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrompu par l'utilisateur.[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
