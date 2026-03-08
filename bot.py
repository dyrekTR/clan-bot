import discord
from discord.ext import commands, tasks

from services.sheets import players, history
from datetime import datetime
import pytz

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

kyiv = pytz.timezone("Europe/Kyiv")

VALID_CLASSES = [
    "Barbarian",
    "Crusader",
    "DemonHunter",
    "Monk",
    "Necromancer",
    "Wizard",
    "BloodKnight",
    "Tempest",
    "Druid"
]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

    if not weekly_report.is_running():
        weekly_report.start()

@bot.command()
async def grill(ctx):
    await ctx.send("Grill bot works")

@bot.command()
async def register(ctx, nick, player_class):

    player_class = player_class.capitalize()

    if player_class not in VALID_CLASSES:
        await ctx.send(
            f"Invalid class.\nChoose one of:\n{', '.join(VALID_CLASSES)}"
        )
        return

    discord_id = str(ctx.author.id)

    rows = players.get_all_records()

# перевірка чи вже зареєстрований
for row in rows:
    if str(row["DiscordID"]).split(".")[0] == discord_id:
        await ctx.send(
f"""{ctx.author.mention}

⚠ Ти вже зареєстрований.

Щоб внести свої стати напиши їх чітко за командою:
!update РЕЗО БР БРОНЯ ПРОБИВ МІЦЬ РЕЗІСТ"""
        )
        return

players.append_row([
    discord_id,
    nick,
    player_class,
    0,
    0,
    0,
    0,
    0,
    0,
    str(datetime.now())
])

try:
    await ctx.author.edit(nick=nick)
except:
    pass

    await ctx.send(
f"""{ctx.author.mention}

✅ Ти успішно зареєструвався як **{player_class}**

Щоб внести свої стати напиши їх чітко за командою:
!update РЕЗО БР БРОНЯ ПРОБИВ МІЦЬ РЕЗІСТ"""
)

@bot.command()
async def changeclass(ctx, new_class):

    new_class = new_class.capitalize()

    if new_class not in VALID_CLASSES:
        await ctx.send(
            f"Invalid class.\nChoose one of:\n{', '.join(VALID_CLASSES)}"
        )
        return

    discord_id = str(ctx.author.id)

    rows = players.get_all_records()

    for i, row in enumerate(rows, start=2):

        if str(row["DiscordID"]).split(".")[0] == discord_id:

            players.update(
                f"C{i}",
                [[new_class]]
            )

            await ctx.send(f"Class updated to {new_class}")
            return

    await ctx.send("You are not registered")

@bot.command()
async def update(ctx, resonance:int, cr:int, armor:int, armorpen:int, potency:int, resistance:int):

    discord_id = str(ctx.author.id)

    rows = players.get_all_records()

    for i, row in enumerate(rows, start=2):

        if str(row["DiscordID"]).split(".")[0] == discord_id:

            players.update(
                [[resonance, cr, armor, armorpen, potency, resistance, str(datetime.now())]],
                f"D{i}:J{i}"
            )

            history.append_row([
                discord_id,
                str(datetime.now()),
                row["Nick"],
                row["Class"],
                resonance,
                cr,
                armor,
                armorpen,
                potency,
                resistance
            ])

            await ctx.send("Stats updated")
            return

    await ctx.send("You are not registered")

@bot.command()
async def me(ctx):

    discord_id = str(ctx.author.id)

    rows = players.get_all_records()

    for row in rows:

        if str(row["DiscordID"]).split(".")[0] == discord_id:

            message = (
                f"Nick: {row['Nick']}\n"
                f"Class: {row['Class']}\n"
                f"CR: {row['CR']}\n"
                f"Resonance: {row['Resonance']}\n"
                f"Armor: {row['Armor']}\n"
                f"ArmorPenetration: {row['ArmorPenetration']}\n"
                f"Potency: {row['Potency']}\n"
                f"Resistance: {row['Resistance']}"
            )

            await ctx.send(message)
            return

    await ctx.send("You are not registered")



async def send_top(ctx, stat_name, title):

    rows = players.get_all_records()

    sorted_players = sorted(
        rows,
        key=lambda x: int(x[stat_name]),
        reverse=True
    )

    message = f"{title}\n\n"

    for i, player in enumerate(sorted_players[:10], start=1):
        message += f"{i}. {player['Nick']} — {player[stat_name]}\n"

    await ctx.send(message)

@bot.command()
async def topcr(ctx):
    await send_top(ctx, "CR", "Top CR Players")

