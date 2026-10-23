# mockrest-cli

[![PyPI version](https://img.shields.io/pypi/v/mockrest-cli.svg)](https://pypi.org/project/mockrest-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/mockrest-cli.svg)](https://pypi.org/project/mockrest-cli/)
[![GitHub stars](https://img.shields.io/github/stars/uchiha-fire/mockrest-cli?style=social)](https://github.com/uchiha-fire/mockrest-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Zephyrus Labs](https://img.shields.io/badge/Developed%20by-Zephyrus%20Labs-6366f1.svg)](https://zephyrus-labs.tech/)

An instant, zero-config mock REST API server with full CRUD, CORS, latency simulation, and OpenAPI 3.0 generation by **[Zephyrus Labs](https://zephyrus-labs.tech/)** for Linux, macOS, and Windows.

---

## Features

- ⚡ **Zero External Dependencies**: Pure Python standard library implementation (`http.server`, `urllib.parse`, `json`, `threading`).
- 🔄 **Full RESTful CRUD**:
  - `GET /<resource>` (list with filtering, sorting, and pagination)
  - `GET /<resource>/:id` (fetch by ID)
  - `POST /<resource>` (create new records with auto-allocated IDs)
  - `PUT /<resource>/:id` (replace record)
  - `PATCH /<resource>/:id` (partial update)
  - `DELETE /<resource>/:id` (remove record)
- 📖 **Automatic OpenAPI 3.0 Docs**: Live interactive schema available at `GET /openapi.json`.
- 🌐 **Built-in CORS**: Pre-configured `Access-Control-Allow-Origin: *` for seamless frontend development.
- ⏱️ **Simulated Network Latency**: Test slow mobile connections and race conditions with `--delay <ms>`.
- 🛡️ **Read-Only Mode**: Protect baseline datasets by rejecting mutations with `--read-only`.
- 🎲 **Instant Synthetic Data**: Start with zero setup—generates realistic users, products, posts, and todos out of the box.
- 🧪 **Programmatic Python API**: Embed `MockServer` directly in pytest integration suites.

---

## Installation

```bash
pip install mockrest-cli
```

Or install the development build directly:

```bash
pip install git+https://github.com/uchiha-fire/mockrest-cli.git
```

---

## Interactive Mode

Run `mockrest` with `--interactive` or invoke it without arguments to launch the wizard:

```bash
mockrest --interactive
```

```text
╔══════════════════════════════════════════════════════════════╗
║               mockrest-cli  v0.1.0                           ║
║     Instant Zero-Config Mock REST API Server                 ║
║     Zephyrus Labs (https://zephyrus-labs.tech/)              ║
╚══════════════════════════════════════════════════════════════╝

Welcome to the mockrest Interactive Setup Wizard!

Choose Data Source:
  [1] Generate realistic synthetic mock data (Users, Products, Posts, Todos) [Default]
  [2] Load an existing JSON database file
Choose [1/2] (default: 1): 1

Enter port number (default: 8000): 8000
Enter simulated network delay in ms (default: 0): 150
Enable read-only mode (disables mutations)? [y/N]: N

🚀 Server is LIVE at: http://127.0.0.1:8000
Simulated Latency: 150 ms | Read-Only: False
OpenAPI 3.0 Documentation: http://127.0.0.1:8000/openapi.json

=================================================================
Available Resources & Endpoints                          Count
=================================================================
  GET/POST   /users                          (4 items)
  GET/PUT/PATCH/DELETE /users/:id
-----------------------------------------------------------------
  GET/POST   /products                       (4 items)
  GET/PUT/PATCH/DELETE /products/:id
-----------------------------------------------------------------
  GET/POST   /posts                          (3 items)
  GET/PUT/PATCH/DELETE /posts/:id
-----------------------------------------------------------------
  GET/POST   /todos                          (3 items)
  GET/PUT/PATCH/DELETE /todos/:id
-----------------------------------------------------------------

Press Ctrl+C to stop the server.
```

---

## CLI Usage & Options

```bash
# Serve synthetic mock data on port 8000
mockrest

# Serve an existing JSON file
mockrest db.json

# Custom port with 250ms artificial latency delay
mockrest db.json --port 3000 --delay 250

# Read-only mode (rejects POST/PUT/PATCH/DELETE)
mockrest db.json --read-only

# Bind to all network interfaces (e.g. for Docker or mobile testing)
mockrest db.json --bind 0.0.0.0
```

### Options Reference

| Flag | Long Option | Default | Description |
| :--- | :--- | :--- | :--- |
| `file` | *(positional)* | None | Path to JSON file (if omitted, synthetic data is generated) |
| `-p` | `--port` | `8000` | Port number to bind the server |
| `-b` | `--bind` | `127.0.0.1` | Network interface to bind |
| `-d` | `--delay` | `0` | Artificial network delay in milliseconds |
| `-r` | `--read-only` | `False` | Disallow mutation requests |
| | `--no-cors` | `False` | Disable permissive CORS headers |
| `-i` | `--interactive` | `False` | Launch interactive configuration wizard |
| `-v` | `--version` | — | Display package version |

---

## Query Parameters: Filtering, Sorting & Pagination

All collection endpoints support query parameter operations:

```bash
# Filter by attribute
curl "http://127.0.0.1:8000/users?city=Berlin"

# Sort ascending
curl "http://127.0.0.1:8000/products?sort=price"

# Sort descending (prefix with '-')
curl "http://127.0.0.1:8000/products?sort=-price"

# Pagination
curl "http://127.0.0.1:8000/posts?page=1&limit=5"
```

---

## Python API Reference

```python
from mockrest import MockServer

# Start in-memory server for integration tests
server = MockServer(
    data={"todos": [{"id": 1, "task": "Ship to production", "completed": False}]},
    port=8080,
    latency_ms=50
)
server.start()

print(f"Mock server running at {server.base_url}")
# Run your frontend, curl, or HTTP client tests here...

server.stop()
```

---

## Developed & Maintained by Zephyrus Labs

Built and maintained by **[Zephyrus Labs](https://zephyrus-labs.tech/)**.

- 🌐 Website: [zephyrus-labs.tech](https://zephyrus-labs.tech/)
- 💻 GitHub: [@uchiha-fire](https://github.com/uchiha-fire)
- ✉️ Contact: [zephyrus.labs@gmail.com](mailto:zephyrus.labs@gmail.com)

If you find this tool helpful, please give it a ⭐️ on [GitHub](https://github.com/uchiha-fire/mockrest-cli)!

---

## Acknowledgements & Attributions

`mockrest-cli` is implemented entirely with Python's standard library (`http.server`, `urllib.parse`, `json`, `threading`). No third-party packages or Node.js runtimes required.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="right">
  <sub>Lead Developer: <a href="https://www.linkedin.com/in/shubham-sharma-28487819b/">Shubham Sharma</a> (<a href="https://github.com/uchiha-fire">@uchiha-fire</a>) &bull; <a href="mailto:sharmashubham25962@gmail.com">sharmashubham25962@gmail.com</a></sub>
</p>
