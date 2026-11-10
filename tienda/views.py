
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from rest_framework.authtoken.models import Token
from .models import Producto, Categoria, Pedido, DetallePedido, Consulta
from .forms import ConsultaForm, UserUpdateForm, ProductoForm


# ============================================================
# PAGINAS PRINCIPALES
# ============================================================

def inicio(request):
    """Página de inicio con productos destacados"""
    productos_destacados = Producto.objects.filter(activo=True)[:8]
    categorias = Categoria.objects.all()
    return render(request, 'inicio.html', {
        'productos': productos_destacados,
        'categorias': categorias,
    })


def nosotros(request):
    """Página institucional de Urban Motion"""
    techs = ['Django', 'Python', 'Bootstrap 5', 'DRF', 'SQLite', 'HTML5', 'CSS3', 'JavaScript']
    return render(request, 'nosotros.html', {'techs': techs})


def catalogo(request):
    """Catálogo de productos con filtros por categoría y búsqueda"""
    productos = Producto.objects.filter(activo=True)
    categorias = Categoria.objects.all()

    # Filtro por categoría
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # Búsqueda por nombre
    busqueda = request.GET.get('q')
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    return render(request, 'catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_id': categoria_id,
        'busqueda': busqueda,
    })


def detalle_producto(request, pk):
    """Detalle de un producto individual"""
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    relacionados = Producto.objects.filter(categoria=producto.categoria, activo=True).exclude(pk=pk)[:4]
    return render(request, 'detalle_producto.html', {
        'producto': producto,
        'relacionados': relacionados,
    })


# ============================================================
# AUTENTICACION
# ============================================================

def registrarse(request):
    """Registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'GET':
        return render(request, 'registrarse.html', {'form': UserCreationForm()})
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    password=request.POST['password1'],
                    email=request.POST.get('email', ''),
                )
                user.save()
                # Crear token automáticamente
                Token.objects.get_or_create(user=user)
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.username}! Tu cuenta fue creada correctamente.')
                return redirect('inicio')
            except Exception:
                messages.error(request, 'El nombre de usuario ya existe. Elegí otro.')
                return render(request, 'registrarse.html', {'form': UserCreationForm()})
        else:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'registrarse.html', {'form': UserCreationForm()})


def loguearse(request):
    """Inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'GET':
        return render(request, 'loguearse.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password'],
        )
        if user is None:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'loguearse.html', {'form': AuthenticationForm()})
        else:
            login(request, user)
            messages.success(request, f'¡Bienvenido de vuelta, {user.username}!')
            return redirect('inicio')


@login_required
def desloguearse(request):
    """Cerrar sesión"""
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('inicio')


# ============================================================
# USUARIOS (CRUD)
# ============================================================

@login_required
def lista_usuarios(request):
    """Lista de todos los usuarios registrados (CRUD)"""
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para ver esta sección.')
        return redirect('inicio')
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'usuarios.html', {'usuarios': usuarios})


@login_required
def editar_usuario(request, pk):
    """Editar datos de un usuario"""
    if not request.user.is_staff and request.user.pk != pk:
        messages.error(request, 'No tenés permisos para editar este usuario.')
        return redirect('inicio')

    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'GET':
        form = UserUpdateForm(instance=usuario)
        return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})
    else:
        form = UserUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('lista_usuarios')
        return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})


@login_required
def eliminar_usuario(request, pk):
    """Eliminar un usuario"""
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para eliminar usuarios.')
        return redirect('inicio')

    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado.')
        return redirect('lista_usuarios')
    return render(request, 'confirmar_eliminar_usuario.html', {'usuario': usuario})


# ============================================================
# PERFIL DE USUARIO - TOKEN Y COOKIES
# ============================================================

@login_required
def mi_perfil(request):
    """Perfil con token y cookies de sesión"""
    token, created = Token.objects.get_or_create(user=request.user)
    # Leer cookies de sesión
    session_data = dict(request.session)
    cookies_data = {k: v for k, v in request.COOKIES.items()}
    mis_pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')[:5]
    return render(request, 'mi_perfil.html', {
        'token': token,
        'session_data': session_data,
        'cookies_data': cookies_data,
        'mis_pedidos': mis_pedidos,
    })


# ============================================================
# CARRITO
# ============================================================

def ver_carrito(request):
    """Ver carrito de compras (almacenado en sesión)"""
    carrito = request.session.get('carrito', {})
    items = []
    total = 0
    for pid, item in carrito.items():
        subtotal = item['precio'] * item['cantidad']
        total += subtotal
        items.append({
            'id': pid,
            'nombre': item['nombre'],
            'precio': item['precio'],
            'cantidad': item['cantidad'],
            'subtotal': subtotal,
            'imagen': item.get('imagen', ''),
        })
    return render(request, 'carrito.html', {'items': items, 'total': total})


def agregar_al_carrito(request, pk):
    """Agregar producto al carrito (sesión)"""
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    carrito = request.session.get('carrito', {})
    pid = str(pk)
    if pid in carrito:
        carrito[pid]['cantidad'] += 1
    else:
        carrito[pid] = {
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'cantidad': 1,
            'imagen': producto.imagen.url if producto.imagen else '',
        }
    request.session['carrito'] = carrito
    messages.success(request, f'"{producto.nombre}" agregado al carrito.')
    return redirect(request.META.get('HTTP_REFERER', 'catalogo'))


