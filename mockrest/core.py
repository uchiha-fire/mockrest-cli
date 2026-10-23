"""
Core HTTP server and dynamic REST router for mockrest.
Pure Python standard library, zero external dependencies.
"""
import copy
import json
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse


def generate_synthetic_data() -> Dict[str, List[Dict[str, Any]]]:
    """Generates realistic synthetic mock REST resources."""
    return {
        "users": [
            {"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin", "city": "San Francisco", "age": 29},
            {"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "developer", "city": "Berlin", "age": 34},
            {"id": 3, "name": "Charlie Davis", "email": "charlie@example.com", "role": "designer", "city": "Tokyo", "age": 26},
            {"id": 4, "name": "Dana Scully", "email": "dana@example.com", "role": "developer", "city": "Washington", "age": 32},
        ],
        "products": [
            {"id": 101, "title": "Wireless Mechanical Keyboard", "price": 129.99, "category": "Electronics", "stock": 45},
            {"id": 102, "title": "Ergonomic Vertical Mouse", "price": 59.99, "category": "Electronics", "stock": 120},
            {"id": 103, "title": "Noise-Cancelling Headphones", "price": 249.50, "category": "Audio", "stock": 18},
            {"id": 104, "title": "Aluminum Laptop Stand", "price": 39.99, "category": "Accessories", "stock": 200},
        ],
        "posts": [
            {"id": 1, "title": "Getting Started with Microservices", "author_id": 2, "likes": 42},
            {"id": 2, "title": "Designing Intuitive Developer APIs", "author_id": 3, "likes": 88},
            {"id": 3, "title": "Zero-Trust Cloud Architecture", "author_id": 1, "likes": 156},
        ],
        "todos": [
            {"id": 1, "task": "Publish Python packages to PyPI", "completed": True, "priority": "high"},
            {"id": 2, "task": "Write comprehensive unit test suites", "completed": True, "priority": "high"},
            {"id": 3, "task": "Deploy staging cluster", "completed": False, "priority": "medium"},
        ]
    }


def generate_openapi_spec(store: Dict[str, List[Dict[str, Any]]], base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Generates an OpenAPI 3.0 specification for all active endpoints in the store."""
    paths = {}
    for resource, items in store.items():
        sample_item = items[0] if items else {"id": 1}
        paths[f"/{resource}"] = {
            "get": {
                "summary": f"List all {resource}",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                    {"name": "sort", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {
                        "description": "Successful retrieval",
                        "content": {"application/json": {"example": items[:2]}}
                    }
                }
            },
            "post": {
                "summary": f"Create new {resource[:-1] if resource.endswith('s') else resource}",
                "requestBody": {
                    "content": {"application/json": {"example": sample_item}}
                },
                "responses": {"201": {"description": "Resource created successfully"}}
            }
        }
        paths[f"/{resource}/{{id}}"] = {
            "get": {
                "summary": f"Get {resource} by ID",
                "responses": {"200": {"description": "Item details"}, "404": {"description": "Item not found"}}
            },
            "put": {
                "summary": f"Replace {resource} by ID",
                "responses": {"200": {"description": "Item replaced"}, "404": {"description": "Item not found"}}
            },
            "patch": {
                "summary": f"Update {resource} fields by ID",
                "responses": {"200": {"description": "Item updated"}, "404": {"description": "Item not found"}}
            },
            "delete": {
                "summary": f"Delete {resource} by ID",
                "responses": {"200": {"description": "Item deleted"}, "404": {"description": "Item not found"}}
            }
        }

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Mock REST API",
            "version": "1.0.0",
            "description": "Auto-generated OpenAPI specification from mockrest-cli"
        },
        "servers": [{"url": base_url}],
        "paths": paths
    }


class MockRESTHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.server_ref = server
        super().__init__(request, client_address, server)

    def log_message(self, format, *args):
        # Override to suppress standard HTTP logging during automated tests unless quiet is False
        if getattr(self.server_ref, "verbose", False):
            sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def _apply_latency(self):
        latency = getattr(self.server_ref, "latency_ms", 0)
        if latency > 0:
            time.sleep(latency / 1000.0)

    def _send_cors_headers(self):
        if getattr(self.server_ref, "enable_cors", True):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json_response(self, status: int, data: Any):
        self._apply_latency()
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self._apply_latency()
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")
        query = parse_qs(parsed.query)

        # Root index
        if not path:
            resources = list(self.server_ref.store.keys())
            self._send_json_response(200, {
                "name": "mockrest-cli",
                "version": "0.1.0",
                "resources": resources,
                "openapi": "/openapi.json"
            })
            return

        # OpenAPI spec
        if path == "openapi.json":
            spec = generate_openapi_spec(
                self.server_ref.store,
                base_url=f"http://{self.server_ref.bind_host}:{self.server_ref.server_port}"
            )
            self._send_json_response(200, spec)
            return

        parts = path.split("/")
        resource = parts[0]

        if resource not in self.server_ref.store:
            self._send_json_response(404, {"error": f"Resource '{resource}' not found"})
            return

        items = self.server_ref.store[resource]

        # Get by ID: /<resource>/<id>
        if len(parts) > 1:
            item_id = parts[1]
            found = next((item for item in items if str(item.get("id")) == item_id), None)
            if found is not None:
                self._send_json_response(200, found)
            else:
                self._send_json_response(404, {"error": f"Item with id '{item_id}' not found in '{resource}'"})
            return

        # List with filtering, sorting, pagination
        result = list(items)

        # 1. Filtering
        for key, values in query.items():
            if key in ("page", "limit", "sort"):
                continue
            filter_val = values[0]
            result = [
                item for item in result
                if str(item.get(key, "")).lower() == filter_val.lower()
            ]

        # 2. Sorting
        if "sort" in query:
            sort_field = query["sort"][0]
            reverse = sort_field.startswith("-")
            field_name = sort_field.lstrip("-")
            try:
                result.sort(key=lambda x: (x.get(field_name) is None, x.get(field_name)), reverse=reverse)
            except Exception:
                pass

        # 3. Pagination
        if "page" in query or "limit" in query:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["10"])[0])
            start_idx = (page - 1) * limit
            result = result[start_idx : start_idx + limit]

        self._send_json_response(200, result)

    def do_POST(self):
        if getattr(self.server_ref, "read_only", False):
            self._send_json_response(403, {"error": "Server is running in read-only mode"})
            return

        path = urlparse(self.path).path.strip("/")
        parts = path.split("/")
        resource = parts[0]

        if resource not in self.server_ref.store:
            self.server_ref.store[resource] = []

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            new_item = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON in request body"})
            return

        # Auto allocate ID if not provided
        existing_items = self.server_ref.store[resource]
        if "id" not in new_item:
            numeric_ids = [item.get("id") for item in existing_items if isinstance(item.get("id"), int)]
            new_item["id"] = (max(numeric_ids) + 1) if numeric_ids else 1

        self.server_ref.store[resource].append(new_item)
        self._send_json_response(201, new_item)

    def do_PUT(self):
        if getattr(self.server_ref, "read_only", False):
            self._send_json_response(403, {"error": "Server is running in read-only mode"})
            return

        path = urlparse(self.path).path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            self._send_json_response(400, {"error": "PUT requires an item ID in route"})
            return

        resource, item_id = parts[0], parts[1]
        if resource not in self.server_ref.store:
            self._send_json_response(404, {"error": f"Resource '{resource}' not found"})
            return

        items = self.server_ref.store[resource]
        target_idx = next((idx for idx, item in enumerate(items) if str(item.get("id")) == item_id), None)
        if target_idx is None:
            self._send_json_response(404, {"error": f"Item '{item_id}' not found in '{resource}'"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            replacement = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON body"})
            return

        # Preserve ID type (int or str)
        orig_id = items[target_idx].get("id")
        replacement["id"] = orig_id
        items[target_idx] = replacement
        self._send_json_response(200, replacement)

    def do_PATCH(self):
        if getattr(self.server_ref, "read_only", False):
            self._send_json_response(403, {"error": "Server is running in read-only mode"})
            return

        path = urlparse(self.path).path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            self._send_json_response(400, {"error": "PATCH requires an item ID in route"})
            return

        resource, item_id = parts[0], parts[1]
        if resource not in self.server_ref.store:
            self._send_json_response(404, {"error": f"Resource '{resource}' not found"})
            return

        items = self.server_ref.store[resource]
        target_idx = next((idx for idx, item in enumerate(items) if str(item.get("id")) == item_id), None)
        if target_idx is None:
            self._send_json_response(404, {"error": f"Item '{item_id}' not found in '{resource}'"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            updates = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON body"})
            return

        item = items[target_idx]
        item.update(updates)
        self._send_json_response(200, item)

    def do_DELETE(self):
        if getattr(self.server_ref, "read_only", False):
            self._send_json_response(403, {"error": "Server is running in read-only mode"})
            return

        path = urlparse(self.path).path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            self._send_json_response(400, {"error": "DELETE requires an item ID in route"})
            return

        resource, item_id = parts[0], parts[1]
        if resource not in self.server_ref.store:
            self._send_json_response(404, {"error": f"Resource '{resource}' not found"})
            return

        items = self.server_ref.store[resource]
        target_idx = next((idx for idx, item in enumerate(items) if str(item.get("id")) == item_id), None)
        if target_idx is None:
            self._send_json_response(404, {"error": f"Item '{item_id}' not found in '{resource}'"})
            return

        deleted_item = items.pop(target_idx)
        self._send_json_response(200, {"success": True, "deleted": deleted_item})


class CustomHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, store, latency_ms, read_only, enable_cors, bind_host, verbose=False):
        self.store = store
        self.latency_ms = latency_ms
        self.read_only = read_only
        self.enable_cors = enable_cors
        self.bind_host = bind_host
        self.verbose = verbose
        super().__init__(server_address, RequestHandlerClass)


class MockServer:
    """
    Programmatic REST mock server runner for tests and application integration.
    """
    def __init__(
        self,
        data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        port: int = 8000,
        bind_host: str = "127.0.0.1",
        latency_ms: int = 0,
        read_only: bool = False,
        enable_cors: bool = True,
        verbose: bool = False,
    ):
        self.store = copy.deepcopy(data) if data is not None else generate_synthetic_data()
        self.bind_host = bind_host
        self.requested_port = port
        self.latency_ms = latency_ms
        self.read_only = read_only
        self.enable_cors = enable_cors
        self.verbose = verbose

        self._httpd: Optional[CustomHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self.port = port

    def start(self):
        """Starts the server in a background daemon thread."""
        self._httpd = CustomHTTPServer(
            (self.bind_host, self.requested_port),
            MockRESTHandler,
            store=self.store,
            latency_ms=self.latency_ms,
            read_only=self.read_only,
            enable_cors=self.enable_cors,
            bind_host=self.bind_host,
            verbose=self.verbose,
        )
        self.port = self._httpd.server_port
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        """Shuts down the server."""
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    @property
    def base_url(self) -> str:
        return f"http://{self.bind_host}:{self.port}"
