import json

import pytest

from app import crud


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Keep every test independent and leave the repository database untouched."""
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"categorias": [], "productos": []}), encoding="utf-8")
    monkeypatch.setattr(crud, "DB_FILE", str(db_file))
    return db_file
