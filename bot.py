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

# Dictionary to dynamically hold all team names and their IDs
TEAM_IDS = {}

def load_premier_league_teams():
    """Dynamically fetch all Premier League teams from the API"""
    url = "https://api.football-data.org/v4/competitions/PL/teams"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for team in data.get("teams", []):
                name = team["name"].lower().strip()
                team_id = team["id"]
                TEAM_IDS[name] = team_id
                # Also map common short names if available (e.g., "Man United" or "Spurs")
                if "shortName" in team:
                    TEAM_IDS[team["shortName"].lower().strip()] = team_id
                if "tla" in team:
                    TEAM_IDS[team["tla"].lower().strip()] = team_id
            print(f"Successfully loaded {len(data.get('teams', []))} Premier League teams!")
        else:
            print(f"Failed to load teams. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching teams: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    load_premier_league_teams()

@bot.command(name="hello")
async def hello(ctx):
    await ctx.send("Hello! I am your soccer bot.")

@bot.command(name="form")
async def team_form(ctx, *, team_name: str = ""):
    team_name = team_name.lower().strip()
    team_id = TEAM_IDS.get(team_name)
    
    if not team_id:
        await ctx.send(f"Sorry, I couldn't find a team named '{team_name}'. Make sure to type a valid Premier League team (e.g., Arsenal, Liverpool, Brighton, etc.).")
        return

    # Fetch all matches for the specific team
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"API Error Code: {response.status_code}, Response: {response.text}")
        await ctx.send(f"⚠️ Error fetching data from Football-Data API (Status: {response.status_code}).")
        return

    data = response.json()
    all_matches = data.get("matches", [])

    # Filter for finished matches to show the last 5 form results
    finished_matches = [m for m in all_matches if m["status"] == "FINISHED"]
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
