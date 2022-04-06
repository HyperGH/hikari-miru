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
import copy
import sys
import traceback
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional
from typing import TypeVar

import hikari

from .abc.item import DecoratedItem
from .abc.item import Item
from .abc.item import ViewItem
from .abc.item_handler import ItemHandler
from .button import Button
from .context import ViewContext
from .interaction import ComponentInteraction
from .select import Select

__all__ = ["View", "get_view"]


class View(ItemHandler):
    """Represents a set of Discord UI components attached to a message.

    Parameters
    ----------
    timeout : Optional[float], optional
        The duration after which the view times out, in seconds, by default 120.0
    autodefer : bool, optional
        If unhandled interactions should be automatically deferred or not, by default True

    Raises
    ------
    ValueError
        Raised if a view has more than 25 components attached.
    RuntimeError
        Raised if miru.load() was never called before instantiation.
    """

    _view_children: ClassVar[List[DecoratedItem]] = []  # Decorated callbacks that need to be turned into items
    # Mapping of message_id: View
    _views: Dict[int, View] = {}  # List of all currently active BOUND views, unbound persistent are not listed here

    def __init_subclass__(cls) -> None:
        """
        Get decorated callbacks
        """
        children: List[DecoratedItem] = []
        for base_cls in reversed(cls.mro()):
            for value in base_cls.__dict__.values():
                if isinstance(value, DecoratedItem):
                    children.append(value)

        if len(children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        cls._view_children = children

    def __init__(
        self,
        *,
        timeout: Optional[float] = 120.0,
        autodefer: bool = True,
    ) -> None:
        super().__init__(timeout=timeout, autodefer=autodefer)
        self._message: Optional[hikari.Message] = None
        self._message_id: Optional[int] = None  # Only for bound persistent views

        for decorated_item in self._view_children:  # Sort and instantiate decorated callbacks
            # Must deepcopy, otherwise multiple views will have the same item reference
            decorated_item = copy.deepcopy(decorated_item)
            item = decorated_item.build(self)
            self.add_item(item)
            setattr(self, decorated_item.name, item)

    @property
    def is_persistent(self) -> bool:
        """
        Determines if this view is persistent or not.
        """

        return self.timeout is None and all(isinstance(item, ViewItem) and item._persistent for item in self.children)

    @property
    def message(self) -> Optional[hikari.Message]:
        """
        The message this view is attached to. This is None if the view was started with start_listener().
        """
        return self._message

    @property
    def is_bound(self) -> bool:
        """
        Determines if the view is bound to a message or not. If this is False, message edits will not be supported.
        """
        return True if self._message_id is not None else False

    @classmethod
    def from_message(cls, message: hikari.Message, *, timeout: Optional[float] = 120, autodefer: bool = True) -> View:
        """Create a new from the components included in the passed message. Returns an empty view if the message has no components attached.

        Parameters
        ----------
        message : hikari.Message
            The message to read components from
        timeout : Optional[float], optional
            The timeout of the created view, by default 120
        autodefer : bool, optional
            If unhandled interactions should be automatically deferred or not, by default True

        Returns
        -------
        View
            The view that represents the components attached to this message.

        .. warning::
            Any custom behaviour (such as callbacks) will not be re-created, if you want to access an already running view that is bound to a message, use :obj:`miru.view.get_view` instead.
        """

        view = cls(timeout=timeout, autodefer=autodefer)

        if not message.components:
            return view

        for row, action_row in enumerate(message.components):
            assert isinstance(action_row, hikari.ActionRowComponent)

            for component in action_row.components:
                if isinstance(component, hikari.ButtonComponent):
                    view.add_item(Button._from_component(component, row))

                elif isinstance(component, hikari.SelectMenuComponent):
                    view.add_item(Select._from_component(component, row))

        return view

    def add_item(self, item: Item) -> ItemHandler:
        """Adds a new item to the view.

        Parameters
        ----------
        item : ViewItem
            The item to be added.

        Raises
        ------
        ValueError
            A view already has 25 components attached.
        TypeError
            Parameter item is not an instance of ViewItem.
        RuntimeError
            The item is already attached to this view.
        RuntimeError
            The item is already attached to another view.

        Returns
        -------
        View
            The item handler the item was added to.
        """

        if not isinstance(item, ViewItem):
            raise TypeError(f"Expected type ViewItem for parameter item, not {item.__class__.__name__}.")

        return super().add_item(item)

    async def view_check(self, context: ViewContext) -> bool:
        """Called before any callback in the view is called. Must evaluate to a truthy value to pass.
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
        self,
        error: Exception,
        item: Optional[ViewItem] = None,
        context: Optional[ViewContext] = None,
    ) -> None:
        """Called when an error occurs in a callback function or the built-in timeout function.
        Override for custom error-handling logic.

        Parameters
        ----------
        error : Exception
            The exception encountered.
        item : Optional[MessageItem[ViewT]], optional
            The item this exception originates from, if any.
        context : Optional[Context], optional
            The context associated with this exception, if any.
        """
        if item:
            print(f"Ignoring exception in view {self} for item {item}:", file=sys.stderr)
        else:
            print(f"Ignoring exception in view {self}:", file=sys.stderr)

        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    def stop(self) -> None:
        """
        Stop listening for interactions.
        """
        if self._message_id:
            View._views.pop(self._message_id, None)

        super().stop()

    async def _handle_callback(self, item: ViewItem, context: ViewContext) -> None:
        """
        Handle the callback of a view item. Seperate task in case the view is stopped in the callback.
        """
        assert isinstance(context.interaction, ComponentInteraction)

        try:
            await item._refresh(context.interaction)
            await item.callback(context)

            if not context.interaction._issued_response and self.autodefer:
                await context.defer()

        except Exception as error:
            await self.on_error(error, item, context)

    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """
        Process incoming interactions and convert interaction to miru.ComponentInteraction
        """

        if isinstance(event.interaction, hikari.ComponentInteraction):

            interaction: ComponentInteraction = ComponentInteraction.from_hikari(event.interaction)

            items = [item for item in self.children if item.custom_id == interaction.custom_id]
            if len(items) > 0:

                context = ViewContext(self, interaction)

                passed = await self.view_check(context)
                if not passed:
                    return

                for item in items:
                    assert isinstance(item, ViewItem)
                    # Create task here to ensure autodefer works even if callback stops view
                    self._create_task(self._handle_callback(item, context))

    async def _listen_for_events(self, message_id: Optional[int] = None) -> None:
        """
        Listen for incoming interaction events through the gateway.
        """

        if message_id:
            predicate = (
                lambda e: isinstance(e.interaction, hikari.ComponentInteraction)
                and e.interaction.message.id == message_id
            )
        else:
            predicate = lambda e: isinstance(e.interaction, hikari.ComponentInteraction)

        while True:
            try:
                event = await self.app.event_manager.wait_for(
                    hikari.InteractionCreateEvent,
                    timeout=self.timeout,
                    predicate=predicate,
                )
            except asyncio.TimeoutError:
                # Handle timeouts, stop listening
                await self._handle_timeout()

            else:
                await self._process_interactions(event)

    async def _handle_timeout(self) -> None:
        """
        Handle the timing out of the view.
        """
        if self._message_id:
            View._views.pop(self._message_id, None)

        await super()._handle_timeout()

    def start_listener(self, message: Optional[hikari.SnowflakeishOr[hikari.PartialMessage]] = None) -> None:
        """Re-registers a persistent view for listening after an application restart.
        Specify message_id to create a bound persistent view that can be edited afterwards.

        Parameters
        ----------
        message: Optional[hikari.SnowflakeishOr[hikari.PartialMessage]], optional
            If provided, the persistent view will be bound to this message, and if the
            message is edited with a new view, that will be taken into account.
            Unbound views do not support message editing with additional views.

        Raises
        ------
        ValueError
            The view is not persistent.
        """
        if not self.is_persistent:
            raise ValueError("This can only be used on persistent views.")

        message_id = hikari.Snowflake(message) if message else None

        if message_id:
            self._message_id = message_id

            # Handle replacement of bound views on message edit
            if message_id in View._views.keys():
                View._views[message_id].stop()

            View._views[message_id] = self

        self._listener_task = asyncio.create_task(self._listen_for_events(message_id))

    def start(self, message: hikari.Message) -> None:
        """Start up the view and begin listening for interactions.

        Parameters
        ----------
        message : hikari.Message
            The message the view was built for.

        Raises
        ------
        TypeError
            Parameter message is not an instance of hikari.Message
        """

        # Optimize URL-button-only views by not starting listener
        if all((isinstance(item, Button) and item.url is not None) for item in self.children):
            return

        if not isinstance(message, hikari.Message):
            raise TypeError("Expected instance of hikari.Message.")

        self._message = message
        self._message_id = message.id
        self._listener_task = asyncio.create_task(self._listen_for_events(message.id))

        # Handle replacement of view on message edit
        if message.id in View._views.keys():
            View._views[message.id].stop()

        View._views[message.id] = self


def get_view(message: hikari.SnowflakeishOr[hikari.PartialMessage]) -> Optional[View]:
    """Get a currently running view that is attached to the provided message.

    Parameters
    ----------
    message : hikari.SnowflakeishOr[hikari.PartialMessage]
        The message the view is attached to.

    Returns
    -------
    Optional[View]
        The view bound to this message, if any.

    Raises
    ------
    RuntimeError
        miru was not loaded before this call.
    """

    if View._app is None:
        raise RuntimeError("miru is not yet loaded! Please call miru.load() first.")

    message_id = hikari.Snowflake(message)

    if view := View._views.get(int(message_id)):
        return view

    return None
