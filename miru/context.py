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

import hikari
from hikari.snowflakes import Snowflake

from .abc.item import ModalItem
from .abc.item_handler import ItemHandler
from .interaction import ComponentInteraction
from .interaction import InteractionResponse
from .interaction import ModalInteraction
from .traits import MiruAware

if t.TYPE_CHECKING:
    from .modal import Modal
    from .view import View

__all__ = ["Context", "ViewContext", "ModalContext", "RawComponentContext", "RawModalContext"]

InteractionT = t.TypeVar("InteractionT", "ComponentInteraction", "ModalInteraction")


class Context(abc.ABC, t.Generic[InteractionT]):
    """An abstract base class for context
    objects that proxying a Discord interaction."""

    def __init__(self, interaction: InteractionT) -> None:
        self._interaction: InteractionT = interaction
        self._responses: t.List[InteractionResponse] = []

    @property
    def interaction(self) -> InteractionT:
        """The underlying interaction object."""
        return self._interaction

    @property
    def custom_id(self) -> str:
        """The developer provided unique identifier for the interaction this context is proxying."""
        return self._interaction.custom_id

    @property
    def responses(self) -> t.List[InteractionResponse]:
        """A list of all responses issued to the interaction this context is proxying."""
        return self._responses

    @property
    def app(self) -> MiruAware:
        """The application that loaded miru."""
        if not ItemHandler._app:
            raise AttributeError(f"miru was not loaded, {self.__class__.__name__} has no property app.")

        return ItemHandler._app

    @property
    def bot(self) -> MiruAware:
        """The application that loaded miru."""
        return self.app

    @property
    def user(self) -> hikari.User:
        """The user who triggered this interaction."""
        return self._interaction.user

    @property
    def author(self) -> hikari.User:
        """Alias for Context.user"""
        return self.user

    @property
    def member(self) -> t.Optional[hikari.InteractionMember]:
        """The member who triggered this interaction. Will be None in DMs."""
        return self._interaction.member

    @property
    def locale(self) -> t.Union[str, hikari.Locale]:
        """The locale of this context."""
        return self._interaction.locale

    @property
    def guild_locale(self) -> t.Optional[t.Union[str, hikari.Locale]]:
        """
        The guild locale of this context, if in a guild.
        This will default to `en-US` if not a community guild.
        """
        return self._interaction.guild_locale

    @property
    def channel_id(self) -> Snowflake:
        """The ID of the channel the context represents."""
        return self._interaction.channel_id

    @property
    def guild_id(self) -> t.Optional[Snowflake]:
        """The ID of the guild the context represents. Will be None in DMs."""
        return self._interaction.guild_id

    def _create_response(self, message: t.Optional[hikari.Message] = None) -> InteractionResponse:
        """Create a new response and add it to the list of tracked responses."""
        response = InteractionResponse(self, message)
        self._responses.append(response)
        return response

    def get_guild(self) -> t.Optional[hikari.GatewayGuild]:
        """Gets the guild this context represents, if any. Requires application cache."""
        return self._interaction.get_guild()

    def get_channel(self) -> t.Optional[hikari.TextableGuildChannel]:
        """Gets the channel this context represents, None if in a DM. Requires application cache."""
        return self._interaction.get_channel()

    async def get_last_response(self) -> InteractionResponse:
        """Get the last response issued to the interaction this context is proxying.

        Returns
        -------
        InteractionResponse
            The response object.

        Raises
        ------
        RuntimeError
            The interaction was not yet responded to.
        """
        if self._responses:
            return self._responses[-1]
        raise RuntimeError("This interaction was not yet issued a response.")

    async def respond(
        self,
        content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
        *,
        flags: t.Union[int, hikari.MessageFlag, hikari.UndefinedType] = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]
        ] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]
        ] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """Short-hand method to respond to the interaction this context represents.

        Parameters
        ----------
        content : undefined.UndefinedOr[t.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[t.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : t.Union[undefined.UndefinedType, int, hikari.MessageFlag], optional
            Message flags that should be included with this message.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        if self.interaction._issued_response:
            message = await self.interaction.execute(
                content,
                tts=tts,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )
            return self._create_response(message)
        else:
            await self.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_CREATE,
                content,
                tts=tts,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )
            return self._create_response()

    async def edit_response(
        self,
        content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
        *,
        flags: t.Union[int, hikari.MessageFlag, hikari.UndefinedType] = hikari.UNDEFINED,
        tts: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        component: hikari.UndefinedOr[hikari.api.ComponentBuilder] = hikari.UNDEFINED,
        components: hikari.UndefinedOr[t.Sequence[hikari.api.ComponentBuilder]] = hikari.UNDEFINED,
        attachment: hikari.UndefinedOr[hikari.Resourceish] = hikari.UNDEFINED,
        attachments: hikari.UndefinedOr[t.Sequence[hikari.Resourceish]] = hikari.UNDEFINED,
        embed: hikari.UndefinedOr[hikari.Embed] = hikari.UNDEFINED,
        embeds: hikari.UndefinedOr[t.Sequence[hikari.Embed]] = hikari.UNDEFINED,
        replace_attachments: bool = False,
        mentions_everyone: hikari.UndefinedOr[bool] = hikari.UNDEFINED,
        user_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]
        ] = hikari.UNDEFINED,
        role_mentions: hikari.UndefinedOr[
            t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]
        ] = hikari.UNDEFINED,
    ) -> InteractionResponse:
        """A short-hand method to edit the last response belonging to this interaction.

        Parameters
        ----------
        content : undefined.UndefinedOr[t.Any], optional
            The content of the message. Anything passed here will be cast to str.
        tts : undefined.UndefinedOr[bool], optional
            If the message should be tts or not.
        attachment : undefined.UndefinedOr[hikari.Resourceish], optional
            An attachment to add to this message.
        attachments : undefined.UndefinedOr[t.Sequence[hikari.Resourceish]], optional
            A sequence of attachments to add to this message.
        component : undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder], optional
            A component to add to this message.
        components : undefined.UndefinedOr[t.Sequence[hikari.api.special_endpoints.ComponentBuilder]], optional
            A sequence of components to add to this message.
        embed : undefined.UndefinedOr[hikari.Embed], optional
            An embed to add to this message.
        embeds : undefined.UndefinedOr[t.Sequence[hikari.Embed]], optional
            A sequence of embeds to add to this message.
        mentions_everyone : undefined.UndefinedOr[bool], optional
            If True, mentioning @everyone will be allowed.
        user_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialUser], bool]], optional
            The set of allowed user mentions in this message. Set to True to allow all.
        role_mentions : undefined.UndefinedOr[t.Union[hikari.SnowflakeishSequence[hikari.PartialRole], bool]], optional
            The set of allowed role mentions in this message. Set to True to allow all.
        flags : t.Union[undefined.UndefinedType, int, hikari.MessageFlag], optional
            Message flags that should be included with this message.

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        if self.interaction._issued_response:
            message = await self.interaction.edit_initial_response(
                content,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                embed=embed,
                embeds=embeds,
                replace_attachments=replace_attachments,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
            )
            return self._create_response(message)

        else:
            await self.interaction.create_initial_response(
                hikari.ResponseType.MESSAGE_UPDATE,
                content,
                component=component,
                components=components,
                attachment=attachment,
                attachments=attachments,
                tts=tts,
                embed=embed,
                embeds=embeds,
                mentions_everyone=mentions_everyone,
                user_mentions=user_mentions,
                role_mentions=role_mentions,
                flags=flags,
            )
            return self._create_response()

    @t.overload
    async def defer(
        self,
        response_type: hikari.ResponseType,
        *,
        flags: hikari.UndefinedOr[t.Union[int, hikari.MessageFlag]] = hikari.UNDEFINED,
    ) -> None:
        ...

    @t.overload
    async def defer(self, *, flags: hikari.UndefinedOr[t.Union[int, hikari.MessageFlag]] = hikari.UNDEFINED) -> None:
        ...

    async def defer(
        self,
        *args: t.Any,
        flags: hikari.UndefinedOr[t.Union[int, hikari.MessageFlag]] = hikari.UNDEFINED,
        **kwargs: t.Any,
    ) -> None:
        """Short-hand method to defer an interaction response. Raises RuntimeError if the interaction was already responded to.

        Parameters
        ----------
        response_type : hikari.ResponseType, optional
            The response-type of this defer action. Defaults to DEFERRED_MESSAGE_UPDATE.
        flags : t.Union[int, hikari.MessageFlag, None], optional
            Message flags that should be included with this defer request, by default None

        Raises
        ------
        RuntimeError
            The interaction was already responded to.
        ValueError
            response_type was not a deffered response type.
        """
        response_type = args[0] if args else hikari.ResponseType.DEFERRED_MESSAGE_UPDATE

        if response_type not in [
            hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
            hikari.ResponseType.DEFERRED_MESSAGE_UPDATE,
        ]:
            raise ValueError(
                "Parameter response_type must be ResponseType.DEFERRED_MESSAGE_CREATE or ResponseType.DEFERRED_MESSAGE_UPDATE."
            )

        if self.interaction._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await self.interaction.create_initial_response(hikari.ResponseType.DEFERRED_MESSAGE_UPDATE, flags=flags)


