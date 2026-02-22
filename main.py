# main.py
import discord
from discord.ext import commands
import asyncio
import random
import time
from flask import Flask
from threading import Thread

# ===== Keep-Alive Server =====
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Start Keep-Alive
keep_alive()

# ===== Giveaway Bot Setup =====
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="d!", intents=intents)
active_giveaways = {}

@bot.event
async def on_ready():
    print(f"🎉 Giveaway Bot Online as {bot.user}!")

# ===== Giveaway Command =====
@bot.command()
async def giveaway(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    inst_msg = await ctx.send(
        "🎉 Type giveaway details in ONE line (format):\n"
        "`duration_seconds, winners, prize, description`\n"
        "Example: `60, 1, 1M, Invite your friends`"
    )

    user_msg = await bot.wait_for("message", check=check)

    try:
        duration, winner_count, prize, description = [x.strip() for x in user_msg.content.split(",", 3)]
        duration = int(duration)
        winner_count = int(winner_count)
    except:
        await ctx.send("❌ Format galat. Dubara try karo (use commas).")
        return

    # Delete setup messages + command
    await asyncio.sleep(0.5)
    try:
        await inst_msg.delete()
        await user_msg.delete()
        await ctx.message.delete()
    except:
        pass

    end_time = int(time.time()) + duration

    embed = discord.Embed(
        title=f"🎉 {prize}",
        description=(
            f"{description}\n"
            f"Ends: <t:{end_time}:R> (<t:{end_time}:f>)\n"
            f"Hosted by: {ctx.author.mention}\n"
            f"Entries: **0**\n"
            f"Winners: **{winner_count}**"
        ),
        color=discord.Color.green()
    )

    gw_msg = await ctx.send(embed=embed)
    await gw_msg.add_reaction("🎉")

    active_giveaways[gw_msg.id] = {
        "channel_id": ctx.channel.id,
        "prize": prize,
        "winner_count": winner_count,
        "host_id": ctx.author.id,
        "end_time": end_time
    }

    # Update embed every 1 second
    while True:
        await asyncio.sleep(1)
        msg = await ctx.channel.fetch_message(gw_msg.id)
        users = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user)
        entries = len(users)

        embed.description = (
            f"{description}\n"
            f"Ends: <t:{end_time}:R> (<t:{end_time}:f>)\n"
            f"Hosted by: {ctx.author.mention}\n"
            f"Entries: **{entries}**\n"
            f"Winners: **{winner_count}**"
        )
        await gw_msg.edit(embed=embed)

        if time.time() >= end_time:
            break

    # End giveaway
    msg = await ctx.channel.fetch_message(gw_msg.id)
    users = []
    for reaction in msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)

    if not users:
        await ctx.channel.send("No participants 😢")
        return

    winners = random.sample(users, min(winner_count, len(users)))
    mentions = " ".join(w.mention for w in winners)
    await ctx.channel.send(f"🎉 Congratulations {mentions}! You won **{prize}**")

# ===== Reroll Command =====
@bot.command()
async def gwreroll(ctx, message_id: int):
    if message_id not in active_giveaways:
        await ctx.send("❌ Giveaway not found (maybe bot restarted or wrong ID).")
        return

    data = active_giveaways[message_id]
    channel = bot.get_channel(data["channel_id"])
    msg = await channel.fetch_message(message_id)

    users = []
    for reaction in msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)

    if not users:
        await ctx.send("No participants 😢")
        return

    winners = random.sample(users, min(data["winner_count"], len(users)))
    mentions = " ".join(w.mention for w in winners)
    await ctx.send(f"🔁 Rerolled! Congratulations {mentions}! You won **{data['prize']}**")

# ===== Run Bot =====
import os
bot.run(os.getenv("DISCORD_TOKEN"))