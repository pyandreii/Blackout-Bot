@bot.command()
async def rebirth(ctx):
    user_id = ctx.author.id
    data = user_data.get(user_id)

    if not data or data.get("level", 0) < 30:
        await ctx.send("Trebuie să ai nivelul 30 pentru a face Rebirth.")
        return

    view = RebirthConfirmView(user_id)
    await ctx.send(f"{ctx.author.mention}, ești sigur că vrei să faci Rebirth? Nivelul și XP vor fi resetate.", view=view)

    # Așteaptă confirmarea sau anularea
    await view.wait()

    if view.value is None:
        # Timeout
        await ctx.send("Timpul pentru confirmare a expirat.")
