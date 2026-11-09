from fastapi.testclient import TestClient
from app.main import app
from app import crud
import json

client = TestClient(app)

# Restaura el estado de la DB al estado original después de cada prueba
def setup_function():
    data_inicial = {"categorias": [{"id": 1, "nombre": "Electrónica"}],
                    "productos": [{"id": 101, "nombre": "Laptop", "categoria_id": 1}]}
    crud._save_db(data_inicial)
    print("\n--- DB RESTAURADA (Estado Inicial) ---")
    print(json.dumps(data_inicial, indent=4))
    print("--------------------------------------")

def test_integration_create_cat_and_product():
    """
    Verifica que las rutas POST de /categorias y /productos funcionen juntas
    (API + CRUD + JSON I/O real).
    """
    # 1. Crear una nueva Categoría (Endpoint 1, toque el disco real)
    response_cat = client.post("/categorias", params={"nombre": "Jardinería Integracion"})
    assert response_cat.status_code == 200
    categoria_creada = response_cat.json()
    categoria_id = categoria_creada["id"]
    # 2. Crear un Producto usando esa Categoria_ID (Endpoint 2)
    response_prod = client.post("/productos", 
                                params={"nombre": "Tijeras", "categoria_id": categoria_id})
    assert response_prod.status_code == 200
    # 3. Verificación final de que el producto se creó correctamente
    producto_creado = response_prod.json()
    # 4. Verificar que ambas existen en la DB final (usando la ruta GET)
    final_cats = client.get("/categorias").json()
    assert any(c['id'] == categoria_id for c in final_cats)
    # 🚨 NUEVO: Mostrar el estado final de la DB después de la prueba
    final_db_data = crud._load_db() 
    print("\n--- DB FINAL (Tras Crear Cat y Prod) ---")
    print(json.dumps(final_db_data, indent=4))
    print("-----------------------------------------")
    # Assertions finales
    assert producto_creado["nombre"] == "Tijeras"
    assert producto_creado["categoria_id"] == categoria_id