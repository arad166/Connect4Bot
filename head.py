import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

bot = commands.Bot(command_prefix='!',intents=discord.Intents.all())
    
BLACK = ":black_large_square:"
RED = ":red_circle:"
BLUE = ":blue_circle:"
#NUMBERS = [":zero:",":one:",":two:",":three:",":four:",":five:",":six:"]
NUMBERS = ['0️⃣','1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']
