[![PyPI](https://img.shields.io/pypi/v/hikari-miru)](https://pypi.org/project/hikari-miru)
[![Documentation Status](https://readthedocs.org/projects/hikari-miru/badge/?version=latest)](https://hikari-miru.readthedocs.io/en/latest/?badge=latest)

# hikari-miru
An optional component handler for [hikari](https://github.com/hikari-py/hikari), inspired by discord.py's views.

## Installation
To install miru, run the following command:
```sh
python3 -m pip install -U hikari-miru
```
To check if miru has successfully installed or not, run the following:
```sh
python3 -m miru
```

## Usage
```py
import hikari
import miru


class MyView(miru.View):

    @miru.button(label="Rock", emoji=chr(129704), style=hikari.ButtonStyle.PRIMARY)
    async def rock_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.respond("Paper!")

    @miru.button(label="Paper", emoji=chr(128220), style=hikari.ButtonStyle.PRIMARY)
    async def paper_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.respond("Scissors!")

    @miru.button(label="Scissors", emoji=chr(9986), style=hikari.ButtonStyle.PRIMARY)
    async def scissors_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.respond("Rock!")

    @miru.button(emoji=chr(9209), style=hikari.ButtonStyle.DANGER, row=2)
    async def stop_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.stop() # Stop listening for interactions


bot = hikari.GatewayBot(token="...")
miru.load(bot) # Load miru and attach it to the bot instance.


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = MyView(timeout=60)  # Create a new view
        message = await event.message.respond("Rock Paper Scissors!", components=view)
        view.start(message)  # Start listening for interactions
        await view.wait() # Wait until the view times out or gets stopped
        await event.message.respond("Thank you for playing!")

bot.run()
```
For more examples see [examples](https://github.com/HyperGH/hikari-miru/tree/main/examples), or refer to the [documentation](https://hikari-miru.readthedocs.io/en/latest/).

## Issues and support
For general usage help or questions, see the `#miru` channel in the [hikari discord](https://discord.gg/Jx4cNGG), if you have found a bug or have a feature request, feel free to [open an issue](https://github.com/HyperGH/hikari-miru/issues/new)!

## Contributing
If you wish to contribute, be sure to first enable the formatting pre-commit hook via `git config core.hooksPath .githooks`, then make your changes. Also make sure to run [nox](https://nox.thea.codes/en/stable/) before pushing your changes, and ensure all pipelines pass.