def eliminar_del_carrito(request, pid):
    """Eliminar producto del carrito"""
    carrito = request.session.get('carrito', {})
    if str(pid) in carrito:
        del carrito[str(pid)]
        request.session['carrito'] = carrito
        messages.info(request, 'Producto eliminado del carrito.')
    return redirect('ver_carrito')


def vaciar_carrito(request):
    """Vaciar el carrito"""
    request.session['carrito'] = {}
    messages.info(request, 'Carrito vaciado.')
    return redirect('ver_carrito')


@login_required
def finalizar_compra(request):
    """Crear pedido desde el carrito"""
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.warning(request, 'El carrito está vacío.')
        return redirect('ver_carrito')

    if request.method == 'GET':
        return render(request, 'finalizar_compra.html', {'carrito': carrito})
    else:
        total = sum(v['precio'] * v['cantidad'] for v in carrito.values())
        pedido = Pedido.objects.create(
            usuario=request.user,
            total=total,
            direccion_envio=request.POST.get('direccion', ''),
        )
        for pid, item in carrito.items():
            try:
                prod = Producto.objects.get(pk=int(pid))
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=prod,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                )
            except Producto.DoesNotExist:
                pass
        request.session['carrito'] = {}
        messages.success(request, f'¡Pedido #{pedido.id} realizado con éxito!')
        return redirect('mi_perfil')


# ============================================================
# CONSULTAS
# ============================================================

def contacto(request):
    """Formulario de consulta"""
    if request.method == 'GET':
        form = ConsultaForm()
    else:
        form = ConsultaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Consulta enviada! Te responderemos a la brevedad.')
            return redirect('contacto')
    return render(request, 'contacto.html', {'form': form})


@login_required
def lista_consultas(request):
    """Ver todas las consultas (solo staff)"""
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para ver esta sección.')
        return redirect('inicio')
    consultas = Consulta.objects.all().order_by('-fecha')
    return render(request, 'lista_consultas.html', {'consultas': consultas})


# ============================================================
# GESTIÓN DE PRODUCTOS (ADMIN) & IMPORTACIÓN API
# ============================================================

@login_required
def admin_productos(request):
    """Lista de productos para administración (CRUD)"""
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para administrar productos.')
        return redirect('inicio')
    productos = Producto.objects.all().order_by('-id')
    return render(request, 'admin_productos.html', {'productos': productos})


@login_required
def crear_producto(request):
    """Crear un nuevo producto desde la web"""
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para agregar productos.')
        return redirect('inicio')

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('admin_productos')
    else:
        form = ProductoForm()

    return render(request, 'form_producto.html', {'form': form, 'titulo': 'Agregar Nuevo Producto'})


@login_required
def editar_producto(request, pk):
    """Editar un producto existente"""
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para editar productos.')
        return redirect('inicio')

    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('admin_productos')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'form_producto.html', {'form': form, 'titulo': f'Editar Producto: {producto.nombre}', 'producto': producto})


@login_required
def eliminar_producto(request, pk):
    """Eliminar un producto"""
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para eliminar productos.')
        return redirect('inicio')

    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado.')
        return redirect('admin_productos')

    return render(request, 'confirmar_eliminar_producto.html', {'producto': producto})


def productos_api_externa(request):
    """Vista para explorar productos de la FakeStore API e importarlos al catálogo local"""
    import urllib.request
    import json
    
    productos_externos = []
    error = None

    try:
        url = 'https://fakestoreapi.com/products'
        req = urllib.request.Request(url, headers={'User-Agent': 'UrbanMotion/1.0'})
        with urllib.request.urlopen(req, timeout=6) as response:
            productos_externos = json.loads(response.read().decode())
    except Exception as e:
        error = f"Error al consultar la API externa: {str(e)}"

    return render(request, 'productos_api.html', {
        'productos_externos': productos_externos,
        'error': error
    })


@login_required
def importar_producto_api(request):
    """Importar un producto de FakeStore API al catálogo local de Urban Motion"""
    if not request.user.is_staff:
        messages.error(request, 'Solo administradores pueden importar productos al catálogo.')
        return redirect('productos_api_externa')

    if request.method == 'POST':
        import urllib.request
        from django.core.files.base import ContentFile

        titulo = request.POST.get('title')
        precio = request.POST.get('price', 0)
        descripcion = request.POST.get('description', '')
        imagen_url = request.POST.get('image', '')
        categoria_raw = request.POST.get('category', 'Accesorios')

        # Asignar o crear categoría correspondiente
        cat_nombre = 'Remeras' if "clothing" in categoria_raw.lower() else 'Accesorios'
        categoria, _ = Categoria.objects.get_or_create(nombre=cat_nombre)

        # Crear producto
        producto = Producto(
            nombre=titulo[:190],
            descripcion=descripcion,
            precio=float(precio) * 1000, # Convertir a ARS estimado
            stock=15,
            categoria=categoria,
            activo=True
        )

        # Descargar y guardar la foto del producto automáticamente
        if imagen_url:
            try:
                req = urllib.request.Request(imagen_url, headers={'User-Agent': 'UrbanMotion/1.0'})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    nombre_archivo = f"api_import_{producto.nombre[:20].replace(' ', '_').replace('/', '_')}.jpg"
                    producto.imagen.save(nombre_archivo, ContentFile(resp.read()), save=False)
            except Exception as e:
                print(f"No se pudo descargar imagen: {e}")

        producto.save()
        messages.success(request, f'¡Producto "{producto.nombre}" importado con éxito al catálogo con su imagen!')
        return redirect('catalogo')

    return redirect('productos_api_externa')

