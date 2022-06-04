from django import template

register = template.Library()


@register.filter("round_large_values")
def round_large_values(value):
    magnitude = 0
    while abs(value) >= 1000:
        magnitude += 1
        value /= 1000.0
    return '%.2f%s' % (value, ['', 'K', 'M', 'B'][magnitude])

@register.filter("round_small_values")
def round_small_values(value):
    value=round(value,8)
    return value

