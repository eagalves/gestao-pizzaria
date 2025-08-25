from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtrai o valor arg do valor value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def centavos_para_reais(value):
    """Converte centavos para reais."""
    try:
        return float(value) / 100
    except (ValueError, TypeError):
        return 0

@register.filter
def reais_para_centavos(value):
    """Converte reais para centavos."""
    try:
        return int(float(value) * 100)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide o valor value pelo valor arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
