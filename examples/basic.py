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

# This is a basic example demonstrating how to create a simple component-based menu.
# This example uses decorators to create the components, if you want to use variables
# instead of static values for the component properties, check out the subclassed example.


class BasicView(miru.View):

    # Define a new Select menu with two options
    @miru.select(
        placeholder="Select me!", 
        options=[
            miru.SelectOption(label="Option 1"), 
            miru.SelectOption(label="Option 2"),
        ],
    )
    async def basic_select(self, select: miru.Select, ctx: miru.ViewContext) -> None:
        await ctx.respond(f"You've chosen {select.values[0]}!")

    # Define a new Button with the Style of success (Green)
    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.respond("You clicked me!")

    # Define a new Button that when pressed will stop the view & invalidate all the buttons in this view
    @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
    async def stop_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.stop()  # Called to stop the view


bot = hikari.GatewayBot("...")
miru.load(bot) # Start miru


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = BasicView()  # Create an instance of our newly created BasicView
        # Attach the components defined in the view to our message
        message = await event.message.respond(
            "This is a basic component menu built with miru!", components=view
        )

        view.start(message)  # Start listening for interactions

        await view.wait()  # Wait until the view is stopped or times out

        print("View stopped or timed out!")


bot.run()