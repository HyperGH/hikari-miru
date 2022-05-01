Getting Started
===============

Installation
------------

miru can be installed using pip via the following command:

``$ python3 -m pip install -U hikari-miru``

.. note::
    To check if miru installed correctly, please run the following command:
    ``$ python3 -m miru``
    This should output version and basic system information.

First steps
-----------
This is what a basic component menu looks like with miru:

::

    import hikari
    import miru

    # Define a new custom View that contains 3 items
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


    # Create an instance of our bot. This doesn't need to be a GatewayBot,
    # but needs to implement RESTAware, CacheAware, and EventManagerAware.
    bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
    miru.load(bot) # Start miru
    # This function must be called on startup, otherwise you cannot instantiate views


    @bot.listen() # Create a hikari message listener
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


    bot.run() # Run the bot

If you run this code, you should see some basic logging information, and your bot will be online!
Typing ``miru`` in any channel should make the bot send the component menu defined above!

Subclassing
-----------

A more advanced way to use miru is to create our own custom classes of buttons, select menus, and more.
This allows us to customize to a great degree their behaviour, pass variables dynamically, add or remove
items on the fly, and more!

Below you can see such an example:

::
    
    import hikari
    import miru

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


    bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
    miru.load(bot)


    @bot.listen()
    async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

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

Running this code and typing ``miru`` in a channel the bot can see should similarly yield a component menu.
The benefits of this approach are that you can define custom methods for your individual components,
and create template items for re-use later, reducing the need to paste the same code over and over again.