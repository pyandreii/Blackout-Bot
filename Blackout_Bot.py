from discord.ext import commands, tasks
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import random
from discord import app_commands
import discord
import asyncio
from dotenv import load_dotenv
import os
import calendar
# --- Configurare ---

ID_SERVER_PRINCIPAL = 1372682829074530335
text_channel_id = 1389616154259226625
CO_OWNER_ROLE_ID = 1397521192092700702
REQUIRED_ROLE_ID = 1397521192092700702

role_nivele = {
    1: 1390238119734935673,
    5: 1390237191212630016,
    10: 1390237775491629129,
    15: 1390237906458775633,
    20: 1391528616172720128,
}
monthly_roles = {
    "2025-07": 1397576340689129482,  # ID rol pentru iulie 2025
    "2025-08": 1397576432166895708,  # ID rol pentru august 2025

}
rebirth_roles = {
    1: 1395364152419029005,
    2: 1395364253627846806,
    3: "Rebirth 3",
    4: "Rebirth 4",
    5: "Rebirth 5",
    # ... poți continua cât ai nevoie
}

# --- DAILY QUESTS ---
DAILY_QUESTS = [{
    "quest": "Trimite 20 de mesaje pe server",
    "type": "messages",
    "target": 20,
    "reward": 100
}, {
    "quest": "Stai 15 minute în voice chat",
    "type": "voice_minutes",
    "target": 15,
    "reward": 120
}, {
    "quest": "Trimite 10 mesaje într-un canal text",
    "type": "messages",
    "target": 10,
    "reward": 80
}, {
    "quest": "Fii activ în voice chat timp de 30 minute",
    "type": "voice_minutes",
    "target": 30,
    "reward": 200
}, {
    "quest": "Dă tag unui prieten într-un mesaj pe server",
    "type": "mention_friend",
    "target": 1,
    "reward": 90
}, {
    "quest": "Reacționează la 5 mesaje ale altor membri",
    "type": "reactions",
    "target": 5,
    "reward": 70
}, {
    "quest": "Răspunde la o întrebare în chat",
    "type": "reply",
    "target": 1,
    "reward": 100
}]

data_file = "data_nou.json"
quest_data_file = "data_quest.json"

if os.path.exists(quest_data_file):
    with open(quest_data_file, "r") as f:
        try:
            quest_data = json.load(f)
        except json.JSONDecodeError:
            quest_data = {}
else:
    quest_data = {}

monthly_data_file = "monthly_data.json"

if os.path.exists(monthly_data_file):
    with open(monthly_data_file, "r") as f:
        try:
            monthly_data = json.load(f)
        except json.JSONDecodeError:
            monthly_data = {}
else:
    monthly_data = {}

def save_monthly_data():
    with open(monthly_data_file, "w") as f:
        json.dump(monthly_data, f, indent=4)

def save_quest_data():
    with open(quest_data_file, "w") as f:
        json.dump(quest_data, f, indent=4)


def save_user_data():
    with open(data_file, "w") as f:
        json.dump(user_data, f, indent=4)


def has_required_role():

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ Eroare: utilizator necunoscut.", ephemeral=True)
            return False
        return any(role.id == REQUIRED_ROLE_ID
                   for role in interaction.user.roles)

    return app_commands.check(predicate)


async def finalize_quest(user: discord.User | discord.Member):
    user_id = str(user.id)
    quest = quest_data.get(user_id)
    if not quest:
        return
    if user_id not in user_data:
        return  # Previi key error

    reward = int(quest.get("reward", 0))
    user_data[user_id]["xp"] += reward

    channel = bot.get_channel(text_channel_id)
    if channel:
        await channel.send(
            f"🎉 {user.mention} ai finalizat misiunea și ai primit {reward} XP!"
        )

    quest_data[user_id] = {}
    save_quest_data()
    save_user_data()

spam_limit_count = 3
spam_limit_seconds = 5

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# --- Variabile globale ---

user_recent_messages = defaultdict(deque)


def generate_daily_quest():
    if random.random() < 0.15:  # 15% șansă pentru quest rar
        rare_quests = [q for q in DAILY_QUESTS if q.get("rare")]
        if rare_quests:
            return random.choice(rare_quests)
    normal_quests = [q for q in DAILY_QUESTS if not q.get("rare")]
    return random.choice(normal_quests)


if os.path.exists(data_file):
    with open(data_file, "r") as f:
        try:
            user_data = json.load(f)
        except json.JSONDecodeError:
            user_data = {}
else:
    user_data = {}


