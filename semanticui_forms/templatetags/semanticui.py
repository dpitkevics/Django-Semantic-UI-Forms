from django import template
from django.utils import six
from django.utils.html import conditional_escape
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def semanticui(form):
    top_errors = form.non_field_errors()  # Errors that should be displayed above all fields.
    output, hidden_fields = [], []

    for name, field in form.fields.items():
        errors_on_separate_row = False
        error_row = '<tr><td colspan="2">%s</td></tr>'
        help_text_html = '<span class="helptext">%s</span>'
        normal_row = '<div class="field">%(label)s%(field)s%(help_text)s</div>'
        row_ender = '</td></tr>'
        html_class_attr = ''

        bf = form[name]
        # Escape and cache in local variable.
        bf_errors = form.error_class([conditional_escape(error) for error in bf.errors])
        if bf.is_hidden:
            if bf_errors:
                top_errors.extend(
                    [_('(Hidden field %(name)s) %(error)s') % {'name': name, 'error': force_text(e)}
                     for e in bf_errors])
            hidden_fields.append(six.text_type(bf))
        else:
            field_class_name = field.__class__.__name__
            if "ChoiceField" in field_class_name or 'MultipleChoiceField' in field_class_name:
                field.widget.attrs['class'] = "ui dropdown"
            elif 'BooleanField' in field_class_name:
                normal_row = '<div class="field"><div class="ui checkbox">%(field)s%(label)s</div></div>'
                field.widget.attrs['class'] = 'hidden'
            elif 'DateField' in field_class_name or 'DateTimeField' in field_class_name:
                normal_row = '<div class="field">%(label)s<div class="ui left icon input"><i class="calendar icon"></i>%(field)s</div></div>'
            elif 'URLField' in field_class_name:
                normal_row = '<div class="field">%(label)s<div class="ui labeled input"><div class="ui label">http(s)://</div>%(field)s</div></div>'

            css_classes = bf.css_classes()
            # Create a 'class="..."' attribute if the row should have any
            # CSS classes applied.
            if css_classes:
                html_class_attr = ' class="%s"' % css_classes

            if errors_on_separate_row and bf_errors:
                output.append(error_row % force_text(bf_errors))

            if bf.label:
                label = conditional_escape(force_text(bf.label))
                label = bf.label_tag(label) or ''
            else:
                label = ''

            if field.help_text:
                help_text = help_text_html % force_text(field.help_text)
            else:
                help_text = ''

            output.append(normal_row % {
                'errors': force_text(bf_errors),
                'label': force_text(label),
                'field': six.text_type(bf),
                'help_text': help_text,
                'html_class_attr': html_class_attr,
                'field_name': bf.html_name,
            })

        if top_errors:
            output.insert(0, error_row % force_text(top_errors))

        if hidden_fields:  # Insert any hidden fields in the last row.
            str_hidden = ''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = (normal_row % {
                        'errors': '',
                        'label': '',
                        'field': '',
                        'help_text': '',
                        'html_class_attr': html_class_attr,
                        'field_name': '',
                    })
                    output.append(last_row)
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)

    return mark_safe('\n'.join(output))