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

import asyncio
import os
import sys
import traceback
from typing import Any
from typing import Dict
from typing import Optional
from typing import TypeVar

import hikari

from .abc.item import Item
from .abc.item import ModalItem
from .abc.item_handler import ItemHandler
from .context import ModalContext
from .interaction import ModalInteraction

ModalT = TypeVar("ModalT", bound="Modal")


class Modal(ItemHandler):
    """Represents a Discord Modal.

    Parameters
    ----------
    title : str
        The title of the modal, appears on the top of the modal dialog box.
    custom_id : str
        The custom identifier of the modal, identifies the modal through interactions.
    autodefer : bool
        If unhandled interactions should be automatically deferred or not, by default True

    Raises
    ------
    ValueError
        Raised if the modal has more than 25 components attached.
    RuntimeError
        Raised if miru.load() was never called before instantiation.
    """

    def __init__(
        self,
        title: str,
        *,
        custom_id: Optional[str] = None,
        timeout: Optional[float] = 300.0,
        autodefer: bool = True,
    ) -> None:
        super().__init__(timeout=timeout, autodefer=autodefer)

        self._title: str = title
        self._custom_id: str = custom_id or os.urandom(16).hex()
        self._values: Optional[Dict[ModalItem[Modal], str]] = None
        self._ctx: Optional[ModalContext] = None

        if len(self._title) > 100:
            raise ValueError("Modal title is too long. Maximum 100 characters.")

        if len(self._custom_id) > 100:
            raise ValueError("Modal custom_id is too long. Maximum 100 characters.")

    @property
    def title(self) -> str:
        """
        The title of this modal. Will be displayed on the top of the modal prompt.
        """
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Expected type str for property title.")

        if len(value) > 100:
            raise ValueError("Modal title is too long. Maximum 100 characters.")

        self._title = value

    @property
    def custom_id(self) -> str:
        """
        The custom identifier of this modal. Interactions belonging to it are tracked by this ID.
        """
        return self._custom_id

    @title.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Expected type str for property custom_id.")

        if len(value) > 100:
            raise ValueError("Modal custom_id is too long. Maximum 100 characters.")

        self._custom_id = value

    @property
    def values(self) -> Optional[Dict[ModalItem[Modal], str]]:
        """
        The input values received by this modal.
        """
        return self._values

    def add_item(self, item: Item) -> None:
        """Adds a new item to the modal.

        Parameters
        ----------
        item : Item
            An instance of ModalItem to be added.

        Raises
        ------
        TypeError
            item is not of type ModalItem.
        ValueError
            The modal already has 25 components attached.
        TypeError
            Parameter item is not an instance of ModalItem.
        RuntimeError
            The item is already attached to this view.
        RuntimeError
            The item is already attached to another view.
        """
        if not isinstance(item, ModalItem):
            raise TypeError("Expected type ModalItem for parameter item.")

        return super().add_item(item)

    async def modal_check(self, context: ModalContext) -> bool:
        """Called before any callback in the modal is called. Must evaluate to a truthy value to pass.
        Override for custom check logic.

        Parameters
        ----------
        context : Context
            The context for this check.

        Returns
        -------
        bool
            A boolean indicating if the check passed or not.
        """
        return True

    async def on_error(
        self: ModalT,
        error: Exception,
        context: Optional[ModalContext] = None,
    ) -> None:
        """Called when an error occurs in a callback function.
        Override for custom error-handling logic.

        Parameters
        ----------
        error : Exception
            The exception encountered.
        item : Optional[Item[ModalT]], optional
            The item this exception originates from, if any.
        context : Optional[Context], optional
            The context associated with this exception, if any.
        """
        print(f"Ignoring exception in modal {self}:", file=sys.stderr)

        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    async def callback(self: ModalT, context: ModalContext) -> None:
        """Called when the modal is submitted.

        Parameters
        ----------
        context : ModalContext
            The context that belongs to this interaction callback.
        """
        pass

    def get_response_context(self) -> ModalContext:
        """Get the context object that was created after submitting the modal.

        Returns
        -------
        ModalContext
            The modal context that was created from the submit interaction.

        Raises
        ------
        RuntimeError
            The modal was not responded to.
        """
        if self._ctx is None:
            raise RuntimeError("This modal was not responded to.")
        return self._ctx

    async def _handle_callback(self: ModalT, context: ModalContext) -> None:
        """
        Handle the callback of a modal item. Seperate task in case the view is stopped in the callback.
        """

        self._values = context.values

        try:
            await self.callback(context)
            self._ctx = context

            if not context.interaction._issued_response and self.autodefer:
                await context.defer()
            self.stop()  # Modals can only receive one response

        except Exception as error:
            await self.on_error(error, context)

    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """
        Process incoming interactions and convert interaction to miru.ModalInteraction.
        """

        if isinstance(event.interaction, hikari.ModalInteraction):

            interaction: ModalInteraction = ModalInteraction.from_hikari(event.interaction)

            context = ModalContext(self, interaction)

            passed = await self.modal_check(context)
            if not passed:
                return

            # Create task here to ensure autodefer works even if callback stops view
            asyncio.create_task(self._handle_callback(context))

    async def _listen_for_events(self) -> None:
        """
        Listen for incoming interaction events through the gateway.
        """

        predicate = (
            lambda e: isinstance(e.interaction, hikari.ModalInteraction) and e.interaction.custom_id == self.custom_id
        )
        try:
            event = await self.app.event_manager.wait_for(
                hikari.InteractionCreateEvent,
                timeout=self._timeout,
                predicate=predicate,
            )
        except asyncio.TimeoutError:
            await self._handle_timeout()
        else:
            await self._process_interactions(event)

    async def wait(self) -> None:
        """
        Wait until the modal is responded to or stopped manually.
        """
        await asyncio.wait_for(self._stopped.wait(), timeout=None)

    def start(self) -> None:
        """Start up the modal and begin listening for interactions."""
        self._listener_task = asyncio.create_task(self._listen_for_events())

    async def send(self, interaction: hikari.MessageResponseMixin[Any]) -> None:
        """Send this modal as a response to the provided interaction."""
        await interaction.create_modal_response(self.title, self.custom_id, components=self.build())
        self.start()