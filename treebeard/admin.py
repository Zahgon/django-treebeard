"""Django admin support for treebeard"""

import sys

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import path
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from treebeard.al_tree import AL_Node
from treebeard.exceptions import InvalidMoveToDescendant, InvalidPosition, MissingNodeOrderBy, PathOverflow


def check_empty_dict(GET_dict):
    """
    Returns True if the GET query string contains no values, but it can contain
    empty keys.
    This is better than doing not bool(request.GET) as an empty key will return True
    """
    pass


class TreeAdmin(admin.ModelAdmin):
    """Django Admin class for treebeard."""

    change_list_template = "admin/tree_change_list.html"




    def get_urls(self):
        """
        Adds a url to move nodes to this admin
        """
        pass





def admin_factory(form_class):
    """Dynamically build a TreeAdmin subclass for the given form class.

    :param form_class:
    :return: A TreeAdmin subclass.
    """
    return type(form_class.__name__ + "Admin", (TreeAdmin,), dict(form=form_class))
