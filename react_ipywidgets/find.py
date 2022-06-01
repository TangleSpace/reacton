from typing import Callable, Generic, List, Set, Type, TypeVar, cast

from ipywidgets import Widget

from .core import Element, _RenderContext

W = TypeVar("W")  # used for widgets
X = TypeVar("X")  # used for widgets


class Finder(Generic[W]):
    def __init__(self, widgets: List[W]) -> None:
        self.widgets = widgets

    def matches(self, **matches):
        widget = self.single
        for name, expected in matches.items():
            if not hasattr(widget, name):
                raise AttributeError(f"Widget {widget} has no attribute {name}")
            value = getattr(widget, name)
            assert value == expected, f"Expected {widget}.{name} == {expected}, got {value}"

    @property
    def single(self) -> W:
        if len(self.widgets) != 1:
            raise ValueError(f"Expected 1 match, got {self.widgets}")
        return self.widgets[0]

    def find(self, widget_class: Type[X], **matches):
        def test(widget: Widget):
            if isinstance(widget, widget_class):
                for name, expected in matches.items():
                    if not hasattr(widget, name):
                        if name.startswith("meta_"):
                            meta_attr_name = name[5:]
                            if hasattr(widget, "_react_meta") and meta_attr_name in widget._react_meta:  # type: ignore
                                value = widget._react_meta[meta_attr_name]  # type: ignore
                            else:
                                return False
                        else:
                            raise AttributeError(f"Widget {widget} has no attribute {name}")
                    else:
                        value = getattr(widget, name)
                    print("test", value, expected, value == expected)
                    if value != expected:
                        return False
                return True
            else:
                return False

        return Finder[X](cast(List[X], self._walk(test)))

    def _walk(self, f: Callable[[Element], bool]):
        visited: Set[Widget] = set()
        queue: List[Widget] = list()
        visited = set(self.widgets)
        queue.extend(self.widgets)

        found: List[Element] = []

        while queue:
            widget = queue.pop(0)
            if f(widget):
                found.append(widget)
            else:
                for name in widget.keys:
                    value = getattr(widget, name)
                    if isinstance(value, Widget):
                        if value not in visited:
                            visited.add(value)
                            queue.append(value)
                    elif isinstance(value, (list, tuple)):
                        for el in value:
                            if isinstance(el, Widget):
                                if el not in visited:
                                    visited.add(el)
                                    queue.append(el)
                    elif isinstance(value, dict):
                        for name, el in value.items():
                            if isinstance(el, Widget):
                                if el not in visited:
                                    visited.add(el)
                                    queue.append(el)
        return found


def finder(rc: _RenderContext):
    assert rc.container is not None
    return Finder[Widget](rc.container.children)