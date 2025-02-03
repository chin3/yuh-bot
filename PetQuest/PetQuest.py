import discord
from discord.ext import commands
import os
from dotenv import load_dotenv  # Import dotenv package
from datetime import datetime
from PetDb import Database

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# Set up bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
#database
db = Database()
#Events
@bot.event
async def on_ready():
    print(f"✅ Bot is online! Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Error: {error}")
    print(f"Error: {error}")
#Commands
@bot.command()
async def hello(ctx):
     await ctx.send('Hello! I am your bot.')


@bot.command()
async def signup(ctx):
    discord_id = ctx.author.id
    if db.add_user(discord_id): 
       await ctx.send("You've signed up! Use `!hatch` to get your first pet!")
    else:
        await ctx.send("You're already signed up!")

@bot.command()
async def hatch(ctx):
    """Allows a user to hatch a pet if they don't have one"""
    discord_id = ctx.author.id

    user =  db.get_user(discord_id)
    pets = db.get_alive_pets_by_user(discord_id)
    if not user:
        await ctx.send("You need to sign up first! Use `!signup`.")
    elif len(pets) !=0: #Right now only allows 1 pet, modify this later if you want to allow users to have muliple pets
        await ctx.send("PET COUNT - " + str(len(pets)))
        await ctx.send("You already have a pet!")
    else:
        pet_name = "Fluffy"  # You can randomize pet names
        db.add_pet(discord_id, pet_name, 0, 1) #user_id + name of pet, + Type_id + Is_alive
        #Think of attributes for maintaince for pet and stats. 
        await ctx.send(f"🎉 Congrats! You've hatched a pet named **{pet_name}**!")

@bot.command()
async def getpets(ctx):
    discord_id = ctx.author.id
    pets = db.get_pet(discord_id)
    for pet in pets:
        await ctx.send(pet)

 

bot.run(DISCORD_BOT_TOKEN) 