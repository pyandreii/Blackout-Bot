from discord.ext import commands, tasks
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import random
from discord import app_commands
import discord
from dotenv import load_dotenv
import os
import copy
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
# --- Configurare ---

ID_SERVER_PRINCIPAL = 1372682829074530335
text_channel_id = 1389616154259226625
CO_OWNER_ROLE_ID = 1397521192092700702
REQUIRED_ROLE_ID = 1397521192092700702
BUMP_CHANNEL_ID = 1390006025532211310
DISBOARD_ID = 302050872383242240
WELCOME_CHANNEL_ID = 1389567710693953606
GOODBYE_CHANNEL_ID = 1389614232948965447
ANIME_ROLE_ID = 1400429087989825669

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
DAILY_QUESTS = [
    {
        "quest": "Trimite 20 de mesaje pe server",
        "type": "messages",
        "target": 20,
        "reward": 100,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Stai 15 minute în voice chat",
        "type": "voice_minutes",
        "target": 15,
        "reward": 120,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Trimite 10 mesaje într-un canal text",
        "type": "messages",
        "target": 10,
        "reward": 80,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Fii activ în voice chat timp de 30 minute",
        "type": "voice_minutes",
        "target": 30,
        "reward": 200,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Dă tag unui prieten într-un mesaj pe server",
        "type": "mention_friend",
        "target": 1,
        "reward": 90,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Reacționează la 5 mesaje ale altor membri",
        "type": "reactions",
        "target": 5,
        "reward": 70,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Răspunde la o întrebare în chat",
        "type": "reply",
        "target": 1,
        "reward": 100,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Dă bump la server",
        "type": "bump_server",
        "target": 1,
        "reward": 100,
        "progress": 0,
        "completed": False
    },
    {
        "quest": "Invită un prieten pe server",
        "type": "invite_friend",
        "target": 1,
        "reward": 400,
        "progress": 0,
        "completed": False
    }
]
color_roles = {
    "❤️ Roșu": 1400413166919352413,  # <- Pune ID-ul rolului roșu
    "🍊 Portocaliu": 1400413294149505024,
    "☘️ Verde": 1400413045670281377,
    "🌸 Roz": 1400412305161846815,
    "👾 Mov": 1400412912690008175,
    "🌊 Albastru": 1400412390117605376,
    "🦇 Gri": 1400412596691009637,
    "☀️ Galben": 1400412453208064060,
    "🌑 Negru": 1400416592361422923,
}

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

def assign_daily_quest(user_id: str):
    if user_id not in quest_data:
        quest_data[user_id] = {}

    # Selectează o misiune aleatorie
    quest = copy.deepcopy(random.choice(DAILY_QUESTS))

    # Inițializează progresul și starea
    quest.setdefault("progress", 0)
    quest.setdefault("completed", False)

    # Salvează în quest_data
    quest_data[user_id] = quest

    save_quest_data()


def add_xp(user_id: str, amount: int, source: str = "text"):
    user_data.setdefault(user_id, {"xp": 0, "level": 0, "rebirth": 0})
    user_data[user_id]["xp"] += amount

    monthly_data.setdefault(user_id, {"xp": 0, "voice_xp": 0})

    if source == "voice":
        monthly_data[user_id]["voice_xp"] += amount
    else:
        monthly_data[user_id]["xp"] += amount

    save_user_data()
    save_monthly_data()

def get_total_monthly_xp(user_id: str) -> int:
    data = monthly_data.get(user_id, {})
    return data.get("xp", 0) + data.get("voice_xp", 0)

def has_required_role():

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ Eroare: utilizator necunoscut.", ephemeral=True)
            return False
        return any(role.id == REQUIRED_ROLE_ID
                   for role in interaction.user.roles)

    return app_commands.check(predicate)


