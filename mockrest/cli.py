"""
CLI interface and interactive server runner for mockrest.
Zephyrus Labs (https://zephyrus-labs.tech/)
Lead Developer: Shubham Sharma
"""
import argparse
import json
import os
import sys
import time
from typing import Dict, List, Optional

from mockrest import __version__
from mockrest.core import MockServer, generate_synthetic_data

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║               mockrest-cli  v{__version__}                         ║
║     Instant Zero-Config Mock REST API Server                 ║
║     Zephyrus Labs (https://zephyrus-labs.tech/)              ║
╚══════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)


def display_server_dashboard(server: MockServer):
    print(f"\n{GREEN}{BOLD}🚀 Server is LIVE at:{RESET} {CYAN}{server.base_url}{RESET}")
    print(f"{BOLD}Simulated Latency:{RESET} {server.latency_ms} ms | {BOLD}Read-Only:{RESET} {server.read_only}")
    print(f"{BOLD}OpenAPI 3.0 Documentation:{RESET} {CYAN}{server.base_url}/openapi.json{RESET}")
    print("\n" + "=" * 65)
    print(f"{BOLD}{'Available Resources & Endpoints':<40} {'Count'}{RESET}")
    print("=" * 65)
    for res_name, items in server.store.items():
        print(f"  {CYAN}GET/POST{RESET}   /{res_name:<30} ({len(items)} items)")
        print(f"  {CYAN}GET/PUT/PATCH/DELETE{RESET} /{res_name}/:id")
        print("-" * 65)
    print(f"\n{YELLOW}Press Ctrl+C to stop the server.{RESET}\n")


def run_interactive_wizard() -> int:
    print_banner()
    print(f"\n{BOLD}Welcome to the mockrest Interactive Setup Wizard!{RESET}\n")

    print(f"{BOLD}Choose Data Source:{RESET}")
    print("  [1] Generate realistic synthetic mock data (Users, Products, Posts, Todos) [Default]")
    print("  [2] Load an existing JSON database file")
    source_choice = input(f"{BOLD}Choose [1/2] (default: 1):{RESET} ").strip() or "1"

    data = None
    if source_choice == "2":
        while True:
            file_path = input(f"{BOLD}Enter path to JSON file:{RESET} ").strip()
            if not file_path or not os.path.exists(file_path):
                print(f"{RED}File not found. Please try again.{RESET}")
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, dict):
                        data = raw_data
                    elif isinstance(raw_data, list):
                        data = {"items": raw_data}
                    else:
                        print(f"{RED}JSON root must be an object or array.{RESET}")
                        continue
                break
            except Exception as e:
                print(f"{RED}Error reading JSON: {e}{RESET}")
                continue
    else:
        data = generate_synthetic_data()

    # Port
    port_str = input(f"{BOLD}Enter port number (default: 8000):{RESET} ").strip() or "8000"
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    # Latency
    delay_str = input(f"{BOLD}Enter simulated network delay in ms (default: 0):{RESET} ").strip() or "0"
    try:
        delay = int(delay_str)
    except ValueError:
        delay = 0

    # Read-only
    ro_str = input(f"{BOLD}Enable read-only mode (disables mutations)? [y/N]:{RESET} ").strip().lower()
    read_only = ro_str == "y"

    server = MockServer(
        data=data,
        port=port,
        bind_host="127.0.0.1",
        latency_ms=delay,
        read_only=read_only,
        verbose=True,
    )
    server.start()
    display_server_dashboard(server)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down server...{RESET}")
        server.stop()
        print(f"{GREEN}Server stopped cleanly.{RESET}")
        return 0


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="mockrest",
        description="Instant Zero-Config Mock REST API Server by Zephyrus Labs",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to JSON file to serve (if omitted, synthetic data is generated)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port number to listen on (default: 8000)",
    )
    parser.add_argument(
        "-b",
        "--bind",
        default="127.0.0.1",
        help="Network interface to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        default=0,
        help="Simulated artificial network latency in ms (default: 0)",
    )
    parser.add_argument(
        "-r",
        "--read-only",
        action="store_true",
        help="Reject POST, PUT, PATCH, and DELETE mutations",
    )
    parser.add_argument(
        "--no-cors",
        action="store_true",
        help="Disable permissive CORS headers",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Launch interactive configuration wizard",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"mockrest-cli {__version__} by Zephyrus Labs",
    )

    args = parser.parse_args(argv)

    if args.interactive:
        return run_interactive_wizard()

    data = None
    if args.file:
        if not os.path.exists(args.file):
            print(f"{RED}Error: File '{args.file}' not found.{RESET}", file=sys.stderr)
            return 1
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, dict):
                    data = raw
                elif isinstance(raw, list):
                    data = {"items": raw}
                else:
                    print(f"{RED}Error: JSON root must be object or array.{RESET}", file=sys.stderr)
                    return 1
        except Exception as e:
            print(f"{RED}Error loading '{args.file}': {e}{RESET}", file=sys.stderr)
            return 1
    else:
        data = generate_synthetic_data()

    server = MockServer(
        data=data,
        port=args.port,
        bind_host=args.bind,
        latency_ms=args.delay,
        read_only=args.read_only,
        enable_cors=not args.no_cors,
        verbose=True,
    )
    server.start()
    display_server_dashboard(server)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down server...{RESET}")
        server.stop()
        print(f"{GREEN}Server stopped cleanly.{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
