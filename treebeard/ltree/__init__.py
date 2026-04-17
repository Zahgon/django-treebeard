"""Postgres Ltree Trees"""

import functools
import itertools
import operator
import string
from collections.abc import Iterable
from typing import Any

from django.core import serializers
from django.db import models, transaction
from django.db.models import F, Func, OuterRef, Q, Subquery, Value
from django.db.models.functions import Concat
from django.utils.translation import gettext_noop as _

from treebeard.exceptions import InvalidMoveToDescendant, NodeAlreadySaved, PathOverflow
from treebeard.models import Node

from .fields import Ltree2Text, PathField, PathValue, Subpath, Text2LTree


class InvalidLabelConstraints(Exception): ...


def generate_label(
    skip: set[str],
    before: str | None = None,
    after: str | None = None,
):
    """
    Generate a new label value that will order the label before `before` and after `after`.

    Uses an alphabet of digits and ascii uppercase letters.
    If no `before` constraint is provided, then chooses only from letters: this allows room
    for digits to be used in future if nodes are inserted to the left of this one, without
    having to move large chunks of the tree.

    :raise InvalidLabelConstraints: when no label could be generated within the given constraints.
    """
    char_choices = string.ascii_uppercase if not before and not after else string.digits + string.ascii_uppercase

    start = after or char_choices[0]

    if before and before <= start:
        raise InvalidLabelConstraints

    # Construct sets of characters for each position, appending one at the end if we need to extend the string
    char_lists = [char_choices[idx:] for idx in [char_choices.index(char) for char in start]]
    char_lists.append(char_choices)

    # There is no point testing portions of the strings that are identical
    start_from = 0
    for ch1, ch2 in zip(before or "", after or ""):
        if ch1 != ch2:
            break
        start_from += 1

    for i in range(start_from, len(char_lists)):
        iter = itertools.product(*char_lists[: i + 1])
        for label_parts in iter:
            label = "".join(label_parts)
            if after and label <= after:
                continue
            if label in skip:
                continue
            if before and label >= before:
                break  # No point looking any further
            return label

    # We should never reach here... right?
    raise ValueError("Failed to generate label. Please report this as a bug.")




class LT_NodeQuerySet(models.query.QuerySet):
    """
    Custom queryset for the tree node manager.

    Needed only for the custom delete method.
    """

    def delete(self, *args, **kwargs):
        """
        Custom delete method, will remove all descendant nodes to ensure a
        consistent tree (no orphans)

        :returns: tuple of the number of objects deleted and a dictionary
                  with the number of deletions per object type
        """
        pass

    delete.alters_data = True
    delete.queryset_only = True


class LT_NodeManager(models.Manager):
    """Custom manager for nodes in a Materialized Path tree."""

    def get_queryset(self):
        """Sets the custom queryset as the default."""
        pass


class LT_ComplexAddMoveHandler:

    def _move_subtree_right(self, start_node):
        """
        Move the node and everything after it in the tree to the right. This is achieved simply by
        appending an extra character (A) to the topmost label in the path.
        """
        pass


class LT_AddRootHandler:
    def __init__(self, cls, **kwargs):
        super().__init__()
        self.cls = cls
        self.kwargs = kwargs



class LT_AddChildHandler:
    def __init__(self, node, creation_kwargs: dict[str, Any]):
        super().__init__()
        self.node = node
        self.node_cls = node.__class__
        # These are deliberately not extracted in the function signature to avoid collision with model field names
        self.kwargs = creation_kwargs



class LT_AddSiblingHandler(LT_ComplexAddMoveHandler):
    def __init__(self, node, pos, creation_kwargs: dict[str, Any]):
        super().__init__()
        self.node = node
        self.node_cls = node.__class__
        self.pos = pos
        # These are deliberately not extracted in the function signature to avoid collision with model field names
        self.kwargs = creation_kwargs



class LT_MoveHandler(LT_ComplexAddMoveHandler):
    def __init__(self, node, target, pos=None):
        super().__init__()
        self.node = node
        self.node_cls = node.__class__
        self.target = target
        self.pos = pos



