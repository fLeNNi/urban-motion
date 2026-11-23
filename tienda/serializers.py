
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


class ItemPedidoInputSerializer(serializers.Serializer):
    """Item de entrada para crear un pedido: el precio NUNCA lo manda el cliente."""
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.filter(activo=True))
    cantidad = serializers.IntegerField(min_value=1, max_value=999)


class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    # Solo escritura: lista de {producto, cantidad}. Obligatoria al crear, para evitar pedidos vacios
    items = ItemPedidoInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Pedido
        fields = ['id', 'usuario', 'usuario_username', 'fecha', 'estado', 'total',
                  'direccion_envio', 'detalles', 'items']
        # Usuario, total y fecha los define el servidor (evita suplantacion y totales arbitrarios)
        read_only_fields = ['id', 'usuario', 'usuario_username', 'fecha', 'total']

    def validate_estado(self, value):
        request = self.context.get('request')
        # Solo el personal administrativo puede alterar estados de pedidos
        if request and not request.user.is_staff:
            if self.instance and self.instance.estado != value:
                raise serializers.ValidationError("Solo el personal administrativo puede modificar el estado de un pedido.")
            return 'pendiente'
        return value

    def validate(self, attrs):
        # Al crear, es obligatorio enviar al menos un item
        if self.instance is None and not attrs.get('items'):
            raise serializers.ValidationError({'items': 'Debe incluir al menos un producto.'})
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        items = validated_data.pop('items')
        with transaction.atomic():
            pedido = Pedido.objects.create(total=0, **validated_data)
            total = 0
            for item in items:
                producto = item['producto']
                # Precio tomado de la base de datos, nunca del cliente
                DetallePedido.objects.create(
                    pedido=pedido, producto=producto,
                    cantidad=item['cantidad'], precio_unitario=producto.precio,
                )
                total += producto.precio * item['cantidad']
            pedido.total = total
            pedido.save(update_fields=['total'])
        return pedido

    def update(self, instance, validated_data):
        # Los items no se modifican despues de creado el pedido
        validated_data.pop('items', None)
        return super().update(instance, validated_data)


class ConsultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consulta
        fields = '__all__'
