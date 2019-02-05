from django import template
from ..models import Bookmark, GeneSetBookmark, GeneBookmark
import logging

logger = logging.getLogger(__name__)
register = template.Library()

@register.simple_tag
# from http://stackoverflow.com/questions/5755150/altering-one-query-parameter-in-a-url-django
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()

@register.filter
#https://stackoverflow.com/questions/1275735/how-to-access-dictionary-element-in-django-template
def hash(h,key):
    return h.get(key, "")

@register.inclusion_tag('bookmark_template_tag.html')
def check_member_status(member, bookmark_id, feature_type):
    bookmark_obj = Bookmark.objects.get(id=bookmark_id)

    if feature_type == 'GS':
        status = GeneSetBookmark.objects.filter(bookmark=bookmark_obj, geneset=member).count()
    elif feature_type == 'G':
        status = GeneBookmark.objects.filter(bookmark=bookmark_obj, gene=member).count()
    else:
        raise NotImplemented('feature_type {} not supported'.format(feature_type))

    logger.debug('Member %s belonging status to bookmark %s is %s', member, bookmark_obj.name, status)
    return {'status': status, 'bookmark_id': bookmark_id, 'feature_id': member.id, 'feature_type': feature_type}
