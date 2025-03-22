import discord
import openai
import asyncio
import random
import os
import re
from discord.ext import commands
from dotenv import load_dotenv  
from rapidfuzz import fuzz
import requests

import hashlib
import json

OPTIONAL_WORDS = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and"}
USED_QUESTIONS_FILE = "used_questions.json"

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
skip_question = False


@bot.command()
async def category(ctx, *, user_category: str):
    global category
    category = user_category
    await ctx.send(f"Category set to **{category}** ✅")

@bot.command()
async def skip(ctx):
    global skip_question
    skip_question = True
    await ctx.send("⏩ Skipping the current question... The correct answer will be revealed!")

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
    global skip_question
    skip_question = False  # Reset skip flag at the start

    await ctx.send(f"**Round {round_num}/{total_rounds}** 🎲\n**{question}** (Keep guessing until someone gets it right! Use `!skip` to skip this question. Type `!hint` for a multiple-choice hint.)")

    def check(m):
        return m.channel == ctx.channel

    correct_answer = clean_answer(answer)  # Normalize the correct answer

    hint_given = False  # Track if hint has been provided

    while True:
        if skip_question:
            await ctx.send(f"⏩ Question skipped! The correct answer was: **{answer}** ✅")
            return

        try:
            response = await bot.wait_for("message", timeout=60.0, check=check)
            user_answer = clean_answer(response.content)

            # If user asks for a hint
            if user_answer.lower() == "!hint" and not hint_given:
                hint_given = True
                options, correct_index = generate_hint_with_ai(answer, category)
                
                if options is None:
                    await ctx.send("⚠️ Could not generate hint. Try answering the question!")
                    continue

                hint_text = "\n".join(options)
                await ctx.send(f"🔍 **Hint:** Here are some options:\n\n{hint_text}\n\n(Type the correct answer!)")
                continue  # Don't check this input as an answer

            # Allow fuzzy matching or partial matching
            if is_fuzzy_match(user_answer, correct_answer) or is_partial_match(user_answer, correct_answer):
                scores[response.author] = scores.get(response.author, 0) + 1
                await ctx.send(f"✅ {response.author.mention} got it right!")
                return

            await ctx.send("❌ Incorrect! Keep guessing!")

        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! No one got the correct answer.\n✅ The correct answer was: **{answer}**")
            return

def get_recent_news():
    """Fetch recent news headlines to use for trivia questions."""
    try:
        NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Ensure you set up a news API key
        if not NEWS_API_KEY:
            print("Error: NEWS_API_KEY is not set.")
            return []
        
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        
        if "articles" in data:
            return [article["title"] for article in data["articles"][:5]]  # Fetch top 5 headlines
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []

def generate_trivia_questions(category, num_questions):
    """Generate trivia questions with OpenAI, ensuring they are unique and avoiding duplicates across sessions."""
    client = openai.Client()
    used_hashes = load_used_question_hashes()
    new_hashes = set()
    questions = []

    prompt_templates = [
        f"Generate {{count}} challenging and unique trivia questions in the category '{category}'. "
        "Avoid well-known or overly repeated questions. Use only real, verified information.\n\n"
        "Format them clearly like this:\n"
        "Question: What is the capital of France?\n"
        "Answer: Paris\n\n"
        "Keep answers short — one word or a short phrase (max 5 words). No multiple-choice.\n"
        "Vary the difficulty. Make some obscure, some tough. Keep it interesting.\n"
        "No fictional info. No repeated ideas.\n",

        f"Trivia time! Generate {{count}} high-quality, unique questions in '{category}'. "
        "All questions must be based on true and verified knowledge.\n"
        "Use this format:\n"
        "Question: Who painted the Mona Lisa?\n"
        "Answer: Leonardo da Vinci\n\n"
        "Answers must be short (under 5 words), not full sentences. No options or multiple choice.\n"
        "Include some hard and obscure questions — make it challenging!\n",

        f"Create {{count}} trivia questions in the category '{category}', with a mix of medium to hard difficulty. "
        "Focus on factual accuracy only. No fictional content.\n"
        "Use the format:\n"
        "Question: What is the capital of Japan?\n"
        "Answer: Tokyo\n\n"
        "Avoid repetition and ensure each question is distinct and concise (short answers only).\n"
        "Skip common knowledge. Go for specificity, detail, or lesser-known facts.\n",
    ]

    attempts = 0
    max_attempts = 6

    while len(questions) < num_questions and attempts < max_attempts:
        needed = num_questions - len(questions)
        prompt_template = random.choice(prompt_templates)
        prompt = prompt_template.format(count=needed + 2)  # Ask for extra to account for filtering
        temperature = round(random.uniform(0.78, 0.92), 2)

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a trivia master."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=temperature
            )

            if not response or not response.choices or not response.choices[0].message.content:
                print("ERROR: Empty or invalid OpenAI response")
                break

            output = response.choices[0].message.content.strip().split("\n\n")

            for item in output:
                if "Question:" in item and "Answer:" in item:
                    question = item.split("Question:")[1].split("Answer:")[0].strip()
                    answer = item.split("Answer:")[1].strip()
                    q_hash = hash_question(question)

                    if q_hash in used_hashes or q_hash in new_hashes:
                        continue  # Skip duplicates

                    questions.append((question, answer))
                    new_hashes.add(q_hash)

                    if len(questions) >= num_questions:
                        break

        except Exception as e:
            print(f"Error generating questions: {e}")
            break

        attempts += 1

    used_hashes.update(new_hashes)
    save_used_question_hashes(used_hashes)

    return questions if questions else [("Error generating questions!", "Unknown")]


