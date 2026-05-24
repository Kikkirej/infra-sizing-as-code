from datetime import date
from pathlib import Path

from src.loader import Flavour, FlavourImage, Partition, Product, Server, Size


def render_document_header(product: Product) -> str:
    revdate = date.today().isoformat()
    lines = [
        f"= {product.display_name}",
        ":doctype: book",
        ":toc:",
        ":title-page:",
        f":revdate: {revdate}",
        ":nofooter:",
    ]
    return "\n".join(lines) + "\n"


def _render_partition(p: Partition) -> str:
    text = f"* {p.size}, {p.performance}"
    if p.comment:
        text += f" — {p.comment}"
    return text


def _render_list_cell(items: list[str]) -> str:
    if not items:
        return ""
    return "\n".join(f"* {item}" for item in items)


def render_server_table(servers: list[Server]) -> str:
    lines = [
        '[cols="2,1,1,1,1,3,2,2,2",options="header"]',
        "|===",
        "| System | Count | CPU | CPU Clocking | Memory | Disk | Network | Software | Comment",
    ]
    for server in servers:
        disk_cell = "\n".join(_render_partition(p) for p in server.disk)
        network_cell = _render_list_cell(server.network)
        software_cell = _render_list_cell(server.software)
        lines += [
            "",
            f"| {server.system}",
            f"| {server.count}",
            f"| {server.cpu}",
            f"| {server.cpu_clocking}",
            f"| {server.memory}",
            f"a| {disk_cell}",
            f"a| {network_cell}",
            f"a| {software_cell}",
            f"| {server.comment}",
        ]
    lines.append("|===")
    return "\n".join(lines) + "\n"


def render_flavour_section(
    flavour: Flavour,
    product_shortname: str,
    size_shortname: str,
) -> str:
    parts = [f"=== {flavour.display_name}\n"]

    if flavour.image:
        img = flavour.image
        base = f"infra/{product_shortname}/{size_shortname}/{flavour.shortname}/{img.value}"
        if img.type == "file":
            parts.append(f"image::{base}[]\n")
        elif img.type == "mermaid":
            mmd_content = Path(base).read_text()
            parts.append("[mermaid]\n----\n" + mmd_content + "\n----\n")

    if flavour.has_preamble:
        parts.append(
            f"include::infra/{product_shortname}/{size_shortname}/{flavour.shortname}/preamble.adoc[]\n"
        )

    parts.append(render_server_table(flavour.servers))

    if flavour.has_suffix:
        parts.append(
            f"include::infra/{product_shortname}/{size_shortname}/{flavour.shortname}/suffix.adoc[]\n"
        )

    return "\n".join(parts)


def render_size_section(
    size: Size,
    product_shortname: str,
    is_single_size: bool,
) -> str:
    parts = []

    if not is_single_size:
        parts.append(f"== {size.display_name}\n")

    if size.prefix_text:
        parts.append(size.prefix_text + "\n")

    for flavour in size.flavours:
        parts.append(render_flavour_section(flavour, product_shortname, size.shortname))

    if size.suffix_text:
        parts.append(size.suffix_text + "\n")

    return "\n".join(parts)


def render_product_document(product: Product, build_date: str = "") -> str:
    parts = [render_document_header(product)]

    parts.append("include::infra/preamble.adoc[]\n")
    parts.append(f"include::{product.preamble_path}[]\n")

    is_single_size = len(product.sizes) == 1
    for size in product.sizes:
        parts.append(render_size_section(size, product.shortname, is_single_size))

    parts.append(f"include::{product.suffix_path}[]\n")
    parts.append("include::infra/suffix.adoc[]\n")

    return "\n".join(parts)
