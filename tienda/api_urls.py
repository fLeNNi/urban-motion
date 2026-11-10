
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'productos', api_views.ProductoViewSet)
router.register(r'categorias', api_views.CategoriaViewSet)
router.register(r'usuarios', api_views.UserViewSet)
router.register(r'pedidos', api_views.PedidoViewSet, basename='pedido')
router.register(r'consultas', api_views.ConsultaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('mi-token/', api_views.mi_token, name='mi_token'),
    path('token/', api_views.obtener_token, name='obtener_token'),
    path('productos-externos/', api_views.api_productos_externo, name='api_productos_externo'),
    path('auth/', include('rest_framework.urls')),
]