async def finalize_quest(user, quest):
    try:
        if quest.get("completed", False):
            print(f"[INFO] Quest-ul este deja completat pentru userul {user.id}. Nu acord XP din nou.")
            return

        print(f"[DEBUG] finalize_quest apelat pentru user: {user} (ID: {user.id}), quest: {quest.get('type')}")

        guild = getattr(user, "guild", None)
        channel = None
        if guild:
            channel = guild.get_channel(text_channel_id)
        else:
            channel = bot.get_channel(text_channel_id)

        if not channel:
            print(f"[WARN] Canalul cu ID {text_channel_id} nu a fost găsit.")
            return

        # ✅ Acordă XP o singură dată
        user_id_str = str(user.id)
        if user_id_str in user_data:
            user_data[user_id_str]["xp"] += quest.get("reward", 0)
        else:
            user_data[user_id_str] = {
                "xp": quest.get("reward", 0),
                "level": 0,
                "rebirth": 0
            }

        quest["completed"] = True
        quest_data[user_id_str] = quest

        # Salvări
        save_user_data()
        save_quest_data()

        # ✅ Trimite mesaj pe canal
        await channel.send(
            f"🎉 {user.mention} ai finalizat misiunea **{quest.get('type', 'necunoscută')}** și ai primit {quest.get('reward', 0)} XP!"
        )

    except Exception as e:
        print(f"[EROARE finalize_quest] {e}")

spam_limit_count = 3
spam_limit_seconds = 5

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True


# --- Variabile globale ---

user_recent_messages = defaultdict(deque)


def generate_daily_quest():
    allowed_types = {"messages", "reactions", "voice_minutes", "mention_friend", "reply", "bump_server", "invite_friend"}
    filtered = []

    for q in DAILY_QUESTS:
        if q["type"] in allowed_types:
            if q["type"] == "invite_friend":
                if random.random() < 0.05:  # 5% șansă
                    filtered.append(q)
            else:
                filtered.append(q)

    if not filtered:
        raise ValueError("Nu există misiuni valide în DAILY_QUESTS!")

    return random.choice(filtered)


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
        channel = guild.get_channel(text_channel_id)
        save_needed = False

        for vc in guild.voice_channels:
            for member in vc.members:
                if member.bot:
                    continue

                voice_state = member.voice
                if not voice_state or voice_state.self_deaf or voice_state.deaf:
                    continue

                user_id = str(member.id)

                # Inițializare user_data
                if user_id not in user_data:
                    user_data[user_id] = {"xp": 0, "level": 0, "rebirth": 0}

                # === QUEST: voice_minutes ===
                quest = quest_data.get(user_id)
                if quest and quest.get("type") == "voice_minutes" and not quest.get("completed", False):
                    quest["progress"] += 1
                    print(f"[VOICE QUEST] {member.display_name}: {quest['progress']}/{quest.get('target', 0)}")

                    if quest["progress"] >= quest.get("target", 0):
                        await finalize_quest(member, quest)

                    quest_data[user_id] = quest
                    save_needed = True

                # === XP + LEVEL-UP ===
                add_xp(user_id, 10, source="voice")
                current_xp = user_data[user_id]["xp"]
                current_level = user_data[user_id]["level"]
                next_level_xp = xp_needed(current_level + 1)

                leveled_up = False
                while current_xp >= next_level_xp:
                    current_xp -= next_level_xp
                    current_level += 1
                    user_data[user_id]["level"] = current_level
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
                        await channel.send(
                            f"{member.mention} a ajuns la nivelul {current_level}! 🎉"
                        )

        if save_needed:
            save_quest_data()
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

invite_cache = {}

async def cache_invites(guild):
    try:
        invite_cache[guild.id] = await guild.invites()
        print(f"✅ Cached invites pentru guild: {guild.name} ({guild.id})")
    except discord.Forbidden:
        print(f"❌ Botul nu are permisiuni pentru `guild.invites()` în: {guild.name} ({guild.id})")
        invite_cache[guild.id] = []

