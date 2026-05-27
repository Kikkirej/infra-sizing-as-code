from __future__ import annotations
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import state_store
from services.writer import write_all
from models.state import ChangeState
from models.versioning import VersionNoteIn

router = APIRouter()
REPO_ROOT = Path(os.environ.get("REPO_ROOT", "."))


def _get_repo():
    try:
        from git import Repo, InvalidGitRepositoryError
        return Repo(REPO_ROOT)
    except Exception as exc:
        raise HTTPException(500, f"Git repository error: {exc}")


@router.get("/git/status")
def git_status():
    repo = _get_repo()
    has_remote = len(repo.remotes) > 0
    try:
        branch = repo.active_branch.name
        is_detached = False
    except TypeError:
        branch = repo.head.commit.hexsha[:8]
        is_detached = True
    return {
        "branch": branch,
        "is_detached": is_detached,
        "has_remote": has_remote,
        "remote_name": repo.remotes[0].name if has_remote else None,
    }


@router.get("/git/changes")
def git_changes():
    state = state_store.get_state()
    changes: list[str] = []

    for p in state.products.values():
        if p.change != ChangeState.CLEAN and p.change != ChangeState.ERROR:
            changes.append(p.shortname)
        if p.prefix_change != ChangeState.CLEAN:
            changes.append(f"infra/{p.shortname}/prefix.adoc")
        if p.suffix_change != ChangeState.CLEAN:
            changes.append(f"infra/{p.shortname}/suffix.adoc")
        for s in p.sizes.values():
            if s.change != ChangeState.CLEAN:
                changes.append(f"{p.shortname} / {s.shortname}")
            if s.prefix_change != ChangeState.CLEAN:
                changes.append(f"infra/{p.shortname}/{s.shortname}/prefix.adoc")
            if s.suffix_change != ChangeState.CLEAN:
                changes.append(f"infra/{p.shortname}/{s.shortname}/suffix.adoc")
            for f in s.flavours.values():
                if f.change != ChangeState.CLEAN:
                    changes.append(f"{p.shortname} / {s.shortname} / {f.shortname}")
                if f.prefix_change != ChangeState.CLEAN:
                    changes.append(f"infra/{p.shortname}/{s.shortname}/{f.shortname}/prefix.adoc")
                if f.suffix_change != ChangeState.CLEAN:
                    changes.append(f"infra/{p.shortname}/{s.shortname}/{f.shortname}/suffix.adoc")
                for i, srv in enumerate(f.servers):
                    if srv.change != ChangeState.CLEAN:
                        changes.append(f"{p.shortname} / {s.shortname} / {f.shortname} / server[{i}]")

    if state.units.change != ChangeState.CLEAN:
        changes.append("infra/units.json")
    if state.global_prefix_change != ChangeState.CLEAN:
        changes.append("infra/prefix.adoc")
    if state.global_suffix_change != ChangeState.CLEAN:
        changes.append("infra/suffix.adoc")
    if state.theme_change != ChangeState.CLEAN:
        changes.append("theme.yml")

    return {"changes": list(dict.fromkeys(changes)), "count": len(set(changes))}


class CommitBody(BaseModel):
    message: str
    push: bool = True
    version_notes: list[VersionNoteIn] = []


def _validate_commit(state) -> list[str]:
    errors = []
    for p in state.products.values():
        if p.change == ChangeState.ERROR:
            continue
        for s in p.sizes.values():
            for f in s.flavours.values():
                for srv in f.servers:
                    if srv.change == ChangeState.DELETED:
                        continue
                    if not srv.system.strip():
                        errors.append(f"{p.shortname}/{s.shortname}/{f.shortname}: server has empty system name")
                    if not srv.disk:
                        errors.append(f"{p.shortname}/{s.shortname}/{f.shortname}: server '{srv.system}' has no disk partitions")
                    for tv_name in ("cpu", "memory"):
                        if getattr(srv, tv_name).invalid:
                            errors.append(f"{p.shortname}/{s.shortname}/{f.shortname}: server '{srv.system}' has invalid unit for {tv_name}")
                    for j, part in enumerate(srv.disk):
                        if part.size.invalid:
                            errors.append(f"{p.shortname}/{s.shortname}/{f.shortname}: server '{srv.system}' disk[{j}] has invalid unit")
    return errors


