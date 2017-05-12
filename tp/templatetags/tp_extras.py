from django import template
register = template.Library()

@register.simple_tag
# from http://stackoverflow.com/questions/5755150/altering-one-query-parameter-in-a-url-django
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()