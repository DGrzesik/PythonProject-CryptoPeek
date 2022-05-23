from django import template

register = template.Library()


@register.filter("round_values")
def round_values(value):
    magnitude = 0
    while abs(value) >= 1000:
        magnitude += 1
        value /= 1000.0
    return '%.2f%s' % (value, ['', 'K', 'M', 'B'][magnitude])
