from __future__ import annotations

import typing as t

import attr
import hikari

from .context import RawComponentContext
from .context import RawModalContext
from .interaction import ComponentInteraction
from .interaction import ModalInteraction

if t.TYPE_CHECKING:
    from .traits import MiruAware

__all__ = [
    "Event",
    "ComponentInteractionCreateEvent",
    "ModalInteractionCreateEvent",
]


@attr.define()
class Event(hikari.Event):
    """A base class for every miru event."""

    app: MiruAware = attr.field()


@attr.define()
class InteractionCreateEvent(Event):
    """Event fired when a miru interaction is received. This may either be a modal or a component interaction."""

    interaction: t.Union[ModalInteraction, ComponentInteraction] = attr.field()

    @property
    def guild_id(self) -> t.Optional[hikari.Snowflake]:
        """The ID of the guild this event was received from."""
        return self.interaction.guild_id

    @property
    def channel_id(self) -> hikari.Snowflake:
        """The ID of the channel this event was received from."""
        return self.interaction.channel_id

    @property
    def user(self) -> hikari.User:
        """The user that triggered this interaction."""
        return self.interaction.user

    @property
    def author(self) -> hikari.User:
        """An alias for 'user'."""
        return self.user

    @property
    def member(self) -> t.Optional[hikari.Member]:
        """The member that triggered this interaction, `None` if not in a guild."""
        return self.interaction.member

    @property
    def message(self) -> t.Optional[hikari.Message]:
        """The message that the interaction belongs to."""
        return self.interaction.message

    def get_channel(self) -> t.Optional[hikari.TextableGuildChannel]:
        """Gets the channel object from the interaction, returns `None` if cache is not enabled."""
        return self.interaction.get_channel()

    def get_guild(self) -> t.Optional[hikari.GatewayGuild]:
        """Gets the guild object from the interaction, returns `None` if cache is not enabled."""
        return self.interaction.get_guild()


@attr.define()
class ComponentInteractionCreateEvent(InteractionCreateEvent):
    """An event that is dispatched when a new component interaction is received."""

    interaction: ComponentInteraction = attr.field()
    context: RawComponentContext = attr.field()


@attr.define()
class ModalInteractionCreateEvent(InteractionCreateEvent):
    """An event that is dispatched when a new modal interaction is received."""

    interaction: ModalInteraction = attr.field()
    context: RawModalContext = attr.field()


class _EventListener:

    # The currently running app instance that will be subscribed to the listener
    _app: t.Optional[MiruAware] = None

    def start_listeners(self, app: MiruAware) -> None:
        """Start all custom event listeners, this is called during miru.load()"""
        if self._app is not None:
            raise RuntimeError(f"miru is already loaded, cannot start listeners.")
        self._app = app
        self._app.event_manager.subscribe(hikari.InteractionCreateEvent, self._sort_interactions)

    def stop_listeners(self) -> None:
        """Stop all custom event listeners for events, this is called during miru.unload()"""
        if self._app is None:
            raise RuntimeError(f"miru was never loaded, cannot stop listeners.")
        self._app.event_manager.unsubscribe(hikari.InteractionCreateEvent, self._sort_interactions)
        self._app = None

    async def _sort_interactions(self, event: hikari.InteractionCreateEvent) -> None:
        """Sort interaction create events and dispatch miru custom events."""

        assert self._app is not None

        if not isinstance(event.interaction, (hikari.ComponentInteraction, hikari.ModalInteraction)):
            return

        # God why does mypy hate me so much for naming two variables the same in two if statement arms >_<
        if isinstance(event.interaction, hikari.ComponentInteraction):
            comp_inter = ComponentInteraction.from_hikari(event.interaction)
            comp_ctx = RawComponentContext(comp_inter)
            self._app.event_manager.dispatch(ComponentInteractionCreateEvent(self._app, comp_inter, comp_ctx))

        elif isinstance(event.interaction, hikari.ModalInteraction):
            modal_inter = ModalInteraction.from_hikari(event.interaction)
            modal_ctx = RawModalContext(modal_inter)
            self._app.event_manager.dispatch(ModalInteractionCreateEvent(self._app, modal_inter, modal_ctx))


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
