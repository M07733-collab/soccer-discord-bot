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

# Comprehensive dictionary covering all Premier League teams
TEAM_IDS = {
    "arsenal": 57,
    "aston villa": 58,
    "bournemouth": 1044,
    "brentford": 402,
    "brighton": 397,
    "brighton & hove albion": 397,
    "chelsea": 61,
    "crystal palace": 354,
    "everton": 62,
    "fulham": 63,
    "ipswich": 349,
    "ipswich town": 349,
    "leicester": 338,
    "leicester city": 338,
    "liverpool": 64,
    "manchester city": 65,
    "man city": 65,
    "manchester united": 66,
    "man utd": 66,
    "newcastle": 67,
    "newcastle united": 67,
    "nottingham": 351,
    "nottingham forest": 351,
    "southampton": 340,
    "tottenham": 73,
    "tottenham hotspur": 73,
    "spurs": 73,
    "west ham": 563,
    "west ham united": 563,
    "wolves": 76,
    "wolverhampton wanderers": 76
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
        await ctx.send(f"Sorry, I couldn't find a team named '{team_name}'. Try typing a valid Premier League team like Arsenal, Liverpool, Chelsea, etc.")
        return

    url = "https://api.football-data.org/v4/competitions/PL/matches?season=2025"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"API Error Code: {response.status_code}, Response: {response.text}")
        await ctx.send(f"⚠️ Error fetching data from Football-Data API (Status: {response.status_code}).")
        return

    data = response.json()
    all_matches = data.get("matches", [])

    team_matches = [
        m for m in all_matches 
        if m["homeTeam"]["id"] == team_id or m["awayTeam"]["id"] == team_id
    ]

    finished_matches = [m for m in team_matches if m["status"] == "FINISHED"]
    matches = finished_matches[-5:]

    if not matches:
        await ctx.send(f"No recent finished matches found for {team_name.title()}.")
        return

    output = [f"📊 **Detailed Last 5 Matches for {team_name.title()}**:\n"]
    
    for match in matches:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        score_home = match["score"]["fullTime"]["home"]
        score_away = match["score"]["fullTime"]["away"]
        date = match["utcDate"].split("T")[0]
        match_id = match["id"]

        # Fetch individual match details for stats (corners, etc.)
        match_url = f"https://api.football-data.org/v4/matches/{match_id}"
        match_res = requests.get(match_url, headers=headers)
        
        stats_text = ""
        if match_res.status_code == 200:
            match_data = match_res.json()
            # Check if statistics are provided in the payload
            stats = match_data.get("statistics")
            if stats:
                # Format available match statistics if present
                stats_text = f"\n   *Stats:* Available"
            else:
                stats_text = f"\n   *Stats:* Detailed metrics not provided by API for this fixture."

        output.append(f"• **{date}** | **{home} {score_home} - {score_away} {away}**{stats_text}")

    await ctx.send("\n".join(output))

if __name__ == "__main__":
    bot.run(TOKEN)
