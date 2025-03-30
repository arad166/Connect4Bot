from head import *
import game

@bot.event
async def on_ready():
    print("on_ready")
    print(discord.__version__)

@bot.command()
async def play(ctx):
    await game.playGame(ctx)
    return

bot.run(TOKEN)