from django.contrib.admin.options import TO_FIELD_VAR
from django.template import Library
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from treebeard.templatetags import needs_checkboxes

register = Library()
CHECKBOX_TMPL = '<input type="checkbox" class="action-select" value="{}" name="_selected_action" /> '






