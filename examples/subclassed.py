import hikari
import miru

# This example demonstrates an alternative syntax to creating and adding new components.
# The benefits of this approach are more flexibility, reusability, and the ability to use
# variables in your component properties. (E.g. set a select menu's options based on user input)


class YesButton(miru.Button):
    def __init__(self) -> None:
        # Initialize our button with some pre-defined properties
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label="Yes")

    # The callback is the function that gets called when the button is pressed
    # If you are subclassing, you must use the name "callback" when defining it.
    async def callback(self, ctx: miru.ViewContext) -> None:
        # You can specify the ephemeral message flag to make your response ephemeral
        await ctx.respond("I'm sorry but this is unacceptable.", flags=hikari.MessageFlag.EPHEMERAL)
        # You can access the view an item is attached to by accessing it's view property
        self.view.answer = True
        self.view.stop()


class NoButton(miru.Button):
    # Let's leave our arguments dynamic this time, instead of hard-coding them
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def callback(self, ctx: miru.ViewContext) -> None:
        await ctx.respond("This is the only correct answer.", flags=hikari.MessageFlag.EPHEMERAL)
        self.view.answer = False
        self.view.stop()


bot = hikari.GatewayBot("...")
miru.load(bot)


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = miru.View()  # Create a new view
        view.add_item(YesButton())  # Add our custom buttons to it
        view.add_item(NoButton(style=hikari.ButtonStyle.DANGER, label="No"))  # Pass arguments to NoButton
        message = await event.message.respond("Do you put pineapple on your pizza?", components=view)

        view.start(message)  # Start listening for interactions

        await view.wait()  # Wait until the view is stopped or times out

        if hasattr(view, "answer"):  # Check if there is an answer
            print(f"Received an answer! It is: {view.answer}")
        else:
            print("Did not receive an answer in time!")


bot.run()

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
