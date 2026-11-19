from django import template

register = template.Library()

@register.filter
def total_articulos_carrito(carrito):
    """Calcula la cantidad total de prendas/unidades en el carrito"""
    if not carrito or not isinstance(carrito, dict):
        return 0
    total = 0
    for item in carrito.values():
        if isinstance(item, dict):
            total += item.get('cantidad', 1)
        else:
            total += 1
    return total
