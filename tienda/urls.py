
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Páginas principales
    path('', views.inicio, name='inicio'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('contacto/', views.contacto, name='contacto'),

    # Autenticación
    path('registro/', views.registrarse, name='registrarse'),
    path('login/', views.loguearse, name='loguearse'),
    path('logout/', views.desloguearse, name='desloguearse'),
    # Recuperacion de contraseña con link firmado (token de un solo uso, vence en 1 hora)
    path('olvide-contrasena/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html',
        email_template_name='password_reset_email.txt',
        subject_template_name='password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='olvide_contrasena'),
    path('olvide-contrasena/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reset/listo/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html',
    ), name='password_reset_complete'),

    # Perfil y usuarios
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    path('perfil/cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),

    # Carrito
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:pk>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/restar/<int:pid>/', views.restar_del_carrito, name='restar_del_carrito'),
    path('carrito/eliminar/<int:pid>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar_carrito'),
    path('carrito/finalizar/', views.finalizar_compra, name='finalizar_compra'),

    # Consultas admin
    path('consultas/', views.lista_consultas, name='lista_consultas'),

    # Gestión de productos (Admin)
    path('admin-productos/', views.admin_productos, name='admin_productos'),
    path('admin-productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('admin-productos/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('admin-productos/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),

    # API externa & importar al catálogo
    path('productos-api/', views.productos_api_externa, name='productos_api_externa'),
    path('productos-api/importar/', views.importar_producto_api, name='importar_producto_api'),
]
