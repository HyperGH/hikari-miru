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

__all__ = ["SelectOption", "Select", "select"]


class SelectOption:
    """
    A more lenient way to instantiate select options.
    """

    def __init__(
        self,
        label: str,
        value: t.Optional[str] = None,
        description: t.Optional[str] = None,
        emoji: t.Optional[t.Union[str, hikari.Emoji]] = None,
        is_default: bool = False,
    ) -> None:
        """A more lenient way to instantiate select options.

        Parameters
        ----------
        label : str
            The option's label.
        value : Optional[str], optional
            The internal value of the option, if None, uses label.
        description : Optional[str], optional
            The description of the option, by default None
        emoji : Optional[Union[str, hikari.Emoji]], optional
            The emoji of the option, by default None
        is_default : bool, optional
            A boolean determining of the option is default or not, by default False
        """
        self.label: str = label
        self.value: str = value or label
        self.description: t.Optional[str] = description
        if isinstance(emoji, str):
            emoji = hikari.Emoji.parse(emoji)
        self.emoji: t.Optional[hikari.Emoji] = emoji
        self.is_default: bool = is_default

    def _convert(self) -> hikari.SelectMenuOption:
        return hikari.SelectMenuOption(
            label=self.label,
            value=self.value,
            description=self.description,
            emoji=self.emoji,
            is_default=self.is_default,
        )


class Select(ViewItem):
    """A view component representing a select menu.

    Parameters
    ----------
    options : Sequence[Union[hikari.SelectMenuOption, SelectOption]]
        A sequence of select menu options that this select menu should use.
    custom_id : Optional[str], optional
        The custom identifier of the select menu, by default None
    placeholder : Optional[str], optional
        Placeholder text displayed on the select menu, by default None
    min_values : int, optional
        The minimum values a user has to select before it can be sent, by default 1
    max_values : int, optional
        The maximum values a user can select, by default 1
    disabled : bool, optional
        A boolean determining if the select menu should be disabled or not, by default False
    row : Optional[int], optional
        The row the select menu should be in, leave as None for auto-placement.

    Raises
    ------
    ValueError
        Exceeded the maximum of 25 select menu options possible.
    """

    def __init__(
        self,
        *,
        options: t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]],
        custom_id: t.Optional[str] = None,
        placeholder: t.Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: t.Optional[int] = None,
    ) -> None:
        super().__init__()
        self._values: t.Sequence[str] = []
        self._persistent: bool = True if custom_id else False
        self._custom_id: str = os.urandom(16).hex() if not custom_id else custom_id
        self._disabled: bool = disabled
        self._options: t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]] = options
        self._min_values: int = min_values
        self._max_values: int = max_values
        self._placeholder: t.Optional[str] = placeholder
        self._row: t.Optional[int] = row if row is not None else None

        if len(self._options) > 25:
            raise ValueError("A select can have a maximum of 25 options.")

    @property
    def type(self) -> hikari.ComponentType:
        return hikari.ComponentType.SELECT_MENU

    @property
    def placeholder(self) -> t.Optional[str]:
        """
        The placeholder text that appears before the select menu is clicked.
        """
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value: t.Optional[str]) -> None:
        if value and not isinstance(value, str):
            raise TypeError("Expected type str for property placeholder.")

    @property
    def options(self) -> t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]]:
        """
        The select menu's options.
        """
        return self._options

    @options.setter
    def options(self, value: t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]]) -> None:
        if not isinstance(value, t.Sequence) or not isinstance(value[0], (hikari.SelectMenuOption, SelectOption)):
            raise TypeError(
                "Expected type Sequence[Union[hikari.SelectMenuOption, SelectOption]] for property options."
            )

        if len(value) > 25:
            raise ValueError("A select can have a maximum of 25 options.")

        self._options = value

    @property
    def min_values(self) -> int:
        """
        The minimum amount of options a user has to select.
        """
        return self._min_values

    @min_values.setter
    def min_values(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected type int for property min_values.")
        self._min_values = value

    @property
    def max_values(self) -> int:
        """
        The maximum amount of options a user is allowed to select.
        """
        return self._max_values

    @max_values.setter
    def max_values(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Expected type int for property max_values.")
        self._max_values = value

    @classmethod
    def _from_component(cls, component: hikari.PartialComponent, row: t.Optional[int] = None) -> ViewItem:
        assert isinstance(component, hikari.SelectMenuComponent)

        return cls(
            options=component.options,
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            min_values=component.min_values,
            max_values=component.max_values,
            disabled=component.is_disabled,
            row=row,
        )

    def _build(self, action_row: hikari.api.ActionRowBuilder) -> None:
        """
        Called internally to build and append to an action row
        """
        assert self.custom_id is not None
        select = action_row.add_select_menu(self.custom_id)
        if self.placeholder:
            select.set_placeholder(self.placeholder)
        select.set_min_values(self.min_values)
        select.set_max_values(self.max_values)
        select.set_is_disabled(self.disabled)

        for option in self.options:
            if isinstance(option, SelectOption):
                option = option._convert()

            _option = select.add_option(option.label, option.value)
            _option.set_is_default(option.is_default)
            if option.description:
                _option.set_description(option.description)
            if option.emoji:
                _option.set_emoji(option.emoji)

            _option.add_to_menu()

        select.add_to_container()

    @property
    def values(self) -> t.Sequence[str]:
        return self._values

    @property
    def width(self) -> int:
        return 5

    async def _refresh(self, interaction: hikari.ComponentInteraction) -> None:
        self._values = interaction.values


def select(
    *,
    options: t.Sequence[t.Union[hikari.SelectMenuOption, SelectOption]],
    custom_id: t.Optional[str] = None,
    placeholder: t.Optional[str] = None,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: t.Optional[int] = None,
) -> t.Callable[[t.Callable[[ViewT, Select, ViewContext], t.Any]], Select]:
    """
    A decorator to transform a function into a Discord UI SelectMenu's callback. This must be inside a subclass of View.
    """

    def decorator(func: t.Callable[..., t.Any]) -> t.Any:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("select must decorate coroutine function.")

        item = Select(
            options=options,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
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
