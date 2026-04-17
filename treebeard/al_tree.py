"""Adjacency List"""

from django.core import serializers
from django.db import models, transaction
from django.db.models import Exists, Max, Min, OuterRef
from django.utils.translation import gettext_noop as _

from treebeard.exceptions import InvalidMoveToDescendant, NodeAlreadySaved
from treebeard.models import Node


class AL_NodeManager(models.Manager):
    """Custom manager for nodes in an Adjacency List tree."""

    def get_queryset(self):
        """Sets the custom queryset as the default."""
        pass


class AL_Node(Node):
    """Abstract model to create your own Adjacency List Trees."""

    objects = AL_NodeManager()
    node_order_by = None

    TREEBEARD_IDENTIFYING_FIELD = "parent"
    MOVENODE_FORM_EXCLUDED_FIELDS = ("sib_order", "parent")

    _cached_attributes = (
        *Node._cached_attributes,
        "_cached_depth",
    )

    @classmethod
    @transaction.atomic
    def add_root(cls, **kwargs):
        """Adds a root node to the tree."""
        pass

    @classmethod
    def get_root_nodes(cls):
        """:returns: A queryset containing the root nodes in the tree."""
        return cls.tree_model().objects.filter(parent=None)

    def get_depth(self, update=False):
        """
        :returns: the depth (level) of the node
            Caches the result in the object itself to help in loops.

        :param update: Updates the cached value.
        """

        if self.parent_id is None:
            return 1

        try:
            if update:
                del self._cached_depth
            else:
                return self._cached_depth
        except AttributeError:
            pass

        depth = 0
        node = self
        while node:
            node = node.parent
            depth += 1
        self._cached_depth = depth
        return depth

    def get_children(self):
        """:returns: A queryset of all the node's children"""
        return self.tree_model().objects.filter(parent=self)

    def get_parent(self, update=False):
        """:returns: the parent node of the current node object."""
        if self._meta.proxy_for_model:
            # the current node is a proxy model; the returned parent
            # should be the same proxy model, so we need to explicitly
            # fetch it as an instance of that model rather than simply
            # following the 'parent' relation
            if self.parent_id is None:
                return None

            return self.__class__.objects.get(pk=self.parent_id)

        return self.parent

    def get_ancestors(self):
        """
        :returns: A *list* containing the current node object's ancestors,
            starting by the root node and descending to the parent.
        """
        ancestors = []
        # We use node.get_parent() instead of .parent because the method does handling of proxy models
        node = self.get_parent()
        while node:
            ancestors.insert(0, node)
            node = node.get_parent()
        return ancestors

    def get_root(self):
        """:returns: the root node for the current node object."""
        pass

    def is_root(self):
        return self.parent_id is None



    def is_descendant_of(self, node):
        """
        :returns: ``True`` if the node if a descendant of another node given
            as an argument, else, returns ``False``
        """
        pass

    @classmethod
    def dump_bulk(cls, parent=None, keep_ids=True):
        """Dumps a tree branch to a python data structure."""
        pass

    @transaction.atomic
    def add_child(self, **kwargs):
        """Adds a child to the node."""
        pass

    @classmethod
    def _get_tree_recursively(cls, results, parent, depth):
        if parent:
            qs = parent.get_children() if parent.node_has_children else cls.objects.none()
        else:
            qs = cls.get_root_nodes()

        # Annotate nodes with `node_has_children`, so that we can avoid unnecessary
        # queries to fetch children on leaf nodes
        qs = qs.annotate(node_has_children=Exists(cls.tree_model().objects.filter(parent=OuterRef("pk"))))
        for node in qs:
            node._cached_depth = depth
            results.append(node)
            cls._get_tree_recursively(results, node, depth + 1)

    @classmethod
    def get_tree(cls, parent=None):
        """
        :returns: A list of nodes ordered as DFS, including the parent. If
                  no parent is given, the entire tree is returned.
        """
        if parent:
            depth = parent.get_depth() + 1
            parent.node_has_children = parent.get_children().exists()
            results = [parent]
        else:
            depth = 1
            results = []
        cls._get_tree_recursively(results, parent, depth)
        return results

    def get_descendants(self, include_self=False):
        """
        :returns: A *list* of all the node's descendants, doesn't
            include the node itself if `include_self` is False
        """
        tree = self.tree_model().get_tree(self)
        return tree if include_self else tree[1:]

    def get_descendant_count(self):
        """:returns: the number of descendants of a node"""
        pass

    def get_siblings(self):
        """
        :returns: A queryset of all the node's siblings, including the node
            itself.
        """
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

    class Meta:
        """Abstract model."""

        abstract = True
