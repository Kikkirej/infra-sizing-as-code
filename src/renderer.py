from datetime import date
from pathlib import Path

from src.loader import Flavour, FlavourImage, Partition, Product, Server, Size
from src.versioning import VersionFileData


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


def _render_partition_table(partitions: list[Partition]) -> str:
    lines = [
        '[cols="3,3,3",options="header"]',
        "!===",
        "! Size ! Perform- +\nance ! Comment/ +\nUsage",
    ]
    for p in partitions:
        comment_cell = p.comment if p.comment else ""
        lines.append(f"! {p.size.render()} ! {p.performance} ! {comment_cell}")
    lines.append("!===")
    return "\n".join(lines)


def _render_comment_cell(server) -> str:
    parts = []
    for item in server.software:
        parts.append(f"* {item}")
    for item in server.network:
        parts.append(f"* {item}")
    if server.comment:
        if parts:
            parts.append("")
        parts.append(server.comment)
    return "\n".join(parts)


def render_server_table(flavour: Flavour) -> str:
    col_spec = '[cols="15,14,13,43,33",options="header"]'
    header = "| System | CPU | Memory | Disk | Comment"
    lines = [col_spec, "|===", header]

    for server in flavour.servers:
        system_cell = server.system if server.count == 1 else f"{server.system} [{server.count}]"
        cpu_cell = f"{server.cpu.render()} ({server.cpu_clocking})"
        memory_cell = server.memory.render()
        disk_cell = _render_partition_table(server.disk)
        comment_cell = _render_comment_cell(server)

        lines += [
            "",
            f"| {system_cell}",
            f"| {cpu_cell}",
            f"| {memory_cell}",
            f"a|\n{disk_cell}",
            f"a| {comment_cell}",
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

    if flavour.has_prefix:
        parts.append(
            f"include::infra/{product_shortname}/{size_shortname}/{flavour.shortname}/prefix.adoc[]\n"
        )

    parts.append(render_server_table(flavour))

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


def render_version_table(version_file: VersionFileData) -> str:
    lines = [
        "== Version History\n",
        '[cols="15,15,30,40",options="header"]',
        "|===",
        "| Version | Date | Author(s) | Notes",
    ]
    for entry in version_file.entries:
        notes_cell = entry.notes or ""
        lines.append(f"| {version_file.version_name} | {entry.date} | {entry.author} | {notes_cell}")
    lines.append("|===")
    return "\n".join(lines) + "\n"


def render_product_document(product: Product, build_date: str = "") -> str:
    parts = [render_document_header(product)]

    parts.append("include::infra/prefix.adoc[]\n")
    parts.append(f"include::{product.prefix_path}[]\n")

    is_single_size = len(product.sizes) == 1
    for size in product.sizes:
        parts.append(render_size_section(size, product.shortname, is_single_size))

    parts.append(f"include::{product.suffix_path}[]\n")
    parts.append("include::infra/suffix.adoc[]\n")

    if product.version_file is not None:
        parts.append(render_version_table(product.version_file))

    return "\n".join(parts)
