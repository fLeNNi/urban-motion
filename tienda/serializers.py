
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Producto, Categoria, Pedido, DetallePedido, Consulta


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'stock', 'categoria',
                  'categoria_nombre', 'imagen', 'fecha_creacion', 'activo']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'date_joined', 'is_active', 'is_staff']


class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal()


class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'usuario', 'usuario_username', 'fecha', 'estado', 'total',
                  'direccion_envio', 'detalles']
        # El usuario, total y fecha son administrados por el servidor para evitar suplantacion o montos arbitrarios
        read_only_fields = ['id', 'usuario', 'usuario_username', 'fecha', 'total']

    def validate_estado(self, value):
        request = self.context.get('request')
        # Solo el personal administrativo puede alterar estados de pedidos
        if request and not request.user.is_staff:
            if self.instance and self.instance.estado != value:
                raise serializers.ValidationError("Solo el personal administrativo puede modificar el estado de un pedido.")
            return 'pendiente'
        return value


class ConsultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consulta
        fields = '__all__'