def load_data():
    if not os.path.exists("data_nou.json"):
        print("[INFO] Fișierul `data_nou.json` nu există. Îl creez automat.")
        with open("data_nou.json", "w") as f:
            json.dump({}, f)
        return {}

    try:
        with open("data_nou.json", "r") as f:
            content = f.read().strip()

            if not content:
                print("[WARN] Fișierul `data_nou.json` e gol. Îl reinițializez.")
                with open("data_nou.json", "w") as wf:
                    json.dump({}, wf)
                return {}

            data = json.loads(content)
            if not isinstance(data, dict):
                print(
                    "[ERROR] Structura fișierului `data_nou.json` nu este un obiect JSON valid."
                )
                return {}

            return data

    except json.JSONDecodeError as e:
        print(f"[ERROR] data_nou.json corupt: {e}. Îl resetez cu structură goală.")
        with open("data_nou.json", "w") as f:
            json.dump({}, f)
        return {}


def save_data(data):
    if not isinstance(data, dict):
        raise ValueError("save_data a primit un obiect invalid (nu e dict)")
    with open("data_nou.json", "w") as f:
        json.dump(data, f, indent=4)


# --- Funcții utile ---


def xp_needed(level):
    return 5 * (level**2) + 50 * level + 100


# --- Bot și grup slash commands ---
blackout = app_commands.Group(name="blackout",
                              description="Comenzi Blackout Bot",
                              guild_ids=[ID_SERVER_PRINCIPAL])


class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)


bot = MyBot()


def update_level(user_id):
    xp = user_data[user_id]["xp"]
    current_level = user_data[user_id].get("level", 0)
    new_level = xp_needed(xp)  # funcția ta de calcul level
    if new_level > current_level:
        user_data[user_id]["level"] = new_level


# --- Task pentru XP din voice ---


async def update_rebirth_role(member: discord.Member, rebirth: int):
    if member is None:
        return
    # Sterge toate rolurile de rebirth vechi (verifică după ID-uri dacă vrei mai sigur)
    rebirth_role_ids = set(rebirth_roles.values())
    roles_to_remove = [
        role for role in member.roles if role.id in rebirth_role_ids
    ]

    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)

    # Adaugă noul rol, dacă există în mapare
    role_id = rebirth_roles.get(rebirth)
    if not role_id:
        return

    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)


@tasks.loop(minutes=1)
async def give_voice_xp():
    for guild in bot.guilds:
        channel = guild.get_channel(text_channel_id)  # luat o singură dată per guild
        for vc in guild.voice_channels:
            for member in vc.members:
                if member.bot:
                    continue
                if member.voice is None or member.voice.deaf or member.voice.self_deaf:
                    continue

                user_id = str(member.id)
                if user_id not in user_data:
                    user_data[user_id] = {"xp": 0, "level": 0, "rebirth": 0}

                # Misiune voice_minutes
                quest = quest_data.get(user_id)
                if quest and isinstance(quest, dict) and quest.get("type") == "voice_minutes":
                    progress = quest.get("progress", 0) + 1
                    quest["progress"] = progress
                    quest_data[user_id] = quest
                    save_quest_data()

                    print(f"[VOICE QUEST] {member.display_name}: {progress}/{quest.get('target', 0)}")

                    if progress >= quest.get("target", 0):
                        user_data[user_id]["xp"] += quest.get("reward", 0)
                        save_user_data()

                        if channel:
                            await channel.send(
                                f"🎉 {member.mention} ai finalizat misiunea voice și ai primit {quest['reward']} XP!"
                            )
                        quest_data[user_id] = {}
                        save_quest_data()

                # XP pentru voice activ
                user_data[user_id]["xp"] += 10
                current_xp = user_data[user_id]["xp"]
                current_level = user_data[user_id]["level"]
                next_level_xp = xp_needed(current_level + 1)

                leveled_up = False
                while current_xp >= next_level_xp:
                    current_xp -= next_level_xp
                    user_data[user_id]["level"] += 1
                    current_level = user_data[user_id]["level"]
                    next_level_xp = xp_needed(current_level + 1)
                    leveled_up = True

                user_data[user_id]["xp"] = current_xp

                if leveled_up:
                    new_role_id = role_nivele.get(current_level)
                    new_role = guild.get_role(new_role_id) if new_role_id else None

                    if new_role and new_role not in member.roles:
                        try:
                            await member.add_roles(new_role)
                            if channel:
                                await channel.send(
                                    f"{member.mention} a ajuns la nivelul {current_level} și a primit rolul {new_role.name}! 🎉"
                                )
                        except discord.Forbidden:
                            print(f"[EROARE] Nu pot da rol lui {member.display_name}")
                    elif channel and current_level != 1:
                        await channel.send(f"{member.mention} a ajuns la nivelul {current_level}! 🎉")

    save_user_data()


