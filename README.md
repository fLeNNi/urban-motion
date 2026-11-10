
# 🚀 Urban Motion - Tienda de Ropa Urbana

Proyecto final del **Seminario de TIC** | Escuela Técnica - Buenos Aires

## Stack Tecnológico

- **Backend:** Python 3 + Django 4.x
- **API REST:** Django REST Framework (DRF)
- **Frontend:** HTML5 + Bootstrap 5 + Django Templates
- **Base de Datos:** SQLite3
- **Autenticación:** Django Auth + Token Auth (DRF)

---

## Requisitos cumplidos del TP

| # | Requisito | Estado |
|---|-----------|--------|
| 1 | Formulario Registro de usuario | ✅ `/registro/` |
| 2 | Página de usuarios registrados con CRUD | ✅ `/usuarios/` |
| 3 | Consulta a una API (mostrar productos) | ✅ `/api/productos-externos/` |
| 4 | Formulario Ingreso (Login) | ✅ `/login/` |
| 5 | Formulario de consultas | ✅ `/contacto/` |
| 6 | Página de la empresa (nosotros) | ✅ `/nosotros/` |
| 7 | Mostrar Token de usuarios | ✅ `/perfil/` |
| 8 | Mostrar Cookies de sesión | ✅ `/perfil/` |

---

## Instalación y Ejecución

### 1. Crear entorno virtual

```bash
py -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Cargar datos de prueba

```bash
python cargar_datos.py
```

### 5. Levantar servidor

```bash
python manage.py runserver
```

---

## Credenciales de acceso

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin123` | Superusuario |
| `juan`  | `juan1234` | Usuario normal |

---

## URLs principales

| URL | Descripción |
|-----|-------------|
| `http://127.0.0.1:8000/` | Inicio |
| `http://127.0.0.1:8000/catalogo/` | Catálogo de productos |
| `http://127.0.0.1:8000/nosotros/` | Página institucional |
| `http://127.0.0.1:8000/contacto/` | Formulario de consulta |
| `http://127.0.0.1:8000/registro/` | Registro de usuarios |
| `http://127.0.0.1:8000/login/` | Iniciar sesión |
| `http://127.0.0.1:8000/perfil/` | Perfil (token + cookies) |
| `http://127.0.0.1:8000/usuarios/` | CRUD de usuarios (staff) |
| `http://127.0.0.1:8000/admin/` | Panel Django Admin |
| `http://127.0.0.1:8000/api/` | API REST (DRF Browsable) |

## Endpoints API REST

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/productos/` | Lista de productos |
| GET | `/api/categorias/` | Lista de categorías |
| GET | `/api/usuarios/` | Lista de usuarios (admin) |
| GET | `/api/pedidos/` | Mis pedidos |
| GET/POST | `/api/consultas/` | Consultas |
| GET | `/api/productos-externos/` | API externa (fakestoreapi) |
| GET | `/api/mi-token/` | Token del usuario actual |
| POST | `/api/token/` | Login y obtener token |

---

## Estructura del Proyecto

```
urban_motion/
├── urban_motion/        # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tienda/              # App principal
│   ├── models.py        # Modelos: Producto, Categoria, Pedido, Consulta
│   ├── views.py         # Vistas del frontend
│   ├── api_views.py     # Vistas de la API REST
│   ├── serializers.py   # Serializers DRF
│   ├── forms.py         # Formularios Django
│   ├── urls.py          # URLs del frontend
│   └── api_urls.py      # URLs de la API
├── templates/           # Templates HTML
│   ├── base.html        # Template base con navbar y footer
│   ├── inicio.html
│   ├── catalogo.html
│   ├── detalle_producto.html
│   ├── registrarse.html
│   ├── loguearse.html
│   ├── mi_perfil.html   # Token + Cookies
│   ├── usuarios.html    # CRUD de usuarios
│   ├── carrito.html
│   ├── contacto.html
│   ├── nosotros.html
│   └── ...
├── static/
│   ├── css/estilos.css
│   └── js/main.js
├── cargar_datos.py      # Script de datos de prueba
└── requirements.txt
```