@bot.command()
async def topres(ctx):
    await send_top(ctx, "Resonance", "Top Resonance Players")

@bot.command()
async def toparmor(ctx):
    await send_top(ctx, "Armor", "Top Armor Players")

@bot.command()
async def toparmorpen(ctx):
    await send_top(ctx, "ArmorPenetration", "Top Armor Penetration Players")

@bot.command()
async def toppotency(ctx):
    await send_top(ctx, "Potency", "Top Potency Players")

@bot.command()
async def topresist(ctx):
    await send_top(ctx, "Resistance", "Top Resistance Players")

@bot.command()
async def whois(ctx, nick):

    rows = players.get_all_records()

    for row in rows:

        if row["Nick"].lower() == nick.lower():

            message = (
                f"Nick: {row['Nick']}\n"
                f"Class: {row['Class']}\n"
                f"CR: {row['CR']}\n"
                f"Resonance: {row['Resonance']}\n"
                f"Armor: {row['Armor']}\n"
                f"ArmorPenetration: {row['ArmorPenetration']}\n"
                f"Potency: {row['Potency']}\n"
                f"Resistance: {row['Resistance']}"
            )

            await ctx.send(message)
            return

    await ctx.send("Player not found")

@bot.command()
async def inactive(ctx):

    rows = players.get_all_records()

    inactive_players = []

    for row in rows:

        last_update = datetime.fromisoformat(row["LastUpdate"])

        days = (datetime.now() - last_update).days

        if days >= 7:

            inactive_players.append(f"{row['Nick']} — {days} days")

    if not inactive_players:

        await ctx.send("No inactive players")
        return

    message = "Inactive players (>7 days)\n\n"

    for player in inactive_players:
        message += player + "\n"

    await ctx.send(message)

@bot.command()
async def progress(ctx, nick):

    rows = history.get_all_records()

    player_rows = []

    for row in rows:
        if row["Nick"].lower() == nick.lower():
            player_rows.append(row)

    if not player_rows:
        await ctx.send("No history found")
        return

    # останні 3 записи
    last_entries = player_rows[-3:]

    message = f"{nick} last updates\n\n"

    for row in last_entries:

        message += (
            f"{row['Date']}\n"
            f"CR: {row['CR']} | "
            f"Res: {row['Resonance']} | "
            f"Armor: {row['Armor']} | "
            f"ArmorPen: {row['ArmorPenetration']} | "
            f"Potency: {row['Potency']} | "
            f"Resist: {row['Resistance']}\n\n"
        )

    # рахуємо приріст
    if len(player_rows) >= 2:

        last = player_rows[-1]
        prev = player_rows[-2]

        cr_diff = int(last["CR"]) - int(prev["CR"])
        res_diff = int(last["Resonance"]) - int(prev["Resonance"])
        armor_diff = int(last["Armor"]) - int(prev["Armor"])
        armorpen_diff = int(last["ArmorPenetration"]) - int(prev["ArmorPenetration"])
        potency_diff = int(last["Potency"]) - int(prev["Potency"])
        resist_diff = int(last["Resistance"]) - int(prev["Resistance"])

        message += (
            "Growth since last update\n\n"
            f"CR +{cr_diff}\n"
            f"Resonance +{res_diff}\n"
            f"Armor +{armor_diff}\n"
            f"ArmorPenetration +{armorpen_diff}\n"
            f"Potency +{potency_diff}\n"
            f"Resistance +{resist_diff}"
        )

    await ctx.send(message)


@bot.command()
async def help(ctx):

    message = (
        "Команди кланового бота\n\n"

        "Реєстрація\n"
        "!register Nick Class — зареєструвати персонажа в базі\n"
        "!changeclass Class — змінити клас персонажа\n"
        "!update R CR Armor ArmorPen Potency Resist — оновити характеристики\n\n"

        "Гравець\n"
        "!me — показати свій профіль\n"
        "!progress Nick — показати останні оновлення гравця\n"
        "!whois Nick — подивитись профіль будь-якого гравця\n\n"

        "Рейтинги\n"
        "!topcr — топ 10 по CR\n"
        "!topres — топ по резонансу\n"
        "!toparmor — топ по броні\n"
        "!toparmorpen — топ по пробиттю броні\n"
        "!toppotency — топ по potency\n"
        "!topresist — топ по resistance\n\n"

        "Клан\n"
        "!inactive — гравці які давно не оновлювали дані\n"
        "!week — тижневий прогрес клану\n"
        "!leaderboard — панель всіх топів\n"
    )

    await ctx.send(message)

