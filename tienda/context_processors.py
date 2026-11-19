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