# --- Eveniment on_ready ---

@tasks.loop(hours=24)
async def check_month_reset():
    today = datetime.utcnow().date()
    if today.day == 1:
        # Încarcă lunar_data curentă
        with open("monthly_data.json", "r") as f:
            monthly_data = json.load(f)

        # Sortează după XP ca să găsești locul 1
        if monthly_data:
            top_user_id = max(monthly_data, key=lambda uid: monthly_data[uid]["xp"])
            guild = bot.get_guild(1372682829074530335)  # pune aici ID serverului tău
            member = guild.get_member(int(top_user_id))
            if member:
                # Mapă rol lunar după lună, ex: "2025-07"
                month_str = (today - timedelta(days=1)).strftime("%Y-%m")  # luna trecută
                role_id = monthly_roles.get(month_str)
                if role_id:
                    role = guild.get_role(role_id)
                    if role and role not in member.roles:
                        await member.add_roles(role)
                        print(f"🎉 {member.display_name} a primit rolul pentru {month_str}!")

        # Resetează datele
        with open("monthly_data.json", "w") as f:
            json.dump({}, f, indent=4)

        print("🔁 Lunar leaderboard resetat!")

@bot.event
async def on_ready():
    print(f"✅ Bot conectat ca {bot.user}")
    await bot.change_presence(activity=discord.CustomActivity(name="❤️ Vă iubesc, BlackOut RO! Mereu voi fi aici"))
    print(f"Guild-uri pe care sunt: {[guild.id for guild in bot.guilds]}")

    if not give_voice_xp.is_running():
        give_voice_xp.start()

    # Înregistrează grupul de comenzi blackout doar dacă nu e deja înregistrat
    try:
        bot.tree.add_command(blackout)
    except discord.app_commands.CommandAlreadyRegistered:
        pass

    guild = discord.Object(id=ID_SERVER_PRINCIPAL)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ {len(synced)} comenzi slash sincronizate pe serverul principal.")
    except Exception as e:
        print(f"❌ Eroare sincronizare slash commands: {e}")

    # Pornește task-ul pentru XP în voice
    if not give_voice_xp.is_running():
        give_voice_xp.start()

@give_voice_xp.before_loop
async def before_voice_xp():
    await bot.wait_until_ready()

@give_voice_xp.error
async def voice_xp_error(error):
    print(f"[Loop Error] {error}")
