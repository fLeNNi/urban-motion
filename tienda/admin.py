
from django.contrib import admin
from .models import Producto, Categoria, Pedido, DetallePedido, Consulta


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'stock', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['precio', 'stock', 'activo']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha', 'estado', 'total']
    list_filter = ['estado']
    inlines = [DetallePedidoInline]


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'email', 'asunto', 'fecha', 'respondida']
    list_filter = ['respondida']
    list_editable = ['respondida']
