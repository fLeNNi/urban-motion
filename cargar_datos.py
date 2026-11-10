
"""
Script para cargar datos de prueba en la base de datos de Urban Motion.
Ejecutar con: python manage.py shell < cargar_datos.py
O: python cargar_datos.py (desde el directorio del proyecto)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'urban_motion.settings')
django.setup()

from django.contrib.auth.models import User
from tienda.models import Categoria, Producto
from rest_framework.authtoken.models import Token

# ============================================================
# CREAR SUPERUSUARIO
# ============================================================
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser('admin', 'admin@urbanmotion.com', 'admin123')
    Token.objects.get_or_create(user=admin)
    print("✓ Superusuario creado: admin / admin123")
else:
    print("→ Superusuario 'admin' ya existe")

# ============================================================
# CREAR USUARIO DE PRUEBA
# ============================================================
if not User.objects.filter(username='juan').exists():
    juan = User.objects.create_user('juan', 'juan@example.com', 'juan1234')
    Token.objects.get_or_create(user=juan)
    print("✓ Usuario de prueba creado: juan / juan1234")
else:
    print("→ Usuario 'juan' ya existe")

# ============================================================
# CATEGORÍAS
# ============================================================
categorias_data = [
    ('Remeras', 'Remeras urbanas de todos los estilos'),
    ('Pantalones', 'Joggers, cargo pants y jeans urbanos'),
    ('Camperas', 'Camperas y hoodies para el frío'),
    ('Accesorios', 'Gorras, bolsas y complementos'),
    ('Calzado', 'Zapatillas y botas urbanas'),
]

categorias = {}
for nombre, desc in categorias_data:
    cat, created = Categoria.objects.get_or_create(nombre=nombre, defaults={'descripcion': desc})
    categorias[nombre] = cat
    if created:
        print(f"✓ Categoría creada: {nombre}")

# ============================================================
# PRODUCTOS
# ============================================================
productos_data = [
    ('Remera Oversize Logo', 'Remera oversize de algodón premium con logo bordado en el pecho. Disponible en negro y blanco.', 4500, 25, 'Remeras'),
    ('Remera Tie Dye Urban', 'Remera con diseño tie-dye exclusivo. Corte relaxed fit ideal para el verano.', 3800, 15, 'Remeras'),
    ('Remera Básica Pack x3', 'Pack de 3 remeras básicas de algodón en colores neutros. Calidad premium.', 8500, 10, 'Remeras'),
    ('Jogger Cargo Utility', 'Pantalón cargo con múltiples bolsillos y ajuste en tobillo. Comodidad total.', 9800, 20, 'Pantalones'),
    ('Jean Distressed Slim', 'Jean slim con roturas estratégicas. Stretch para mayor movimiento.', 11500, 12, 'Pantalones'),
    ('Pantalón Técnico Running', 'Pantalón técnico liviano para correr o usar casual. Con bolsillos laterales con cierre.', 7500, 18, 'Pantalones'),
    ('Hoodie Logo Bordado', 'Buzo con capucha y logo bordado. Algodón pesado 380g. Perfecto para el invierno.', 15000, 8, 'Camperas'),
    ('Campera Rompeviento', 'Campera rompeviento impermeable con capucha desmontable. Estilo urbano funcional.', 18500, 6, 'Camperas'),
    ('Puffer Vest Urban', 'Chaleco inflado liviano. Perfecto como capa intermedia en días fríos.', 12000, 10, 'Camperas'),
    ('Gorra 5 Paneles', 'Gorra de 5 paneles con visera plana y logo bordado. Ajuste strapback.', 3200, 30, 'Accesorios'),
    ('Mochila Urban 20L', 'Mochila urbana de 20 litros con múltiples compartimentos y tela resistente.', 8900, 15, 'Accesorios'),
    ('Riñonera Crossbody', 'Riñonera pequeña ajustable para el día a día. Cierre YKK de calidad.', 4200, 20, 'Accesorios'),
]

for nombre, desc, precio, stock, cat_nombre in productos_data:
    prod, created = Producto.objects.get_or_create(
        nombre=nombre,
        defaults={
            'descripcion': desc,
            'precio': precio,
            'stock': stock,
            'categoria': categorias[cat_nombre],
            'activo': True,
        }
    )
    if created:
        print(f"✓ Producto creado: {nombre} - ${precio}")

print("\n✅ Datos de prueba cargados correctamente!")
print("\n📋 Credenciales:")
print("   Admin:  admin / admin123  →  http://127.0.0.1:8000/admin/")
print("   User:   juan  / juan1234  →  http://127.0.0.1:8000/login/")
print("\n🌐 Sitio:   http://127.0.0.1:8000/")
print("🔌 API:     http://127.0.0.1:8000/api/")
