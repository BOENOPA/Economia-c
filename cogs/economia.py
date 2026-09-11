import json
import random
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "economia.json"

# FIX PARA RENDER
DATA_DIR.mkdir(parents=True, exist_ok=True)

if not DATA_FILE.exists():
    DATA_FILE.write_text(
        '{"guilds": {}}',
        encoding="utf-8"
    )


# ============================================================
# CONFIGURACIÓN
# ============================================================

PURPLE = discord.Color.from_rgb(115, 55, 210)

START_MONEY = 1000

DAILY_MIN = 500
DAILY_MAX = 1500

WORK_MIN = 100
WORK_MAX = 500

BEG_MIN = 50
BEG_MAX = 250

MAX_BET = 100000

DAILY_COOLDOWN = 86400
WORK_COOLDOWN = 3600
BEG_COOLDOWN = 1800


# ============================================================
# UTILIDADES
# ============================================================

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            data = {"guilds": {}}

        if "guilds" not in data:
            data["guilds"] = {}

        return data

    except (FileNotFoundError, json.JSONDecodeError):
        return {"guilds": {}}


def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = DATA_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    temp_file.replace(DATA_FILE)


def now():
    return int(time.time())


def format_money(amount):
    return f"${amount:,}".replace(",", ".")


# ============================================================
# COG
# ============================================================