@router.post("/git/commit")
def commit(body: CommitBody):
    state = state_store.get_state()
    repo = _get_repo()

    if repo.head.is_detached:
        raise HTTPException(409, "Repository is in detached HEAD state. Run 'git checkout <branch>' before committing.")

    errors = _validate_commit(state)
    if errors:
        raise HTTPException(422, "Commit blocked: " + "; ".join(errors))

    # Append version notes to wip.json files before writing
    if body.version_notes:
        import json as _json
        from pathlib import Path as _Path
        for i, note in enumerate(body.version_notes):
            wip_path = REPO_ROOT / "infra" / note.product_shortname / "versioning" / "wip.json"
            if wip_path.exists():
                try:
                    raw = _json.loads(wip_path.read_text())
                    raw.setdefault("entries", []).append({
                        "author": note.author,
                        "date": note.date,
                        "notes": note.notes,
                    })
                    wip_path.write_text(_json.dumps(raw, indent=2, ensure_ascii=False))
                except Exception as exc:
                    raise HTTPException(422, f"version_notes[{i}]: failed to update wip.json: {exc}")
            else:
                # Create a minimal wip.json if the product exists
                product_dir = REPO_ROOT / "infra" / note.product_shortname
                if product_dir.is_dir():
                    wip_path.parent.mkdir(parents=True, exist_ok=True)
                    raw = {"version_name": "", "entries": [{
                        "author": note.author,
                        "date": note.date,
                        "notes": note.notes,
                    }]}
                    wip_path.write_text(_json.dumps(raw, indent=2, ensure_ascii=False))

    write_all(state, REPO_ROOT)

    repo.git.add(A=True)
    commit_obj = repo.index.commit(body.message)

    pushed = False
    push_failed = False
    error_detail = None

    if body.push and repo.remotes:
        try:
            origin = repo.remote("origin")
            origin.push()
            pushed = True
        except Exception as exc:
            push_failed = True
            error_detail = str(exc)

    if push_failed:
        raise HTTPException(500, detail={
            "message": f"Commit created ({commit_obj.hexsha[:7]}) but push failed: {error_detail}",
            "commit_sha": commit_obj.hexsha[:7],
            "push_failed": True,
        })

    # Reset all change states to CLEAN after successful commit
    for p in state.products.values():
        p.change = ChangeState.CLEAN
        p.prefix_change = ChangeState.CLEAN
        p.suffix_change = ChangeState.CLEAN
        for s in p.sizes.values():
            s.change = ChangeState.CLEAN
            s.prefix_change = ChangeState.CLEAN
            s.suffix_change = ChangeState.CLEAN
            for f in s.flavours.values():
                f.change = ChangeState.CLEAN
                f.prefix_change = ChangeState.CLEAN
                f.suffix_change = ChangeState.CLEAN
                f.servers = [sv for sv in f.servers if sv.change != ChangeState.DELETED]
                for sv in f.servers:
                    sv.change = ChangeState.CLEAN
    state.products = {sn: p for sn, p in state.products.items() if p.change != ChangeState.DELETED}
    state.units.change = ChangeState.CLEAN
    state.global_prefix_change = ChangeState.CLEAN
    state.global_suffix_change = ChangeState.CLEAN
    state.theme_change = ChangeState.CLEAN

    return {"commit_sha": commit_obj.hexsha[:7], "pushed": pushed}


@router.post("/git/push")
def retry_push():
    repo = _get_repo()
    if not repo.remotes:
        raise HTTPException(400, "No remote configured")
    try:
        repo.remote("origin").push()
        return {"pushed": True}
    except Exception as exc:
        raise HTTPException(500, detail={"message": str(exc), "push_failed": True})