# --- Anti-spam & leveling mesaj text ---

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return  # ignoră reacțiile botului

    user_id = str(payload.user_id)

    quest = quest_data.get(user_id)
    if isinstance(quest, dict) and quest.get("type") == "reaction":
        if quest.get("progress", 0) < quest.get("target", 0):
            quest["progress"] += 1
            quest_data[user_id]["progress"] = quest["progress"]
            save_quest_data()

            if quest["progress"] >= quest["target"]:
                # Dă XP
                user_data.setdefault(user_id, {"xp": 0, "level": 0, "rebirth": 0})
                user_data[user_id]["xp"] += quest["reward"]
                save_user_data()

                guild = bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                channel = guild.get_channel(text_channel_id)
                if member and channel:
                    await channel.send(
                        f"🎉 {member.mention} ai finalizat misiunea cu reacții și ai primit {quest['reward']} XP!"
                    )

                quest_data[user_id] = {}  # Reset
                save_quest_data()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.guild:
        return

    user_id = str(message.author.id)
    now = datetime.now(timezone.utc)

    # Inițializează user_data dacă nu există
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 0, "rebirth": 0}

    # Inițializează coada de mesaje recente pentru anti-spam
    if user_id not in user_recent_messages:
        user_recent_messages[user_id] = deque()

    recent = user_recent_messages[user_id]
    recent.append(message)

    # Curăță mesaje vechi (> spam_limit_seconds)
    while recent and (now - recent[0].created_at).total_seconds() > spam_limit_seconds:
        recent.popleft()

    # Detectare spam
    if len(recent) > spam_limit_count:
        try:
            for msg in list(recent):
                try:
                    await msg.delete()
                except:
                    pass
            recent.clear()
            warn_msg = await message.channel.send(
                f"{message.author.mention}, nu spamma, te rog! Vei fi mutat temporar."
            )
            if isinstance(message.author, discord.Member):
                await message.author.timeout(timedelta(seconds=30), reason="Spam detectat")
            await warn_msg.delete(delay=5)
        except Exception as e:
            print(f"[Eroare spam] {e}")
        return  # Nu mai procesăm dacă e spam

    # --- ADĂUGĂ XP NORMAL IMEDIAT după anti-spam ---
    user_data[user_id]["xp"] += 5

    if user_id not in monthly_data:
        monthly_data[user_id] = {"xp": 0}
    monthly_data[user_id]["xp"] += 10
    save_monthly_data()

    # Quest progres
    quest = quest_data.get(user_id, {})

    # 1. Questuri tip "text_messages" sau "messages" (unificat)
    if quest.get("type") in ["text_messages", "messages"] and quest.get("progress", 0) < quest.get("target", 0):
        quest["progress"] += 1
        if quest["progress"] >= quest.get("target", 0):
            await finalize_quest(message.author)
        else:
            quest_data[user_id]["progress"] = quest["progress"]
            save_quest_data()

    # 2. mention_friend
    if quest.get("type") == "mention_friend" and quest.get("progress", 0) < quest.get("target", 0):
        if message.mentions:
            # Considerăm că menționarea oricărui utilizator (altul decât autorul) contează
            if any(m.id != message.author.id for m in message.mentions):
                quest["progress"] += 1
                if quest["progress"] >= quest.get("target", 0):
                    await finalize_quest(message.author)
                else:
                    quest_data[user_id]["progress"] = quest["progress"]
                    save_quest_data()

    # 3. reply
    if quest.get("type") == "reply" and quest.get("progress", 0) < quest.get("target", 0):
        if message.reference and message.reference.message_id:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
            except discord.NotFound:
                return  # Mesajul răspuns a fost șters
            if ref_msg.author.id != message.author.id:
                quest["progress"] += 1
                if quest["progress"] >= quest.get("target", 0):
                    await finalize_quest(message.author)
                else:
                    quest_data[user_id]["progress"] = quest["progress"]
                    save_quest_data()

    # --- NIVELARE (level up) cu while, pentru multiple niveluri ---
    xp = user_data[user_id]["xp"]
    level = user_data[user_id]["level"]
    rebirth = user_data[user_id].get("rebirth", 0)

    next_level_xp = xp_needed(level + 1)
    channel = message.guild.get_channel(text_channel_id)

    while xp >= next_level_xp:
        xp -= next_level_xp
        level += 1
        user_data[user_id]["level"] = level
        user_data[user_id]["xp"] = xp

        # Reset rebirth dacă nivelul atinge 25
        if level >= 25:
            user_data[user_id]["level"] = 0
            user_data[user_id]["xp"] = 0
            user_data[user_id]["rebirth"] = rebirth + 1
            rebirth = user_data[user_id]["rebirth"]

            if channel:
                await channel.send(
                    f"🔁 {message.author.mention} a făcut **Rebirth {rebirth}** și nivelul a fost resetat!"
                )

            # Setează rolul de rebirth după ID
            role_id = rebirth_roles.get(rebirth)
            if role_id:
                rb_role = message.guild.get_role(role_id)
                if rb_role and rb_role not in message.author.roles:
                    await message.author.add_roles(rb_role)

            # Elimină celelalte roluri de rebirth
            for lvl, rid in rebirth_roles.items():
                if lvl != rebirth:
                    old_role = message.guild.get_role(rid)
                    if old_role and old_role in message.author.roles:
                        await message.author.remove_roles(old_role)

            # Reset next_level_xp după rebirth
            next_level_xp = xp_needed(user_data[user_id]["level"] + 1)
            break  # Ieșim după rebirth

        else:
            # Adaugă rol pentru nivelul nou
            role_id = role_nivele.get(level)
            role = message.guild.get_role(role_id) if role_id else None
            if role and role not in message.author.roles:
                await message.author.add_roles(role)
                if channel:
                    await channel.send(
                        f"{message.author.mention} a ajuns la nivelul {level} și a primit rolul {role.name}! 🎉"
                    )
            elif channel and level != 1:
                await channel.send(
                    f"{message.author.mention} a ajuns la nivelul {level}! 🎉"
                )

        next_level_xp = xp_needed(level + 1)

    user_data[user_id]["xp"] = xp

    # Salvează datele după orice modificare
    save_user_data()
    save_quest_data()

    # Permite procesarea altor comenzi
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    user_id = str(user.id)
    quest = quest_data.get(user_id)

    # ✅ Verificăm dacă e o misiune de tip 'reaction'
    if isinstance(quest, dict) and quest.get("type") == "reaction":
        progress = quest.get("progress", 0) + 1
        target = quest.get("target", 0)
        quest["progress"] = progress
        quest_data[user_id] = quest
        save_quest_data()

        print(f"[REACTION QUEST] {user.display_name}: {progress}/{target}")  # DEBUG

        if progress >= target:
            user_data[user_id]["xp"] += quest.get("reward", 0)
            save_user_data()

            guild = reaction.message.guild  # <- aici luăm guildul corect
            channel = guild.get_channel(text_channel_id)
            if channel:
                await channel.send(
                    f"🎉 {user.mention} ai finalizat misiunea cu reacții și ai primit {quest['reward']} XP!"
                )

            # Resetare misiune
            quest_data[user_id] = {}
            save_quest_data()


