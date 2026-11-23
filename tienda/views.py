import json
import urllib.request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.core.files.base import ContentFile
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token
from .models import Producto, Categoria, Pedido, DetallePedido, Consulta
from .forms import (
    ConsultaForm, UserCreateForm, UserUpdateForm,
    UserProfileForm, UserAdminUpdateForm, ProductoForm, ResetPasswordForm
)


# --- Vistas publicas ---

def inicio(request):
    # Traemos los primeros 8 productos activos para la portada
    productos_destacados = Producto.objects.filter(activo=True)[:8]
    categorias = Categoria.objects.all()
    return render(request, 'inicio.html', {
        'productos': productos_destacados,
        'categorias': categorias,
    })


def nosotros(request):
    techs = ['Django', 'Python', 'Bootstrap 5', 'DRF', 'SQLite', 'HTML5', 'CSS3', 'JavaScript']
    return render(request, 'nosotros.html', {'techs': techs})


def catalogo(request):
    productos = Producto.objects.filter(activo=True)
    categorias = Categoria.objects.all()

    # Filtro opcional por categoria seleccionada
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # Buscador por nombre o descripcion
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
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    # Productos de la misma categoria para recomendar abajo
    relacionados = Producto.objects.filter(categoria=producto.categoria, activo=True).exclude(pk=pk)[:4]
    return render(request, 'detalle_producto.html', {
        'producto': producto,
        'relacionados': relacionados,
    })


# --- Autenticacion y cuentas ---

