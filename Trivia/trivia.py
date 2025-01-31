import discord
import openai
import asyncio
import random
import os
from discord.ext import commands
from dotenv import load_dotenv  # Import dotenv package

# Load environment variables from .env file
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API Key
openai.api_key = OPENAI_API_KEY

# Set up bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Game state variables
category = None
current_question = None
correct_answer = None
game_active = False

### 📌 Command: Choose Category ###
@bot.command()
async def category(ctx, *, user_category: str):
    """Users can choose a trivia category."""
    global category
    category = user_category
    await ctx.send(f"Category set to **{category}** ✅")

### 📌 Command: Start Game ###
@bot.command()
async def startgame(ctx):
    """Starts a new trivia game (everyone can participate)."""
    global game_active

    if game_active:
        await ctx.send("A game is already in progress! ⏳")
        return

    if not category:
        await ctx.send("No category selected! Use `!category [name]` to set one.")
        return

    game_active = True
    await ctx.send(f"🎮 Trivia game is starting! Category: **{category}** 🎮")

    scores = {}  # Store scores for all participants

    for round_num in range(1, 11):  # 10 rounds
        await ask_question(ctx, round_num, scores)

    # Announce winner
    game_active = False
    if scores:
        winner = max(scores, key=scores.get)
        await ctx.send(f"🏆 Trivia game over! Winner: **{winner.name}** with **{scores[winner]} points!**")
    else:
        await ctx.send("🏆 Trivia game over! No one answered any questions. 😢")

async def ask_question(ctx, round_num, scores):
    """Fetch AI-generated question and check answers from anyone in chat."""
    global current_question, correct_answer

    # Generate question using OpenAI
    question, answer = generate_trivia_question(category)
    current_question = question
    correct_answer = answer.lower()

    await ctx.send(f"**Round {round_num}/10** 🎲\n**{current_question}** (You have 60 seconds!)")

    def check(m):
        return m.channel == ctx.channel  # Accept answers from anyone in the channel

    try:
        response = await bot.wait_for("message", timeout=60.0, check=check)
        if response.content.lower() == correct_answer:
            scores[response.author] = scores.get(response.author, 0) + 1
            await ctx.send(f"✅ {response.author.mention} got it right! The answer was **{correct_answer}**.")
        else:
            await ctx.send(f"❌ Incorrect! The correct answer was **{correct_answer}**.")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Time's up! The correct answer was **{correct_answer}**.")

def generate_trivia_question(category):
    """Generates a trivia question using OpenAI's newer API format."""
    prompt = f"Generate a multiple-choice trivia question in the category '{category}'. Format as 'Question: ... Answer: ...'"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Updated model
        messages=[{"role": "system", "content": "You are a trivia master."},
                  {"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7
    )

    output = response["choices"][0]["message"]["content"].strip()
    
    if "Question:" in output and "Answer:" in output:
        question = output.split("Question:")[1].split("Answer:")[0].strip()
        answer = output.split("Answer:")[1].strip()
        return question, answer
    else:
        return "Error generating question!", "Unknown"

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
