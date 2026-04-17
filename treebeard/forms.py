"""Forms for treebeard."""

from django import forms
from django.forms.models import modelform_factory as django_modelform_factory
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from treebeard.al_tree import AL_Node


class TreeNodeChoiceField(forms.ModelChoiceField):
    """
    ModelChoiceField for use with tree models. Applies indentation
    to the label to reflect the depth of the node.

    The queryset/choices provided to the field must be ordered
    in order for the choices to appear in the order that the tree is organised.
    """

    DEPTH_SEPARATOR = mark_safe("&nbsp;&nbsp;&nbsp;&nbsp;")




class MoveNodeForm(forms.ModelForm):
    """
    Form to handle moving a node in a tree.

    Handles sorted/unsorted trees.

    It adds two fields to the form:

    - Relative to: The target node where the current node will
                   be moved to.
    - Position: The position relative to the target node that
                will be used to move the node. These can be:

                - For sorted trees: ``Child of`` and ``Sibling of``
                - For unsorted trees: ``First child of``, ``Before`` and
                  ``After``

    .. warning::

        Subclassing :py:class:`MoveNodeForm` directly is
        discouraged, since special care is needed to handle
        excluded fields, and these change depending on the
        tree type.

        It is recommended that the :py:func:`movenodeform_factory`
        function is used instead.
    """

    __position_choices_sorted = (
        ("sorted-child", _("Child of")),
        ("sorted-sibling", _("Sibling of")),
    )

    __position_choices_unsorted = (
        ("first-child", _("First child of")),
        ("left", _("Before")),
        ("right", _("After")),
    )

    treebeard_position = forms.ChoiceField(required=True, label=_("Position"))
    treebeard_ref_node = TreeNodeChoiceField(
        required=False,
        label=_("Relative to"),
        empty_label=_("-- root --"),
        queryset=None,  # Populated in __init__
    )


    def _set_ref_model_queryset(self, opts, instance):
        """
        Sets the queryset (or choices) on the treebeard_ref_model field.

        For AL trees, this sets a list of nodes as the choices. For all other trees,
        sets a queryset.

        Excludes the instance and its descendants since a move relative to those would be invalid
        """
        pass

    def __init__(self, *args, initial=None, instance=None, **kwargs):
        opts = self._meta
        if opts.model is None:
            raise ValueError("ModelForm has no model class specified")

        self.is_sorted = getattr(opts.model, "node_order_by", False)

        # Set initial values for treebeard fields

        initial_ = self._get_initial(instance) if instance else {}
        if initial is not None:
            initial_.update(initial)

        super().__init__(*args, instance=instance, initial=initial_, **kwargs)

        # update the 'treebeard_position' field choices
        self.fields["treebeard_position"].choices = (
            self.__position_choices_sorted if self.is_sorted else self.__position_choices_unsorted
        )

        self._set_ref_model_queryset(opts, instance)

    def save(self, commit=True):
        """
        Saves the model form.

        WARNING: Treebeard does not respect commit=False: other nodes that
        need to be modified to make space for the edited node will be updated
        in the database, and thus it is difficult to avoid writing any changes to the database.

        TreeAdmin handles this by rolling back the entire transaction if the form or any
        inlines report an error. If you use this form elsewhere, you will need to do the same.
        """
        pass


def movenodeform_factory(model, form=MoveNodeForm, exclude=None, **kwargs):
    """Dynamically build a MoveNodeForm subclass with the proper Meta.

    :param Node model:

        The subclass of :py:class:`Node` that will be handled
        by the form.

    :param form:

        The form class that will be used as a base. By
        default, :py:class:`MoveNodeForm` will be used.

    Accepts all other kwargs that can be passed to Django's `modelform_factory`.

    :return: A :py:class:`MoveNodeForm` subclass
    """
    if exclude is None:
        exclude = ()
    exclude += getattr(model, "MOVENODE_FORM_EXCLUDED_FIELDS", ())
    return django_modelform_factory(model, form, exclude=exclude, **kwargs)