@bot.command()
async def week(ctx):

    rows = history.get_all_records()

    players_data = {}

    for row in rows:

        nick = row["Nick"]

        if nick not in players_data:
            players_data[nick] = []

        players_data[nick].append(row)

    growth = {
        "CR": [],
        "Resonance": [],
        "Armor": [],
        "ArmorPenetration": [],
        "Potency": [],
        "Resistance": []
    }

    for nick, entries in players_data.items():

        if len(entries) < 2:
            continue

        first = entries[0]
        last = entries[-1]

        growth["CR"].append((nick, int(last["CR"]) - int(first["CR"])))
        growth["Resonance"].append((nick, int(last["Resonance"]) - int(first["Resonance"])))
        growth["Armor"].append((nick, int(last["Armor"]) - int(first["Armor"])))
        growth["ArmorPenetration"].append((nick, int(last["ArmorPenetration"]) - int(first["ArmorPenetration"])))
        growth["Potency"].append((nick, int(last["Potency"]) - int(first["Potency"])))
        growth["Resistance"].append((nick, int(last["Resistance"]) - int(first["Resistance"])))

    message = "Weekly Clan Growth\n\n"

    for stat, data in growth.items():

        sorted_data = sorted(data, key=lambda x: x[1], reverse=True)

        message += f"{stat}\n"

        for i, (nick, value) in enumerate(sorted_data[:5], start=1):
            message += f"{i} {nick} +{value}\n"

        message += "\n"

    await ctx.send(message)

@tasks.loop(hours=24)
async def weekly_report():

    now = datetime.now()

    # перевіряємо чи неділя
    if now.weekday() != 1:
        return

    channel = bot.get_channel(1479901358139379833)

    rows = history.get_all_records()

    players_data = {}

    for row in rows:

        nick = row["Nick"]

        if nick not in players_data:
            players_data[nick] = []

        players_data[nick].append(row)

    growth = {
        "CR": [],
        "Resonance": [],
        "Armor": [],
        "ArmorPenetration": [],
        "Potency": [],
        "Resistance": []
    }

    for nick, entries in players_data.items():

        if len(entries) < 2:
            continue

        first = entries[0]
        last = entries[-1]

        growth["CR"].append((nick, int(last["CR"]) - int(first["CR"])))
        growth["Resonance"].append((nick, int(last["Resonance"]) - int(first["Resonance"])))
        growth["Armor"].append((nick, int(last["Armor"]) - int(first["Armor"])))
        growth["ArmorPenetration"].append((nick, int(last["ArmorPenetration"]) - int(first["ArmorPenetration"])))
        growth["Potency"].append((nick, int(last["Potency"]) - int(first["Potency"])))
        growth["Resistance"].append((nick, int(last["Resistance"]) - int(first["Resistance"])))

    message = "Weekly Clan Growth\n\n"

    for stat, data in growth.items():

        sorted_data = sorted(data, key=lambda x: x[1], reverse=True)

        message += f"{stat}\n"

        for i, (nick, value) in enumerate(sorted_data[:5], start=1):
            message += f"{i}. {nick} +{value}\n"

        message += "\n"

    await channel.send(message)

@bot.command()
async def weektest(ctx):
    await week(ctx)

@bot.command()
async def leaderboard(ctx):

    rows = players.get_all_records()

    stats = {
        "CR": "CR",
        "Resonance": "Resonance",
        "Armor": "Armor",
        "ArmorPenetration": "ArmorPenetration",
        "Potency": "Potency",
        "Resistance": "Resistance"
    }

    message = "Clan Leaderboard\n\n"

    for title, column in stats.items():

        sorted_players = sorted(
            rows,
            key=lambda x: int(x[column]),
            reverse=True
        )

        message += f"{title}\n"

        for i, player in enumerate(sorted_players[:3], start=1):
            message += f"{i} {player['Nick']} — {player[column]}\n"

        message += "\n"

    await ctx.send(message)

@bot.command()
async def remind(ctx):

    rows = players.get_all_records()

    now = datetime.now()

    inactive = []

    for row in rows:

        last_update = datetime.fromisoformat(row["LastUpdate"])

        days = (now - last_update).days

        if days >= 5:
            inactive.append(row["DiscordID"])

    if not inactive:
        await ctx.send("Everyone updated recently")
        return

    message = "Players need to update stats\n\n"

    for discord_id in inactive:
        message += f"<@{discord_id}>\n"

    message += "\nUse !update"

    await ctx.send(message)

bot.run(TOKEN)