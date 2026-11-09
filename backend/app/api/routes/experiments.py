"""Owner-scoped imports of aggregate Kaggle results; no execution of uploaded code."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import AppError
from app.models.user import User
from app.schemas.experiments import ExperimentImport

router = APIRouter(prefix="/experiments", tags=["experiments"])
MAX_IMPORT_BYTES = 1_000_000


def _directory(user: User) -> Path:
    return get_settings().resolved_storage_dir / "experiments" / str(user.id)


def _items(user: User) -> list[dict]:
    directory = _directory(user)
    if not directory.exists(): return []
    return sorted((json.loads(p.read_text(encoding="utf-8")) for p in directory.glob("*.json")), key=lambda r: r["created_at"], reverse=True)


@router.get("")
def list_experiments(current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    return {"items": _items(current_user), "notice": "Imported measurements are user-supplied and have not been independently verified."}


@router.post("/import", status_code=201)
async def import_experiments(request: Request, current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_IMPORT_BYTES:
            raise AppError(status_code=413, detail="Results JSON must be smaller than 1 MB. Import aggregate scores, not predictions or model weights.")
    try:
        payload = ExperimentImport.model_validate_json(body)
    except ValidationError:
        raise AppError(status_code=422, detail="Invalid experiment export. Use the schema-version 1 aggregate JSON from the handwriting notebook.") from None
    for run in payload.runs:
        if run.samples != run.metrics.samples or run.metrics.digit_samples > run.samples:
            raise AppError(status_code=422, detail="Sample counts in the result and metrics must agree.")
    directory = _directory(current_user); directory.mkdir(parents=True, exist_ok=True)
    if len(list(directory.glob("*.json"))) + len(payload.runs) > 500:
        raise AppError(status_code=409, detail="This workspace has reached its 500-result limit.")
    imported = []
    for run in payload.runs:
        value = run.model_dump(mode="json")
        canonical = json.dumps(value, sort_keys=True, ensure_ascii=False)
        identifier = hashlib.sha256(canonical.encode()).hexdigest()
        value.update(id=identifier, verification="user_supplied", status="imported")
        destination = directory / f"{identifier}.json"
        if not destination.exists():
            # A temporary sibling plus replace prevents readers seeing a partial result.
            handle, name = tempfile.mkstemp(prefix="result-", suffix=".tmp", dir=directory)
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as f:
                    json.dump(value, f, ensure_ascii=False)
                os.replace(name, destination)
            finally:
                Path(name).unlink(missing_ok=True)
        imported.append(value)
    return {"items": imported, "notice": "Imported measurements are user-supplied and have not been independently verified."}
