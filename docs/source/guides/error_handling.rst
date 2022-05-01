==============
Error Handling
==============

Error handling within views is provided via the :obj:`miru.views.View.on_error` coroutine method.
When an error occurs in any item's callback or the timeout function, this function is called.

The first parameter is always the exception that occured, and if the the exception occured in an
item's callback, the item and the context are also passed. If you do not override this function,
it will, by default, print the exception and traceback to the console.

Example:
--------

::

    from typing import Optional

    import hikari
    import miru

    class ErrorView(miru.View):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            await ctx.respond("You clicked me!")

        # Create a button that raises an exception
        @miru.button(label="Error", style=hikari.ButtonStyle.DANGER)
        async def error_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            raise RuntimeError("I'm an error!")
        
        # Define our custom error-handler
        # Keep in mind that if you override the error-handler, tracebacks will no longer be printed
        # in the console.
        async def on_error(self, error: Exception, item: Optional[miru.Item] = None, ctx: Optional[miru.ViewContext] = None) -> None:
            if ctx is not None: # ctx is only passed if the error is raised in an item callback
                await ctx.respond(f"Oh no! This error occured: {error}")

    ...