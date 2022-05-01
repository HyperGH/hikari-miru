import hikari
import miru


class ModalView(miru.View):

    # Create a new button that will invoke our modal
    @miru.button(label="Click me!", style=hikari.ButtonStyle.PRIMARY)
    async def modal_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        modal = MyModal("Example Title")
        modal.add_item(miru.TextInput(label="Example Label", placeholder="Type something!", required=True))
        modal.add_item(miru.TextInput(label="Paragraph example", value="Pre-filled content!", style=hikari.TextInputStyle.PARAGRAPH))
        # You may also use Modal.send() if not working withhin a miru context. (e.g. slash commands)
        # Keep in mind that modals can only be sent in response to interactions.
        await ctx.respond_with_modal(modal)


class MyModal(miru.Modal):

    # The callback function is called after the user hits 'Submit'
    async def callback(self, ctx: miru.ModalContext) -> None:
        # ModalContext.values is a mapping of {TextInput: value}
        values = [value for value in ctx.values.values()]
        await ctx.respond(f"Received the following input: ```{' | '.join(values)}```")
    # You may also access the values the modal holds by using Modal.values


bot = hikari.GatewayBot("...")
miru.load(bot)

@bot.listen()
async def modals(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = ModalView()
        message = await event.message.respond(
            "This is a basic component menu built with miru!", components=view
        )
        view.start(message)


bot.run()