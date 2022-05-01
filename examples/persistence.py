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

import hikari
import miru

# If you want your components to work and persist after an application restart,
# you have to make them persistent. There are two conditions to this:
# - The view's timeout must explicitly be set to None
# - All components MUST have a unique custom_id
# It is recommended to tie custom_ids to some variable to ensure they do not match,
# to avoid conflicts. (e.g. a UUID stored in a database), but that is outside the
# scope of this example.

# Tip: It is recommended to subclass components to have the ability to pass
# custom_id variables. See the subclassed example on how to do this.

# Tip 2: To check if your view can be persistent or not, use the View.is_persistent
# boolean property.


class Persistence(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)  # Setting timeout to None

    @miru.button(label="Button 1", custom_id="my_unique_custom_id_1")
    async def button_one(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.respond("You pressed button 1.")

    @miru.button(label="Button 2", custom_id="my_unique_custom_id_2")
    async def button_two(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.respond("You pressed button 2.")


bot = hikari.GatewayBot("...")
miru.load(bot)


@bot.listen()
async def startup_views(event: hikari.StartedEvent) -> None:
    # You must reinstantiate the view in the same state it was before shutdown (e.g. same custom_ids)
    view = Persistence()
    # Restart the listener for the view, if you do not pass a message_id, this will handle
    # all interactions for every view of type 'Persistence'.
    # If you pass a message_id to start_listener(), it will only handle interactions for that message,
    # and will be considered a bound persistent view.
    view.start_listener()


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = Persistence()
        await event.message.respond(
            "This is a persistent component menu, and works after bot restarts!",
             components=view,
        )
        # Unbound views do not need to be started, as starting one listener will handle all views of the same type.
        # Bound views (ones that are bound to a message) must be started here via view.start().


bot.run()
