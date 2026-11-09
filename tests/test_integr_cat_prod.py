from fastapi.testclient import TestClient
from app.main import app
from app import crud
import json

client = TestClient(app)

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


def test_integration_categoria_se_guarda_y_se_recupera(isolated_db):
    respuesta = client.post("/categorias", params={"nombre": "Libros"})

    assert respuesta.status_code == 200
    categoria = respuesta.json()
    assert categoria == {"id": 1, "nombre": "Libros"}
    assert json.loads(isolated_db.read_text(encoding="utf-8"))["categorias"] == [categoria]
    assert client.get("/categorias").json() == [categoria]


def test_integration_productos_incrementan_id_y_persisten(isolated_db):
    categoria = client.post("/categorias", params={"nombre": "Papelería"}).json()
    primero = client.post("/productos", params={"nombre": "Lápiz", "categoria_id": categoria["id"]})
    segundo = client.post("/productos", params={"nombre": "Cuaderno", "categoria_id": categoria["id"]})

    assert primero.status_code == segundo.status_code == 200
    assert [primero.json()["id"], segundo.json()["id"]] == [101, 102]
    productos = json.loads(isolated_db.read_text(encoding="utf-8"))["productos"]
    assert productos == [primero.json(), segundo.json()]
    assert client.get("/productos").json() == productos
