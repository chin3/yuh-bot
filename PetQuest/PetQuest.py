import discord
from discord.ext import commands
import os
from dotenv import load_dotenv  # Import dotenv package
from datetime import datetime
from PetDb import Database
import random
from Pet import ElementalType, SpeciesType

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# Set up bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
#database
db = Database()
#Events
#@bot.event
#async def on_ready():
#    print(f"✅ Bot is online! Logged in as {bot.user}")

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

    user = db.get_user(discord_id)
    pets = db.get_alive_pets_by_user(discord_id)

    if not user:
        await ctx.send("You need to sign up first! Use `!signup`.")
    elif len(pets) != 0:  # Only allows 1 pet for now
        await ctx.send("PET COUNT - " + str(len(pets)))
        await ctx.send("You already have a pet!")
    else:
        # Randomly select species and elemental type
        species = random.choice(list(SpeciesType))
        elemental_type = random.choice(list(ElementalType))

        await ctx.send(
            f"✨ A {species.name} with {elemental_type.name} element has been hatched! "
            "What would you like to name your new pet? Reply with `!name <your pet's name>`. Expires in 2 Minutes"
        )

        def check(m):
            return m.author == ctx.author and m.content.startswith("!name ")

        try:
            msg = await bot.wait_for("message", check=check, timeout=120.0)
            pet_name = msg.content[6:].strip()

            if not pet_name:
                pet_name = "Nathan"  # Default name if empty

            db.add_pet(discord_id, pet_name, species.value, 1, elemental_type.value)  # Save pet to DB
            await ctx.send(f"🎉 Congrats! Your {elemental_type} {species.name} named **{pet_name}** has been hatched!")
        except TimeoutError:
            await ctx.send("⏳ You took too long to name your pet! Try again with `!hatch`.")

@bot.command()
async def getpets(ctx):
    discord_id = ctx.author.id
    pets = db.get_pet(discord_id)
    for pet in pets:
        await ctx.send(pet)
#command to feed pet. 

@bot.command()
async def feed(ctx):
    """Feed the pet to extend lifespan and reduce hunger"""
    discord_id = ctx.author.id
    pets = db.get_pet(discord_id)

    if not pets:
        await ctx.send("You don't have a pet to feed!")
        return

    pet = pets[0]  # Assuming one pet for now
    result = db.feed_pet(discord_id, pet.pet_id)
    await ctx.send(result)

@bot.command()
async def petstatus(ctx):
    """Check pet hunger and lifespan"""
    discord_id = ctx.author.id
    pets = db.get_pet(discord_id)
    if not pets:
        await ctx.send("You don't have a pet.")
        return

    response = []
    for pet in pets:
        pet.update_lifespan()
        response.append(f"🍼 {pet.name} | Hunger: {pet.hunger} | Lifespan: {pet.LIFESPAN} hours or {pet.LIFESPAN/24} days")

    await ctx.send("\n".join(response))
 

#TASKS and RUNNING JOBS
import asyncio

async def pet_decay_task():
    """Runs every hour to apply decay"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        users = db.cursor.execute("SELECT user_id FROM user").fetchall()
        for user in users:
            db.update_pet_decay(user[0])
        await asyncio.sleep(3600)  # Run every hour

@bot.event
async def on_ready():
    """Start the decay task when the bot is ready"""
    print(f"✅ Bot is online! Logged in as {bot.user}")
    asyncio.create_task(pet_decay_task())  # Start the task safely

bot.run(DISCORD_BOT_TOKEN) 