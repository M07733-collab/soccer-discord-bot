import os
import discord
from discord.ext import commands
import requests

BOT_PREFIX = "$"
TOKEN = os.getenv("DISCORD_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

TEAM_IDS = {
    "arsenal": 57,
    "aston villa": 58,
    "chelsea": 61,
    "liverpool": 64,
    "manchester city": 65,
    "manchester united": 66,
    "tottenham": 73,
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")

@bot.command(name="hello")
async def hello(ctx):
    await ctx.send("Hello! I am your soccer bot.")

@bot.command(name="form")
async def team_form(ctx, *, team_name: str = ""):
    team_name = team_name.lower().strip()
    team_id = TEAM_IDS.get(team_name)
    
    if not team_id:
        await ctx.send(f"Sorry, I couldn't find a team named '{team_name}'. Try one like: Arsenal, Liverpool, Chelsea, etc.")
        return

    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        await ctx.send("⚠️ Error fetching data from Football-Data API.")
        return

    data = response.json()
    matches = data.get("matches", [])

    if not matches:
        await ctx.send(f"No recent finished matches found for {team_name.title()}.")
        return

    output = [f"📊 **Last 5 Matches for {team_name.title()}**:\n"]
    for match in matches:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        score_home = match["score"]["fullTime"]["home"]
        score_away = match["score"]["fullTime"]["away"]
        date = match["utcDate"].split("T")[0]
        
        output.append(f"• *{date}* | **{home} {score_home} - {score_away} {away}**")

    await ctx.send("\n".join(output))

bot.run(TOKEN)
