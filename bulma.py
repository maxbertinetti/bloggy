from emmett.forms import FormStyle
from emmett.html import tag, cat
from emmett.validators import isEmptyOr
from emmett.datastructures import sdict


class BulmaFormStyle(FormStyle):
    _stack = []

    @staticmethod
    def _field_options(field):
        validator = FormStyle._validation_woptions(field)
        return validator.options(), validator.multiple

    @staticmethod
    def widget_string(attr, field, value, _class="input", _id=None):
        return tag.input(
            _type="text",
            _name=field.name,
            _value=value if value is not None else "",
            _class=_class,
            _id=_id or field.name
        )

    @staticmethod
    def widget_text(attr, field, value, _class="textarea", _id=None):
        return tag.textarea(
            value or "",
            _name=field.name,
            _class=_class,
            _id=_id or field.name
        )

    @staticmethod
    def widget_int(attr, field, value, _class="input", _id=None):
        return FormStyle.widget_string(attr, field, value, _class, _id)

    @staticmethod
    def widget_bigint(attr, field, value, _class="input", _id=None):
        return FormStyle.widget_string(attr, field, value, _class, _id)

    @staticmethod
    def widget_float(attr, field, value, _class="input", _id=None):
        return FormStyle.widget_string(attr, field, value, _class, _id)

    @staticmethod
    def widget_date(attr, field, value, _class="date", _id=None):
        return FormStyle.widget_string(attr, field, value, _class, _id)

    @staticmethod
    def widget_time(attr, field, value, _class="time", _id=None):
        return FormStyle.widget_string(attr, field, value, _class, _id)

    @staticmethod
    def widget_datetime(attr, field, value, _class="datetime", _id=None):
        return FormStyle.widget_string(attr, field, value, _class, _id)

    @staticmethod
    def widget_password(attr, field, value, _class="input", _id=None):
        return tag.input(
            _type="password",
            _name=field.name,
            _value=value or "",
            _class=_class,
            _id=_id or field.name
        )

    @staticmethod
    def widget_bool(attr, field, value, _class="bool", _id=None):
        return tag.input(
            _type="checkbox",
            _name=field.name,
            _checked="checked" if value else None,
            _class=_class,
            _id=_id or field.name
        )

    @staticmethod
    def widget_select(attr, field, value, _class="select", _id=None):
        def selected(k):
            return "selected" if str(value) == str(k) else None

        options, multiple = FormStyle._field_options(field)
        if multiple:
            return FormStyle.widget_multiple(
                attr, field, value, options, _class=_class, _id=_id
            )
        return tag.select(
            *[
                tag.option(n, _value=k, _selected=selected(k)) for k, n in options
            ],
            _name=field.name,
            _class=_class,
            _id=_id or field.name
        )

    @staticmethod
    def widget_multiple(attr, field, values, options, _class="select", _id=None):
        def selected(k):
            return "selected" if str(k) in [str(v) for v in values] else None

        values = values or []
        return tag.select(
            *[
                tag.option(n, _value=k, _selected=selected(k)) for k, n in options
            ],
            _name=field.name,
            _class=_class,
            _multiple="multiple",
            _id=_id or field.name
        )

    @staticmethod
    def widget_upload(attr, field, value, _class="upload", _id=None):
        def is_image(value):
            return value.split(".")[-1].lower() in ["gif", "png", "jpg", "jpeg", "bmp"]

        def _coerce_value(value):
            if isinstance(value, str) or isinstance(value, bytes):
                return value or ""
            return ""

        elements = []
        _value = _coerce_value(value)
        download_url = attr.get("upload")
        inp = tag.input(_type="file", _name=field.name, _class=_class, _id=_id)
        elements.append(inp)
        if _value and download_url:
            if callable(download_url):
                url = download_url(value)
            else:
                url = download_url + "/" + value
            if is_image(_value):
                elements.append(
                    tag.img(_src=url, _width="120px", _class="xupload_img"))
            else:
                elements.append(tag.div(tag.a(_value, _href=url)))
            requires = field.requires or []
            # delete checkbox
            if not requires or any(isinstance(v, isEmptyOr) for v in requires):
                elements.append(
                    tag.div(
                        tag.input(
                            _type="checkbox",
                            _class="xcheckbox",
                            _id=_id + "__del",
                            _name=field.name + "__del",
                            _style="display: inline;"
                        ),
                        tag.label(
                            "delete",
                            _for=_id + "__del",
                            _class="file-label"
                        ),
                        _class="file"
                    )
                )
        return tag.div(*elements, _class="file")

    @staticmethod
    def widget_json(attr, field, value, _id=None):
        return FormStyle.widget_text(attr, field, value, _id=_id or field.name)

    @staticmethod
    def widget_jsonb(attr, field, value, _id=None):
        return FormStyle.widget_text(attr, field, value, _id=_id or field.name)

    @staticmethod
    def widget_radio(field, value):
        options, _ = FormStyle._field_options(field)
        return cat(*[
            tag.div(
                tag.input(
                    _id=f"{field.name}_{k}",
                    _name=field.name,
                    _value=k,
                    _type="radio",
                    _checked=("checked" if str(k) == str(value) else None)
                ),
                tag.label(n, _for=f"{field.name}_{k}"),
                _class="xoption_wrap"
            ) for k, n in options
        ])

    def __init__(self, attributes):
        self.attr = attributes

    @staticmethod
    def _validation_woptions(field):
        ftype = field._type.split(":")[0]
        if ftype != "bool" and field.requires:
            for v in field.requires:
                if hasattr(v, "options"):
                    return v
        return None

    #: returns the widget for the field and a boolean (True if widget is
    #  defined by user, False if it comes from styler default ones)
    def _get_widget(self, field, value):
        if field.widget:
            return field.widget(field, value), True
        widget_id = self.attr["id_prefix"] + field.name
        wtype = field._type.split(":")[0]
        if self._validation_woptions(field) is not None:
            wtype = "select"
        elif wtype.startswith("reference"):
            wtype = "int"
        elif wtype.startswith("decimal"):
            wtype = "float"
        try:
            widget = getattr(self, "widget_" + wtype)(
                self.attr, field, value, _id=widget_id
            )
            if not field.writable:
                self._disable_widget(widget)
            return widget, False
        except AttributeError:
            raise RuntimeError(
                f"Missing form widget for field {field.name} of type {wtype}"
            )

    def _disable_widget(self, widget):
        widget.attributes["_disabled"] = "disabled"

    def _proc_element(self, field, value, error):
        widget, wfield = self._get_widget(field, value)
        self._stack.append(sdict(widget=widget, _wffield=wfield))
        self._add_element(field.label, field.comment, error)
        self._stack.pop(-1)

    def _add_element(self, label, comment, error):
        # style only widgets not defined by user
        if not self.element._wffield:
            self.style_widget(self.element.widget)
        self.element.label = self.create_label(label)
        if comment:
            self.element.comment = self.create_comment(comment)
        if error:
            self.element.error = self.create_error(error)
        self.add_widget(self.element.widget)

    def _add_hidden(self, key, value):
        self.parent.append(tag.input(_name=key, _type="hidden", _value=value))

    def _add_formkey(self, key):
        self.parent.append(tag.input(_name="_csrf_token",
                           _type="hidden", _value=key))

    @property
    def element(self):
        return self._stack[-1] if self._stack else None

    def on_start(self):
        self.parent = cat()

    def style_widget(self, widget):
        pass

    def create_label(self, label):
        return tag.label(label, _for=self.element.widget["_id"], _class="label")

    def create_error(self, error):
        return tag.div(error, _class="emt_error")

    def create_comment(self, comment):
        return tag.p(comment, _class="emt_help")

    def add_widget(self, widget):
        wrapper = tag.div(widget)
        if self.element.error:
            wrapper.append(self.element.error)
        if self.element.comment:
            wrapper.append(self.element.comment)
        self.parent.append(tag.div(self.element.label, wrapper))

    def add_buttons(self):
        submit = tag.input(
            _type="submit", _value=self.attr["submit"], _class="button is-primary")
        self.parent.append(tag.div(submit))

    def render(self):
        return tag.form(self.parent, **self.attr)
