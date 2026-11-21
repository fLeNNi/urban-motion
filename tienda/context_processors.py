def carrito_total(request):
    """Context processor que hace disponible el total de unidades del carrito en todos los templates."""
    carrito = request.session.get('carrito', {})
    total = 0
    for item in carrito.values():
        if isinstance(item, dict):
            total += item.get('cantidad', 1)
        else:
            total += 1
    return {'total_unidades_carrito': total}


def token_y_sesion(request):
    """Context processor para tener token y datos de sesión en templates y consola"""
    context = {
        'session_key': request.session.session_key or '',
    }
    if request.user.is_authenticated:
        try:
            from rest_framework.authtoken.models import Token
            token_obj, _ = Token.objects.get_or_create(user=request.user)
            context['user_token'] = token_obj.key
        except Exception:
            context['user_token'] = ''
    return context
