from fastapi.testclient import TestClient
from app.main import app
import time
import json

client = TestClient(app)
# NO USAMOS setup_function aquí, ya que queremos simular un entorno persistente
# y que las pruebas anteriores (Integración) hayan modificado la DB real (db.json)
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