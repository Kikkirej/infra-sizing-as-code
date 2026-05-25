from src.loader import Flavour, FlavourImage, Partition, Product, Server, Size
from src.renderer import (
    render_document_header,
    render_flavour_section,
    render_product_document,
    render_server_table,
    render_size_section,
)


def _make_server(disk=None, network=None, software=None, comment="", count=1):
    return Server(
        system="Web",
        cpu="4 vCPU",
        cpu_clocking="3.0 GHz",
        memory="16 GB",
        disk=disk or [Partition(size="100 GB", performance="SSD")],
        network=network or [],
        software=software or [],
        comment=comment,
        count=count,
    )


def test_render_server_table_9_columns():
    server = _make_server()
    table = render_server_table([server])
    assert '[cols="2,1,1,1,1,3,2,2,2",options="header"]' in table
    assert "| System | Count | CPU | CPU Clocking | Memory | Disk | Network | Software | Comment" in table


def test_render_server_table_single_partition():
    server = _make_server(disk=[Partition(size="100 GB", performance="SSD", comment="OS")])
    table = render_server_table([server])
    assert "* 100 GB, SSD — OS" in table


def test_render_server_table_multi_partition():
    server = _make_server(disk=[
        Partition(size="100 GB", performance="SSD", comment="OS"),
        Partition(size="500 GB", performance="HDD"),
    ])
    table = render_server_table([server])
    assert "* 100 GB, SSD — OS" in table
    assert "* 500 GB, HDD" in table


def test_render_server_table_empty_network_blank_cell():
    server = _make_server(network=[])
    table = render_server_table([server])
    assert "a| \n" in table or "a| " in table


def test_render_server_table_partition_no_comment():
    server = _make_server(disk=[Partition(size="200 GB", performance="NVMe")])
    table = render_server_table([server])
    assert "— " not in table
    assert "* 200 GB, NVMe" in table


def test_render_size_section_suppresses_heading_when_single():
    size = Size(
        shortname="size-s",
        display_name="Small",
        flavours=[Flavour(
            shortname="flavour-f",
            display_name="F",
            servers=[_make_server()],
        )],
    )
    section = render_size_section(size, "product-a", is_single_size=True)
    assert "== Small" not in section


def test_render_size_section_includes_heading_when_multiple():
    size = Size(
        shortname="size-s",
        display_name="Small",
        flavours=[Flavour(
            shortname="flavour-f",
            display_name="F",
            servers=[_make_server()],
        )],
    )
    section = render_size_section(size, "product-a", is_single_size=False)
    assert "== Small" in section


def test_render_flavour_section_no_preamble_no_suffix():
    flavour = Flavour(
        shortname="flavour-f",
        display_name="F",
        servers=[_make_server()],
        has_preamble=False,
        has_suffix=False,
    )
    section = render_flavour_section(flavour, "product-a", "size-s")
    assert "include::" not in section


def test_render_flavour_section_with_preamble():
    flavour = Flavour(
        shortname="flavour-f",
        display_name="F",
        servers=[_make_server()],
        has_preamble=True,
        has_suffix=False,
    )
    section = render_flavour_section(flavour, "product-a", "size-s")
    assert "include::infra/product-a/size-s/flavour-f/preamble.adoc[]" in section


def test_render_flavour_section_with_suffix():
    flavour = Flavour(
        shortname="flavour-f",
        display_name="F",
        servers=[_make_server()],
        has_preamble=False,
        has_suffix=True,
    )
    section = render_flavour_section(flavour, "product-a", "size-s")
    assert "include::infra/product-a/size-s/flavour-f/suffix.adoc[]" in section


def test_render_product_document_section_order():
    product = Product(
        shortname="product-a",
        display_name="Product A",
        sizes=[Size(
            shortname="size-s",
            display_name="Small",
            flavours=[Flavour(
                shortname="flavour-f",
                display_name="F",
                servers=[_make_server()],
            )],
        )],
        preamble_path="infra/product-a/preamble.adoc",
        suffix_path="infra/product-a/suffix.adoc",
    )
    doc = render_product_document(product)
    assert doc.index("include::infra/preamble.adoc[]") < doc.index("include::infra/product-a/preamble.adoc[]")
    assert doc.index("include::infra/product-a/preamble.adoc[]") < doc.index("=== F")
    assert doc.index("=== F") < doc.index("include::infra/product-a/suffix.adoc[]")
    assert doc.index("include::infra/product-a/suffix.adoc[]") < doc.index("include::infra/suffix.adoc[]")


def test_render_product_document_per_product_includes():
    product_a = Product(
        shortname="product-a",
        display_name="Product A",
        sizes=[Size(
            shortname="size-s",
            display_name="Small",
            flavours=[Flavour(
                shortname="flavour-f",
                display_name="F",
                servers=[_make_server()],
            )],
        )],
        preamble_path="infra/product-a/preamble.adoc",
        suffix_path="infra/product-a/suffix.adoc",
    )
    product_b = Product(
        shortname="product-b",
        display_name="Product B",
        sizes=[Size(
            shortname="size-l",
            display_name="Large",
            flavours=[Flavour(
                shortname="flavour-g",
                display_name="G",
                servers=[_make_server()],
            )],
        )],
        preamble_path="infra/product-b/preamble.adoc",
        suffix_path="infra/product-b/suffix.adoc",
    )
    doc_a = render_product_document(product_a)
    doc_b = render_product_document(product_b)
    assert "include::infra/product-a/preamble.adoc[]" in doc_a
    assert "include::infra/product-a/suffix.adoc[]" in doc_a
    assert "include::infra/product-b/preamble.adoc[]" in doc_b
    assert "include::infra/product-b/suffix.adoc[]" in doc_b
    assert "include::infra/product-a/preamble.adoc[]" not in doc_b
