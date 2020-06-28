from django import forms, template
from django.forms import BoundField
from django.template.loader import get_template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def a17t(element):
    markup_classes = {"label": "", "value": "", "single_value": ""}
    return render(element, markup_classes)


@register.filter
def a17t_inline(element):
    markup_classes = {"label": "", "value": "", "single_value": ""}
    return render(element, markup_classes)


def render(element, markup_classes):
    if isinstance(element, BoundField):
        template = get_template("a17t/includes/field.html")
        context = {"field": element, "classes": markup_classes, "form": element.form}
    else:
        has_management = getattr(element, "management_form", None)
        if has_management:
            template = get_template("a17t/includes/formset.html")
            context = {"formset": element, "classes": markup_classes}
        else:
            template = get_template("a17t/includes/form.html")
            context = {"form": element, "classes": markup_classes}

    return template.render(context)


@register.filter
def widget_type(field):
    return field.field.widget


@register.filter
def is_select(field):
    return isinstance(field.field.widget, forms.Select)


@register.filter
def is_multiple_select(field):
    return isinstance(field.field.widget, forms.SelectMultiple)


@register.filter
def is_textarea(field):
    return isinstance(field.field.widget, forms.Textarea)


@register.filter
def is_input(field):
    return isinstance(
        field.field.widget,
        (
            forms.TextInput,
            forms.NumberInput,
            forms.EmailInput,
            forms.PasswordInput,
            forms.URLInput,
        ),
    )


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def is_multiple_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxSelectMultiple)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, forms.RadioSelect)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, forms.FileInput)


@register.filter
def add_class(field, css_class):
    if len(field.errors) > 0:
        css_class += " ~critical"
    if field.field.widget.attrs.get("class") != None:
        css_class += " " + field.field.widget.attrs["class"]
    return field.as_widget(attrs={"class": field.css_classes(extra_classes=css_class)})
