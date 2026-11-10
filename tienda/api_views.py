
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from .models import Producto, Categoria, Pedido, Consulta
from .serializers import (
    ProductoSerializer, CategoriaSerializer, UserSerializer,
    PedidoSerializer, ConsultaSerializer
)


# ============================================================
# VIEWSETS (CRUD API REST)
# ============================================================

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.filter(activo=True)
    serializer_class = ProductoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        categoria = self.request.query_params.get('categoria')
        q = self.request.query_params.get('q')
        if categoria:
            qs = qs.filter(categoria_id=categoria)
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Pedido.objects.all()
        return Pedido.objects.filter(usuario=self.request.user)


class ConsultaViewSet(viewsets.ModelViewSet):
    queryset = Consulta.objects.all()
    serializer_class = ConsultaSerializer


# ============================================================
# ENDPOINTS ESPECIALES
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_token(request):
    """Devuelve el token del usuario autenticado"""
    token, created = Token.objects.get_or_create(user=request.user)
    return Response({
        'username': request.user.username,
        'token': token.key,
        'created': created,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def obtener_token(request):
    """Login por API y obtiene token"""
    from django.contrib.auth import authenticate
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.username})
    return Response({'error': 'Credenciales incorrectas'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_productos_externo(request):
    """Consulta a API externa de productos (ropa en fakestoreapi)"""
    import urllib.request
    import json
    try:
        headers = {'User-Agent': 'UrbanMotion/1.0'}
        url_men = 'https://fakestoreapi.com/products/category/men%27s%20clothing'
        url_women = 'https://fakestoreapi.com/products/category/women%27s%20clothing'

        req_men = urllib.request.Request(url_men, headers=headers)
        with urllib.request.urlopen(req_men, timeout=5) as resp_m:
            prods_men = json.loads(resp_m.read().decode())

        req_women = urllib.request.Request(url_women, headers=headers)
        with urllib.request.urlopen(req_women, timeout=5) as resp_w:
            prods_women = json.loads(resp_w.read().decode())

        data = prods_men + prods_women
        return Response({'fuente': 'fakestoreapi.com (ropa/indumentaria)', 'productos': data})
    except Exception as e:
        return Response({'error': str(e), 'mensaje': 'No se pudo conectar a la API externa'}, 
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
