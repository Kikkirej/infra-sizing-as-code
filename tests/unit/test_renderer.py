from src.loader import Flavour, FlavourImage, Partition, Product, Server, Size, TypedValue
from src.renderer import (
    render_document_header,
    render_flavour_section,
    render_product_document,
    render_server_table,
    render_size_section,
)


def _tv(value, unit):
    return TypedValue(type="static", unit=unit, value=float(value))


def _tv_dyn(formula, unit):
    return TypedValue(type="dynamic", unit=unit, formula=formula)


def _make_partition(size_value, unit="GB", performance="SSD", comment=""):
    return Partition(size=_tv(size_value, unit), performance=performance, comment=comment)


def _make_server(disk=None, network=None, software=None, comment="", count=1,
                 cpu_value=4, cpu_unit="vCPU", cpu_clocking="3.0 GHz",
                 memory_value=16, memory_unit="GB"):
    return Server(
        system="Web",
        cpu=_tv(cpu_value, cpu_unit),
        cpu_clocking=cpu_clocking,
        memory=_tv(memory_value, memory_unit),
        disk=disk or [_make_partition(100)],
        network=network or [],
        software=software or [],
        comment=comment,
        count=count,
    )


def _make_flavour(servers=None, **kwargs):
    return Flavour(
        shortname="flavour-f",
        display_name="F",
        servers=servers or [_make_server()],
        **kwargs,
    )


# ── render_server_table: always 5 columns ────────────────────────────────────

def test_render_server_table_always_5_columns():
    flavour = _make_flavour(servers=[_make_server(count=1)])
    table = render_server_table(flavour)
    assert '[cols="15,14,13,43,33"' in table


def test_render_server_table_5_columns_with_count_greater_than_one():
    flavour = _make_flavour(servers=[_make_server(count=3)])
    table = render_server_table(flavour)
    assert '[cols="15,14,13,43,33"' in table


def test_render_server_table_header_has_no_count_or_network_or_software_columns():
    flavour = _make_flavour(servers=[_make_server(count=2)])
    table = render_server_table(flavour)
    assert "| System | CPU | Memory | Disk | Comment" in table
    assert "| Count" not in table
    assert "| Network" not in table
    assert "| Software" not in table


# ── render_server_table: System cell count annotation ────────────────────────

def test_render_server_table_count_one_no_annotation():
    flavour = _make_flavour(servers=[_make_server(count=1)])
    table = render_server_table(flavour)
    assert "| Web\n" in table
    assert "Web [1]" not in table


def test_render_server_table_count_greater_than_one_shows_bracket_annotation():
    flavour = _make_flavour(servers=[_make_server(count=3)])
    table = render_server_table(flavour)
    assert "| Web [3]" in table


def test_render_server_table_count_two_shows_bracket_annotation():
    flavour = _make_flavour(servers=[_make_server(count=2)])
    table = render_server_table(flavour)
    assert "| Web [2]" in table


def test_render_server_table_mixed_counts():
    flavour = _make_flavour(servers=[_make_server(count=1), _make_server(count=4)])
    table = render_server_table(flavour)
    assert "| Web\n" in table
    assert "| Web [4]" in table


# ── render_server_table: CPU column ──────────────────────────────────────────

def test_render_server_table_cpu_column_format_static():
    flavour = _make_flavour(servers=[_make_server(cpu_value=8, cpu_unit="vCPU", cpu_clocking="3.2 GHz")])
    table = render_server_table(flavour)
    assert "8 vCPU (3.2 GHz)" in table


def test_render_server_table_cpu_column_no_separate_clocking_column():
    flavour = _make_flavour(servers=[_make_server()])
    table = render_server_table(flavour)
    assert "CPU Clocking" not in table


def test_render_server_table_dynamic_cpu():
    flavour = _make_flavour(servers=[Server(
        system="Node",
        cpu=_tv_dyn("n × 4", "vCPU"),
        cpu_clocking="3.0 GHz",
        memory=_tv(16, "GB"),
        disk=[_make_partition(100)],
        count=1,
    )])
    table = render_server_table(flavour)
    assert "n × 4 vCPU (3.0 GHz)" in table


# ── render_server_table: memory column ───────────────────────────────────────

def test_render_server_table_memory_renders_typed_value():
    flavour = _make_flavour(servers=[_make_server(memory_value=32, memory_unit="GB")])
    table = render_server_table(flavour)
    assert "| 32 GB" in table


# ── render_server_table: Disk nested partition table ─────────────────────────

def test_render_server_table_disk_uses_nested_table():
    flavour = _make_flavour(servers=[_make_server(
        disk=[_make_partition(100, comment="OS"), _make_partition(500, performance="HDD")]
    )])
    table = render_server_table(flavour)
    assert "!===" in table
    assert "! Size ! Perform- +" in table
    assert "ance ! Comment/ +\nUsage" in table
    assert "! 100 GB ! SSD ! OS" in table
    assert "! 500 GB ! HDD !" in table


def test_render_server_table_disk_blank_comment_cell():
    flavour = _make_flavour(servers=[_make_server(
        disk=[_make_partition(200, comment="")]
    )])
    table = render_server_table(flavour)
    assert "! 200 GB ! SSD ! " in table


