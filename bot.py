import os
import asyncio
import discord
from discord.ext import commands
import requests

BOT_PREFIX = "$"
TOKEN = os.getenv("DISCORD_TOKEN")
# Strip stray spaces/quotes that sometimes sneak into environment variables
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip().strip("\"'")

API_BASE = "https://api.football-data.org/v4"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Premier League team IDs (football-data.org).
# Leeds, Burnley and Sunderland IDs are from memory: verify at
# https://api.football-data.org/v4/competitions/PL/teams
TEAM_IDS = {
    "arsenal": 57,
    "aston villa": 58,
    "bournemouth": 1044,
    "brentford": 402,
    "brighton": 397,
    "brighton & hove albion": 397,
    "burnley": 328,
    "chelsea": 61,
    "crystal palace": 354,
    "everton": 62,
    "fulham": 63,
    "ipswich": 349,
    "ipswich town": 349,
    "leeds": 341,
    "leeds united": 341,
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
    "sunderland": 71,
    "tottenham": 73,
    "tottenham hotspur": 73,
    "spurs": 73,
    "west ham": 563,
    "west ham united": 563,
    "wolves": 76,
    "wolverhampton wanderers": 76,
}


async def api_get(path, params=None):
    """Call the football-data API without freezing the bot.
    Returns (status_code, response) or (None, error_text) if the request failed."""
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    try:
        response = await asyncio.to_thread(
            requests.get, f"{API_BASE}{path}", headers=headers, params=params, timeout=10
        )
        return response.status_code, response
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None, str(e)


async def send_api_error(ctx, status, response):
    if status is None:
        await ctx.send("⚠️ Couldn't reach the Football-Data API. Try again in a moment.")
    elif status == 429:
        await ctx.send("⚠️ Too many requests. The free plan allows about 10 per minute, so wait a minute and try again.")
    else:
        print(f"API Error Code: {status}, Response: {response.text}")
        await ctx.send(
            f"⚠️ Error fetching data from Football-Data API (Status: {status}).\n"
            f"```{response.text[:500]}```"
        )


def find_team_id(team_name):
    return TEAM_IDS.get(team_name.lower().strip())


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    print(f"Football API key length: {len(FOOTBALL_API_KEY)}")


@bot.command(name="hello")
async def hello(ctx):
    await ctx.send("Hello! I am your soccer bot.")


@bot.command(name="form")
async def team_form(ctx, *, team_name: str = ""):
    team_id = find_team_id(team_name)
    if not team_id:
        await ctx.send(
            f"Sorry, I couldn't find a team named '{team_name}'. "
            "Try typing a valid Premier League team like Arsenal, Liverpool, Chelsea, etc."
        )
        return

    status, response = await api_get(f"/teams/{team_id}/matches", {"status": "FINISHED"})
    if status != 200:
        await send_api_error(ctx, status, response)
        return

    # Keep only Premier League games. Matches come back oldest to newest,
    # so the last 5 are the most recent.
    all_matches = response.json().get("matches", [])
    pl_matches = [m for m in all_matches if m.get("competition", {}).get("code") == "PL"]
    matches = pl_matches[-5:]

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


def format_goals(match):
    goals = match.get("goals") or []
    score = match["score"]["fullTime"]
    total = (score.get("home") or 0) + (score.get("away") or 0)

    if not goals:
        if total == 0:
            return ["No goals in this match."]
        return ["Scorer details aren't available for this match on the current plan."]

    lines = []
    for g in goals:
        minute = g.get("minute")
        extra = g.get("injuryTime")
        time_text = f"{minute}+{extra}'" if extra else f"{minute}'"
        scorer = (g.get("scorer") or {}).get("name", "Unknown")
        team = (g.get("team") or {}).get("name", "")
        tag = ""
        if g.get("type") == "OWN":
            tag = " (own goal)"
        elif g.get("type") == "PENALTY":
            tag = " (pen)"
        assist = (g.get("assist") or {}).get("name")
        assist_text = f", assist: {assist}" if assist else ""
        lines.append(f"⚽ {time_text} {scorer}{tag} ({team}){assist_text}")
    return lines


STAT_LABELS = [
    ("ball_possession", "Possession (%)"),
    ("shots", "Shots"),
    ("shots_on_goal", "Shots on target"),
    ("corner_kicks", "Corners"),
    ("fouls", "Fouls"),
    ("offsides", "Offsides"),
    ("saves", "Saves"),
    ("yellow_cards", "Yellow cards"),
    ("red_cards", "Red cards"),
]


def format_stats(match):
    home = match["homeTeam"]
    away = match["awayTeam"]
    home_stats = home.get("statistics") or {}
    away_stats = away.get("statistics") or {}

    if not home_stats and not away_stats:
        return ["Match stats (corners, shots, possession) aren't included in your plan for this match."]

    lines = [f"{'':<18}{home['name'][:14]:<16}{away['name'][:14]}"]
    for key, label in STAT_LABELS:
        h = home_stats.get(key)
        a = away_stats.get(key)
        if h is None and a is None:
            continue
        lines.append(f"{label:<18}{str(h if h is not None else '-'):<16}{a if a is not None else '-'}")
    return lines


@bot.command(name="last")
async def last_match(ctx, *, team_name: str = ""):
    """Details of a team's most recent Premier League match: scorers and stats."""
    team_id = find_team_id(team_name)
    if not team_id:
        await ctx.send(
            f"Sorry, I couldn't find a team named '{team_name}'. "
            "Try a Premier League team like Arsenal, Liverpool, Chelsea, etc."
        )
        return

    # Step 1: find the team's most recent finished Premier League match
    status, response = await api_get(f"/teams/{team_id}/matches", {"status": "FINISHED"})
    if status != 200:
        await send_api_error(ctx, status, response)
        return

    pl_matches = [
        m for m in response.json().get("matches", [])
        if m.get("competition", {}).get("code") == "PL"
    ]
    if not pl_matches:
        await ctx.send(f"No recent finished matches found for {team_name.title()}.")
        return
    match_id = pl_matches[-1]["id"]

    # Step 2: get the full details of that match
    status, response = await api_get(f"/matches/{match_id}")
    if status != 200:
        await send_api_error(ctx, status, response)
        return
    match = response.json()

    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    score = match["score"]["fullTime"]
    date = match["utcDate"].split("T")[0]

    message = [f"📋 **{home} {score['home']} - {score['away']} {away}** ({date})", ""]
    message += format_goals(match)
    message += ["", "```"] + format_stats(match) + ["```"]
    message.append("_Passes aren't available from this data source._")

    await ctx.send("\n".join(message))


if __name__ == "__main__":
    bot.run(TOKEN)
