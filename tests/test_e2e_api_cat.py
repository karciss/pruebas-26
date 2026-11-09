from fastapi.testclient import TestClient
from app.main import app
import httpx
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import json
import pytest

client = TestClient(app)


@pytest.fixture
def live_server(tmp_path):
    """Run the actual ASGI server against a private JSON database."""
    db_file = tmp_path / "server-db.json"
    db_file.write_text(json.dumps({"categorias": [], "productos": []}), encoding="utf-8")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = os.environ.copy()
    env["APP_DB_FILE"] = str(db_file)
    log_file = tmp_path / "uvicorn.log"
    with log_file.open("w+", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        base_url = f"http://127.0.0.1:{port}"
        try:
            ready = False
            for _ in range(100):
                if server.poll() is not None:
                    break
                try:
                    if httpx.get(f"{base_url}/categorias", timeout=0.25).status_code == 200:
                        ready = True
                        break
                except httpx.RequestError:
                    pass
                time.sleep(0.1)
            if server.poll() is not None:
                log.flush()
                pytest.fail(f"Uvicorn terminó antes de iniciar:\n{log_file.read_text(encoding='utf-8')}")
            if not ready:
                log.flush()
                pytest.fail(f"Uvicorn no respondió en {base_url}:\n{log_file.read_text(encoding='utf-8')}")
            yield base_url
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


def test_e2e_full_category_lifecycle():
    """
    Simula un flujo completo del usuario (End-to-End):
    1. Revisa si existe.
    2. Crea el recurso.
    3. Revisa la lista para confirmar la creación.
    """
    cat_name = f"E2E Cat {int(time.time())}" # Nombre único
    # 1. Paso de usuario: Intenta obtener todas las categorías
    response_get_initial = client.get("/categorias")
    initial_list = response_get_initial.json()
    initial_count = len(initial_list)
    print("\n--- E2E: LISTA INICIAL DE CATEGORÍAS (Antes de crear) ---")
    print(json.dumps(initial_list, indent=4))
    print(f"Número inicial de categorías: {initial_count}")
    print("----------------------------------------------------------")
    # 2. Paso de usuario: Crea una nueva categoría
    response_post = client.post("/categorias", params={"nombre": cat_name})
    assert response_post.status_code == 200
    categoria_creada = response_post.json()
    print(f"\n--- E2E: CATEGORÍA CREADA ---")
    print(json.dumps(categoria_creada, indent=4))
    print("------------------------------")
    # 3. Paso de usuario: Verifica la lista final
    response_get_final = client.get("/categorias")
    final_list = response_get_final.json()
    print("\n--- E2E: LISTA FINAL DE CATEGORÍAS (Tras crear) ---")
    print(json.dumps(final_list, indent=4))
    print("--------------------------------------------------")
    # E2E Assertions:
    assert len(final_list) == initial_count + 1
    assert any(c['nombre'] == cat_name for c in final_list)


def test_e2e_crear_categoria_y_producto_por_http(live_server):
    with httpx.Client(base_url=live_server) as api:
        assert api.get("/categorias").json() == []
        categoria = api.post("/categorias", params={"nombre": "Deportes"})
        assert categoria.status_code == 200
        producto = api.post("/productos", params={
            "nombre": "Balón", "categoria_id": categoria.json()["id"]})
        assert producto.status_code == 200
        assert producto.json()["categoria_id"] == categoria.json()["id"]
        assert api.get("/productos").json() == [producto.json()]


def test_e2e_producto_invalido_no_contamina_flujo_http(live_server):
    with httpx.Client(base_url=live_server) as api:
        invalido = api.post("/productos", params={"nombre": "Fantasma", "categoria_id": 999})
        assert invalido.status_code == 404
        assert invalido.json()["detail"] == "Categoría no encontrada"
        assert api.get("/productos").json() == []

        categoria = api.post("/categorias", params={"nombre": "Hogar"}).json()
        valido = api.post("/productos", params={
            "nombre": "Lámpara", "categoria_id": categoria["id"]})
        assert valido.status_code == 200
        assert valido.json()["id"] == 101
        assert api.get("/productos").json() == [valido.json()]
