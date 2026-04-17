"""Nested Sets"""

import operator
from functools import reduce

from django.core import serializers
from django.db import models, transaction
from django.db.models import Case, F, Q, When
from django.utils.translation import gettext_noop as _

from treebeard.exceptions import InvalidMoveToDescendant, NodeAlreadySaved
from treebeard.models import Node


def merge_deleted_counters(c1, c2):
    """
    Merge return values from Django's Queryset.delete() method.
    """
    pass


class NS_NodeQuerySet(models.query.QuerySet):
    """
    Custom queryset for the tree node manager.

    Needed only for the customized delete method.
    """

    def delete(self, *args, removed_ranges=None, deleted_counter=None, **kwargs):
        """
        Custom delete method, will remove all descendant nodes to ensure a
        consistent tree (no orphans)

        :returns: tuple of the number of objects deleted and a dictionary
                  with the number of deletions per object type
        """
        pass

    delete.alters_data = True
    delete.queryset_only = True


class NS_NodeManager(models.Manager):
    """Custom manager for nodes in a Nested Sets tree."""

    def get_queryset(self):
        """Sets the custom queryset as the default."""
        pass


class NS_Node(Node):
    """Abstract model to create your own Nested Sets Trees."""

    node_order_by = []

    lft = models.PositiveIntegerField(db_index=True)
    rgt = models.PositiveIntegerField(db_index=True)
    tree_id = models.PositiveIntegerField(db_index=True)
    depth = models.PositiveIntegerField(db_index=True)

    TREEBEARD_IDENTIFYING_FIELD = "lft"
    MOVENODE_FORM_EXCLUDED_FIELDS = ("depth", "lft", "rgt", "tree_id")

    objects = NS_NodeManager()

    _cached_attributes = (
        *Node._cached_attributes,
        "_cached_parent_obj",
    )

    @classmethod
    @transaction.atomic
    def add_root(cls, **kwargs):
        """Adds a root node to the tree."""
        pass



    @transaction.atomic
    def add_child(self, **kwargs):
        """Adds a child to the node."""
        pass

    @transaction.atomic
    def add_sibling(self, pos=None, **kwargs):
        """Adds a new node as a sibling to the current node object."""
        pass

    @transaction.atomic
    def move(self, target, pos=None):
        """
        Moves the current node and all it's descendants to a new position
        relative to another node.
        """
        pass


    def get_children(self):
        """:returns: A queryset of all the node's children"""
        return self.get_descendants().filter(depth=self.depth + 1)

    def get_depth(self):
        """:returns: the depth (level) of the node"""
        return self.depth

    def is_leaf(self):
        """:returns: True if the node is a leaf node (else, returns False)"""
        return self.rgt - self.lft == 1

    def get_root(self):
        """:returns: the root node for the current node object."""
        pass

    def is_root(self):
        """:returns: True if the node is a root node (else, returns False)"""
        return self.lft == 1

    def get_siblings(self):
        """
        :returns: A queryset of all the node's siblings, including the node
            itself.
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
            If no parent is given, all trees are returned.
        """
        cls = cls.tree_model()

        if parent is None:
            # return the entire tree
            return cls.objects.all()
        if parent.is_leaf():
            return cls.objects.filter(pk=parent.pk)
        return cls.objects.filter(tree_id=parent.tree_id, lft__range=(parent.lft, parent.rgt - 1))

    def get_descendants(self, include_self=False):
        """
        :returns: A queryset of all the node's descendants as DFS, doesn't
            include the node itself if `include_self` is `False`
        """
        if include_self:
            return self.__class__.get_tree(self)
        if self.is_leaf():
            return self.tree_model().objects.none()
        return self.__class__.get_tree(self).exclude(pk=self.pk)

    def get_descendant_count(self):
        """:returns: the number of descendants of a node."""
        pass

    def get_ancestors(self):
        """
        :returns: A queryset containing the current node object's ancestors,
            starting by the root node and descending to the parent.
        """
        if self.is_root():
            return self.tree_model().objects.none()
        return self.tree_model().objects.filter(tree_id=self.tree_id, lft__lt=self.lft, rgt__gt=self.rgt)

    def is_descendant_of(self, node):
        """
        :returns: ``True`` if the node if a descendant of another node given
            as an argument, else, returns ``False``
        """
        pass

    def get_parent(self, update=False):
        """
        :returns: the parent node of the current node object.
            Caches the result in the object itself to help in loops.
        """
        if self.is_root():
            return
        try:
            if update:
                del self._cached_parent_obj
            else:
                return self._cached_parent_obj
        except AttributeError:
            pass
        # parent = our most direct ancestor
        self._cached_parent_obj = self.get_ancestors().reverse()[0]
        return self._cached_parent_obj

    @classmethod
    def get_root_nodes(cls):
        """:returns: A queryset containing the root nodes in the tree."""
        return cls.tree_model().objects.filter(lft=1)

    class Meta:
        """Abstract model."""

        abstract = True
