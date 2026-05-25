import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TypedValue:
    type: str       # "static" | "dynamic"
    unit: str
    value: float = 0.0
    formula: str = ""

    def render(self) -> str:
        if self.type == "static":
            v = int(self.value) if self.value == int(self.value) else self.value
            return f"{v} {self.unit}"
        return f"{self.formula} {self.unit}"


def _parse_typed_value(raw: dict, field_name: str, context: str) -> TypedValue:
    t = raw.get("type")
    if t not in ("static", "dynamic"):
        raise ValueError(f"{context}: {field_name}.type must be 'static' or 'dynamic', got {t!r}")
    unit = raw.get("unit", "")
    if not unit:
        raise ValueError(f"{context}: {field_name}.unit is required")
    if t == "static":
        value = raw.get("value")
        if value is None or float(value) <= 0:
            raise ValueError(f"{context}: {field_name}.value must be a positive number for static type")
        return TypedValue(type="static", unit=unit, value=float(value))
    formula = raw.get("formula", "")
    if not formula:
        raise ValueError(f"{context}: {field_name}.formula is required for dynamic type")
    return TypedValue(type="dynamic", unit=unit, formula=formula)


@dataclass
class Partition:
    size: TypedValue
    performance: str
    comment: str = ""


@dataclass
class Server:
    system: str
    cpu: TypedValue
    cpu_clocking: str
    memory: TypedValue
    disk: list[Partition]
    count: int = 1
    network: list[str] = field(default_factory=list)
    software: list[str] = field(default_factory=list)
    comment: str = ""


@dataclass
class FlavourImage:
    type: str
    value: str


@dataclass
class Flavour:
    shortname: str
    display_name: str
    servers: list[Server]
    image: FlavourImage | None = None
    has_preamble: bool = False
    has_suffix: bool = False


@dataclass
class Size:
    shortname: str
    display_name: str
    flavours: list[Flavour]
    prefix_text: str = ""
    suffix_text: str = ""


@dataclass
class Product:
    shortname: str
    display_name: str
    sizes: list[Size]
    preamble_path: str = ""
    suffix_path: str = ""


def check_theme(repo_root: Path) -> None:
    if not (repo_root / "theme.yml").exists():
        print("ERROR: theme.yml not found at repo root", file=sys.stderr)
        raise SystemExit(1)