def test_render_server_table_disk_dynamic_partition():
    flavour = _make_flavour(servers=[Server(
        system="Node",
        cpu=_tv(4, "vCPU"),
        cpu_clocking="3.0 GHz",
        memory=_tv(16, "GB"),
        disk=[Partition(size=_tv_dyn("n × 500", "GB"), performance="NVMe", comment="Data")],
        count=1,
    )])
    table = render_server_table(flavour)
    assert "! n × 500 GB ! NVMe ! Data" in table


# ── render_server_table: Comment cell (software + network + comment) ─────────

def test_render_server_table_software_items_appear_in_comment_cell():
    flavour = _make_flavour(servers=[_make_server(software=["OpenJDK 17", "NGINX 1.25"])])
    table = render_server_table(flavour)
    assert "* OpenJDK 17" in table
    assert "* NGINX 1.25" in table


def test_render_server_table_network_items_appear_in_comment_cell():
    flavour = _make_flavour(servers=[_make_server(network=["2× 10GbE", "1× 1GbE"])])
    table = render_server_table(flavour)
    assert "* 2× 10GbE" in table
    assert "* 1× 1GbE" in table


def test_render_server_table_software_before_network_in_comment():
    flavour = _make_flavour(servers=[_make_server(
        software=["Java 17"], network=["2× 10GbE"]
    )])
    table = render_server_table(flavour)
    java_pos = table.index("* Java 17")
    net_pos = table.index("* 2× 10GbE")
    assert java_pos < net_pos


def test_render_server_table_original_comment_in_comment_cell():
    flavour = _make_flavour(servers=[_make_server(comment="Hot standby")])
    table = render_server_table(flavour)
    assert "Hot standby" in table


def test_render_server_table_all_three_combined_in_comment_cell():
    flavour = _make_flavour(servers=[_make_server(
        software=["Redis 7"], network=["2× 10GbE"], comment="Active/passive pair"
    )])
    table = render_server_table(flavour)
    assert "* Redis 7" in table
    assert "* 2× 10GbE" in table
    assert "Active/passive pair" in table


def test_render_server_table_empty_network_software_comment_blank_cell():
    flavour = _make_flavour(servers=[_make_server(network=[], software=[], comment="")])
    table = render_server_table(flavour)
    assert "a| \n" in table or "a|\n" in table


def test_render_server_table_no_separate_network_column():
    flavour = _make_flavour(servers=[_make_server(network=["2× 10GbE"])])
    table = render_server_table(flavour)
    assert "| Network" not in table
    assert "| Software" not in table


# ── render_size_section ───────────────────────────────────────────────────────

def test_render_size_section_suppresses_heading_when_single():
    size = Size(shortname="size-s", display_name="Small", flavours=[_make_flavour()])
    section = render_size_section(size, "product-a", is_single_size=True)
    assert "== Small" not in section


def test_render_size_section_includes_heading_when_multiple():
    size = Size(shortname="size-s", display_name="Small", flavours=[_make_flavour()])
    section = render_size_section(size, "product-a", is_single_size=False)
    assert "== Small" in section


# ── render_flavour_section ────────────────────────────────────────────────────

def test_render_flavour_section_no_preamble_no_suffix():
    flavour = _make_flavour(has_preamble=False, has_suffix=False)
    section = render_flavour_section(flavour, "product-a", "size-s")
    assert "include::" not in section


def test_render_flavour_section_with_preamble():
    flavour = _make_flavour(has_preamble=True, has_suffix=False)
    section = render_flavour_section(flavour, "product-a", "size-s")
    assert "include::infra/product-a/size-s/flavour-f/preamble.adoc[]" in section


def test_render_flavour_section_with_suffix():
    flavour = _make_flavour(has_preamble=False, has_suffix=True)
    section = render_flavour_section(flavour, "product-a", "size-s")
    assert "include::infra/product-a/size-s/flavour-f/suffix.adoc[]" in section


# ── render_product_document ───────────────────────────────────────────────────

def test_render_product_document_section_order():
    product = Product(
        shortname="product-a",
        display_name="Product A",
        sizes=[Size(
            shortname="size-s",
            display_name="Small",
            flavours=[_make_flavour()],
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
    def _product(shortname, size_sn, flavour_sn):
        return Product(
            shortname=shortname,
            display_name=shortname,
            sizes=[Size(
                shortname=size_sn,
                display_name="S",
                flavours=[Flavour(
                    shortname=flavour_sn,
                    display_name="F",
                    servers=[_make_server()],
                )],
            )],
            preamble_path=f"infra/{shortname}/preamble.adoc",
            suffix_path=f"infra/{shortname}/suffix.adoc",
        )

    doc_a = render_product_document(_product("product-a", "size-s", "flavour-f"))
    doc_b = render_product_document(_product("product-b", "size-l", "flavour-g"))

    assert "include::infra/product-a/preamble.adoc[]" in doc_a
    assert "include::infra/product-a/suffix.adoc[]" in doc_a
    assert "include::infra/product-b/preamble.adoc[]" in doc_b
    assert "include::infra/product-b/suffix.adoc[]" in doc_b
    assert "include::infra/product-a/preamble.adoc[]" not in doc_b
