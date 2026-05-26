import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from mcp_server import reader

REPO_ROOT = Path(os.environ.get("REPO_ROOT", "."))

mcp = FastMCP("infra-sizing")


@mcp.tool()
def get_flavour_spec(product: str, size: str, flavour: str) -> str:
    """Retrieve the full hardware specification for a specific flavour."""
    try:
        spec = reader.read_flavour_spec(REPO_ROOT, product, size, flavour)
        return json.dumps(spec)
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def list_products() -> str:
    """List all infrastructure products available in the repository."""
    try:
        products = reader.read_products(REPO_ROOT)
        return json.dumps([{"shortname": p["shortname"], "display_name": p["display_name"]} for p in products])
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def list_sizes(product: str) -> str:
    """List all size tiers available for a given product."""
    try:
        sizes = reader.read_sizes(REPO_ROOT, product)
        return json.dumps([{"shortname": s["shortname"], "display_name": s["display_name"]} for s in sizes])
    except ValueError as exc:
        return str(exc)


@mcp.tool()
def list_flavours(product: str, size: str) -> str:
    """List all flavours available within a given product and size combination."""
    try:
        flavours = reader.read_flavours(REPO_ROOT, product, size)
        return json.dumps([{"shortname": f["shortname"], "display_name": f["display_name"]} for f in flavours])
    except ValueError as exc:
        return str(exc)
