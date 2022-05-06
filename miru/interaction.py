from __future__ import annotations

import functools
import typing as t

import hikari

if t.TYPE_CHECKING:
    from .context import Context

__all__ = ["ComponentInteraction", "ModalInteraction", "InteractionResponse"]


class ComponentInteraction(hikari.ComponentInteraction):
    """
    Represents a component interaction on Discord. This object is practically identical to hikari.ComponentInteraction,
    with the only exception being that response status is tracked for automatic deferring and short-hand methods.
    """

    _issued_response: bool = False

    @classmethod
    def from_hikari(cls, interaction: hikari.ComponentInteraction) -> ComponentInteraction:
        """Create a new ComponentInteraction object from a hikari.ComponentInteraction. This should be rarely used.

        Parameters
        ----------
        interaction : hikari.ComponentInteraction
            The ComponentInteraction this object should be created from.

        Returns
        -------
        ComponentInteraction
            The created interaction object.
        """
        return cls(
            channel_id=interaction.channel_id,
            component_type=interaction.component_type,
            custom_id=interaction.custom_id,
            values=interaction.values,
            guild_id=interaction.guild_id,
            message=interaction.message,
            member=interaction.member,
            user=interaction.user,
            locale=interaction.locale,
            guild_locale=interaction.guild_locale,
            app=interaction.app,
            id=interaction.id,
            application_id=interaction.application_id,
            type=interaction.type,
            token=interaction.token,
            version=interaction.version,
        )

    @functools.wraps(hikari.ComponentInteraction.create_initial_response)
    async def create_initial_response(self, *args: t.Any, **kwargs: t.Any) -> None:
        await super().create_initial_response(*args, **kwargs)
        self._issued_response = True

    @functools.wraps(hikari.ComponentInteraction.create_modal_response)
    async def create_modal_response(self, *args: t.Any, **kwargs: t.Any) -> None:
        await super().create_modal_response(*args, **kwargs)
        self._issued_response = True


class ModalInteraction(hikari.ModalInteraction):
    """
    Represents modal interaction on Discord. This object is practically identical to hikari.ModalInteraction,
    with the only exception being that response status is tracked for automatic deferring and short-hand methods.
    """

    _issued_response: bool = False

    @classmethod
    def from_hikari(cls, interaction: hikari.ModalInteraction) -> ModalInteraction:
        """Create a new ModalInteraction object from a hikari.ModalInteraction. This should be rarely used.

        Parameters
        ----------
        interaction : hikari.ModalInteraction
            The ModalInteraction this object should be created from.

        Returns
        -------
        ModalInteraction
            The created interaction object.
        """
        return cls(
            channel_id=interaction.channel_id,
            components=interaction.components,
            custom_id=interaction.custom_id,
            guild_id=interaction.guild_id,
            message=interaction.message,
            member=interaction.member,
            user=interaction.user,
            locale=interaction.locale,
            guild_locale=interaction.guild_locale,
            app=interaction.app,
            id=interaction.id,
            application_id=interaction.application_id,
            type=interaction.type,
            token=interaction.token,
            version=interaction.version,
        )

    @functools.wraps(hikari.ComponentInteraction.create_initial_response)
    async def create_initial_response(self, *args: t.Any, **kwargs: t.Any) -> None:
        await super().create_initial_response(*args, **kwargs)
        self._issued_response = True


InteractionT = t.TypeVar("InteractionT", "ComponentInteraction", "ModalInteraction")


class InteractionResponse:
    """
    Represents a response to an interaction, allows for standardized handling of responses.
    This class is not meant to be directly instantiated, and is instead returned by :obj:`miru.context.Context`.
    """

    def __init__(self, context: Context[InteractionT], message: t.Optional[hikari.Message] = None) -> None:
        self._context: Context[t.Any] = context  # Before you ask why it is Any, because mypy is dumb
        self._message: t.Optional[hikari.Message] = message

    async def retrieve_message(self) -> hikari.Message:
        """Get or fetch the message created by this response.
        Initial responses need to be fetched, while followups will be provided directly.

        Returns
        -------
        hikari.Message
            The message created by this response.
        """
        if self._message:
            return self._message

        assert isinstance(self._context.interaction, (ComponentInteraction, ModalInteraction))
        return await self._context.interaction.fetch_initial_response()

    async def delete(self) -> None:
        """Delete the response issued to the interaction this object represents."""

        if self._message:
            await self._context.interaction.delete_message(self._message)

        await self._context.interaction.delete_initial_response()

    async def edit(
        self,
        content: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED,
        *,
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
        """A short-hand method to edit the message belonging to this response.

        Parameters
        ----------
        content : undefined.UndefinedOr[t.Any], optional
            The content of the message. Anything passed here will be cast to str.
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

        Returns
        -------
        InteractionResponse
            A proxy object representing the response to the interaction.
        """
        if self._message:
            message = await self._context.interaction.edit_message(
                self._message,
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
            return self._context._create_response(message)

        message = await self._context.interaction.edit_initial_response(
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
        return self._context._create_response()


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
