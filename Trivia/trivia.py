import discord
import openai
import asyncio
import random
import os
import re
from discord.ext import commands
from dotenv import load_dotenv  
from rapidfuzz import fuzz

OPTIONAL_WORDS = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and"}


load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

category = None
questions = []
game_active = False

@bot.command()
async def category(ctx, *, user_category: str):
    global category
    category = user_category
    await ctx.send(f"Category set to **{category}** ✅")

@bot.command()
async def startgame(ctx, num_questions: int = 10):
    global game_active, questions

    if game_active:
        await ctx.send("A game is already in progress! ⏳")
        return

    if not category:
        await ctx.send("No category selected! Use `!category [name]` to set one.")
        return

    game_active = True
    await ctx.send(f"🎮 Trivia game is starting! Category: **{category}** with {num_questions} questions 🎮")
    
    questions = generate_trivia_questions(category, num_questions)
    if not questions or all(q[0] == "Error generating questions!" for q in questions):
        await ctx.send("⚠️ Failed to generate questions. Try again later or with a different category.")
        game_active = False
        return
    
    scores = {}
    for round_num, (question, answer) in enumerate(questions, start=1):
        await ask_question(ctx, round_num, num_questions, question, answer, scores)

    game_active = False
    if scores:
        winner = max(scores, key=scores.get)
        await ctx.send(f"🏆 Trivia game over! Winner: **{winner.name}** with **{scores[winner]} points!**")
    else:
        await ctx.send("🏆 Trivia game over! No one answered any questions. 😢")

def clean_answer(answer):
    """Lowercases, strips whitespace, and removes optional words."""
    return " ".join(word for word in answer.lower().strip().split() if word not in OPTIONAL_WORDS)

def is_fuzzy_match(user_answer, correct_answer, threshold=80):
    """Checks if the user answer is a close match using fuzzy logic."""
    return fuzz.ratio(user_answer, correct_answer) >= threshold

def is_partial_match(user_answer, correct_answer):
    """Allows partial matches if at least one word from the correct answer is in the user's answer."""
    correct_parts = set(correct_answer.split())
    user_parts = set(user_answer.split())

    return len(correct_parts & user_parts) > 0  # At least one word must match



async def ask_question(ctx, round_num, total_rounds, question, answer, scores):
    await ctx.send(f"**Round {round_num}/{total_rounds}** 🎲\n**{question}** (Keep guessing until someone gets it right!)")

    def check(m):
        return m.channel == ctx.channel

    correct_answer = clean_answer(answer)  # Normalize the correct answer

    while True:
        try:
            response = await bot.wait_for("message", timeout=60.0, check=check)
            user_answer = clean_answer(response.content)

            # Allow fuzzy matching or partial matching
            if is_fuzzy_match(user_answer, correct_answer) or is_partial_match(user_answer, correct_answer):
                scores[response.author] = scores.get(response.author, 0) + 1
                await ctx.send(f"✅ {response.author.mention} got it right!")
                return

            await ctx.send("❌ Incorrect! Keep guessing!")

        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! No one got the correct answer.\n✅ The correct answer was: **{answer}**")
            return

def generate_trivia_questions(category, num_questions):
    client = openai.Client()
    prompt = (
        f"Generate {num_questions} unique and challenging trivia questions in the category '{category}'. "
        "Format them clearly as follows:\n\n"
        "For standard questions:\n"
        "Question: What is the capital of France?\n"
        "Answer: Paris\n\n"
        "For multiple-choice questions, include four answer choices (a, b, c, d) and specify the correct one:\n"
        "Question: Which of these is a fruit?\n"
        "Options: a.) Apple, b.) Carrot, c.) Broccoli, d.) Onion\n"
        "Correct Answer: a.) Apple\n\n"
        "Ensure questions vary in difficulty and are factually accurate.\n"
        "Include a mix of easy, medium, and hard questions.\n"
        "Ensure no two questions are too similar."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a trivia master."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        output = response.choices[0].message.content.strip().split("\n\n")
        questions = []
        for item in output:
            if "Question:" in item and "Answer:" in item:
                question = item.split("Question:")[1].split("Answer:")[0].strip()
                answer = item.split("Answer:")[1].strip()
                questions.append((question, answer))
        
        return questions if questions else [("Error generating questions!", "Unknown")]
    except Exception as e:
        print(f"Error generating questions: {e}")
        return [("Error generating questions!", "Unknown")]

bot.run(DISCORD_BOT_TOKEN)
