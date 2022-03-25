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
import asyncio
import itertools
import sys
import typing as t

import hikari

from ..traits import MiruAware
from .item import Item

__all__ = ["ItemHandler"]


class _Weights:
    """
    Calculate the position of an item based on it's width, and keep track of item positions
    """

    def __init__(self) -> None:

        self._weights = [0, 0, 0, 0, 0]

    def add_item(self, item: Item) -> None:
        if item.row is not None:
            if item.width + self._weights[item.row] > 5:
                raise ValueError(f"Item does not fit on row {item.row}!")

            self._weights[item.row] += item.width
            item._rendered_row = item.row
        else:
            for row, weight in enumerate(self._weights):
                if weight + item.width <= 5:
                    self._weights[row] += item.width
                    item._rendered_row = row
                    return
            raise ValueError("Item does not fit on this item handler.")

    def remove_item(self, item: Item) -> None:
        if item._rendered_row is not None:
            self._weights[item._rendered_row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        self._weights = [0, 0, 0, 0, 0]


class ItemHandler(abc.ABC):
    """Abstract base class all item-handlers (e.g. views, modals) inherit from.

    Parameters
    ----------
    timeout : Optional[float], optional
        The duration after which the item handler times out, in seconds, by default 120.0
    autodefer : bool
        If unhandled interactions should be automatically deferred or not, by default True

    Raises
    ------
    ValueError
        Raised if the item handler has more than 25 components attached.
    RuntimeError
        Raised if miru.load() was never called before instantiation.
    """

    _app: t.ClassVar[t.Optional[MiruAware]] = None

    def __init__(self, *, timeout: t.Optional[float] = 120.0, autodefer: bool = True) -> None:
        self._timeout: t.Optional[float] = float(timeout) if timeout else None
        self._children: t.List[Item] = []
        self._autodefer: bool = autodefer

        self._weights: _Weights = _Weights()
        self._stopped: asyncio.Event = asyncio.Event()
        self._listener_task: t.Optional[asyncio.Task[None]] = None
        self._running_tasks: t.List[asyncio.Task[t.Any]] = []

        if len(self.children) > 25:
            raise ValueError(f"{self.__class__.__name__} cannot have more than 25 components attached.")

        if self.app is None:
            raise RuntimeError(f"miru.load() was never called before instantiation of {self.__class__.__name__}.")

    @property
    def children(self) -> t.List[Item]:
        """
        A list of all items attached to the item handler.
        """
        return self._children

    @property
    def timeout(self) -> t.Optional[float]:
        """
        The amount of time the item handler is allowed to idle for, in seconds. Must be None for persistent views.
        """
        return self._timeout

    @property
    def app(self) -> MiruAware:
        """
        The application that loaded the miru extension.
        """
        if not self._app:
            raise AttributeError(f"miru was not loaded, {self.__class__.__name__} has no attribute app.")

        return self._app

    @property
    def bot(self) -> MiruAware:
        """
        The application that loaded the miru extension.
        """
        return self.app

    @property
    def autodefer(self) -> t.Optional[bool]:
        """
        A boolean indicating if the received interaction should automatically be deferred if not responded to or not.
        """
        return self._autodefer

    def add_item(self, item: Item) -> ItemHandler:
        """Adds a new item to the item handler.

        Parameters
        ----------
        item : Item[Any]
            The item to be added.

        Raises
        ------
        ValueError
            ItemHandler already has 25 components attached.
        TypeError
            Parameter item is not an instance of Item.
        RuntimeError
            The item is already attached to this item handler.
        RuntimeError
            The item is already attached to another item handler.

        Returns
        -------
        ItemHandler
            The item handler the item was added to.
        """

        if len(self.children) > 25:
            raise ValueError("View cannot have more than 25 components attached.")

        if not isinstance(item, Item):
            raise TypeError(f"Expected Item not {type(item)} for parameter item.")

        if item in self.children:
            raise RuntimeError("Item is already attached to this item handler.")

        if hasattr(item, "_handler") and item._handler is not None:
            raise RuntimeError("Item is already attached to an item handler-")

        self._weights.add_item(item)

        item._handler = self
        self.children.append(item)

        return self

    def remove_item(self, item: Item) -> ItemHandler:
        """Removes the specified item from the item handler.

        Parameters
        ----------
        item : Item[Any]
            The item to be removed.

        Returns
        -------
        ItemHandler
            The item handler the item was removed from.
        """
        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self._weights.remove_item(item)
            item._handler = None

        return self

    def clear_items(self) -> ItemHandler:
        """Removes all items from this item handler.

        Returns
        -------
        ItemHandler
            The item handler items were cleared from.
        """
        for item in self.children:
            item._handler = None
            item._rendered_row = None

        self.children.clear()
        self._weights.clear()

        return self

    def build(self) -> t.List[hikari.impl.ActionRowBuilder]:
        """Converts the view into action rows, must be called before sending.

        Returns
        -------
        List[hikari.impl.ActionRowBuilder]
            A list of action rows containing all items attached to this item handler,
            converted to hikari component objects. If the view has no items attached,
            this returns an empty list.
        """
        if not self.children:
            return []

        self.children.sort(key=lambda i: i._rendered_row if i._rendered_row is not None else sys.maxsize)

        action_rows = []

        for row, items in itertools.groupby(self.children, lambda i: i._rendered_row):
            action_row = hikari.impl.ActionRowBuilder()
            for item in items:
                item._build(action_row)
            action_rows.append(action_row)
        return action_rows

    async def on_timeout(self) -> None:
        """
        Called when the item handler times out. Override for custom timeout logic.
        """
        pass

    def stop(self) -> None:
        """
        Stop listening for interactions.
        """
        self._stopped.set()

        if self._listener_task is not None:
            self._listener_task.cancel()

        self._listener_task = None

    @abc.abstractmethod
    async def _process_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """
        Process incoming interactions.
        """

    @abc.abstractmethod
    async def _listen_for_events(self) -> None:
        """
        Listen for incoming interaction events through the gateway.
        """

    async def _handle_timeout(self) -> None:
        """
        Handle the timing out of the view.
        """
        try:
            await self.on_timeout()
        except Exception as error:
            if on_error := getattr(self, "on_error", None):
                await on_error(error)

        self._stopped.set()

        if self._listener_task is not None:
            self._listener_task.cancel()

        self._listener_task = None

    def _create_task(self, coro: t.Awaitable[t.Any], *, name: t.Optional[str] = None) -> asyncio.Task[t.Any]:
        """
        Run tasks inside the itemhandler internally while keeping a reference to the provided task.
        """
        task = asyncio.create_task(coro, name=name)
        self._running_tasks.append(task)
        task.add_done_callback(lambda t: self._running_tasks.remove(t))
        return task

    async def wait(self) -> None:
        """
        Wait until the item handler has stopped.
        """
        await asyncio.wait_for(self._stopped.wait(), timeout=None)
