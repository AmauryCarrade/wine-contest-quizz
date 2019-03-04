from django.forms.widgets import CheckboxSelectMultiple, Widget
from django.utils.safestring import mark_safe


class CheckboxTreeSelectMultiple(CheckboxSelectMultiple):
    template_name = "widgets/checkboxes_tree_select.html"

    def __init__(
        self,
        container_classes=None,
        columns_classes=None,
        bold_parents=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.columns_classes = columns_classes
        self.container_classes = container_classes
        self.bold_parents = bold_parents

    def options(self, name, value, attrs=None):
        for item in self.flat_tree(name, value, attrs):
            yield item[1]

    def flat_tree(self, name, value, attrs=None):
        """Return a list of options for this widget, including the level."""
        items = []
        has_selected = False
        prev_level = -1

        for (
            index,
            (option_value, option_label, option_level, is_leaf_node),
        ) in enumerate(self.choices):
            if option_value is None:
                option_value = ""

            if not is_leaf_node and self.bold_parents:
                option_label = mark_safe(f"<strong>{option_label}</strong>")

            if isinstance(option_label, (list, tuple)):
                continue

            selected = str(option_value) in value and (
                not has_selected or self.allow_multiple_selected
            )
            has_selected |= selected
            option = self.create_option(
                name, option_value, option_label, selected, index, attrs=attrs
            )
            option["level"] = option_level
            option["level_diff"] = option_level - prev_level
            option["leaf"] = is_leaf_node

            prev_level = option_level

            items.append((index, option))
        return items

    def get_context(self, name, value, attrs):
        # We bypass the ChoiceWidget context to avoid `optgroups` from
        # being called, as the choices format is not compatible with it.
        context = Widget.get_context(self, name, value, attrs)

        context["widget"]["flat_tree"] = self.flat_tree(
            name, context["widget"]["value"], attrs
        )
        context["widget"]["columns_classes"] = self.columns_classes
        context["widget"]["container_classes"] = self.container_classes

        return context
