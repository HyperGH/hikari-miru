import hikari
import miru
from miru.ext import nav


class MyNavButton(nav.NavButton):
    # This is how you can create your own navigator button
    # The extension also comes with the following nav buttons built-in:
    #
    # FirstButton - Goes to the first page
    # PrevButton - Goes to previous page
    # IndicatorButton - Indicates current page number
    # StopButton - Stops the navigator session and disables all buttons
    # NextButton - Goes to next page
    # LastButton - Goes to the last page

    async def callback(self, ctx: miru.ViewContext) -> None:
        await ctx.respond("You clicked me!", flags=hikari.MessageFlag.EPHEMERAL)

    async def before_page_change(self) -> None:
        # This function is called before the new page is sent by
        # NavigatorView.send_page()
        self.label = f"Page: {self.view.current_page+1}"


bot = hikari.GatewayBot("...")
miru.load(bot)


@bot.listen()
async def navigator(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("mirunav"):
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
        pages = ["I'm the first page!", embed, "I'm the last page!"]
        # Define our navigator and pass in our list of pages
        navigator = nav.NavigatorView(pages=pages)
        # You may also pass an interaction object to this function
        await navigator.send(event.channel_id)

    elif event.content.startswith("mirucustom"):
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
        pages = ["I'm a customized navigator!", embed, "I'm the last page!"]
        # Define our custom buttons for this navigator
        # All navigator buttons MUST subclass NavButton
        buttons = [nav.PrevButton(), nav.StopButton(), nav.NextButton(), MyNavButton(label="Page: 1", row=1)]
        # Pass our list of NavButton to the navigator
        navigator = nav.NavigatorView(pages=pages, buttons=buttons)

        await navigator.send(event.channel_id)


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