def check_products_json(repo_root: Path) -> None:
    products_json = repo_root / "infra" / "products.json"
    if not products_json.exists():
        print("ERROR: infra/products.json not found", file=sys.stderr)
        raise SystemExit(1)
    try:
        json.loads(products_json.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: infra/products.json is not valid JSON: {e}", file=sys.stderr)
        raise SystemExit(1)


def load_product_registry(repo_root: Path) -> list[dict]:
    products_json = repo_root / "infra" / "products.json"
    entries = json.loads(products_json.read_text())
    errors = []
    for entry in entries:
        product_dir = repo_root / "infra" / entry["shortname"]
        if not product_dir.is_dir():
            errors.append(f"Product folder missing: infra/{entry['shortname']}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
    return entries


def load_size_registry(product_dir: Path) -> list[dict]:
    sizes_json = product_dir / "sizes.json"
    entries = json.loads(sizes_json.read_text())
    return entries


def load_flavour_registry(size_dir: Path) -> list[dict]:
    flavours_json = size_dir / "flavours.json"
    entries = json.loads(flavours_json.read_text())
    return entries


def load_product_meta(product_dir: Path) -> dict:
    meta = json.loads((product_dir / "meta.json").read_text())
    for field_name in ("preamble", "suffix"):
        path = product_dir / meta[field_name]
        if not path.exists():
            raise FileNotFoundError(f"{field_name} file not found: {path}")
    return meta


def load_size_meta(size_dir: Path) -> dict:
    meta = json.loads((size_dir / "meta.json").read_text())
    return {
        "prefix_text": meta.get("prefix_text") or "",
        "suffix_text": meta.get("suffix_text") or "",
    }


def load_flavour_meta(flavour_dir: Path) -> dict:
    meta = json.loads((flavour_dir / "meta.json").read_text())
    image = meta.get("image")
    if image:
        if image.get("type") not in ("file", "mermaid"):
            raise ValueError(f"Invalid image type '{image.get('type')}' in {flavour_dir}/meta.json")
        img_path = flavour_dir / image["value"]
        if not img_path.exists():
            raise FileNotFoundError(f"Image file not found: {img_path}")
    return meta


def load_servers(flavour_dir: Path) -> list[Server]:
    servers_json = flavour_dir / "servers.json"
    raw = json.loads(servers_json.read_text())
    servers = []
    for entry in raw:
        system = entry.get("system", "")
        context = f"server '{system}' in {flavour_dir}"

        disk_raw = entry.get("disk", [])
        if not disk_raw:
            raise ValueError(f"Server '{system}' in {flavour_dir} has no disk partitions")

        partitions = []
        for p in disk_raw:
            size_tv = _parse_typed_value(p["size"], "size", f"{context} partition")
            partitions.append(Partition(
                size=size_tv,
                performance=p["performance"],
                comment=p.get("comment", ""),
            ))

        cpu_tv = _parse_typed_value(entry["cpu"], "cpu", context)
        memory_tv = _parse_typed_value(entry["memory"], "memory", context)

        servers.append(Server(
            system=system,
            cpu=cpu_tv,
            cpu_clocking=entry["cpu_clocking"],
            memory=memory_tv,
            disk=partitions,
            count=entry.get("count", 1),
            network=entry.get("network", []),
            software=entry.get("software", []),
            comment=entry.get("comment", ""),
        ))
    return servers


def load_product(repo_root: Path, shortname: str, display_name: str) -> Product | None:
    errors = []
    product_dir = repo_root / "infra" / shortname

    if not product_dir.is_dir():
        errors.append(f"[{shortname}]: product folder missing")
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return None

    try:
        meta = load_product_meta(product_dir)
        preamble_path = f"infra/{shortname}/{meta['preamble']}"
        suffix_path = f"infra/{shortname}/{meta['suffix']}"
    except Exception as e:
        print(f"ERROR [{shortname}]: {e}", file=sys.stderr)
        return None

    try:
        size_entries = load_size_registry(product_dir)
    except Exception as e:
        print(f"ERROR [{shortname}]: failed to load sizes.json: {e}", file=sys.stderr)
        return None

    if not size_entries:
        print(f"ERROR [{shortname}]: no sizes defined", file=sys.stderr)
        return None

    sizes = []
    for size_entry in size_entries:
        size_dir = product_dir / size_entry["shortname"]
        if not size_dir.is_dir():
            errors.append(f"[{shortname}]: size folder missing: {size_entry['shortname']}")
            continue
        try:
            size_meta = load_size_meta(size_dir)
            flavour_entries = load_flavour_registry(size_dir)
        except Exception as e:
            errors.append(f"[{shortname}]: {e}")
            continue

        if not flavour_entries:
            errors.append(f"[{shortname}]: no flavours defined for size {size_entry['shortname']}")
            continue

        flavours = []
        for fl_entry in flavour_entries:
            flavour_dir = size_dir / fl_entry["shortname"]
            if not flavour_dir.is_dir():
                errors.append(f"[{shortname}]: flavour folder missing: {fl_entry['shortname']}")
                continue
            try:
                fl_meta = load_flavour_meta(flavour_dir)
                servers = load_servers(flavour_dir)
            except Exception as e:
                errors.append(f"[{shortname}]: {e}")
                continue

            if not servers:
                errors.append(f"[{shortname}]: no servers for flavour {fl_entry['shortname']}")
                continue

            image = None
            raw_image = fl_meta.get("image")
            if raw_image:
                image = FlavourImage(type=raw_image["type"], value=raw_image["value"])

            has_preamble = (flavour_dir / "preamble.adoc").exists()
            has_suffix = (flavour_dir / "suffix.adoc").exists()

            flavours.append(Flavour(
                shortname=fl_entry["shortname"],
                display_name=fl_entry["display_name"],
                servers=servers,
                image=image,
                has_preamble=has_preamble,
                has_suffix=has_suffix,
            ))

        if not flavours:
            errors.append(f"[{shortname}]: no valid flavours for size {size_entry['shortname']}")
            continue

        sizes.append(Size(
            shortname=size_entry["shortname"],
            display_name=size_entry["display_name"],
            flavours=flavours,
            prefix_text=size_meta["prefix_text"],
            suffix_text=size_meta["suffix_text"],
        ))

    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        return None

    if not sizes:
        print(f"ERROR [{shortname}]: no valid sizes", file=sys.stderr)
        return None

    return Product(
        shortname=shortname,
        display_name=display_name,
        sizes=sizes,
        preamble_path=preamble_path,
        suffix_path=suffix_path,
    )
