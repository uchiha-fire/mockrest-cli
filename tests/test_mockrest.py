"""
Comprehensive test suite for mockrest-cli.
TDD coverage: MockServer lifecycle, full REST CRUD, filtering, sorting,
pagination, CORS headers, latency simulation, read-only mode, and OpenAPI 3.0 generation.
"""
import json
import time
import urllib.request
import urllib.error
import pytest

from mockrest.core import MockServer, generate_synthetic_data


@pytest.fixture
def mock_db():
    return {
        "users": [
            {"id": 1, "name": "Alice", "city": "Berlin", "age": 28},
            {"id": 2, "name": "Bob", "city": "Munich", "age": 35},
            {"id": 3, "name": "Charlie", "city": "Berlin", "age": 22},
        ],
        "products": [
            {"id": 101, "title": "Mechanical Keyboard", "price": 89.99},
            {"id": 102, "title": "Ergonomic Mouse", "price": 49.99},
        ]
    }


@pytest.fixture
def running_server(mock_db):
    server = MockServer(data=mock_db, port=0, bind_host="127.0.0.1")
    server.start()
    yield server
    server.stop()


def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            resp_headers = dict(resp.getheaders())
            resp_body = resp.read().decode("utf-8")
            json_data = json.loads(resp_body) if resp_body else None
            return status, json_data, resp_headers
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        json_data = json.loads(resp_body) if resp_body else None
        return e.code, json_data, dict(e.headers)


# ---------------------------------------------------------------------------
# Core Server & Read Endpoints
# ---------------------------------------------------------------------------

def test_server_root_index(running_server):
    status, data, _ = make_request(f"{running_server.base_url}/")
    assert status == 200
    assert "users" in data["resources"]
    assert "products" in data["resources"]


def test_get_resource_list(running_server):
    status, data, _ = make_request(f"{running_server.base_url}/users")
    assert status == 200
    assert len(data) == 3
    assert data[0]["name"] == "Alice"


def test_get_resource_by_id(running_server):
    status, data, _ = make_request(f"{running_server.base_url}/users/1")
    assert status == 200
    assert data["id"] == 1
    assert data["name"] == "Alice"

    # Non-existent ID
    status_404, err, _ = make_request(f"{running_server.base_url}/users/999")
    assert status_404 == 404
    assert "error" in err


# ---------------------------------------------------------------------------
# Mutations (CRUD)
# ---------------------------------------------------------------------------

def test_post_create(running_server):
    new_user = {"name": "Dana", "city": "Hamburg", "age": 30}
    status, data, _ = make_request(
        f"{running_server.base_url}/users",
        method="POST",
        data=new_user
    )
    assert status == 201
    assert data["name"] == "Dana"
    assert "id" in data
    allocated_id = data["id"]

    # Verify persistent in server store
    get_status, get_data, _ = make_request(f"{running_server.base_url}/users/{allocated_id}")
    assert get_status == 200
    assert get_data["name"] == "Dana"


def test_put_replace(running_server):
    replacement = {"name": "Alice Cooper", "city": "London", "age": 29}
    status, data, _ = make_request(
        f"{running_server.base_url}/users/1",
        method="PUT",
        data=replacement
    )
    assert status == 200
    assert data["id"] == 1
    assert data["name"] == "Alice Cooper"
    assert data["city"] == "London"


def test_patch_update(running_server):
    update = {"city": "Frankfurt"}
    status, data, _ = make_request(
        f"{running_server.base_url}/users/2",
        method="PATCH",
        data=update
    )
    assert status == 200
    assert data["id"] == 2
    assert data["name"] == "Bob"  # retained
    assert data["city"] == "Frankfurt"  # updated


def test_delete(running_server):
    status, data, _ = make_request(f"{running_server.base_url}/users/3", method="DELETE")
    assert status in (200, 204)

    # Verify deleted
    status_after, _, _ = make_request(f"{running_server.base_url}/users/3")
    assert status_after == 404


# ---------------------------------------------------------------------------
# Filtering, Sorting, and Pagination
# ---------------------------------------------------------------------------

def test_filtering_query_params(running_server):
    status, data, _ = make_request(f"{running_server.base_url}/users?city=Berlin")
    assert status == 200
    assert len(data) == 2
    assert all(u["city"] == "Berlin" for u in data)


def test_sorting_ascending_and_descending(running_server):
    # Ascending sort by age
    status_asc, data_asc, _ = make_request(f"{running_server.base_url}/users?sort=age")
    assert status_asc == 200
    ages_asc = [u["age"] for u in data_asc]
    assert ages_asc == sorted(ages_asc)

    # Descending sort by -age
    status_desc, data_desc, _ = make_request(f"{running_server.base_url}/users?sort=-age")
    assert status_desc == 200
    ages_desc = [u["age"] for u in data_desc]
    assert ages_desc == sorted(ages_asc, reverse=True)


def test_pagination(running_server):
    status, data, _ = make_request(f"{running_server.base_url}/users?page=1&limit=2")
    assert status == 200
    assert len(data) == 2
    assert data[0]["name"] == "Alice"
    assert data[1]["name"] == "Bob"


# ---------------------------------------------------------------------------
# CORS, Latency, Read-Only, and OpenAPI
# ---------------------------------------------------------------------------

def test_cors_options_preflight(running_server):
    status, _, headers = make_request(f"{running_server.base_url}/users", method="OPTIONS")
    assert status == 204
    # Case-insensitive header check
    headers_lower = {k.lower(): v for k, v in headers.items()}
    assert "access-control-allow-origin" in headers_lower
    assert headers_lower["access-control-allow-origin"] == "*"


def test_read_only_mode(mock_db):
    server = MockServer(data=mock_db, port=0, read_only=True)
    server.start()
    try:
        status, _, _ = make_request(
            f"{server.base_url}/users",
            method="POST",
            data={"name": "Hacker"}
        )
        assert status == 403
    finally:
        server.stop()


def test_latency_simulation(mock_db):
    server = MockServer(data=mock_db, port=0, latency_ms=100)
    server.start()
    try:
        start_t = time.time()
        status, _, _ = make_request(f"{server.base_url}/users")
        duration = time.time() - start_t
        assert status == 200
        assert duration >= 0.08  # Account for minor clock precision
    finally:
        server.stop()


def test_openapi_spec_endpoint(running_server):
    status, spec, _ = make_request(f"{running_server.base_url}/openapi.json")
    assert status == 200
    assert spec["openapi"] == "3.0.0"
    assert "/users" in spec["paths"]
    assert "/products" in spec["paths"]


def test_synthetic_data_generation():
    data = generate_synthetic_data()
    assert "users" in data
    assert "products" in data
    assert "posts" in data
    assert "todos" in data
    assert len(data["users"]) > 0