class RawComponentContext(Context[ComponentInteraction]):
    """Raw context proxying component interactions received directly over the gateway."""

    @property
    def message(self) -> hikari.Message:
        """The message object for the view this context is proxying."""
        return self._interaction.message

    async def respond_with_modal(self, modal: Modal) -> None:
        """Respond to this interaction with a modal."""

        if self.interaction._issued_response:
            raise RuntimeError("Interaction was already responded to.")

        await self.interaction.create_modal_response(modal.title, modal.custom_id, modal.build())
        modal.start()


class RawModalContext(Context[ModalInteraction]):
    """Raw context object proxying a ModalInteraction received directly over the gateway."""

    ...


class ViewContext(RawComponentContext):
    """A context object proxying a ComponentInteraction for a view item."""

    def __init__(self, view: View, interaction: ComponentInteraction) -> None:
        super().__init__(interaction)
        self._view = view

    @property
    def view(self) -> View:
        """The view this context originates from."""
        return self._view


class ModalContext(RawModalContext):
    """A context object proxying a ModalInteraction received by a miru modal."""

    def __init__(self, modal: Modal, interaction: ModalInteraction, values: t.Dict[ModalItem, str]) -> None:
        super().__init__(interaction)
        self._modal = modal
        self._values = values

    @property
    def modal(self) -> Modal:
        """The modal this context originates from."""
        return self._modal

    @property
    def values(self) -> t.Dict[ModalItem, str]:
        """The values received as input for this modal."""
        return self._values
