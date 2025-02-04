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
word_history = []  # Track words in order
current_player = None
turn_timeout = 20

word_list = [
    # 🌿 Nature & Environment
    "ocean", "mountain", "river", "volcano", "desert", "forest", "glacier", "waterfall", "tornado", "sunset", 
    "earthquake", "canyon", "island", "tsunami", "reef",

    # 🌌 Space & Astronomy
    "eclipse", "galaxy", "meteor", "nebula", "comet", "asteroid", "blackhole", "supernova", "satellite", "cosmos",
    "spaceship", "gravity", "orbit", "starlight", "telescope",

    # 😊 Emotions & Feelings
    "joy", "anger", "fear", "hope", "curiosity", "melancholy", "excitement", "anxiety", "serenity", "admiration",
    "confusion", "loneliness", "pride", "jealousy", "gratitude",

    # 🏃‍♂️ Actions & Verbs
    "dance", "run", "paint", "whisper", "jump", "climb", "shout", "sprint", "crawl", "dive",
    "write", "laugh", "sing", "breathe", "drift",

    # 🎸 Objects & Everyday Items
    "book", "guitar", "camera", "puzzle", "robot", "microscope", "mirror", "umbrella", "backpack", "clock",
    "lantern", "suitcase", "headphones", "notebook", "compass",

    # 📚 Concepts & Ideas
    "history", "science", "philosophy", "myth", "dream", "memory", "destiny", "paradox", "illusion", "imagination",
    "balance", "infinity", "wisdom", "creativity", "justice",

    # 🍕 Food & Drinks
    "chocolate", "pizza", "sushi", "coffee", "cheese", "pasta", "popcorn", "lemon", "honey", "coconut",
    "carrot", "blueberry", "mango", "watermelon", "croissant",

    # 🏰 Fantasy & Mythology
    "dragon", "wizard", "castle", "treasure", "sword", "phoenix", "fairy", "magic", "spell", "goblin",
    "unicorn", "riddle", "sorcery", "knight", "portal",

    # 🔬 Science & Technology
    "electric", "magnetic", "laser", "neon", "quantum", "android", "hologram", "satellite", "circuit", "algorithm",
    "DNA", "radiation", "nanotechnology", "biotech", "gravity",

    # 🌍 Geography & Places
    "city", "village", "jungle", "temple", "bridge", "harbor", "pyramid", "oasis", "fountain", "lighthouse",
    "cathedral", "tundra", "cave", "skyscraper", "cemetery",

    # 🎭 Entertainment & Pop Culture
    "theater", "circus", "comedy", "mystery", "detective", "cartoon", "superhero", "villain", "adventure", "illusion",
    "concert", "festival", "movie", "painting", "animation",

    # 🚀 Travel & Transportation
    "airplane", "bicycle", "subway", "motorcycle", "spaceship", "hotairballoon", "yacht", "skateboard", "train", "zeppelin",
    "carriage", "hoverboard", "cruise", "rocket", "gondola",

    # 💎 Luxury & Lifestyle
    "diamond", "silk", "perfume", "caviar", "champagne", "mansion", "fountain", "royalty", "throne", "gold",
    "artwork", "boutique", "jewelry", "orchestra", "tuxedo",

    # ⏳ Time & Seasons
    "sunrise", "midnight", "autumn", "spring", "twilight", "weekend", "nostalgia", "yesterday", "millennium", "epoch",
    "newyear", "solstice", "dawn", "afternoon", "century"
]

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

@bot.command()
async def startgame(ctx):
    global game_active, players, current_player
    if game_active:
        await ctx.send("A game is already in progress!")
        return
    
    if len(players) < 2:
        await ctx.send("Need at least 2 players to start the game! Use !signup to join. If you want to play alone, use !startgamealone.")
        return

    # Initialize game state
    game_active = True
    word_history.clear()
    current_player = random.choice(players)
    starting_word = get_random_word()
    word_history.append(starting_word)
    
    await ctx.send(f"**Word Association Game Started!** 🎉\nFirst word: **{starting_word}**\n{current_player.mention}, it's your turn!")
    
    await player_turn(ctx, current_player)

async def player_turn(ctx, player):
    global current_player

    if player not in players:
        return  

    def check(m):
        return m.author == player and m.channel == ctx.channel  

    try:
        msg = await bot.wait_for("message", timeout=turn_timeout, check=check)
        word = msg.content.lower()
        last_word = word_history[-1]  
        
        await ctx.send(f"Checking word similarity. Please wait!")
        similarity_score = nltkhelper.get_similarity_score(last_word, word)
        is_related = similarity_score >= 0.5  # Set a threshold for relation
        
        if word in word_history:  
            await ctx.send(f"❌ {player.mention}, that word has already been used! You're eliminated!")
            players.remove(player)
        elif not is_related:  
            await ctx.send(f"❌ {player.mention}, {word} is NOT related to {last_word}! (Similarity Score: {similarity_score:.2f}) You're eliminated!")
            players.remove(player)
        else:
            word_history.append(word)  
            current_player = get_next_player()
            if current_player:
                await ctx.send(f"✅ {word} accepted! (Similarity Score: {similarity_score:.2f}) {current_player.mention}, your turn!")
                await player_turn(ctx, current_player)
                return
    except asyncio.TimeoutError:
        await ctx.send(f"⏳ {player.mention} took too long! Eliminated!")
        players.remove(player)

def get_next_player():
    """ Get the next player in the rotation, skipping eliminated players. """
    if not players:
        return None  # No players left

    if len(players) == 1:
        return players[0]  # Only one player left, they win

    if current_player not in players:
        return players[0]  # Pick the first player if the current player was removed

    current_index = players.index(current_player)
    return players[(current_index + 1) % len(players)]

def reset_game():
    """ Reset game state """
    global game_active, players, word_history, current_player
    game_active = False
    if len(players) > 1:
        players.clear()  # Don't clear if a single player wins
    word_history.clear()
    current_player = None

bot.run(TOKEN)
