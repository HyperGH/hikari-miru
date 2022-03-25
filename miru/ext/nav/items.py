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

import abc
from typing import TYPE_CHECKING
from typing import Optional
from typing import TypeVar
from typing import Union

import hikari

from miru.abc.item import ViewItem
from miru.button import Button
from miru.context import ViewContext
from miru.modal import Modal
from miru.select import Select
from miru.text_input import TextInput

if TYPE_CHECKING:
    from .navigator import NavigatorView

NavigatorViewT = TypeVar("NavigatorViewT", bound="NavigatorView")


class NavItem(ViewItem[NavigatorViewT], abc.ABC):
    """A baseclass for all navigation items. NavigatorView requires instances of this class as it's items."""

    async def before_page_change(self) -> None:
        """
        Called when the navigator is about to transition to the next page. Also called before the first page is sent.
        """
        pass


class NavButton(NavItem[NavigatorViewT], Button[NavigatorViewT]):
    """A base class for all navigation buttons."""

    ...


class NavSelect(NavItem[NavigatorViewT], Select[NavigatorViewT]):
    """A base class for all navigation selects."""

    ...


class NextButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to the next page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9654),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page += 1
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == len(self.view.pages) - 1:
            self.disabled = True
        else:
            self.disabled = False


class PrevButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to previous page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9664),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page -= 1
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == 0:
            self.disabled = True
        else:
            self.disabled = False


class FirstButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to first page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9194),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page = 0
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == 0:
            self.disabled = True
        else:
            self.disabled = False


class LastButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to jump to the last page.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9193),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, context: ViewContext) -> None:
        self.view.current_page = len(self.view.pages) - 1
        await self.view.send_page(context)

    async def before_page_change(self) -> None:
        if self.view.current_page == len(self.view.pages) - 1:
            self.disabled = True
        else:
            self.disabled = False


class IndicatorButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to show the current page's number.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.SECONDARY,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = None,
        disabled: bool = False,
        row: Optional[int] = None,
    ):
        # Either label or emoji is required, so we pass a placeholder
        super().__init__(style=style, label="0/0", custom_id=custom_id, emoji=emoji, disabled=disabled, row=row)

    async def before_page_change(self) -> None:
        self.label = f"{self.view.current_page+1}/{len(self.view.pages)}"
        self.disabled = self.disabled if len(self.view.pages) != 1 else True

    async def callback(self, context: ViewContext) -> None:
        modal = Modal("Jump to page", autodefer=False)
        modal.add_item(TextInput(label="Page Number", placeholder="Enter a page number to jump to it..."))
        await context.respond_with_modal(modal)
        await modal.wait()

        if not modal.values:
            return

        try:
            page_number = int(list(modal.values.values())[0]) - 1
        except (ValueError, TypeError):
            self.view._inter = modal.get_response_context().interaction
            return await modal.get_response_context().defer()

        self.view.current_page = page_number
        await self.view.send_page(modal.get_response_context())


class StopButton(NavButton[NavigatorViewT]):
    """
    A built-in NavButton to stop the navigator and disable all buttons.
    """

    def __init__(
        self,
        *,
        style: Union[hikari.ButtonStyle, int] = hikari.ButtonStyle.DANGER,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        emoji: Union[hikari.Emoji, str, None] = chr(9209),
        row: Optional[int] = None,
    ):
        super().__init__(style=style, label=label, custom_id=custom_id, emoji=emoji, row=row)

    async def callback(self, context: ViewContext) -> None:
        if not self.view.message and not self.view._inter:
            return

        for button in self.view.children:
            assert isinstance(button, NavButton)
            button.disabled = True

        if self.view._inter and self.view.ephemeral:
            await self.view._inter.edit_initial_response(components=self.view.build())
        elif self.view.message:
            await self.view.message.edit(components=self.view.build())
        self.view.stop()