def registrarse(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        # Generamos el token DRF para el usuario nuevo
        Token.objects.get_or_create(user=user)
        login(request, user)
        messages.success(request, f'Bienvenido {user.username}, cuenta creada con éxito.')
        return redirect('inicio')

    return render(request, 'registrarse.html', {'form': form})


def loguearse(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'GET':
        return render(request, 'loguearse.html', {'form': AuthenticationForm()})
    else:
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user is None:
            messages.error(request, 'Usuario o contraseña incorrectos.')
            return render(request, 'loguearse.html', {'form': AuthenticationForm()})
        else:
            login(request, user)
            messages.success(request, f'Sesión iniciada como {user.username}.')
            return redirect('inicio')


@login_required
def desloguearse(request):
    logout(request)
    messages.info(request, 'Sesión finalizada.')
    return redirect('inicio')


# --- Gestion de usuarios (Admin) ---

@login_required
def lista_usuarios(request):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado: solo para administradores.')
        return redirect('inicio')
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'usuarios.html', {'usuarios': usuarios})


@login_required
def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    # Solo staff o el propio usuario pueden editar
    if not request.user.is_staff and request.user.pk != pk:
        messages.error(request, 'No tenés permisos para editar este usuario.')
        return redirect('inicio')

    # Proteccion de superusuario: solo superuser puede modificar a otro superuser
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tenés permisos para modificar a un superadministrador.')
        return redirect('lista_usuarios' if request.user.is_staff else 'inicio')

    # Separamos formulario: staff usa UserAdminUpdateForm (con flags), usuario comun usa UserProfileForm (sin flags)
    FormClass = UserAdminUpdateForm if request.user.is_staff else UserProfileForm

    if request.method == 'GET':
        form = FormClass(instance=usuario)
        return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})
    else:
        form = FormClass(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos de usuario actualizados.')
            if request.user.is_staff:
                return redirect('lista_usuarios')
            return redirect('mi_perfil')
        return render(request, 'editar_usuario.html', {'form': form, 'usuario': usuario})


@login_required
def eliminar_usuario(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'No tenés permisos para realizar esta acción.')
        return redirect('inicio')

    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('lista_usuarios')
    return render(request, 'confirmar_eliminar_usuario.html', {'usuario': usuario})


# --- Perfil y contraseñas ---

@login_required
def mi_perfil(request):
    # Token y cookies de sesion del usuario
    token, _ = Token.objects.get_or_create(user=request.user)
    session_data = dict(request.session)
    cookies_data = {k: v for k, v in request.COOKIES.items()}
    mis_pedidos = Pedido.objects.filter(usuario=request.user).order_by('-fecha')[:5]
    return render(request, 'mi_perfil.html', {
        'token': token,
        'session_data': session_data,
        'cookies_data': cookies_data,
        'mis_pedidos': mis_pedidos,
    })


@login_required
def cambiar_contrasena(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # update_session_auth_hash evita que Django cierre la sesion al cambiar la clave
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Contraseña actualizada con éxito.')
            return redirect('mi_perfil')
        else:
            messages.error(request, 'Por favor revisá los datos ingresados.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'cambiar_contrasena.html', {'form': form})


def olvide_contrasena(request):
    # Recuperacion verificando usuario y correo en BD con validacion robusta
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            email = form.cleaned_data['email'].strip().lower()
            nueva_password = form.cleaned_data['nueva_password']
            try:
                user = User.objects.get(username__iexact=username)
                if user.email and user.email.strip().lower() == email:
                    # Validar fortaleza de contraseña con validadores oficiales de Django
                    try:
                        validate_password(nueva_password, user=user)
                    except Exception as err:
                        messages.error(request, f"La contraseña no cumple las reglas de seguridad: {', '.join(err.messages)}")
                        return render(request, 'olvide_contrasena.html', {'form': form})

                    user.set_password(nueva_password)
                    user.save()
                    messages.success(request, 'Contraseña restablecida con éxito. Ya podés iniciar sesión.')
                    return redirect('loguearse')
                else:
                    # Mensaje generico para mitigar enumeracion de usuarios
                    messages.error(request, 'Los datos ingresados no coinciden con ningún registro activo.')
            except User.DoesNotExist:
                # Mensaje generico para mitigar enumeracion de usuarios
                messages.error(request, 'Los datos ingresados no coinciden con ningún registro activo.')
        else:
            messages.error(request, 'Por favor revisá los campos del formulario.')
    else:
        form = ResetPasswordForm()
    return render(request, 'olvide_contrasena.html', {'form': form})


# --- Carrito de compras (guardado en request.session) ---

def ver_carrito(request):
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
    carrito = request.session.get('carrito', {})
    if str(pid) in carrito:
        del carrito[str(pid)]
        request.session['carrito'] = carrito
        messages.info(request, 'Producto eliminado del carrito.')
    return redirect('ver_carrito')


def restar_del_carrito(request, pid):
    carrito = request.session.get('carrito', {})
    pid_str = str(pid)
    if pid_str in carrito:
        if carrito[pid_str]['cantidad'] > 1:
            carrito[pid_str]['cantidad'] -= 1
        else:
            del carrito[pid_str]
        request.session['carrito'] = carrito
    return redirect('ver_carrito')


def vaciar_carrito(request):
    request.session['carrito'] = {}
    messages.info(request, 'Se vació el carrito.')
    return redirect('ver_carrito')


@login_required
def finalizar_compra(request):
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
        # Pasamos cada item de la sesion a lineas de la tabla DetallePedido
        for pid, item in carrito.items():
            try:
                prod = Producto.objects.get(pk=int(pid))
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=prod,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'], # precio historico congelado
                )
            except Producto.DoesNotExist:
                pass
        request.session['carrito'] = {}
        messages.success(request, f'Pedido #{pedido.id} confirmado con éxito.')
        return redirect('mi_perfil')


# --- Consultas y contacto ---

def contacto(request):
    if request.method == 'GET':
        form = ConsultaForm()
    else:
        form = ConsultaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta enviada. Te responderemos a la brevedad.')
            return redirect('contacto')
    return render(request, 'contacto.html', {'form': form})


@login_required
def lista_consultas(request):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado.')
        return redirect('inicio')
    consultas = Consulta.objects.all().order_by('-fecha')
    return render(request, 'lista_consultas.html', {'consultas': consultas})


# --- Administracion de productos (Staff) ---

@login_required
def admin_productos(request):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado.')
        return redirect('inicio')
    productos = Producto.objects.all().order_by('-id')
    return render(request, 'admin_productos.html', {'productos': productos})


@login_required
def crear_producto(request):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado.')
        return redirect('inicio')

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado.')
            return redirect('admin_productos')
    else:
        form = ProductoForm()

    return render(request, 'form_producto.html', {'form': form, 'titulo': 'Agregar Nuevo Producto'})


@login_required
def editar_producto(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado.')
        return redirect('inicio')

    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Producto "{producto.nombre}" modificado.')
            return redirect('admin_productos')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'form_producto.html', {'form': form, 'titulo': f'Editar Producto: {producto.nombre}', 'producto': producto})


@login_required
def eliminar_producto(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado.')
        return redirect('inicio')

    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado.')
        return redirect('admin_productos')

    return render(request, 'confirmar_eliminar_producto.html', {'producto': producto})


# --- API Externa FakeStore ---

def productos_api_externa(request):
    productos_externos = []
    error = None

    try:
        # Traemos categorias de ropa de hombre y mujer
        headers = {'User-Agent': 'UrbanMotion/1.0'}
        url_men = 'https://fakestoreapi.com/products/category/men%27s%20clothing'
        url_women = 'https://fakestoreapi.com/products/category/women%27s%20clothing'

        req_men = urllib.request.Request(url_men, headers=headers)
        with urllib.request.urlopen(req_men, timeout=6) as response:
            prods_men = json.loads(response.read().decode())

        req_women = urllib.request.Request(url_women, headers=headers)
        with urllib.request.urlopen(req_women, timeout=6) as response:
            prods_women = json.loads(response.read().decode())

        # Unimos las listas filtradas
        productos_externos = prods_men + prods_women
    except Exception as e:
        error = f"Error al conectar con FakeStore: {str(e)}"

    return render(request, 'productos_api.html', {
        'productos_externos': productos_externos,
        'error': error
    })


@login_required
def importar_producto_api(request):
    if not request.user.is_staff:
        messages.error(request, 'Acceso denegado: solo administradores pueden importar.')
        return redirect('productos_api_externa')

    if request.method == 'POST':
        titulo = request.POST.get('title')
        precio = request.POST.get('price', 0)
        descripcion = request.POST.get('description', '')
        imagen_url = request.POST.get('image', '')
        categoria_raw = request.POST.get('category', 'Accesorios')

        # Asignamos la categoria local segun el tipo de prenda
        cat_nombre = 'Remeras' if "clothing" in categoria_raw.lower() else 'Accesorios'
        categoria, _ = Categoria.objects.get_or_create(nombre=cat_nombre)

        producto = Producto(
            nombre=titulo[:190],
            descripcion=descripcion,
            precio=float(precio) * 1000, # multiplicador de cambio aproximado a ARS
            stock=15,
            categoria=categoria,
            activo=True
        )

        # Descargamos el archivo binario de la imagen para que quede local en media/
        if imagen_url:
            try:
                req = urllib.request.Request(imagen_url, headers={'User-Agent': 'UrbanMotion/1.0'})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    nombre_archivo = f"api_import_{producto.nombre[:20].replace(' ', '_').replace('/', '_')}.jpg"
                    producto.imagen.save(nombre_archivo, ContentFile(resp.read()), save=False)
            except Exception as e:
                print(f"No se pudo descargar la imagen: {e}")

        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" importado al catálogo.')
        return redirect('catalogo')

    return redirect('productos_api_externa')
