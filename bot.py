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

    # Fetch all matches via the Premier League competition endpoint
    url = "https://api.football-data.org/v4/competitions/PL/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"API Error Code: {response.status_code}, Response: {response.text}")
        await ctx.send(f"⚠️️ Error fetching data from Football-Data API (Status: {response.status_code}).")
        return

    data = response.json()
    all_matches = data.get("matches", [])

    # Filter matches belonging to this specific team ID
    team_matches = [
        m for m in all_matches 
        if m["homeTeam"]["id"] == team_id or m["awayTeam"]["id"] == team_id
    ]

    # Grab only the finished ones
    finished_matches = [m for m in team_matches if m["status"] == "FINISHED"]
    matches = finished_matches[-5:]

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

if __name__ == "__main__":
    bot.run(TOKEN)