class Economia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    # ========================================================
    # DATOS
    # ========================================================

    def get_guild(self, guild_id):

        guild_id = str(guild_id)

        if guild_id not in self.data["guilds"]:
            self.data["guilds"][guild_id] = {
                "users": {},
                "permissions": {
                    "give-money": [],
                    "remove-money": [],
                    "set-money": [],
                    "reset-money": [],
                    "add-bank": [],
                    "remove-bank": [],
                    "set-bank": []
                },
                "log_channel": None
            }

        guild = self.data["guilds"][guild_id]

        if "users" not in guild:
            guild["users"] = {}

        if "permissions" not in guild:
            guild["permissions"] = {}

        default_permissions = {
            "give-money": [],
            "remove-money": [],
            "set-money": [],
            "reset-money": [],
            "add-bank": [],
            "remove-bank": [],
            "set-bank": []
        }

        for key, value in default_permissions.items():
            guild["permissions"].setdefault(key, value)

        guild.setdefault("log_channel", None)

        return guild

    def get_user(self, guild_id, user_id):

        guild = self.get_guild(guild_id)

        user_id = str(user_id)

        if user_id not in guild["users"]:
            guild["users"][user_id] = {
                "cash": START_MONEY,
                "bank": 0,

                "daily": 0,
                "work": 0,
                "beg": 0,

                "inventory": {},

                "stats": {
                    "messages": 0,
                    "daily_claims": 0,
                    "work_claims": 0,
                    "beg_claims": 0,
                    "money_earned": 0,
                    "money_spent": 0,
                    "games_played": 0,
                    "games_won": 0,
                    "games_lost": 0
                }
            }

        user = guild["users"][user_id]

        user.setdefault("cash", START_MONEY)
        user.setdefault("bank", 0)

        user.setdefault("daily", 0)
        user.setdefault("work", 0)
        user.setdefault("beg", 0)

        user.setdefault("inventory", {})

        user.setdefault("stats", {})

        stats_defaults = {
            "messages": 0,
            "daily_claims": 0,
            "work_claims": 0,
            "beg_claims": 0,
            "money_earned": 0,
            "money_spent": 0,
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0
        }

        for key, value in stats_defaults.items():
            user["stats"].setdefault(key, value)

        return user

    # ========================================================
    # PERMISOS DE ECONOMÍA
    # ========================================================

    def can_use_economy_admin(
        self,
        interaction: discord.Interaction,
        action: str
    ):

        if interaction.guild is None:
            return False

        member = interaction.user

        # Dueño del servidor
        if member.id == interaction.guild.owner_id:
            return True

        guild = self.get_guild(interaction.guild.id)

        allowed_roles = guild["permissions"].get(action, [])

        # Si no hay ningún rol configurado,
        # Administradores pueden usarlo.
        if not allowed_roles:
            return member.guild_permissions.administrator

        member_roles = {role.id for role in member.roles}

        return any(
            int(role_id) in member_roles
            for role_id in allowed_roles
        )

    # ========================================================
    # LOGS
    # ========================================================

    async def economy_log(
        self,
        guild: discord.Guild,
        title: str,
        description: str
    ):

        guild_data = self.get_guild(guild.id)

        channel_id = guild_data.get("log_channel")

        if not channel_id:
            return

        channel = guild.get_channel(int(channel_id))

        if channel is None:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=PURPLE,
            timestamp=discord.utils.utcnow()
        )

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    # ========================================================
    # BALANCE
    # ========================================================

    @app_commands.command(
        name="balance",
        description="Muestra tu dinero y banco."
    )
    async def balance(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member | None = None
    ):

        target = usuario or interaction.user

        user = self.get_user(
            interaction.guild.id,
            target.id
        )

        total = user["cash"] + user["bank"]

        embed = discord.Embed(
            title="💰 Balance",
            color=PURPLE
        )

        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url
        )

        embed.add_field(
            name="💵 Efectivo",
            value=format_money(user["cash"]),
            inline=True
        )

        embed.add_field(
            name="🏦 Banco",
            value=format_money(user["bank"]),
            inline=True
        )

        embed.add_field(
            name="💎 Total",
            value=format_money(total),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ========================================================
    # DAILY
    # ========================================================

    @app_commands.command(
        name="daily",
        description="Reclama tu recompensa diaria."
    )
    async def daily(self, interaction):

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        current = now()

        if current - user["daily"] < DAILY_COOLDOWN:

            remaining = DAILY_COOLDOWN - (
                current - user["daily"]
            )

            hours = remaining // 3600
            minutes = (remaining % 3600) // 60

            return await interaction.response.send_message(
                f"⏳ Ya reclamaste tu recompensa diaria.\n"
                f"Podés volver en **{hours}h {minutes}m**.",
                ephemeral=True
            )

        amount = random.randint(
            DAILY_MIN,
            DAILY_MAX
        )

        user["cash"] += amount
        user["daily"] = current

        user["stats"]["daily_claims"] += 1
        user["stats"]["money_earned"] += amount

        save_data(self.data)

        embed = discord.Embed(
            title="🎁 Recompensa diaria",
            description=(
                f"Recibiste **{format_money(amount)}**.\n\n"
                f"💰 Ahora tenés "
                f"**{format_money(user['cash'])}**."
            ),
            color=PURPLE
        )

        await interaction.response.send_message(embed=embed)

    # ========================================================
    # WORK
    # ========================================================

    @app_commands.command(
        name="work",
        description="Trabaja para ganar dinero."
    )
    async def work(self, interaction):

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        current = now()

        if current - user["work"] < WORK_COOLDOWN:

            remaining = WORK_COOLDOWN - (
                current - user["work"]
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"⏳ Ya trabajaste recientemente.\n"
                f"Podés volver a trabajar en **{minutes} minutos**.",
                ephemeral=True
            )

        jobs = [
            "programador",
            "delivery",
            "diseñador",
            "streamer",
            "mecánico",
            "fotógrafo",
            "barista",
            "desarrollador",
            "vendedor"
        ]

        job = random.choice(jobs)

        amount = random.randint(
            WORK_MIN,
            WORK_MAX
        )

        user["cash"] += amount
        user["work"] = current

        user["stats"]["work_claims"] += 1
        user["stats"]["money_earned"] += amount

        save_data(self.data)

        embed = discord.Embed(
            title="💼 Trabajo realizado",
            description=(
                f"Trabajaste como **{job}**.\n\n"
                f"💵 Ganaste **{format_money(amount)}**."
            ),
            color=PURPLE
        )

        await interaction.response.send_message(embed=embed)

    # ========================================================
    # BEG
    # ========================================================

    @app_commands.command(
        name="beg",
        description="Pide dinero a la gente."
    )
    async def beg(self, interaction):

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        current = now()

        if current - user["beg"] < BEG_COOLDOWN:

            remaining = BEG_COOLDOWN - (
                current - user["beg"]
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"⏳ Ya pediste dinero recientemente.\n"
                f"Esperá **{minutes} minutos**.",
                ephemeral=True
            )

        amount = random.randint(
            BEG_MIN,
            BEG_MAX
        )

        user["cash"] += amount
        user["beg"] = current

        user["stats"]["beg_claims"] += 1
        user["stats"]["money_earned"] += amount

        save_data(self.data)

        await interaction.response.send_message(
            f"🥺 Alguien te dio **{format_money(amount)}**."
        )

    # ========================================================
    # DEPOSITAR
    # ========================================================

    @app_commands.command(
        name="depositar",
        description="Deposita dinero en el banco."
    )
    @app_commands.describe(cantidad="Cantidad a depositar")
    async def depositar(
        self,
        interaction,
        cantidad: int
    ):

        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        if cantidad > user["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        user["cash"] -= cantidad
        user["bank"] += cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Depositaste **{format_money(cantidad)}**."
        )

    # ========================================================
    # RETIRAR
    # ========================================================

    @app_commands.command(
        name="retirar",
        description="Retira dinero del banco."
    )
    async def retirar(
        self,
        interaction,
        cantidad: int
    ):

        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        if cantidad > user["bank"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero en el banco.",
                ephemeral=True
            )

        user["bank"] -= cantidad
        user["cash"] += cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Retiraste **{format_money(cantidad)}**."
        )

    # ========================================================
    # PAY
    # ========================================================

    @app_commands.command(
        name="pay",
        description="Envía dinero a otro usuario."
    )
    async def pay(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        if usuario.bot:
            return await interaction.response.send_message(
                "❌ No podés enviar dinero a un bot.",
                ephemeral=True
            )

        if usuario.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ No podés enviarte dinero a vos mismo.",
                ephemeral=True
            )

        sender = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        receiver = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        if cantidad > sender["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        sender["cash"] -= cantidad
        receiver["cash"] += cantidad

        sender["stats"]["money_spent"] += cantidad
        receiver["stats"]["money_earned"] += cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"💸 Enviaste **{format_money(cantidad)}** "
            f"a {usuario.mention}."
        )

    # ========================================================
    # LEADERBOARD
    # ========================================================

    @app_commands.command(
        name="leaderboard",
        description="Muestra los usuarios más ricos."
    )
    async def leaderboard(self, interaction):

        guild = self.get_guild(interaction.guild.id)

        users = []

        for user_id, data in guild["users"].items():

            total = data.get("cash", 0) + data.get("bank", 0)

            users.append(
                (int(user_id), total)
            )

        users.sort(
            key=lambda x: x[1],
            reverse=True
        )

        description = ""

        for position, (user_id, money) in enumerate(
            users[:10],
            start=1
        ):

            member = interaction.guild.get_member(user_id)

            if member:
                name = member.display_name
            else:
                name = f"Usuario {user_id}"

            description += (
                f"**#{position}** "
                f"{name} — "
                f"**{format_money(money)}**\n"
            )

        if not description:
            description = "Todavía no hay usuarios registrados."

        embed = discord.Embed(
            title="🏆 Ranking de riqueza",
            description=description,
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # PROFILE
    # ========================================================

    @app_commands.command(
        name="profile",
        description="Muestra tu perfil económico."
    )
    async def profile(
        self,
        interaction,
        usuario: discord.Member | None = None
    ):

        target = usuario or interaction.user

        user = self.get_user(
            interaction.guild.id,
            target.id
        )

        stats = user["stats"]

        total = user["cash"] + user["bank"]

        embed = discord.Embed(
            title="👤 Perfil económico",
            color=PURPLE
        )

        embed.set_thumbnail(
            url=target.display_avatar.url
        )

        embed.add_field(
            name="💰 Patrimonio",
            value=format_money(total),
            inline=False
        )

        embed.add_field(
            name="💵 Efectivo",
            value=format_money(user["cash"]),
            inline=True
        )

        embed.add_field(
            name="🏦 Banco",
            value=format_money(user["bank"]),
            inline=True
        )

        embed.add_field(
            name="📨 Mensajes",
            value=str(stats["messages"]),
            inline=True
        )

        embed.add_field(
            name="🎁 Daily",
            value=str(stats["daily_claims"]),
            inline=True
        )

        embed.add_field(
            name="💼 Trabajos",
            value=str(stats["work_claims"]),
            inline=True
        )

        embed.add_field(
            name="🎮 Partidas",
            value=str(stats["games_played"]),
            inline=True
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # SLOTS
    # ========================================================

    @app_commands.command(
        name="slots",
        description="Juega a las tragamonedas."
    )
    async def slots(
        self,
        interaction,
        apuesta: int
    ):

        if apuesta <= 0:
            return await interaction.response.send_message(
                "❌ La apuesta debe ser mayor que 0.",
                ephemeral=True
            )

        if apuesta > MAX_BET:
            return await interaction.response.send_message(
                f"❌ La apuesta máxima es "
                f"**{format_money(MAX_BET)}**.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        if apuesta > user["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        symbols = [
            "🍒",
            "🍋",
            "🍊",
            "🍇",
            "💎",
            "7️⃣"
        ]

        result = [
            random.choice(symbols),
            random.choice(symbols),
            random.choice(symbols)
        ]

        user["stats"]["games_played"] += 1

        if result[0] == result[1] == result[2]:

            multiplier = 5

            winnings = apuesta * multiplier

            user["cash"] += winnings

            user["stats"]["games_won"] += 1
            user["stats"]["money_earned"] += winnings

            text = (
                f"🎉 **¡JACKPOT!**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💰 Ganaste "
                f"**{format_money(winnings)}**."
            )

        elif result[0] == result[1] or result[1] == result[2]:

            winnings = apuesta * 2

            user["cash"] += winnings

            user["stats"]["games_won"] += 1
            user["stats"]["money_earned"] += winnings

            text = (
                f"✨ **Ganaste!**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💰 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["cash"] -= apuesta

            user["stats"]["games_lost"] += 1
            user["stats"]["money_spent"] += apuesta

            text = (
                f"💀 **Perdiste.**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💸 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        save_data(self.data)

        embed = discord.Embed(
            title="🎰 Slots",
            description=text,
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # COINFLIP
    # ========================================================

    @app_commands.command(
        name="coinflip",
        description="Apuesta en cara o cruz."
    )
    @app_commands.describe(
        lado="Cara o cruz",
        apuesta="Cantidad a apostar"
    )
    @app_commands.choices(
        lado=[
            app_commands.Choice(
                name="Cara",
                value="cara"
            ),
            app_commands.Choice(
                name="Cruz",
                value="cruz"
            )
        ]
    )
    async def coinflip(
        self,
        interaction,
        lado: app_commands.Choice[str],
        apuesta: int
    ):

        if apuesta <= 0:
            return await interaction.response.send_message(
                "❌ La apuesta debe ser mayor que 0.",
                ephemeral=True
            )

        if apuesta > MAX_BET:
            return await interaction.response.send_message(
                f"❌ La apuesta máxima es "
                f"**{format_money(MAX_BET)}**.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        if apuesta > user["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        result = random.choice(
            ["cara", "cruz"]
        )

        user["stats"]["games_played"] += 1

        if result == lado.value:

            user["cash"] += apuesta

            user["stats"]["games_won"] += 1
            user["stats"]["money_earned"] += apuesta

            text = (
                f"🪙 Salió **{result.upper()}**.\n\n"
                f"🎉 Ganaste **{format_money(apuesta)}**."
            )

        else:

            user["cash"] -= apuesta

            user["stats"]["games_lost"] += 1
            user["stats"]["money_spent"] += apuesta

            text = (
                f"🪙 Salió **{result.upper()}**.\n\n"
                f"💀 Perdiste **{format_money(apuesta)}**."
            )

        save_data(self.data)

        await interaction.response.send_message(
            text
        )

    # ========================================================
    # DICE
    # ========================================================

    @app_commands.command(
        name="dice",
        description="Apuesta al dado."
    )
    async def dice(
        self,
        interaction,
        numero: int,
        apuesta: int
    ):

        if numero < 1 or numero > 6:
            return await interaction.response.send_message(
                "❌ Elegí un número del 1 al 6.",
                ephemeral=True
            )

        if apuesta <= 0:
            return await interaction.response.send_message(
                "❌ La apuesta debe ser mayor que 0.",
                ephemeral=True
            )

        if apuesta > MAX_BET:
            return await interaction.response.send_message(
                f"❌ La apuesta máxima es "
                f"**{format_money(MAX_BET)}**.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        if apuesta > user["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        result = random.randint(1, 6)

        user["stats"]["games_played"] += 1

        if result == numero:

            winnings = apuesta * 5

            user["cash"] += winnings

            user["stats"]["games_won"] += 1
            user["stats"]["money_earned"] += winnings

            text = (
                f"🎲 Salió **{result}**.\n\n"
                f"🎉 ¡Ganaste "
                f"**{format_money(winnings)}**!"
            )

        else:

            user["cash"] -= apuesta

            user["stats"]["games_lost"] += 1
            user["stats"]["money_spent"] += apuesta

            text = (
                f"🎲 Salió **{result}**.\n\n"
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        save_data(self.data)

        await interaction.response.send_message(
            text
        )

    # ========================================================
    # BLACKJACK
    # ========================================================

    @app_commands.command(
        name="blackjack",
        description="Juega una partida rápida de blackjack."
    )
    async def blackjack(
        self,
        interaction,
        apuesta: int
    ):

        if apuesta <= 0:
            return await interaction.response.send_message(
                "❌ La apuesta debe ser mayor que 0.",
                ephemeral=True
            )

        if apuesta > MAX_BET:
            return await interaction.response.send_message(
                f"❌ La apuesta máxima es "
                f"**{format_money(MAX_BET)}**.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        if apuesta > user["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        player = random.randint(15, 21)
        dealer = random.randint(15, 21)

        user["stats"]["games_played"] += 1

        if player == 21 and dealer != 21:

            winnings = apuesta * 2

            user["cash"] += winnings

            user["stats"]["games_won"] += 1
            user["stats"]["money_earned"] += winnings

            result = (
                "🃏 **BLACKJACK**\n\n"
                f"Vos: **{player}**\n"
                f"Dealer: **{dealer}**\n\n"
                f"🎉 Ganaste **{format_money(winnings)}**."
            )

        elif player > dealer:

            winnings = apuesta

            user["cash"] += winnings

            user["stats"]["games_won"] += 1
            user["stats"]["money_earned"] += winnings

            result = (
                "🃏 **Ganaste**\n\n"
                f"Vos: **{player}**\n"
                f"Dealer: **{dealer}**\n\n"
                f"💰 Ganancia: "
                f"**{format_money(winnings)}**."
            )

        elif player == dealer:

            result = (
                "🃏 **Empate**\n\n"
                f"Vos: **{player}**\n"
                f"Dealer: **{dealer}**\n\n"
                "No ganaste ni perdiste dinero."
            )

        else:

            user["cash"] -= apuesta

            user["stats"]["games_lost"] += 1
            user["stats"]["money_spent"] += apuesta

            result = (
                "🃏 **Perdiste**\n\n"
                f"Vos: **{player}**\n"
                f"Dealer: **{dealer}**\n\n"
                f"💸 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        save_data(self.data)

        embed = discord.Embed(
            title="🃏 Blackjack",
            description=result,
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # INVENTORY
    # ========================================================

    @app_commands.command(
        name="inventory",
        description="Muestra tu inventario."
    )
    async def inventory(self, interaction):

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        inventory = user["inventory"]

        if not inventory:

            return await interaction.response.send_message(
                "🎒 Tu inventario está vacío."
            )

        description = ""

        for item, amount in inventory.items():

            description += (
                f"• **{item}** × `{amount}`\n"
            )

        embed = discord.Embed(
            title="🎒 Inventario",
            description=description,
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # SHOP
    # ========================================================

    @app_commands.command(
        name="shop",
        description="Muestra la tienda."
    )
    async def shop(self, interaction):

        embed = discord.Embed(
            title="🛒 Tienda",
            description=(
                "**🎨 Rol personalizado** — $5.000\n"
                "`ID: custom_role`\n\n"

                "**💎 VIP** — $25.000\n"
                "`ID: vip`\n\n"

                "**✨ Boost** — $10.000\n"
                "`ID: boost`"
            ),
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # BUY
    # ========================================================

    @app_commands.command(
        name="buy",
        description="Compra un artículo de la tienda."
    )
    async def buy(
        self,
        interaction,
        item: str
    ):

        items = {
            "custom_role": 5000,
            "vip": 25000,
            "boost": 10000
        }

        item = item.lower()

        if item not in items:

            return await interaction.response.send_message(
                "❌ Ese artículo no existe.",
                ephemeral=True
            )

        price = items[item]

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        if user["cash"] < price:

            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        user["cash"] -= price

        user["inventory"][item] = (
            user["inventory"].get(item, 0) + 1
        )

        user["stats"]["money_spent"] += price

        save_data(self.data)

        await interaction.response.send_message(
            f"🛒 Compraste **{item}** por "
            f"**{format_money(price)}**."
        )

    # ========================================================
    # SELL
    # ========================================================

    @app_commands.command(
        name="sell",
        description="Vende un artículo de tu inventario."
    )
    async def sell(
        self,
        interaction,
        item: str
    ):

        items = {
            "custom_role": 5000,
            "vip": 25000,
            "boost": 10000
        }

        item = item.lower()

        if item not in items:

            return await interaction.response.send_message(
                "❌ Ese artículo no existe.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            interaction.user.id
        )

        amount = user["inventory"].get(item, 0)

        if amount <= 0:

            return await interaction.response.send_message(
                "❌ No tenés ese artículo.",
                ephemeral=True
            )

        price = items[item] // 2

        user["inventory"][item] -= 1

        if user["inventory"][item] <= 0:
            del user["inventory"][item]

        user["cash"] += price

        user["stats"]["money_earned"] += price

        save_data(self.data)

        await interaction.response.send_message(
            f"💰 Vendiste **{item}** por "
            f"**{format_money(price)}**."
        )

    # ========================================================
    # GIVE MONEY
    # ========================================================

    @app_commands.command(
        name="give-money",
        description="Da dinero a un usuario."
    )
    async def give_money(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_use_economy_admin(
            interaction,
            "give-money"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

        if cantidad <= 0:

            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        user["cash"] += cantidad

        user["stats"]["money_earned"] += cantidad

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "💰 GIVE MONEY",
            (
                f"**Administrador:** {interaction.user.mention}\n"
                f"**Usuario:** {usuario.mention}\n"
                f"**Cantidad:** {format_money(cantidad)}"
            )
        )

        await interaction.response.send_message(
            f"💰 Le diste **{format_money(cantidad)}** "
            f"a {usuario.mention}."
        )

    # ========================================================
    # REMOVE MONEY
    # ========================================================

    @app_commands.command(
        name="remove-money",
        description="Quita dinero a un usuario."
    )
    async def remove_money(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_use_economy_admin(
            interaction,
            "remove-money"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

        if cantidad <= 0:

            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        removed = min(
            cantidad,
            user["cash"]
        )

        user["cash"] -= removed

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "💸 REMOVE MONEY",
            (
                f"**Administrador:** {interaction.user.mention}\n"
                f"**Usuario:** {usuario.mention}\n"
                f"**Cantidad:** {format_money(removed)}"
            )
        )

        await interaction.response.send_message(
            f"💸 Le quitaste **{format_money(removed)}** "
            f"a {usuario.mention}."
        )

    # ========================================================
    # SET MONEY
    # ========================================================

    @app_commands.command(
        name="set-money",
        description="Establece el dinero de un usuario."
    )
    async def set_money(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_use_economy_admin(
            interaction,
            "set-money"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

        if cantidad < 0:

            return await interaction.response.send_message(
                "❌ La cantidad no puede ser negativa.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        old = user["cash"]

        user["cash"] = cantidad

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "⚙️ SET MONEY",
            (
                f"**Administrador:** {interaction.user.mention}\n"
                f"**Usuario:** {usuario.mention}\n"
                f"**Anterior:** {format_money(old)}\n"
                f"**Nuevo:** {format_money(cantidad)}"
            )
        )

        await interaction.response.send_message(
            f"⚙️ El balance de {usuario.mention} ahora es "
            f"**{format_money(cantidad)}**."
        )

    # ========================================================
    # RESET MONEY
    # ========================================================

    @app_commands.command(
        name="reset-money",
        description="Reinicia el dinero de un usuario."
    )
    async def reset_money(
        self,
        interaction,
        usuario: discord.Member
    ):

        if not self.can_use_economy_admin(
            interaction,
            "reset-money"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        user["cash"] = START_MONEY
        user["bank"] = 0

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "🔄 RESET MONEY",
            (
                f"**Administrador:** {interaction.user.mention}\n"
                f"**Usuario:** {usuario.mention}\n"
                f"**Nuevo balance:** "
                f"{format_money(START_MONEY)}"
            )
        )

        await interaction.response.send_message(
            f"🔄 Economía de {usuario.mention} reiniciada."
        )

    # ========================================================
    # ADD BANK
    # ========================================================

    @app_commands.command(
        name="add-bank",
        description="Agrega dinero al banco de un usuario."
    )
    async def add_bank(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_use_economy_admin(
            interaction,
            "add-bank"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

        if cantidad <= 0:

            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        user["bank"] += cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Agregaste **{format_money(cantidad)}** "
            f"al banco de {usuario.mention}."
        )

    # ========================================================
    # REMOVE BANK
    # ========================================================

    @app_commands.command(
        name="remove-bank",
        description="Quita dinero del banco de un usuario."
    )
    async def remove_bank(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_use_economy_admin(
            interaction,
            "remove-bank"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

        if cantidad <= 0:

            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        removed = min(
            cantidad,
            user["bank"]
        )

        user["bank"] -= removed

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Quitaste **{format_money(removed)}** "
            f"del banco de {usuario.mention}."
        )

    # ========================================================
    # SET BANK
    # ========================================================

    @app_commands.command(
        name="set-bank",
        description="Establece el dinero del banco."
    )
    async def set_bank(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_use_economy_admin(
            interaction,
            "set-bank"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

        if cantidad < 0:

            return await interaction.response.send_message(
                "❌ La cantidad no puede ser negativa.",
                ephemeral=True
            )

        user = self.get_user(
            interaction.guild.id,
            usuario.id
        )

        user["bank"] = cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 El banco de {usuario.mention} ahora tiene "
            f"**{format_money(cantidad)}**."
        )

    # ========================================================
    # ECONOMYSET
    # ========================================================

    economy_actions = [
        app_commands.Choice(
            name="give-money",
            value="give-money"
        ),
        app_commands.Choice(
            name="remove-money",
            value="remove-money"
        ),
        app_commands.Choice(
            name="set-money",
            value="set-money"
        ),
        app_commands.Choice(
            name="reset-money",
            value="reset-money"
        ),
        app_commands.Choice(
            name="add-bank",
            value="add-bank"
        ),
        app_commands.Choice(
            name="remove-bank",
            value="remove-bank"
        ),
        app_commands.Choice(
            name="set-bank",
            value="set-bank"
        )
    ]

    @app_commands.command(
        name="economyset",
        description="Configura qué rol puede administrar la economía."
    )
    @app_commands.describe(
        accion="Acción que podrá realizar el rol",
        rol="Rol que tendrá permiso"
    )
    @app_commands.choices(
        accion=economy_actions
    )
    async def economyset(
        self,
        interaction,
        accion: app_commands.Choice[str],
        rol: discord.Role
    ):

        if interaction.guild.owner_id != interaction.user.id:

            return await interaction.response.send_message(
                "❌ Solo el dueño del servidor puede configurar "
                "los permisos de economía.",
                ephemeral=True
            )

        guild = self.get_guild(
            interaction.guild.id
        )

        roles = guild["permissions"].setdefault(
            accion.value,
            []
        )

        role_id = str(rol.id)

        if role_id in roles:

            roles.remove(role_id)

            action = "quitado"

        else:

            roles.append(role_id)

            action = "agregado"

        save_data(self.data)

        await interaction.response.send_message(
            f"⚙️ Permiso **{accion.value}** "
            f"{action} para {rol.mention}."
        )

    # ========================================================
    # ECONOMY PERMISSIONS
    # ========================================================

    @app_commands.command(
        name="economy-permissions",
        description="Muestra los permisos de economía."
    )
    async def economy_permissions(
        self,
        interaction
    ):

        if interaction.guild.owner_id != interaction.user.id:

            return await interaction.response.send_message(
                "❌ Solo el dueño del servidor puede ver "
                "esta configuración.",
                ephemeral=True
            )

        guild = self.get_guild(
            interaction.guild.id
        )

        description = ""

        for action, role_ids in guild["permissions"].items():

            if role_ids:

                roles_text = []

                for role_id in role_ids:

                    role = interaction.guild.get_role(
                        int(role_id)
                    )

                    if role:
                        roles_text.append(
                            role.mention
                        )

                roles = ", ".join(roles_text)

            else:

                roles = "👑 Administradores"

            description += (
                f"**{action}**\n"
                f"{roles}\n\n"
            )

        embed = discord.Embed(
            title="⚙️ Permisos de economía",
            description=description,
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ========================================================
    # ECONOMY LOG
    # ========================================================

    @app_commands.command(
        name="economy-log",
        description="Configura el canal de logs de economía."
    )
    async def economy_log_command(
        self,
        interaction,
        canal: discord.TextChannel
    ):

        if interaction.guild.owner_id != interaction.user.id:

            return await interaction.response.send_message(
                "❌ Solo el dueño del servidor puede configurar "
                "los logs.",
                ephemeral=True
            )

        guild = self.get_guild(
            interaction.guild.id
        )

        guild["log_channel"] = canal.id

        save_data(self.data)

        await interaction.response.send_message(
            f"✅ Los logs de economía ahora se enviarán en "
            f"{canal.mention}."
        )

    # ========================================================
    # MENSAJES
    # ========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):

        if message.author.bot:
            return

        if message.guild is None:
            return

        user = self.get_user(
            message.guild.id,
            message.author.id
        )

        user["stats"]["messages"] += 1

        # Guardamos cada 10 mensajes para reducir escrituras.
        if user["stats"]["messages"] % 10 == 0:
            save_data(self.data)


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Economia(bot)
    )