font = ImageFont.truetype("Font/arial.ttf", 40)

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    # ========================
    # 🎯 INVITE TRACKING
    # ========================
    inviter = await get_inviter(member)
    if inviter:
        user_id = str(inviter.id)
        quest = quest_data.get(user_id)

        if quest and quest.get("type") == "invite_friend" and not quest.get("completed", False):
            quest["progress"] += 1
            if quest["progress"] >= quest.get("target", 1):
                await finalize_quest(inviter, quest)

            quest_data[user_id] = quest
            save_quest_data()

        # 🔁 actualizează cache-ul de invitații
        try:
            invite_cache[guild.id] = await guild.invites()
        except discord.Forbidden:
            invite_cache[guild.id] = []

    # ========================
    # 👋 WELCOME MESSAGE
    # ========================
    welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel:
        embed = discord.Embed(
            title=f"👋 Bun venit pe {guild.name}!",
            description=f"{member.mention}, ne bucurăm că ești aici! 🎉",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 Nume", value=member.name, inline=True)
        embed.add_field(name="📆 Cont creat", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        embed.set_footer(text="BlackOut RO • Welcome System")
        embed.timestamp = datetime.now(timezone.utc)

        try:
            await welcome_channel.send(embed=embed)
        except Exception as e:
            print(f"[EROARE welcome embed] {e}")

            # ========================
            # 🖼️ Imagine de welcome
            # ========================
            try:
                avatar_url = member.display_avatar.replace(format="png", size=128).url

                # ✅ Descarcă avatarul userului
                async with aiohttp.ClientSession() as session:
                    async with session.get(avatar_url) as resp:
                        if resp.status != 200:
                            raise Exception("Nu am putut descărca avatarul.")
                        avatar_bytes = await resp.read()

                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                avatar_img = avatar_img.resize((128, 128))

                # ✅ Creează banner simplu (800x250)
                bg = Image.new("RGBA", (800, 250), (30, 30, 30, 255))
                draw = ImageDraw.Draw(bg)

                # ✅ Încarcă font (folosește unul local sau system)
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except:
                    font = ImageFont.load_default()

                # ✅ Scrie text pe imagine
                text = f"Bun venit, {member.name}!"
                draw.text((180, 90), text, font=font, fill=(255, 255, 255, 255))

                # ✅ Adaugă avatar pe imagine
                bg.paste(avatar_img, (30, 60), avatar_img)

                # ✅ Salvează temporar
                path = f"/tmp/welcome_{member.id}.png"
                bg.save(path)

                # ✅ Trimite imagine în canal
                await welcome_channel.send(file=discord.File(path))

            except Exception as e:
                print(f"[EROARE WELCOME IMAGE] {e}")

@bot.event
async def on_member_remove(member: discord.Member):
    guild = member.guild
    goodbye_channel = guild.get_channel(GOODBYE_CHANNEL_ID)

    if goodbye_channel:
        embed = discord.Embed(
            title="👋 Un membru a părăsit serverul...",
            description=f"{member.mention} ne-a părăsit. Sper să revii pe server. 😢",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Nume", value=member.name, inline=True)
        embed.add_field(name="Cont creat", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        embed.set_footer(text="BlackOut RO • Goodbye System")
        embed.timestamp = datetime.now(timezone.utc)

        try:
            await goodbye_channel.send(embed=embed)
        except Exception as e:
            print(f"[EROARE goodbye embed] {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot conectat ca {bot.user}")
    await bot.change_presence(activity=discord.CustomActivity(name="❤️ Vă iubesc, BlackOut RO! Mereu voi fi aici"))
    print(f"Guild-uri pe care sunt: {[guild.id for guild in bot.guilds]}")

    for guild in bot.guilds:
        await cache_invites(guild)

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
        return

    user_id = str(payload.user_id)
    quest = quest_data.get(user_id)

    if quest and quest.get("type") == "reactions" and not quest.get("completed", False):
        quest["progress"] += 1
        target = quest.get("target", 0)

        if quest["progress"] >= target:
            save_user_data()
            await finalize_quest(await bot.fetch_user(payload.user_id), quest)
        else:
            print(f"[REACTION QUEST] {payload.user_id} progres: {quest['progress']}/{target}")

        quest_data[user_id] = quest
        save_quest_data()

async def get_inviter(member):
    guild = member.guild
    old_invites = invite_cache.get(guild.id, [])
    new_invites = await guild.invites()

    invite_cache[guild.id] = new_invites  # update cache

    for invite in new_invites:
        for old_inv in old_invites:
            if invite.code == old_inv.code and invite.uses > old_inv.uses:
                return invite.inviter
    return None

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    user_id = str(message.author.id)
    now = datetime.now(timezone.utc)

    # === XP & Anti-Spam ===
    user_recent_messages[user_id].append(message)
    while user_recent_messages[user_id] and (now - user_recent_messages[user_id][0].created_at).total_seconds() > spam_limit_seconds:
        user_recent_messages[user_id].popleft()

    if len(user_recent_messages[user_id]) > spam_limit_count:
        try:
            for msg in list(user_recent_messages[user_id]):
                try:
                    await msg.delete()
                except:
                    pass
            user_recent_messages[user_id].clear()
            warn_msg = await message.channel.send(f"{message.author.mention}, nu spamma, te rog! Vei fi mutat temporar.")
            await message.author.timeout(timedelta(seconds=30), reason="Spam detectat")
            await warn_msg.delete(delay=5)
        except Exception as e:
            print(f"[Eroare spam] {e}")
        return

    # === XP normal ===
    add_xp(user_id, 5, source="text")
    monthly_data.setdefault(user_id, {"xp": 0, "voice_xp": 0})
    monthly_data[user_id]["xp"] += 10
    save_monthly_data()

    # === Questuri ===
    quest = quest_data.get(user_id)
    if quest and not quest.get("completed", False):
        qtype = quest.get("type")

        if qtype == "messages":
            quest["progress"] += 1

        elif qtype == "mention_friend":
            if message.mentions and any(m.id != message.author.id for m in message.mentions):
                quest["progress"] += 1

        elif qtype == "reply":
            if message.reference:
                quest["progress"] += 1

    # === BUMP ===
    if message.channel.id == BUMP_CHANNEL_ID and message.author.id == DISBOARD_ID:
        if "bump done" in message.content.lower() or "server bumped" in message.content.lower():
            if message.mentions:
                bumper = message.mentions[0]
                user_id = str(bumper.id)
                quest = quest_data.get(user_id)

                if quest and quest.get("type") == "bump_server" and not quest.get("completed", False):
                    quest["progress"] = quest.get("progress", 0) + 1

                    if quest["progress"] >= quest.get("target", 1):
                        await finalize_quest(bumper, quest)

                    quest_data[user_id] = quest
                    save_quest_data()

    # === Finalizare quest dacă e complet ===
    if quest and quest["progress"] >= quest.get("target", 0) and not quest.get("completed", False):
        await finalize_quest(message.author, quest)

    # Salvare
    if quest:
        quest_data[user_id] = quest
        save_quest_data()
    save_user_data()

    # Level up check
    await level_up_check(message, user_id)
    await bot.process_commands(message)



async def level_up_check(message, user_id):
    xp = user_data[user_id]["xp"]
    level = user_data[user_id]["level"]
    rebirth = user_data[user_id].get("rebirth", 0)
    channel = message.guild.get_channel(text_channel_id)

    next_level_xp = xp_needed(level + 1)

    while xp >= next_level_xp:
        xp -= next_level_xp
        level += 1
        user_data[user_id]["level"] = level
        user_data[user_id]["xp"] = xp

        # Reset rebirth dacă nivelul atinge 30
        if level >= 30:
            user_data[user_id]["level"] = 0
            user_data[user_id]["xp"] = 0
            user_data[user_id]["rebirth"] = rebirth + 1
            rebirth = user_data[user_id]["rebirth"]

            if channel:
                await channel.send(
                    f"🔁 {message.author.mention} a făcut **Rebirth {rebirth}** și nivelul a fost resetat!"
                )

            role_id = rebirth_roles.get(rebirth)
            if role_id:
                rb_role = message.guild.get_role(role_id)
                if rb_role and rb_role not in message.author.roles:
                    await message.author.add_roles(rb_role)

            for lvl, rid in rebirth_roles.items():
                if lvl != rebirth:
                    old_role = message.guild.get_role(rid)
                    if old_role and old_role in message.author.roles:
                        await message.author.remove_roles(old_role)

            next_level_xp = xp_needed(user_data[user_id]["level"] + 1)
            break

        else:
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

    save_user_data()
    save_quest_data()

    await bot.process_commands(message)


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

class AnimeRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎌 Sunt fan Anime", style=discord.ButtonStyle.primary, custom_id="anime_fan_role")
    async def anime_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ANIME_ROLE_ID)

        if not role:
            await interaction.response.send_message("❌ Rolul Anime Fan nu a fost găsit.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Ți-am scos rolul {role.name}.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"🎌 Ți-am dat rolul {role.name}.", ephemeral=True)

class ColorRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for emoji_label, role_id in color_roles.items():
            button = discord.ui.Button(label=emoji_label, style=discord.ButtonStyle.secondary, custom_id=str(role_id))
            button.callback = self.color_button_callback
            self.add_item(button)

    async def color_button_callback(self, interaction: discord.Interaction):
        role_id = int(interaction.data['custom_id'])
        role = interaction.guild.get_role(role_id)

        if not role:
            await interaction.response.send_message("❌ Rolul nu a fost găsit.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Ți-am scos rolul {role.name}.", ephemeral=True)
        else:
            # Eliminăm alte culori existente
            user_roles = [interaction.guild.get_role(rid) for rid in color_roles.values()]
            roles_to_remove = [r for r in user_roles if r in interaction.user.roles]

            if roles_to_remove:
                await interaction.user.remove_roles(*roles_to_remove)

            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"🎨 Ți-am dat rolul {role.name}.", ephemeral=True)

class RebirthConfirmView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)  # timeout 60 sec
        self.user_id = user_id
        self.value = None  # pentru a ști ce a ales userul

    @discord.ui.button(label="✅ Confirmă Rebirth", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Aceasta nu e comanda ta!", ephemeral=True)
            return

        # Resetează nivelul, XP și crește rebirth
        data = user_data.get(self.user_id)
        if not data:
            await interaction.response.send_message("Nu am găsit datele tale.", ephemeral=True)
            self.value = False
            self.stop()
            return

        if data.get("level", 0) < 30:
            await interaction.response.send_message("Trebuie să fii nivel 30 pentru Rebirth.", ephemeral=True)
            self.value = False
            self.stop()
            return

        data["level"] = 0
        data["xp"] = 0
        data["rebirth"] = data.get("rebirth", 0) + 1

        await interaction.response.edit_message(content=f"🔁 Felicitări! Ai făcut Rebirth **{data['rebirth']}**. Nivelul tău a fost resetat.", view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label="❌ Renunță", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Aceasta nu e comanda ta!", ephemeral=True)
            return

        await interaction.response.edit_message(content="Rebirth anulat.", view=None)
        self.value = False
        self.stop()


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

    embed = discord.Embed(
        title="🏆 Clasament Global — Top XP",
        description="Cei mai activi membri de pe server:",
        color=discord.Color.gold()
    )

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

        if member:
            await update_rebirth_role(member, rebirth)

        # 🏅 Emoji-uri pentru top 3
        if i == 1:
            medal = "🥇"
            if member and member.avatar:
                first_user = member
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"`#{i}`"

        # 🔁 Afisare rebirth doar dacă există
        rebirth_display = f"• 🔁 `{rebirth}`" if rebirth > 0 else ""

        # 🧾 Conținutul fiecărei linii
        value = (
            f"🧱 Nivel: `{level}`\n"
            f"✨ XP: `{xp}`\n"
            f"{rebirth_display}"
        )

        embed.add_field(name=f"{medal} {name}", value=value.strip(), inline=False)

    # 🖼️ Avatar top 1 ca thumbnail
    if first_user and first_user.avatar:
        embed.set_thumbnail(url=first_user.avatar.url)

    embed.set_footer(text="📊 Clasament actualizat live • BlackOut RO")
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
    await interaction.response.defer(ephemeral=True)

    try:
        user_id = str(interaction.user.id)
        today = datetime.utcnow().date()

        if user_id not in user_data:
            user_data[user_id] = {"xp": 0, "level": 0, "rebirth": 0}

        last_claim_str = user_data[user_id].get("last_daily", "2000-01-01")
        last_claim = datetime.strptime(last_claim_str, "%Y-%m-%d").date()
        if today > last_claim or user_id not in quest_data:
            quest = generate_daily_quest()
            user_data[user_id]["last_daily"] = str(today)

            quest_data[user_id] = {
                "quest": quest["quest"],
                "type": quest["type"],
                "target": quest["target"],
                "reward": quest["reward"],
                "progress": 0,
                "completed": False
            }

            save_quest_data()
            save_user_data()

            await interaction.followup.send(
                f"🗓️ Misiunea ta zilnică: **{quest['quest']}**\n"
                f"🎁 Recompensă: `{quest['reward']} XP`\n"
                f"📈 Progres: `0 / {quest['target']}`\nSucces!"
            )

        else:
            # ✅ Arată progresul dacă deja are un quest azi
            current_quest = quest_data.get(user_id)
            if current_quest:
                progres = current_quest.get("progress", 0)
                target = current_quest.get("target", 1)
                bar_length = 20
                filled = int(bar_length * progres / target)
                bar = "█" * filled + "░" * (bar_length - filled)

                await interaction.followup.send(
                    f"⏳ Ai deja o misiune zilnică activă:\n"
                    f"📌 **{current_quest['quest']}**\n"
                    f"📈 Progres: `{progres} / {target}`\n"
                    f"[{bar}]\n"
                    f"🎁 Recompensă: **{current_quest['reward']} XP**\n"
                    f"🔁 Revino mâine pentru o nouă misiune!"
                )
            else:
                await interaction.followup.send(
                    "⚠️ Ai folosit comanda, dar nu există nicio misiune activă. Raportează asta unui admin.",
                    ephemeral=True
                )

    except Exception as e:
        print(f"[EROARE DAILY] {e}")
        await interaction.followup.send(f"❌ A apărut o eroare: `{e}`", ephemeral=True)

from discord import app_commands
from discord.ext.commands import has_role

@app_commands.command(
    name="sent_anunt",
    description="Trimite anunțul oficial despre leaderboard-ul lunar și comenzile BlackOut")
@app_commands.describe(channel="Canalul în care vrei să trimiți anunțul")
@has_required_role()  # Asigură-te că ai definit decoratorul corect sau înlocuiește cu @app_commands.check
async def sent_anunt(interaction: discord.Interaction,
                     channel: discord.TextChannel):
    embed = discord.Embed(
        title="📢 Noutăți BlackOut RO: Leaderboard Lunar și Misiuni Zilnice!",
        description=(
            "Am lansat un **Leaderboard Lunar** unde poți câștiga roluri exclusive pentru activitatea ta lunară! 🏆\n\n"
            "**Folosește comenzile disponibile pentru a fi mereu la curent și pentru a revendica recompense:**\n"
            "✨ `/blackout daily` — revendică misiunea zilnică și câștigă XP bonus.\n"
            "📋 `/blackout quest` — verifică progresul misiunilor tale curente.\n"
            "🏅 `/blackout leaderboard_lunar` — vezi topul celor mai activi membri ai lunii.\n\n"
            "Fii activ, completează misiuni și urcă în clasament pentru a primi roluri speciale! 🎉"
        ),
        color=discord.Color.blue()
    )
    embed.set_footer(text="BlackOut RO")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)

    await channel.send(embed=embed)
    await interaction.response.send_message(f"Anunțul a fost trimis în {channel.mention}", ephemeral=True)

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
         "🔹 **Regula 13**\nRegulile nu se aplică în VC privat.\n\n"
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

@blackout.command(name="quest", description="Afișează progresul tău la misiunea zilnică")
async def quest_status(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    quest = quest_data.get(user_id)

    if not quest:
        await interaction.response.send_message("❌ Nu ai nicio misiune activă.", ephemeral=True)
        return

    progres = quest.get("progress", 0)
    target = quest.get("target", 1)
    bar_length = 20
    filled = int(bar_length * progres / target)
    bar = "█" * filled + "░" * (bar_length - filled)

    await interaction.response.send_message(
        f"📌 Misiunea ta: **{quest['quest']}**\n"
        f"📈 Progres: `{progres}/{target}`\n"
        f"[{bar}]\n"
        f"🎁 Recompensă: **{quest['reward']} XP**",
        ephemeral=True
    )

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
                          key=lambda x: x[1].get("xp", 0) + x[1].get("voice_xp", 0),
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

        xp_text = data.get("xp", 0)
        xp_voice = data.get("voice_xp", 0)
        total_xp = xp_text + xp_voice

        embed.add_field(
            name=f"{i}. {name}",
            value=f"✨ XP lunar: `{total_xp}` (Text: `{xp_text}`, Voice: `{xp_voice}`)",
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
    name="rebirth",
    description="Efectuează Rebirth dacă ai nivelul 30"
)
async def rebirth(interaction: Interaction):
    user_id = interaction.user.id
    data = user_data.get(user_id)

    if not data or data.get("level", 0) < 30:
        await interaction.response.send_message(
            "Trebuie să ai nivelul 30 pentru a face Rebirth.", ephemeral=True
        )
        return

    view = RebirthConfirmView(user_id)
    await interaction.response.send_message(
        f"{interaction.user.mention}, ești sigur că vrei să faci Rebirth? Nivelul și XP vor fi resetate.",
        view=view,
        ephemeral=True
    )

    await view.wait()

    if view.value is None:
        await interaction.followup.send(
            "Timpul pentru confirmare a expirat.", ephemeral=True
        )

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

@blackout.command(name="colors", description="(OWNER) Trimite mesajul de alegere culori")
@app_commands.describe(channel="Canalul în care să trimiți mesajul")
async def colors(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("⛔ Nu ai permisiunea să folosești această comandă.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎨 Alege-ți culoarea preferată!",
        description="Apasă pe unul dintre butoanele de mai jos pentru a-ți seta culoarea pe server.\n"
                    "Dacă apesi din nou pe aceeași culoare, rolul ți se va scoate.",
        color=discord.Color.blurple()
    )

    await channel.send(embed=embed, view=ColorRoleView())
    await interaction.response.send_message(f"✅ Mesajul a fost trimis în {channel.mention}", ephemeral=True)

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

@blackout.command(name="anime", description="(OWNER) Trimite mesajul pentru rolul Anime Fan")
@app_commands.describe(channel="Canalul în care să trimiți mesajul")
async def anime(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("⛔ Nu ai permisiunea să folosești această comandă.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎌 Ești fan Anime?",
        description="Dacă ești pasionat de anime și vrei să primești notificări sau să discuți cu alți otaku, apasă butonul de mai jos!",
        color=discord.Color.magenta()
    )

    await channel.send(embed=embed, view=AnimeRoleView())
    await interaction.response.send_message(f"✅ Mesajul a fost trimis în {channel.mention}", ephemeral=True)

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


    embed = discord.Embed(
        title=f"🧑‍🚀 Profilul lui {user.display_name}",
        description=f"🆔 `{user.id}`",
        color=discord.Color.from_str("#9c88ff")  # violet deschis
    )

    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(
        name="🏅 Nivel & XP",
        value=f"**{level}**  •  `{xp} / {next_level_xp}` XP",
        inline=False
    )

    embed.add_field(
        name="🔁 Rebirth",
        value=f"`{rebirth}` {rebirth_display}",
        inline=True
    )

    embed.add_field(
        name="📈 Progres",
        value=f"{progress_bar} `{progress_percent}%`",
        inline=True
    )

    embed.set_footer(text="⚡ Sistemul de leveling BlackOut")
    embed.timestamp = datetime.now(timezone.utc)

    await interaction.response.send_message(embed=embed)


# --- Pornire bot ---
# --- ENV PENTRU TOKEN ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ TOKEN is missing! Asigură-te că este setat în .env")

bot.run(TOKEN)