@blackout.command(name="rank", description="Vezi nivelul și XP-ul unui membru")
@app_commands.describe(member="Membrul căruia vrei să-i vezi rankul")
async def blackout_rank(interaction: discord.Interaction,
                        member: discord.Member = None):
    member = member or interaction.user
    user_id = str(member.id)

    if user_id not in user_data:
        await interaction.response.send_message(
            f"{member.mention} nu are încă XP.")
        user_data.setdefault(user_id, {"xp": 0, "level": 0, "rebirth": 0})
        return

    xp = user_data[user_id]["xp"]
    level = user_data[user_id]["level"]
    next_level_xp = xp_needed(level + 1)
    xp_ramas = next_level_xp - xp
    await interaction.response.send_message(
        f"{member.mention} este nivel {level} cu {xp} XP.\n"
        f"✨ Mai ai nevoie de {xp_ramas} XP până la nivelul {level + 1}.")



@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction,
                               error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ Nu ai permisiunea să folosești această comandă.",
            ephemeral=True)
    else:
        await interaction.response.send_message(
            "❌ A apărut o eroare la executarea comenzii.", ephemeral=True)
        print(f"[Slash Error] {error}")


@blackout.command(name="leaderboard",
                  description="Vezi top 10 utilizatori după nivel și XP")
