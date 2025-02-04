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

async def getPetSprite(ctx, speciesName):
    sprite_path = f"assets/species/{speciesName}.png"
    if not os.path.exists(sprite_path):
        await ctx.send(f"⚠️ Error: Pet sprite not found! Expected path: `{sprite_path}`")
        await ctx.send(f"DEBUG: Current working directory: {os.getcwd()}")
        return
    try:
        with open(sprite_path, "rb") as sprite_file:
            print(f"DEBUG: Looking for sprite at {sprite_path}")
            picture = discord.File(sprite_file)
            return picture

    except FileNotFoundError:
        await ctx.send("⚠️ Error: Pet sprite not found!")

@bot.command()
async def hatch(ctx):
    """Allows a user to hatch a pet if they don't have one"""
    discord_id = ctx.author.id

    user = db.get_user(discord_id)
    pets = db.get_alive_pets_by_user(discord_id)

    if not user:
        await ctx.send("You need to sign up first! Use `!signup`.")
    elif len(pets) != 0:  # Only allows 1 pet for now
        #await ctx.send("PET COUNT - " + str(len(pets)))
        await ctx.send("You already have a pet!")
    else:
        # Randomly select species and elemental type
        species = random.choice(list(SpeciesType))
        elemental_type = random.choice(list(ElementalType))

        await ctx.send(
            f"✨ A {species.name} with {elemental_type.name} element has been hatched! "
            "What would you like to name your new pet? Reply with `!name <your pet's name>`. Expires in 2 Minutes"
        )
        sprite = await getPetSprite(ctx, species.name.lower())
        await ctx.send(file=sprite)
        
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
async def release(ctx):
    """Allows a user to release (delete) their pet, setting is_alive to 0."""
    discord_id = ctx.author.id
    pets = db.get_pet(discord_id)

    if not pets:
        await ctx.send("You don't have a pet to release!")
        return

    pet = pets[0]  # Assuming one pet per user for now

    await ctx.send(
        f"⚠️ Are you sure you want to release **{pet.name}**? This action is irreversible! "
        "Type `!confirmrelease` within 30 seconds to proceed."
    )

    def check(m):
        return m.author == ctx.author and m.content.lower() == "!confirmrelease"

    try:
        await bot.wait_for("message", check=check, timeout=30.0)
        db.cursor.execute("UPDATE pet SET is_alive = 0 WHERE pet_id = ?", (pet.pet_id,))
        db.conn.commit()

        await ctx.send(f"💔 {pet.name} has been released and is no longer with you.")
    except TimeoutError:
        await ctx.send("⏳ Release action canceled. Your pet is safe!")

@bot.command()
async def getpets(ctx):
    discord_id = ctx.author.id
    pets = db.get_pet(discord_id)
    for pet in pets:
        await ctx.send(pet)
#command to feed pet. 

@bot.command()
async def feed(ctx):
    #right now automatically just gives the pet 20 food. Will eventually have it based on items in your inventory.
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

#BATTLE MECHANIC
battles = {}  # Dictionary to track active battles

@bot.command()
async def challenge(ctx, opponent: discord.Member):
    if opponent.id == ctx.author.id:
        await ctx.send("You can't challenge yourself!")
        return
    
    battles[ctx.author.id] = {
        "opponent": opponent.id,
        "accepted": False
    }
    
    print("Battles Dictionary:", battles)  # Debugging output
    await ctx.send(f"{opponent.mention}, you have been challenged to a pet battle by {ctx.author.mention}! Type `!accept` or `!reject`.")

@bot.command()
async def accept(ctx):
    for challenger_id, battle in battles.items():
        if battle["opponent"] == ctx.author.id:
            battles[challenger_id]["accepted"] = True
            await ctx.send(f"{ctx.author.mention} has accepted the battle! The fight begins now.")
            await start_battle(ctx, challenger_id, ctx.author.id)
            return
    
    await ctx.send("You haven't been challenged to a battle!")

@bot.command()
async def reject(ctx):
    for challenger_id, battle in battles.items():
        if battle["opponent"] == ctx.author.id:
            del battles[challenger_id]
            await ctx.send(f"{ctx.author.mention} has rejected the challenge. No battle today!")
            return
    
    await ctx.send("You haven't been challenged to a battle!")

async def start_battle(ctx, player1_id, player2_id):
    player1_pets = db.get_pet(player1_id)
    player2_pets = db.get_pet(player2_id)
    
    if not player1_pets or not player2_pets:
        await ctx.send("Both players must have a pet to battle!")
        return
    
    player1_pet = player1_pets[0]
    player2_pet = player2_pets[0]
    
    await ctx.send(f"⚔️ {player1_pet.name} (ATK: {player1_pet.ATK}, HP: {player1_pet.HP}) vs {player2_pet.name} (ATK: {player2_pet.ATK}, HP: {player2_pet.HP})! Choose your move: `!attack`, `!block`, or `!run`.")
    
    battles[player1_id] = {
        "opponent": player2_id,
        "pet": player1_pet,
        "turn": True
    }
    
    battles[player2_id] = {
        "opponent": player1_id,
        "pet": player2_pet,
        "turn": False
    }

@bot.command()
async def attack(ctx):
    print("Battles Dictionary before attack:", battles)  # Debugging
    
    for challenger_id, battle in battles.items():
        if ctx.author.id in (challenger_id, battle["opponent"]) and battle.get("accepted"):
            attacker_id = ctx.author.id
            defender_id = battle["opponent"] if attacker_id == challenger_id else challenger_id
            
            # Ensure both players have valid pets
            if defender_id not in battles or "pet" not in battles[defender_id]:
                await ctx.send("Error: Defender's pet not found.")
                return
            
            attacker_pet = battles[attacker_id]["pet"]
            defender_pet = battles[defender_id]["pet"]
            
            damage = random.randint(attacker_pet.ATK // 2, attacker_pet.ATK)
            defender_pet.HP -= damage
            
            await ctx.send(f"💥 {attacker_pet.name} attacks {defender_pet.name} for {damage} damage! {defender_pet.name} has {max(0, defender_pet.HP)} HP left.")
            
            if defender_pet.HP <= 0:
                await ctx.send(f"🏆 {attacker_pet.name} wins the battle!")
                del battles[challenger_id]
                return
            
            battles[challenger_id]["turn"] = not battles[challenger_id]["turn"]
            return
    
    await ctx.send("You are not in a battle!")

@bot.command()
async def block(ctx):
    await ctx.send(f"🛡️ {ctx.author.mention} chooses to block! Damage will be reduced next turn.")

@bot.command()
async def run(ctx):
    for challenger_id, battle in battles.items():
        if ctx.author.id in (challenger_id, battle["opponent"]):
            del battles[challenger_id]
            await ctx.send(f"{ctx.author.mention} ran away! The battle is over.")
            return
    
    await ctx.send("You are not in a battle!")

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