class LT_Node(Node):
    """Abstract model to create your own Postgres LTree trees."""

    node_order_by = []
    path = PathField(unique=True)

    TREEBEARD_IDENTIFYING_FIELD = "path"
    MOVENODE_FORM_EXCLUDED_FIELDS = ("path",)

    objects = LT_NodeManager()

    _cached_attributes = (*Node._cached_attributes,)

    @classmethod
    @transaction.atomic
    def add_root(cls, **kwargs):
        """
        Adds a root node to the tree.

        This method saves the node in database. The object is populated as if via:

        ```
        obj = cls(**kwargs)
        ```
        """
        pass

    @classmethod
    def dump_bulk(cls, parent=None, keep_ids=True):
        """Dumps a tree branch to a python data structure."""
        pass

    @classmethod
    def get_tree(cls, parent=None):
        """
        :returns:

            A *queryset* of nodes ordered as DFS, including the parent.
            If no parent is given, the entire tree is returned.
        """
        cls = cls.tree_model()

        if parent is None:
            # return the entire tree
            return cls.objects.all()

        return cls.objects.filter(path__descendants=parent.path)

    @classmethod
    def get_root_nodes(cls):
        """:returns: A queryset containing the root nodes in the tree."""
        return cls.tree_model().objects.filter(path__depth=1).order_by("path")

    @classmethod
    def get_descendants_group_count(cls, parent=None):
        """
        Helper for a very common case: get a group of siblings and the number
        of *descendants* (not only children) in every sibling.

        :param parent:

            The parent of the siblings to return. If no parent is given, the
            root nodes will be returned.

        :returns:

            A Queryset of node objects with an extra attribute: `descendants_count`.
        """
        pass

    def get_depth(self):
        """:returns: the depth (level) of the node"""
        return len(self.path)

    def get_siblings(self):
        """
        :returns: A queryset of all the node's siblings, including the node
            itself.
        """
        pass

    def get_children(self):
        """:returns: A queryset of all the node's children"""
        return self.tree_model().objects.filter(path__descendants=self.path, path__depth=len(self.path) + 1)

    def get_next_sibling(self):
        """
        :returns: The next node's sibling, or None if it was the rightmost
            sibling.
        """
        pass

    def get_descendants(self, include_self=False):
        """
        :returns: A queryset of all the node's descendants as DFS, doesn't
            include the node itself if `include_self` is False
        """
        if include_self:
            return self.__class__.get_tree(self)

        return self.__class__.get_tree(self).exclude(pk=self.pk)

    def get_prev_sibling(self):
        """
        :returns: The previous node's sibling, or None if it was the leftmost
            sibling.
        """
        pass

    def get_children_count(self):
        """
        :returns: The number the node's children, calculated in the most
        efficient possible way.
        """
        pass

    def is_sibling_of(self, node) -> bool:
        """
        :returns: ``True`` if the node is a sibling of another node given as an
            argument, else, returns ``False``
        """
        pass

    def is_child_of(self, node) -> bool:
        """
        :returns: ``True`` is the node if a child of another node given as an
            argument, else, returns ``False``
        """
        pass

    def is_descendant_of(self, node) -> bool:
        """
        :returns: ``True`` if the node is a descendant of another node given
            as an argument, else, returns ``False``
        """
        pass

    @transaction.atomic
    def add_child(self, **kwargs):
        """
        Adds a child to the node.

        This method saves the node in database. The object is populated as if via:

        ```
        obj = self.__class__(**kwargs)
        ```
        """
        pass

    @transaction.atomic
    def add_sibling(self, pos=None, **kwargs):
        """
        Adds a new node as a sibling to the current node object.

        This method saves the node in database. The object is populated as if via:

        ```
        obj = self.__class__(**kwargs)
        ```
        """
        pass

    def get_root(self):
        """:returns: the root node for the current node object."""
        pass

    def is_root(self):
        """:returns: True if the node is a root node (else, returns False)"""
        return len(self.path) == 1

    def is_leaf(self):
        """:returns: True if the node is a leaf node (else, returns False)"""
        return not self.get_children().exists()

    def get_ancestors(self):
        """
        :returns: A queryset containing the current node object's ancestors,
            starting by the root node and descending to the parent.
        """
        return self.tree_model().objects.filter(path__ancestors=self.path).exclude(pk=self.pk)

    def get_parent(self, update=False):
        """
        :returns: the parent node of the current node object.
        """
        if len(self.path) == 1:
            return

        parentpath = self.path[:-1]
        return self.tree_model().objects.get(path=parentpath)

    @transaction.atomic
    def move(self, target, pos=None):
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.
        """
        pass

    class Meta:
        abstract = True
