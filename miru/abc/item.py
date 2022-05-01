# MIT License
#
# Copyright (c) 2022-present HyperGH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import abc
import typing as t
from abc import abstractmethod
from functools import partial

import hikari

from ..interaction import ComponentInteraction

if t.TYPE_CHECKING:
    from ..context import ViewContext
    from ..modal import Modal
    from ..view import View
    from .item_handler import ItemHandler

__all__ = ["Item", "DecoratedItem", "ViewItem", "ModalItem"]


class Item(abc.ABC):
    """
    An abstract base class for all components. Cannot be directly instantiated.
    """

    def __init__(self) -> None:
        self._row: t.Optional[int] = None
        self._width: int = 1
        self._rendered_row: t.Optional[int] = None  # Where it actually ends up when rendered by Discord
        self._custom_id: t.Optional[str] = None
        self._handler: t.Optional[ItemHandler] = None

    @property
    def row(self) -> t.Optional[int]:
        """
        The row the item should occupy. Leave as None for automatic placement.
        """
        return self._row

    @row.setter
    def row(self, value: t.Optional[int]) -> None:
        if self._rendered_row is not None:
            raise RuntimeError("Item is already attached to a view, row cannot be changed.")

        if value is None:
            self._row = None
        elif 5 > value >= 0:
            self._row = value
        else:
            raise ValueError("Row must be between 0 and 4.")

    @property
    def width(self) -> int:
        """
        The item's width taken up in a Discord UI action row.
        """
        return self._width

    @property
    def custom_id(self) -> t.Optional[str]:
        """
        The item's custom identifier. This will be used to track the item through interactions and
        is required for persistent views.
        """
        return self._custom_id

    @custom_id.setter
    def custom_id(self, value: t.Optional[str]) -> None:
        if value and not isinstance(value, str):
            raise TypeError("Expected type str for property custom_id.")
        if value and len(value) > 100:
            raise ValueError("custom_id has a max length of 100.")

        self._custom_id = value

    @property
    @abstractmethod
    def type(self) -> hikari.ComponentType:
        """
        The component's underlying component type.
        """
        ...

    @abstractmethod
    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        """
        Called internally to build and append the item to an action row
        """
        ...


class ViewItem(Item, abc.ABC):
    """
    An abstract base class for view components. Cannot be directly instantiated.
    """

    def __init__(self) -> None:
        super().__init__()
        self._handler: t.Optional[View] = None
        self._persistent: bool = False
        self._disabled: bool = False

    @property
    def view(self) -> View:
        """
        The view this item is attached to.
        """
        if not self._handler:
            raise AttributeError(f"{self.__class__.__name__} hasn't been attached to a view yet")

        return self._handler

    @property
    def disabled(self) -> bool:
        """
        Indicates whether the item is disabled or not.
        """
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("Expected type bool for property disabled.")
        self._disabled = value

    @classmethod
    @abstractmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> ViewItem:
        """
        Converts the passed hikari component into a miru ViewItem.
        """
        ...

    async def _refresh(self, interaction: ComponentInteraction) -> None:
        """
        Called on an item to refresh it's internal data.
        """
        pass

    async def callback(self, context: ViewContext) -> None:
        """
        The component's callback, gets called when the component receives an interaction.
        """
        pass


class ModalItem(Item, abc.ABC):
    """
    An abstract base class for modal components. Cannot be directly instantiated.
    """

    def __init__(self) -> None:
        super().__init__()
        self._handler: t.Optional[Modal] = None
        self._persistent: bool = False
        self._required: bool = False

    @property
    def modal(self) -> t.Optional[Modal]:
        """
        The modal this item is attached to.
        """
        if not self._handler:
            raise AttributeError(f"{self.__class__.__name__} hasn't been attached to a modal yet.")

        return self._handler

    @property
    def required(self) -> bool:
        """
        Indicates whether the item is required or not.
        """
        return self._required

    @required.setter
    def required(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("Expected type bool for property required.")
        self._required = value


class DecoratedItem:
    """A partial item made using a decorator."""

    def __init__(self, item: ViewItem, callback: t.Callable[..., t.Any]) -> None:
        self.item = item
        self.callback = callback

    def build(self, view: View) -> ViewItem:
        """Convert a DecoratedItem into a ViewItem.

        Parameters
        ----------
        view : ViewT
            The view this decorated item is attached to.

        Returns
        -------
        ViewItem[ViewT]
            The converted item.
        """
        self.item.callback = partial(self.callback, view, self.item)  # type: ignore[assignment]

        return self.item

    @property
    def name(self) -> str:
        """The name of the callback this item decorates.

        Returns
        -------
        str
            The name of the callback.
        """
        return self.callback.__name__

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self.callback(*args, **kwargs)