async def blackout_leaderboard(interaction: discord.Interaction):
    if not user_data:
        await interaction.response.send_message(
            "Nu există date despre utilizatori.")
        return

    sorted_users = sorted(user_data.items(),
                          key=lambda x: (x[1]['level'], x[1]['xp']),
                          reverse=True)

    embed = discord.Embed(title="🏆 Blackout Leaderboard",
                          description="Top 10 utilizatori după nivel și XP",
                          color=discord.Color.dark_gold())

    first_user = None
    for i, (user_id, data) in enumerate(sorted_users[:10], start=1):
        try:
            member = interaction.guild.get_member(int(user_id))
            if member is None:
                member = await interaction.guild.fetch_member(int(user_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            member = None

        name = member.display_name if member else f"User ID {user_id}"
        level = data.get("level", 0)
        xp = data.get("xp", 0)
        rebirth = data.get("rebirth", 0)
        rebirth_display = f" 🔁x{rebirth}" if rebirth > 0 else ""

        if member:
            await update_rebirth_role(member, rebirth)

        if i == 1 and member and member.avatar:
            first_user = member

        embed.add_field(
            name=f"{i}. {name}",
            value=f"⭐ Nivel: `{level}` • ✨ XP: `{xp}`{rebirth_display}",
            inline=False)

    if first_user and first_user.avatar:
        embed.set_thumbnail(url=first_user.avatar.url)

    embed.set_footer(text="🔢 Clasament actualizat")
    embed.timestamp = datetime.now(timezone.utc)

    await interaction.response.send_message(embed=embed)


@blackout.command(name="sent",
                  description="Trimite un mesaj personalizat într-un canal.")
@app_commands.describe(channel="Canalul în care să fie trimis mesajul",
                       mesaj="Conținutul mesajului",
                       format="Tipul mesajului: simplu, boldat, cu numerotare")
@app_commands.choices(format=[
    app_commands.Choice(name="Simplu", value="normal"),
    app_commands.Choice(name="Boldat", value="bold"),
    app_commands.Choice(name="Numerotat", value="numerotat"),
    app_commands.Choice(name="Boldat și Numerotat", value="bold_numerotat")
])
async def sent(interaction: discord.Interaction, channel: discord.TextChannel,
               mesaj: str, format: app_commands.Choice[str]):
    CO_OWNER_ROLE_ID = 1397521192092700702  # Pune aici ID-ul corect al rolului tău

    # Obține membrul din guild (pentru a avea acces la roluri)
    member = interaction.guild.get_member(interaction.user.id)
    if member is None:
        try:
            member = await interaction.guild.fetch_member(interaction.user.id)
        except Exception:
            await interaction.response.send_message(
                "⛔ Nu am putut verifica rolurile tale.", ephemeral=True)
            return

    # Verifică dacă membrul are rolul necesar
    if CO_OWNER_ROLE_ID not in [role.id for role in member.roles]:
        await interaction.response.send_message(
            "⛔ Nu ai permisiunea să folosești această comandă.",
            ephemeral=True)
        return

    # Formatează mesajul
    lines = mesaj.split("\n")
    formatted_lines = []

    for i, line in enumerate(lines, start=1):
        if format.value == "normal":
            formatted_lines.append(line)
        elif format.value == "bold":
            formatted_lines.append(f"**{line}**")
        elif format.value == "numerotat":
            formatted_lines.append(f"{i}. {line}")
        elif format.value == "bold_numerotat":
            formatted_lines.append(f"{i}. **{line}**")

    final_message = "\n".join(formatted_lines)

    try:
        await channel.send(final_message,
                           allowed_mentions=discord.AllowedMentions.all())
        await interaction.response.send_message(
            f"✅ Mesaj trimis în {channel.mention}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Eroare: {e}",
                                                ephemeral=True)


@blackout.command(name="daily", description="Primește o misiune zilnică aleatorie")
async def daily(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)
        today = datetime.utcnow().date()

        if user_id not in user_data:
            user_data.setdefault(user_id, {"xp": 0, "level": 0, "rebirth": 0})

        last_claim_str = user_data[user_id].get("last_daily", "2000-01-01")
        last_claim = datetime.strptime(last_claim_str, "%Y-%m-%d").date()

        if today > last_claim:
            quest = generate_daily_quest()
            user_data[user_id]["last_daily"] = str(today)

            quest_data[user_id] = {
                "quest": quest["quest"],
                "type": quest["type"],
                "target": quest["target"],
                "reward": quest["reward"],
                "progress": 0
            }
            save_quest_data()
            save_user_data()

            await interaction.response.send_message(
                f"🗓️ Misiunea ta zilnică: **{quest['quest']}**\n"
                f"Recompensă: {quest['reward']} XP\n"
                "Succes!"
            )
        else:
            await interaction.response.send_message(
                "⏳ Ai deja o misiune zilnică activă sau ai revendicat deja azi. Revino mâine!"
            )
    except Exception as e:
        await interaction.response.send_message(f"❌ A apărut o eroare: `{e}`")

@app_commands.command(
    name="sent_anunt",
    description="Trimite anunțul oficial de YouTube în canalul ales")
@app_commands.describe(channel="Canalul în care vrei să trimiți anunțul")
@has_required_role()
async def sent_anunt(interaction: discord.Interaction,
                     channel: discord.TextChannel):
    embed = discord.Embed(
        title="🎉 Lansare YouTube BlackOut RO!",
        description=
        ("Suntem aproape 100 de membri pe acest server, iar ca răsplată BlackOut RO lansează canalul nostru oficial de YouTube! 🔥\n\n"
         "Vom juca jocuri împreună cu cei mai tari oameni din staff – și nu glumim:\n"
         "🎮 @pyandrei, @blacky, @bondes, @danly, @mazare, @rias sunt deja confirmați!\n\n"
         "Hai cu un subscribe aici și fii parte din vibe:\n👉 https://www.youtube.com/@blackout-ro\n\n"
         "📝 Vrei și TU să apari pe canal?\n"
         "Avem un formular deschis în #aplicatii-staff la secțiunea YouTube.\n"
         "Intră, aplică și fă parte din echipă! 🚀\n\n"
         "⚡ Powered by: BlackOut RO"),
        color=discord.Color.red())

    embed.set_footer(text="BlackOut RO")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.
                        icon else discord.Embed.Empty)

    await channel.send(embed=embed)
    await interaction.response.send_message(
        f"✅ Anunțul a fost trimis în {channel.mention}", ephemeral=True)


@blackout.command(name="rules",
                  description="Afișează regulamentul oficial BlackOut RO")
async def rules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Regulament Oficial — BlackOut RO",
        description=
        ("Citește cu atenție. Ignoranța nu scuză încălcarea regulilor.\n\n"
         "🔹 **Regula 1**\nRespectul față de toți membrii și staff este obligatoriu. Jignirile, rasismul, sexismul sau orice formă de discriminare sunt interzise.\n\n"
         "🔹 **Regula 2**\nReclama la alte servere, comunități, canale YouTube/Twitch etc. fără acordul staffului este interzisă.\n\n"
         "🔹 **Regula 3**\nSpam-ul, flood-ul, trimiterea de link-uri suspecte sau periculoase sunt interzise.\n\n"
         "🔹 **Regula 4**\nNumele, nickname-urile sau avatarurile indecente, provocatoare sau jignitoare sunt interzise.\n\n"
         "🔹 **Regula 5**\nGlumele sunt permise, dar fără umor ofensator sau provocator.\n\n"
         "🔹 **Regula 6**\nEvitați conflictele; apelați la staff sau rezolvați calm disputele.\n\n"
         "🔹 **Regula 7**\nÎn canalele vocale: nu vorbiți peste alții, nu țipați, păstrați atmosfera relaxată.\n\n"
         "🔹 **Regula 8**\nVoice changer & soundboard sunt permise doar cu acordul tuturor sau în canale speciale.\n\n"
         "🔹 **Regula 9**\nRespectă regulile și deciziile organizatorilor la evenimente.\n\n"
         "🔹 **Regula 10**\nNu cere premii sau role dacă nu ai câștigat la giveaway-uri.\n\n"
         "🔹 **Regula 11**\nÎncălcarea regulilor poate duce la mute, kick sau ban, în funcție de gravitate.\n\n"
         "🔹 **Regula 12**\nReclamațiile se fac în ticket, cu dovezi clare (poze/video).\n\n"
         "🔹 **Regula 13**\nRegulile nu se aplică în VC privat, dar fără conținut adult și cu bun simț.\n\n"
         "🔹 **Regula 14**\nEste interzis să ceri sau să oferi informații personale (nume, adresă, cont bancar etc.).\n\n"
         "🔹 **Regula 15**\nDacă ai probleme cu staff-ul, contactează fondatorii cu dovezi clare.\n\n"
         "🔹 **Regula 16**\nEste interzisă folosirea conturilor secundare pentru spam sau evitarea pedepselor.\n\n"
         "🔹 **Regula 17**\nRespectă regulile la jocuri și evenimente; trișatul duce la eliminare.\n\n"
         "🔹 **Regula 18**\nNu posta conținut șocant, violent sau deranjant.\n\n"
         "🔹 **Regula 19**\nStaff-ul nu e obligat să răspundă în DM. Folosește sistemul de ticket.\n\n"
         "🔹 **Regula 20**\nEste interzisă publicarea de poze/video din camere fără acordul persoanelor implicate.\n\n"
         "🔹 **Regula 21**\nNu folosiți @membru, @everyone sau @here.\n\n"
         "Respectă comunitatea • BlackOut RO"),
        color=discord.Color.dark_blue())
    embed.set_footer(
        text="📢 Pentru orice nelămurire, contactează staff-ul serverului.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

YOUR_OWNER_ID = 711202139434647642

import json
from discord import app_commands, Interaction

OWNER_ID = 711202139434647642  # Replace with your Discord user ID


@blackout.command(name="leaderboard_lunar",
                  description="Vezi top 10 utilizatori după XP lunar")
async def leaderboard_lunar(interaction: discord.Interaction):
    try:
        with open("monthly_data.json", "r", encoding="utf-8") as f:
            monthly_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        monthly_data = {}

    if not monthly_data:
        await interaction.response.send_message("📭 Nu există date pentru luna aceasta.")
        return

    sorted_users = sorted(monthly_data.items(),
                          key=lambda x: x[1].get("xp", 0),
                          reverse=True)

    embed = discord.Embed(title="📅 Leaderboard Lunar",
                          description="Top 10 utilizatori cu cel mai mult XP în această lună",
                          color=discord.Color.teal())

    first_user = None
    for i, (user_id, data) in enumerate(sorted_users[:10], start=1):
        try:
            member = interaction.guild.get_member(int(user_id))
            if member is None:
                member = await interaction.guild.fetch_member(int(user_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            member = None

        name = member.display_name if member else f"User ID {user_id}"
        xp = data.get("xp", 0)

        if i == 1 and member and member.avatar:
            first_user = member

        embed.add_field(
            name=f"{i}. {name}",
            value=f"✨ XP lunar: `{xp}`",
            inline=False
        )

    if first_user and first_user.avatar:
        embed.set_thumbnail(url=first_user.avatar.url)

    embed.set_footer(text="📆 Clasament lunar actualizat")
    embed.timestamp = datetime.now(timezone.utc)

    await interaction.response.send_message(embed=embed)

@blackout.command(
    name="showdata",
    description="Arată datele JSON ale botului (doar owner)"
)
async def showdata(interaction: Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "Nu ai permisiunea să folosești această comandă.", ephemeral=True
        )
        return

    # Load JSON data
    with open('data_nou.json', 'r') as f:
        data = json.load(f)

    data_str = json.dumps(data, indent=4)

    # If data is too large to send in one message
    if len(data_str) > 1900:
        await interaction.response.send_message(
            "Datele sunt prea mari, le trimit prin DM.", ephemeral=True
        )
        try:
            await interaction.user.send(file=discord.File('data_nou.json'))
        except Exception:
            await interaction.followup.send(
                "Nu pot să trimit mesaj privat.", ephemeral=True
            )
    else:
        await interaction.response.send_message(f"```json\n{data_str}\n```", ephemeral=True)

@blackout.command(
    name="showmonthly",
    description="Arată leaderboard-ul lunar (doar owner)"
)
async def showmonthly(interaction: Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "Nu ai permisiunea să folosești această comandă.", ephemeral=True
        )
        return

    try:
        with open('monthly_data.json', 'r', encoding='utf-8') as f:
            monthly_data = json.load(f)
    except Exception as e:
        await interaction.response.send_message(
            f"Eroare la încărcarea leaderboard-ului lunar: {e}", ephemeral=True
        )
        return

    data_str = json.dumps(monthly_data, indent=4, ensure_ascii=False)

    if len(data_str) > 1900:
        await interaction.response.send_message(
            "Leaderboard-ul este prea mare, îl trimit prin mesaj privat.", ephemeral=True
        )
        try:
            await interaction.user.send(file=discord.File('monthly_data.json'))
        except Exception:
            await interaction.followup.send(
                "Nu pot să trimit mesaj privat. Verifică setările tale de DM.", ephemeral=True
            )
    else:
        await interaction.response.send_message(f"```json\n{data_str}\n```", ephemeral=True)

# Then register this group in your bot setup code:
@blackout.command(
    name="quest_data",
    description="Arată datele JSON ale misiunilor (doar owner)"
)
async def show_quest_data(interaction: Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "Nu ai permisiunea să folosești această comandă.", ephemeral=True
        )
        return

    # Load JSON quest data
    with open('data_quest.json', 'r') as f:
        data = json.load(f)

    data_str = json.dumps(data, indent=4)

    if len(data_str) > 1900:
        await interaction.response.send_message(
            "Datele sunt prea mari, le trimit prin DM.", ephemeral=True
        )
        try:
            await interaction.user.send(file=discord.File('data_quest.json'))
        except Exception:
            await interaction.followup.send(
                "Nu pot să trimit mesaj privat.", ephemeral=True
            )
    else:
        await interaction.response.send_message(f"```json\n{data_str}\n```", ephemeral=True)

@blackout.command(name="profile", description="Vezi profilul tău Blackout")
@app_commands.describe(user="Utilizatorul căruia vrei să-i vezi profilul")
async def profile(interaction: discord.Interaction,
                  user: discord.Member = None):
    user = user or interaction.user
    user_id = str(user.id)
    data = user_data.get(user_id, {"xp": 0, "level": 0, "rebirth": 0})

    level = data["level"]
    xp = data["xp"]
    rebirth = data.get("rebirth", 0)
    next_level_xp = xp_needed(level + 1)

    # 🔄 Calcul progres pentru bară XP
    progress_percent = round((xp / next_level_xp) * 100)
    filled_blocks = progress_percent // 10
    progress_bar = f"[{'█' * filled_blocks}{'—' * (10 - filled_blocks)}]"

    # 🔥 Emoji vizual rebirth
    rebirth_display = f"🔥 x{rebirth}" if rebirth > 0 else "—"

    embed = discord.Embed(title=f"🎮 Profil — {user.display_name}",
                          description=f"🆔 `{user.id}`",
                          color=discord.Color.purple())

    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(name="🧱 Nivel", value=f"`{level}`", inline=True)
    embed.add_field(name="💥 XP",
                    value=f"`{xp} / {next_level_xp}`",
                    inline=True)
    embed.add_field(name="🔁 Rebirth",
                    value=f"`{rebirth_display}`",
                    inline=True)

    embed.add_field(name="📊 Progres către nivelul următor",
                    value=f"{progress_bar} `{progress_percent}%`",
                    inline=False)

    embed.set_footer(text="Sistemul de leveling Blackout")
    embed.timestamp = datetime.now(timezone.utc)

    await interaction.response.send_message(embed=embed)


# --- Pornire bot ---
# --- ENV PENTRU TOKEN ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ TOKEN is missing! Asigură-te că este setat în .env")

bot.run(TOKEN)
