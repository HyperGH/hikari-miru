from __future__ import annotations

import inspect
import os
import typing as t

import hikari

from .abc.item import DecoratedItem
from .abc.item import ViewItem

if t.TYPE_CHECKING:
    from .context import ViewContext
    from .view import View

    ViewT = t.TypeVar("ViewT", bound="View")

__all__ = ["Button", "button"]


class Button(ViewItem):
    """A view component representing a button.

    Parameters
    ----------
    style : Union[hikari.ButtonStyle, int], optional
        The button's style, by default hikari.ButtonStyle.PRIMARY
    label : Optional[str], optional
        The button's label, by default None
    disabled : bool, optional
        A boolean determining if the button should be disabled or not, by default False
    custom_id : Optional[str], optional
        The custom identifier of the button, by default None
    url : Optional[str], optional
        The URL of the button, by default None
    emoji : Union[hikari.Emoji, str, None], optional
        The emoji present on the button, by default None
    row : Optional[int], optional
        The row the button should be in, leave as None for auto-placement.

    Raises
    ------
    TypeError
        If both label and emoji are left empty.
    TypeError
        if both custom_id and url are provided.
    """

    def __init__(
        self,
        *,
        style: t.Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: t.Optional[str] = None,
        disabled: bool = False,
        custom_id: t.Optional[str] = None,
        url: t.Optional[str] = None,
        emoji: t.Union[hikari.Emoji, str, None] = None,
        row: t.Optional[int] = None,
    ) -> None:
        super().__init__()

        self._style: t.Union[hikari.ButtonStyle, int] = style
        self._label: t.Optional[str] = label
        self._disabled: bool = disabled
        self._emoji: t.Union[str, hikari.Emoji, None] = emoji
        self._custom_id: t.Optional[str] = custom_id
        self._row: t.Optional[int] = int(row) if row is not None else None
        self._url: t.Optional[str] = url

        self._persistent: bool = True if custom_id else False

        if self._emoji is None and self._label is None:
            raise TypeError("Must provide at least one of emoji or label")

        if self._custom_id and self._url:
            raise TypeError("Cannot provide both url and custom_id")

        if self.url is None and self.custom_id is None:
            self.custom_id = os.urandom(16).hex()

        if isinstance(self._emoji, str):
            self._emoji = hikari.Emoji.parse(self._emoji)

        if self.url is not None:
            # Assign underlying style
            self._style = hikari.ButtonStyle.LINK

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.BUTTON

    @property
    def style(self) -> t.Union[hikari.ButtonStyle, int]:
        """
        The button's style.
        """
        return self._style

    @style.setter
    def style(self, value: t.Union[hikari.ButtonStyle, int]) -> None:
        if not isinstance(value, (hikari.ButtonStyle, int)):
            raise TypeError("Expected type hikari.ButtonStyle or int for property style.")

        if self.url is not None:
            raise ValueError("A link button cannot have it's style changed. Remove the url first.")

        self._style = value

    @property
    def label(self) -> t.Optional[str]:
        """
        The button's label. This is the text visible on the button.
        """
        return self._label

    @label.setter
    def label(self, value: t.Optional[str]) -> None:
        self._label = str(value) if value else None

    @property
    def emoji(self) -> t.Union[str, hikari.Emoji, None]:
        """
        The emoji that should be visible on the button.
        """
        return self._emoji

    @emoji.setter
    def emoji(self, value: t.Union[str, hikari.Emoji, None]) -> None:
        if value and isinstance(value, str):
            value = hikari.Emoji.parse(value)

        if value and not isinstance(value, hikari.Emoji):
            raise TypeError("Expected types str or hikari.Emoji for property emoji.")
        self._emoji = value

    @property
    def url(self) -> t.Optional[str]:
        """
        The button's URL. If specified, the button will turn into a link button,
        and the style parameter will be ignored.
        """
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Expected type str for property url.")

        if value:
            self.style = hikari.ButtonStyle.LINK

        self._url = value

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> ViewItem:
        assert isinstance(component, hikari.ButtonComponent)

        return cls(
            style=component.style,
            label=component.label,
            disabled=component.is_disabled,
            custom_id=component.custom_id,
            url=component.url,
            emoji=component.emoji,
            row=row,
        )

    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        button: t.Union[
            hikari.api.InteractiveButtonBuilder[hikari.api.ActionRowBuilder],
            hikari.api.LinkButtonBuilder[hikari.api.ActionRowBuilder],
        ]
        if self.style is hikari.ButtonStyle.LINK:
            assert self.url is not None
            button = action_row.add_button(hikari.ButtonStyle.LINK, self.url)
        else:
            assert self.custom_id is not None
            button = action_row.add_button(self.style, self.custom_id)

        if self.label:
            button.set_label(self.label)
        if self.emoji:
            button.set_emoji(self.emoji)
        button.set_is_disabled(self.disabled)
        button.add_to_container()


def button(
    *,
    label: t.Optional[str] = None,
    custom_id: t.Optional[str] = None,
    style: hikari.ButtonStyle = hikari.ButtonStyle.PRIMARY,
    emoji: t.Optional[t.Union[str, hikari.Emoji]] = None,
    row: t.Optional[int] = None,
    disabled: bool = False,
) -> t.Callable[[t.Callable[[ViewT, Button, ViewContext], t.Any]], Button]:
    """A decorator to transform a coroutine function into a Discord UI Button's callback.
    This must be inside a subclass of View.

    Parameters
    ----------
    label : Optional[str], optional
        The button's label, by default None
    custom_id : Optional[str], optional
        The button's custom identifier, by default None
    style : hikari.ButtonStyle, optional
        The style of the button, by default hikari.ButtonStyle.PRIMARY
    emoji : Optional[Union[str, hikari.Emoji]], optional
        The emoji shown on the button, by default None
    row : Optional[int], optional
        The row the button should be in, leave as None for auto-placement.
    disabled : bool, optional
        A boolean determining if the button should be disabled or not, by default False

    Returns
    -------
    Callable[[CallableT], CallableT]
        The decorated callback coroutine function.
    """

    def decorator(func: t.Callable[..., t.Any]) -> t.Any:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("button must decorate coroutine function.")
        item = Button(
            label=label,
            custom_id=custom_id,
            style=style,
            emoji=emoji,
            row=row,
            disabled=disabled,
            url=None,
        )

        return DecoratedItem(item, func)

    return decorator


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
