import discord
import asyncio
import random
import os
from discord.ext import commands
from dotenv import load_dotenv
import nltkhelper

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

game_active = False
players = []
used_words = set()
current_player = None
turn_timeout = 20

word_list = ["apple", "banana", "cherry", "dog", "elephant", "fire", "grass", "hat", "ice", "jungle"]

def get_random_word():
    return random.choice(word_list)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def signup(ctx):
    global players
    if ctx.author in players:
        await ctx.send(f"{ctx.author.mention}, you are already signed up!")
    else:
        players.append(ctx.author)
        await ctx.send(f"{ctx.author.mention} has signed up to play!")
@bot.command()
async def hello(ctx):
     await ctx.send('Hello! I am your bot.')

##Start Game, assign inital configuration parameters 
@bot.command()
async def startgame(ctx):
    global game_active, players, used_words, current_player
    if game_active:
        await ctx.send("A game is already in progress!")
        return
    
    if len(players) < 2:
        await ctx.send("Need at least 2 players to start the game! Use !signup to join. If you wanna play alone use !startgamealone")
        return
    #initial configurations and set up
    game_active = True
    used_words.clear()
    current_player = random.choice(players)
    starting_word = get_random_word()
    used_words.add(starting_word)
    
    await ctx.send(f"**Word Association Game Started!** 🎉\nFirst word: **{starting_word}**\n{current_player.mention}, it's your turn!")
    
    await player_turn(ctx, current_player) #goes to player turn to start

@bot.command()
async def startgamealone(ctx):
    global game_active, players, used_words, current_player
    if len(players) < 1:
        await ctx.send("Need at least 1 players to start the game alone! Use !signup to join.")
        return
    if game_active:
        await ctx.send("A game is already in progress!")
        return
    await ctx.send("I guess you have no friends")
#    if len(players) < 2:
#        await ctx.send("Need at least 2 players to start the game! Use !signup to join.")
#        return

    game_active = True
    used_words.clear()
    current_player = random.choice(players)
    starting_word = get_random_word()
    used_words.add(starting_word)
    
    await ctx.send(f"**Word Association Game Started!** 🎉\nFirst word: **{starting_word}**\n{current_player.mention}, it's your turn!")
    
    await player_turn(ctx, current_player)


async def player_turn(ctx, player):
    global current_player
    
    def check(m):
        return m.author == player and m.channel == ctx.channel #check if the player is here
    
    try:
        msg = await bot.wait_for("message", timeout=turn_timeout, check=check) #wait turn_timeout long for a message
        word = msg.content.lower()
        
        if word in used_words: #checks if that word is in the set. 
            await ctx.send(f"❌ {player.mention}, that word has already been used! You're eliminated!")
            players.remove(player)
        else:
            used_words.add(word)
            current_player = get_next_player()
            if current_player:
                await ctx.send(f"✅ {word} accepted! {current_player.mention}, your turn!")
                await player_turn(ctx, current_player)
            elif not nltkhelper.is_word_related(list(used_words)[-1], word):  # Check if related
                await ctx.send(f"❌ {player.mention}, {word} is NOT related to {list(used_words)[-1]}! You're eliminated!")
                players.remove(player)
            else:
                await ctx.send(f"🎉 **Game Over! {player.mention} wins!** 🎉")
                reset_game()
    except asyncio.TimeoutError:
        await ctx.send(f"⏳ {player.mention} took too long! Eliminated!")
        players.remove(player)
        if len(players) > 1:
            current_player = get_next_player()
            await ctx.send(f"Next player: {current_player.mention}")
            await player_turn(ctx, current_player)
        else:
            await ctx.send(f"🎉 **Game Over! {players[0].mention} wins!** 🎉")
            reset_game()

def get_next_player():
    if players:
        return players[0] if len(players) == 1 else players[(players.index(current_player) + 1) % len(players)]
    return None

def reset_game():
    global game_active, players, used_words, current_player
    game_active = False
    players.clear()
    used_words.clear()
    current_player = None

bot.run(TOKEN)
