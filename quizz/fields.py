from django.forms.models import ModelChoiceIterator
from mptt.forms import TreeNodeMultipleChoiceField

from quizz.widgets import CheckboxTreeSelectMultiple


class TreeModelChoiceIterator(ModelChoiceIterator):
    """
    A model choice iterator yielding the level of each object instead
    of only the value & label.
    """

    def choice(self, obj):
        return (
            self.field.prepare_value(obj),
            self.field.label_from_instance(obj),
            getattr(obj, obj._mptt_meta.level_attr),
            obj.is_leaf_node(),
        )


class TreeNodeAllMultipleChoiceField(TreeNodeMultipleChoiceField):
    widget = CheckboxTreeSelectMultiple
    iterator = TreeModelChoiceIterator

    def label_from_instance(self, obj):
        """
        The TreeNodeMultipleChoiceField orders correctly the queryset
        (we want that) and adds dashes to represent depth (we don't).
        So we remove these.
        """
        return str(obj)
