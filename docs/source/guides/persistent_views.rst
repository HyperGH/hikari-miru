Persistent Views
================

You may have noticed that after an application restart, your views will no longer work,
even if the timeout did not expire. The solution to this problem are persistent views.

Persistent views are views that persist and keep functioning, even after an application restart.

Two conditions need to be met in order for a view to be considered persistent:
- The view must have a timeout of ``None``.
- All items attached to the view must have a ``custom_id`` provided to it.

There are two variants of them, bound and unbound. Let's explore the differences between the two.

.. warning::
    :obj:`miru.views.View.message` will in all cases be ``None`` for persistent views.

Unbound
-------

Unbound persistent views are the simpler of the two, they provide simple stateless logic, and are
not bound to any one message. They are best suited for views and items that are expected to return
the same results regardless of the context.

The limitations for this way of handling persistent views are that you cannot edit the view during runtime,
as unbound views have no concept of what message they are attached to.

::

    class Persistence(miru.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)  # Setting timeout to None

        # Providing custom IDs to all items
        @miru.button(label="Button 1", custom_id="my_unique_custom_id_1")
        async def button_one(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            await ctx.respond("You pressed button 1.")

        @miru.button(label="Button 2", custom_id="my_unique_custom_id_2")
        async def button_two(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            await ctx.respond("You pressed button 2.")


    bot = hikari.GatewayBot("...")
    miru.load(bot)

    # Handle the restarting of our views on application startup
    @bot.listen()
    async def startup_views(event: hikari.StartedEvent) -> None:
        # You must reinstantiate the view in the same state it was before shutdown (e.g. same custom_ids)
        view = Persistence()
        # Restart the listener for the view after application startup
        view.start_listener()


    @bot.listen()
    async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

        # Do not process messages from bots or empty messages
        if event.is_bot or not event.content:
            return

        if event.content.startswith("miru"):
            view = Persistence()
            message = await event.message.respond(
                "This is a persistent view, and works after bot restarts!",
                components=view,
            )

            # You do not need to start unbound persistent views, as a single listener handles
            # all views of the same type.


    bot.run()

Try restarting the bot after sending your view, your buttons should keep working! 

.. note::
    In practice, you want to most likely use some form of database to store your custom_ids, 
    and load the values from it on application startup, to avoid conflicts with multiple views using the same custom_id.

Bound
-----

Bound views are different in the sense that they are bound to a specific message instead of globally handling
interactions for every view of the same type. To create a bound view, instead of an unbound one,
simply pass a message ID to ``start_listener()``. This also allows for the view to be edited during runtime.

::

    class Persistence(miru.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)  # Setting timeout to None

        # Providing custom IDs to all items
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

        view = Persistence()

        # For this example, you should store your message IDs in a database
        # along with your custom IDs.
        message_id = example_database_fetching_the_id()

        # Restart the listener for the view after application startup
        # This view will only accept interactions coming from this specific message.
        view.start_listener(message_id)


    @bot.listen()
    async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

        # Do not process messages from bots or empty messages
        if event.is_bot or not event.content:
            return

        if event.content.startswith("miru"):
            view = Persistence()
            message = await event.message.respond(
                "This is a persistent component menu, and works after bot restarts!",
                components=view,
            )
            # Bound persistent views need to be started for every message.
            view.start(message)


    bot.run()
