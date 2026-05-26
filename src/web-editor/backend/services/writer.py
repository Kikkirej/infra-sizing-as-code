from __future__ import annotations
import json
import os
import shutil
import tempfile
from pathlib import Path

from models.state import ChangeState, EditorState


def atomic_write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_all(state: EditorState, repo_root: Path) -> None:
    infra = repo_root / "infra"
    dirs_to_delete: list[Path] = []

    products_list = []
    for product in state.products.values():
        if product.change == ChangeState.DELETED:
            dirs_to_delete.append(infra / product.shortname)
            continue
        products_list.append({"shortname": product.shortname, "display_name": product.display_name})
        product_dir = infra / product.shortname
        product_dir.mkdir(parents=True, exist_ok=True)

        if product.change in (ChangeState.ADDED, ChangeState.MODIFIED):
            atomic_write_json(product_dir / "meta.json", {"prefix": "prefix.adoc", "suffix": "suffix.adoc"})

        if product.prefix_change != ChangeState.CLEAN:
            atomic_write_text(product_dir / "prefix.adoc", product.prefix_content)
        if product.suffix_change != ChangeState.CLEAN:
            atomic_write_text(product_dir / "suffix.adoc", product.suffix_content)

        sizes_list = []
        for size in product.sizes.values():
            if size.change == ChangeState.DELETED:
                dirs_to_delete.append(product_dir / size.shortname)
                continue
            sizes_list.append({"shortname": size.shortname, "display_name": size.display_name})
            size_dir = product_dir / size.shortname
            size_dir.mkdir(parents=True, exist_ok=True)

            if size.prefix_change != ChangeState.CLEAN:
                atomic_write_text(size_dir / "prefix.adoc", size.prefix_content)
            if size.suffix_change != ChangeState.CLEAN:
                atomic_write_text(size_dir / "suffix.adoc", size.suffix_content)

            flavours_list = []
            for flavour in size.flavours.values():
                if flavour.change == ChangeState.DELETED:
                    dirs_to_delete.append(size_dir / flavour.shortname)
                    continue
                flavours_list.append({"shortname": flavour.shortname, "display_name": flavour.display_name})
                flavour_dir = size_dir / flavour.shortname
                flavour_dir.mkdir(parents=True, exist_ok=True)

                if flavour.change in (ChangeState.ADDED, ChangeState.MODIFIED):
                    meta: dict = {}
                    if flavour.image_type:
                        meta["image"] = {"type": flavour.image_type, "value": flavour.image_value}
                    atomic_write_json(flavour_dir / "meta.json", meta)

                    servers_data = []
                    for srv in flavour.servers:
                        if srv.change == ChangeState.DELETED:
                            continue
                        cpu: dict = {"type": srv.cpu.type, "unit": srv.cpu.unit}
                        if srv.cpu.type == "static":
                            cpu["value"] = srv.cpu.value
                        else:
                            cpu["formula"] = srv.cpu.formula

                        mem: dict = {"type": srv.memory.type, "unit": srv.memory.unit}
                        if srv.memory.type == "static":
                            mem["value"] = srv.memory.value
                        else:
                            mem["formula"] = srv.memory.formula

                        disk = []
                        for p in srv.disk:
                            sz: dict = {"type": p.size.type, "unit": p.size.unit}
                            if p.size.type == "static":
                                sz["value"] = p.size.value
                            else:
                                sz["formula"] = p.size.formula
                            disk.append({"size": sz, "performance": p.performance, "comment": p.comment})

                        servers_data.append({
                            "system": srv.system,
                            "count": srv.count,
                            "cpu": cpu,
                            "cpu_clocking": srv.cpu_clocking,
                            "memory": mem,
                            "disk": disk,
                            "network": srv.network,
                            "software": srv.software,
                            "comment": srv.comment,
                        })
                    atomic_write_json(flavour_dir / "servers.json", servers_data)

                if flavour.prefix_change != ChangeState.CLEAN:
                    atomic_write_text(flavour_dir / "prefix.adoc", flavour.prefix_content)
                if flavour.suffix_change != ChangeState.CLEAN:
                    atomic_write_text(flavour_dir / "suffix.adoc", flavour.suffix_content)

            atomic_write_json(size_dir / "flavours.json", flavours_list)

        atomic_write_json(product_dir / "sizes.json", sizes_list)

    atomic_write_json(infra / "products.json", products_list)

    if state.units.change != ChangeState.CLEAN:
        atomic_write_json(infra / "units.json", state.units.units)
    if state.global_prefix_change != ChangeState.CLEAN:
        atomic_write_text(infra / "prefix.adoc", state.global_prefix_content)
    if state.global_suffix_change != ChangeState.CLEAN:
        atomic_write_text(infra / "suffix.adoc", state.global_suffix_content)
    if state.theme_change != ChangeState.CLEAN:
        atomic_write_text(repo_root / "theme.yml", state.theme_content)

    for d in sorted(dirs_to_delete, key=lambda p: len(p.parts), reverse=True):
        if d.exists():
            shutil.rmtree(d)