##adding random category
@bot.command()
async def randomcategory(ctx):
    
    """Randomly selects a trivia category from a predefined list."""
    global category
    categories = [
        "World History", "Science & Technology", "Mythology", "Video Games", 
        "Anime & Manga", "Famous Inventions", "Geography", "Space & Astronomy", 
        "Pop Culture", "Music Trivia", "Animals & Nature", "Sports & Olympics", 
        "Movies & TV Shows", "Food & Beverages", "Art & Literature", 
        "Cryptocurrency & Finance", "Famous Scientists & Mathematicians", 
        "Marvel & DC Comics", "Board Games & Tabletop RPGs", "Famous Conspiracies"
    ]
    
    category = random.choice(categories)  # Pick a random category
    await ctx.send(f"🎲 Random Category Selected: **{category}** 🎲")

def generate_hint_with_ai(correct_answer, category):
    """Generate AI-powered multiple-choice options with similar incorrect answers."""
    client = openai.Client()

    prompt = (
        f"Generate ten incorrect but plausible answers for a trivia question in the category '{category}'.\n"
        f"The correct answer is: {correct_answer}\n"
        "Make the incorrect answers challenging and similar in style to the correct answer.\n"
        "Do NOT include numbers (like 1., 2., 3.) or dashes before the answers. Just give plain text answers.\n"
        "Format the answers as follows, one per line with no dashes or numbers:\n"
        "Apple\n"
        "Banana\n"
        "Cherry"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a trivia master."},
                      {"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.8
        )

        incorrect_answers = response.choices[0].message.content.strip().split("\n")
        incorrect_answers = [ans.strip() for ans in incorrect_answers if ans.strip()]

        # Ensure we only have three incorrect options
        incorrect_answers = incorrect_answers[:3]

        # Add correct answer and shuffle
        options = [correct_answer] + incorrect_answers
        random.shuffle(options)

        # Convert to multiple-choice format (without numbers)
        labeled_options = [f"{chr(97+i)}.) {option}" for i, option in enumerate(options)]
        correct_index = options.index(correct_answer)

        return labeled_options, correct_index

    except Exception as e:
        print(f"Error generating AI hints: {e}")
        return None, None
    
@bot.command()
async def quitgame(ctx):
    global game_active
    if not game_active:
        await ctx.send("No game is currently running! ❌")
        return

    game_active = False
    await ctx.send("🛑 The trivia game has been ended by the host! 🛑")

#Hashing previous used answers temporarily to a used file
def load_used_question_hashes():
    if os.path.exists(USED_QUESTIONS_FILE):
        with open(USED_QUESTIONS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_used_question_hashes(hashes):
    with open(USED_QUESTIONS_FILE, "w") as f:
        json.dump(list(hashes), f)

def hash_question(question):
    return hashlib.sha256(question.encode("utf-8")).hexdigest()


bot.run(DISCORD_BOT_TOKEN)
