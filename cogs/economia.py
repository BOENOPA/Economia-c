import json
import os
import random
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIG
# ============================================================

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "economia.json"

PURPLE = discord.Color.from_rgb(115, 55, 210)

START_MONEY = 1000
START_BANK = 0

DAILY_MIN = 500
DAILY_MAX = 1500

WORK_MIN = 100
WORK_MAX = 500

BEG_MIN = 50
BEG_MAX = 250

MAX_BET = 100000

COOLDOWN_DAILY = 86400
COOLDOWN_WORK = 3600
COOLDOWN_BEG = 300


# ============================================================
# DATA
# ============================================================

DEFAULT_DATA = {
    "guilds": {}
}


def load_data():

    if not DATA_FILE.exists():

        save_data(DEFAULT_DATA.copy())
        return {
            "guilds": {}
        }

    try:

        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if "guilds" not in data:
            data["guilds"] = {}

        return data

    except Exception:

        return {
            "guilds": {}
        }


def save_data(data):

    temp_file = DATA_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    temp_file.replace(DATA_FILE)


# ============================================================
# UTILIDADES
# ============================================================

def now():

    return datetime.now(timezone.utc)


def timestamp():

    return now().timestamp()


def money(value):

    return f"${value:,}"


def default_user():

    return {
        "cash": START_MONEY,
        "bank": START_BANK,

        "daily": 0,
        "work": 0,
        "beg": 0,

        "inventory": {},

        "stats": {
            "messages": 0,
            "earned": 0,
            "spent": 0,
            "games": 0,
            "wins": 0,
            "losses": 0
        }
    }


def default_guild():

    return {
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


# ============================================================
# COG
# ============================================================

class Economia(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.data = load_data()

        self.locks = {}

        print("💰 Sistema de economía iniciado.")

    # ========================================================
    # DATA HELPERS
    # ========================================================

    def guild_data(self, guild_id):

        guild_id = str(guild_id)

        if guild_id not in self.data["guilds"]:

            self.data["guilds"][guild_id] = default_guild()

        return self.data["guilds"][guild_id]


    def user_data(self, guild_id, user_id):

        guild = self.guild_data(guild_id)

        user_id = str(user_id)

        if user_id not in guild["users"]:

            guild["users"][user_id] = default_user()

        user = guild["users"][user_id]

        # Compatibilidad con datos antiguos
        if "inventory" not in user:
            user["inventory"] = {}

        if "stats" not in user:

            user["stats"] = {
                "messages": 0,
                "earned": 0,
                "spent": 0,
                "games": 0,
                "wins": 0,
                "losses": 0
            }

        return user


    def get_lock(self, guild_id, user_id):

        key = f"{guild_id}:{user_id}"

        if key not in self.locks:
            self.locks[key] = asyncio.Lock()

        return self.locks[key]


    # ========================================================
    # PERMISOS
    # ========================================================

    def is_owner(self, interaction):

        return interaction.guild.owner_id == interaction.user.id


    def has_economy_permission(self, interaction, action):

        if self.is_owner(interaction):
            return True

        guild = self.guild_data(interaction.guild.id)

        allowed_roles = guild["permissions"].get(
            action,
            []
        )

        # Si no hay roles configurados:
        # solamente administrador.
        if not allowed_roles:

            return interaction.user.guild_permissions.administrator

        user_role_ids = {
            role.id for role in interaction.user.roles
        }

        return any(
            role_id in user_role_ids
            for role_id in allowed_roles
        )


    # ========================================================
    # LOG
    # ========================================================

    async def economy_log(
        self,
        guild,
        title,
        description
    ):

        guild_data = self.guild_data(guild.id)

        channel_id = guild_data.get("log_channel")

        if not channel_id:
            return

        channel = guild.get_channel(channel_id)

        if not channel:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=PURPLE,
            timestamp=now()
        )

        try:
            await channel.send(embed=embed)
        except Exception:
            pass


    # ========================================================
    # BALANCE
    # ========================================================

    @app_commands.command(
        name="balance",
        description="Muestra el dinero y banco de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario que quieres consultar."
    )
    async def balance(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member = None
    ):

        usuario = usuario or interaction.user

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        total = data["cash"] + data["bank"]

        embed = discord.Embed(
            title="💰 Balance",
            color=PURPLE
        )

        embed.set_author(
            name=usuario.display_name,
            icon_url=usuario.display_avatar.url
        )

        embed.add_field(
            name="💵 Efectivo",
            value=money(data["cash"]),
            inline=True
        )

        embed.add_field(
            name="🏦 Banco",
            value=money(data["bank"]),
            inline=True
        )

        embed.add_field(
            name="💎 Total",
            value=money(total),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # DAILY
    # ========================================================

    @app_commands.command(
        name="daily",
        description="Reclama tu recompensa diaria."
    )
    async def daily(
        self,
        interaction: discord.Interaction
    ):

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        current = timestamp()

        remaining = COOLDOWN_DAILY - (
            current - data["daily"]
        )

        if remaining > 0:

            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)

            await interaction.response.send_message(
                f"⏳ Ya reclamaste tu recompensa.\n"
                f"Volvé en **{hours}h {minutes}m**.",
                ephemeral=True
            )

            return

        amount = random.randint(
            DAILY_MIN,
            DAILY_MAX
        )

        data["cash"] += amount
        data["daily"] = current

        data["stats"]["earned"] += amount

        save_data(self.data)

        embed = discord.Embed(
            title="🎁 Recompensa diaria",
            description=(
                f"Recibiste **{money(amount)}**."
            ),
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # WORK
    # ========================================================

    @app_commands.command(
        name="work",
        description="Trabaja para ganar dinero."
    )
    async def work(
        self,
        interaction: discord.Interaction
    ):

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        current = timestamp()

        remaining = COOLDOWN_WORK - (
            current - data["work"]
        )

        if remaining > 0:

            minutes = int(remaining // 60)

            await interaction.response.send_message(
                f"⏳ Todavía no podés trabajar.\n"
                f"Esperá aproximadamente **{minutes} minutos**.",
                ephemeral=True
            )

            return

        jobs = [
            "👨‍💻 Programaste una aplicación.",
            "🍔 Trabajaste en un restaurante.",
            "🚚 Hiciste unas entregas.",
            "🎨 Diseñaste un logo.",
            "🎧 Trabajaste como DJ.",
            "🛠️ Arreglaste algunos equipos."
        ]

        job = random.choice(jobs)

        amount = random.randint(
            WORK_MIN,
            WORK_MAX
        )

        data["cash"] += amount
        data["work"] = current

        data["stats"]["earned"] += amount

        save_data(self.data)

        embed = discord.Embed(
            title="💼 Trabajo completado",
            description=(
                f"{job}\n\n"
                f"Ganaste **{money(amount)}**."
            ),
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ========================================================
    # BEG
    # ========================================================

    @app_commands.command(
        name="beg",
        description="Pedí dinero y quizás alguien te ayude."
    )
    async def beg(
        self,
        interaction: discord.Interaction
    ):

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        current = timestamp()

        remaining = COOLDOWN_BEG - (
            current - data["beg"]
        )

        if remaining > 0:

            await interaction.response.send_message(
                f"⏳ Esperá **{int(remaining)} segundos**.",
                ephemeral=True
            )

            return

        data["beg"] = current

        chance = random.randint(1, 100)

        if chance <= 20:

            amount = 0

            text = "😢 Nadie te dio dinero."

        else:

            amount = random.randint(
                BEG_MIN,
                BEG_MAX
            )

            data["cash"] += amount
            data["stats"]["earned"] += amount

            text = f"💵 Conseguíste **{money(amount)}**."

        save_data(self.data)

        await interaction.response.send_message(
            text
        )


    # ========================================================
    # DEPOSITAR
    # ========================================================

    @app_commands.command(
        name="depositar",
        description="Deposita dinero en el banco."
    )
    @app_commands.describe(
        cantidad="Cantidad a depositar."
    )
    async def depositar(
        self,
        interaction: discord.Interaction,
        cantidad: int
    ):

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a 0.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        if cantidad > data["cash"]:

            await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

            return

        data["cash"] -= cantidad
        data["bank"] += cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Depositaste **{money(cantidad)}**."
        )


    # ========================================================
    # RETIRAR
    # ========================================================

    @app_commands.command(
        name="retirar",
        description="Retira dinero del banco."
    )
    @app_commands.describe(
        cantidad="Cantidad a retirar."
    )
    async def retirar(
        self,
        interaction: discord.Interaction,
        cantidad: int
    ):

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a 0.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        if cantidad > data["bank"]:

            await interaction.response.send_message(
                "❌ No tenés suficiente dinero en el banco.",
                ephemeral=True
            )

            return

        data["bank"] -= cantidad
        data["cash"] += cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏧 Retiraste **{money(cantidad)}**."
        )


    # ========================================================
    # PAY
    # ========================================================

    @app_commands.command(
        name="pay",
        description="Transfiere dinero a otro usuario."
    )
    @app_commands.describe(
        usuario="Usuario que recibirá el dinero.",
        cantidad="Cantidad a enviar."
    )
    async def pay(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if usuario.bot:

            await interaction.response.send_message(
                "❌ No podés enviar dinero a un bot.",
                ephemeral=True
            )

            return

        if usuario.id == interaction.user.id:

            await interaction.response.send_message(
                "❌ No podés enviarte dinero a vos mismo.",
                ephemeral=True
            )

            return

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a 0.",
                ephemeral=True
            )

            return

        sender = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        receiver = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        async with self.get_lock(
            interaction.guild.id,
            interaction.user.id
        ):

            if cantidad > sender["cash"]:

                await interaction.response.send_message(
                    "❌ No tenés suficiente dinero.",
                    ephemeral=True
                )

                return

            sender["cash"] -= cantidad
            receiver["cash"] += cantidad

            sender["stats"]["spent"] += cantidad
            receiver["stats"]["earned"] += cantidad

            save_data(self.data)

        await interaction.response.send_message(
            f"💸 Enviaste **{money(cantidad)}** a {usuario.mention}."
        )


    # ========================================================
    # LEADERBOARD
    # ========================================================

    @app_commands.command(
        name="leaderboard",
        description="Muestra los usuarios con más dinero."
    )
    async def leaderboard(
        self,
        interaction: discord.Interaction
    ):

        guild_data = self.guild_data(
            interaction.guild.id
        )

        ranking = []

        for user_id, data in guild_data["users"].items():

            total = data["cash"] + data["bank"]

            ranking.append(
                (
                    int(user_id),
                    total
                )
            )

        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )

        ranking = ranking[:10]

        if not ranking:

            await interaction.response.send_message(
                "📊 Todavía no hay usuarios en la economía."
            )

            return

        lines = []

        medals = [
            "🥇",
            "🥈",
            "🥉"
        ]

        for index, (user_id, total) in enumerate(ranking):

            member = interaction.guild.get_member(
                user_id
            )

            name = (
                member.display_name
                if member
                else f"Usuario {user_id}"
            )

            medal = (
                medals[index]
                if index < 3
                else f"**{index + 1}.**"
            )

            lines.append(
                f"{medal} {name} — **{money(total)}**"
            )

        embed = discord.Embed(
            title="🏆 Leaderboard",
            description="\n".join(lines),
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
        description="Muestra las estadísticas económicas de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario a consultar."
    )
    async def profile(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member = None
    ):

        usuario = usuario or interaction.user

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        total = data["cash"] + data["bank"]

        stats = data["stats"]

        embed = discord.Embed(
            title="👤 Perfil económico",
            color=PURPLE
        )

        embed.set_thumbnail(
            url=usuario.display_avatar.url
        )

        embed.add_field(
            name="💰 Patrimonio",
            value=money(total),
            inline=False
        )

        embed.add_field(
            name="💵 Efectivo",
            value=money(data["cash"]),
            inline=True
        )

        embed.add_field(
            name="🏦 Banco",
            value=money(data["bank"]),
            inline=True
        )

        embed.add_field(
            name="📈 Ganado",
            value=money(stats["earned"]),
            inline=True
        )

        embed.add_field(
            name="📉 Gastado",
            value=money(stats["spent"]),
            inline=True
        )

        embed.add_field(
            name="🎮 Partidas",
            value=str(stats["games"]),
            inline=True
        )

        embed.add_field(
            name="🏆 Victorias",
            value=str(stats["wins"]),
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
        description="Juega a las slots usando dinero virtual."
    )
    @app_commands.describe(
        cantidad="Cantidad de dinero virtual para apostar."
    )
    async def slots(
        self,
        interaction: discord.Interaction,
        cantidad: int
    ):

        if not await self.validate_bet(
            interaction,
            cantidad
        ):
            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
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
            random.choice(symbols)
            for _ in range(3)
        ]

        data["stats"]["games"] += 1

        if result[0] == result[1] == result[2]:

            multiplier = 10
            reward = cantidad * multiplier

            data["cash"] += reward
            data["stats"]["earned"] += reward
            data["stats"]["wins"] += 1

            result_text = (
                f"🎉 **JACKPOT x{multiplier}!**\n"
                f"Ganaste **{money(reward)}**."
            )

        elif len(set(result)) == 2:

            reward = cantidad * 2

            data["cash"] += reward
            data["stats"]["earned"] += reward
            data["stats"]["wins"] += 1

            result_text = (
                f"✨ ¡Dos iguales!\n"
                f"Ganaste **{money(reward)}**."
            )

        else:

            data["cash"] -= cantidad
            data["stats"]["spent"] += cantidad
            data["stats"]["losses"] += 1

            result_text = (
                f"💀 Perdiste **{money(cantidad)}**."
            )

        save_data(self.data)

        embed = discord.Embed(
            title="🎰 SLOTS",
            description=(
                f"## {' | '.join(result)}\n\n"
                f"{result_text}"
            ),
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
        cantidad="Cantidad a apostar.",
        elección="Cara o cruz."
    )
    @app_commands.choices(
        elección=[
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
        interaction: discord.Interaction,
        cantidad: int,
        elección: app_commands.Choice[str]
    ):

        if not await self.validate_bet(
            interaction,
            cantidad
        ):
            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        result = random.choice(
            ["cara", "cruz"]
        )

        data["stats"]["games"] += 1

        if result == elección.value:

            reward = cantidad

            data["cash"] += reward
            data["stats"]["earned"] += reward
            data["stats"]["wins"] += 1

            text = (
                f"🪙 Salió **{result.title()}**.\n"
                f"Ganaste **{money(reward)}**."
            )

        else:

            data["cash"] -= cantidad
            data["stats"]["spent"] += cantidad
            data["stats"]["losses"] += 1

            text = (
                f"🪙 Salió **{result.title()}**.\n"
                f"Perdiste **{money(cantidad)}**."
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
        description="Apuesta adivinando el resultado del dado."
    )
    @app_commands.describe(
        cantidad="Cantidad a apostar.",
        número="Número del 1 al 6."
    )
    async def dice(
        self,
        interaction: discord.Interaction,
        cantidad: int,
        número: int
    ):

        if número < 1 or número > 6:

            await interaction.response.send_message(
                "❌ Elegí un número entre **1 y 6**.",
                ephemeral=True
            )

            return

        if not await self.validate_bet(
            interaction,
            cantidad
        ):
            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        result = random.randint(1, 6)

        data["stats"]["games"] += 1

        if result == número:

            reward = cantidad * 5

            data["cash"] += reward
            data["stats"]["earned"] += reward
            data["stats"]["wins"] += 1

            text = (
                f"🎲 Salió **{result}**.\n"
                f"🎉 Ganaste **{money(reward)}**."
            )

        else:

            data["cash"] -= cantidad
            data["stats"]["spent"] += cantidad
            data["stats"]["losses"] += 1

            text = (
                f"🎲 Salió **{result}**.\n"
                f"💀 Perdiste **{money(cantidad)}**."
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
        description="Juega blackjack con dinero virtual."
    )
    @app_commands.describe(
        cantidad="Cantidad a apostar."
    )
    async def blackjack(
        self,
        interaction: discord.Interaction,
        cantidad: int
    ):

        if not await self.validate_bet(
            interaction,
            cantidad
        ):
            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        player = random.randint(16, 23)
        dealer = random.randint(16, 23)

        data["stats"]["games"] += 1

        if player <= 21 and (
            dealer > 21 or player > dealer
        ):

            reward = cantidad

            data["cash"] += reward
            data["stats"]["earned"] += reward
            data["stats"]["wins"] += 1

            result = (
                f"🃏 Vos: **{player}**\n"
                f"🎩 Dealer: **{dealer}**\n\n"
                f"🎉 Ganaste **{money(reward)}**."
            )

        elif player == dealer:

            result = (
                f"🃏 Vos: **{player}**\n"
                f"🎩 Dealer: **{dealer}**\n\n"
                f"🤝 Empate. No ganaste ni perdiste."
            )

        else:

            data["cash"] -= cantidad
            data["stats"]["spent"] += cantidad
            data["stats"]["losses"] += 1

            result = (
                f"🃏 Vos: **{player}**\n"
                f"🎩 Dealer: **{dealer}**\n\n"
                f"💀 Perdiste **{money(cantidad)}**."
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
    # VALIDAR APUESTA
    # ========================================================

    async def validate_bet(
        self,
        interaction,
        cantidad
    ):

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a 0.",
                ephemeral=True
            )

            return False

        if cantidad > MAX_BET:

            await interaction.response.send_message(
                f"❌ La apuesta máxima es **{money(MAX_BET)}**.",
                ephemeral=True
            )

            return False

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        if cantidad > data["cash"]:

            await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

            return False

        return True


    # ========================================================
    # INVENTORY
    # ========================================================

    @app_commands.command(
        name="inventory",
        description="Muestra tu inventario."
    )
    async def inventory(
        self,
        interaction: discord.Interaction
    ):

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        inventory = data["inventory"]

        if not inventory:

            await interaction.response.send_message(
                "🎒 Tu inventario está vacío."
            )

            return

        lines = []

        for item, amount in inventory.items():

            lines.append(
                f"• **{item}** × {amount}"
            )

        embed = discord.Embed(
            title="🎒 Inventario",
            description="\n".join(lines),
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
    async def shop(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="🛒 Tienda",
            description=(
                "Comprá artículos usando tu dinero virtual.\n\n"
                "🪄 **vip** — $5,000\n"
                "🎨 **color** — $2,500\n"
                "💎 **gem** — $10,000\n"
                "🎁 **box** — $7,500"
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
    @app_commands.describe(
        item="Artículo que querés comprar."
    )
    async def buy(
        self,
        interaction: discord.Interaction,
        item: str
    ):

        prices = {
            "vip": 5000,
            "color": 2500,
            "gem": 10000,
            "box": 7500
        }

        item = item.lower()

        if item not in prices:

            await interaction.response.send_message(
                "❌ Ese artículo no existe.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        price = prices[item]

        if data["cash"] < price:

            await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

            return

        data["cash"] -= price
        data["inventory"][item] = (
            data["inventory"].get(item, 0) + 1
        )

        data["stats"]["spent"] += price

        save_data(self.data)

        await interaction.response.send_message(
            f"🛒 Compraste **{item}** por **{money(price)}**."
        )


    # ========================================================
    # SELL
    # ========================================================

    @app_commands.command(
        name="sell",
        description="Vende un artículo."
    )
    @app_commands.describe(
        item="Artículo que querés vender."
    )
    async def sell(
        self,
        interaction: discord.Interaction,
        item: str
    ):

        prices = {
            "vip": 2500,
            "color": 1250,
            "gem": 5000,
            "box": 3750
        }

        item = item.lower()

        if item not in prices:

            await interaction.response.send_message(
                "❌ Ese artículo no existe.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            interaction.user.id
        )

        amount = data["inventory"].get(
            item,
            0
        )

        if amount <= 0:

            await interaction.response.send_message(
                "❌ No tenés ese artículo.",
                ephemeral=True
            )

            return

        price = prices[item]

        data["inventory"][item] -= 1

        if data["inventory"][item] <= 0:
            del data["inventory"][item]

        data["cash"] += price
        data["stats"]["earned"] += price

        save_data(self.data)

        await interaction.response.send_message(
            f"📦 Vendiste **{item}** por **{money(price)}**."
        )


    # ========================================================
    # GIVE MONEY
    # ========================================================

    @app_commands.command(
        name="give-money",
        description="Entrega dinero a un usuario."
    )
    @app_commands.describe(
        usuario="Usuario que recibirá el dinero.",
        cantidad="Cantidad de dinero."
    )
    async def give_money(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.has_economy_permission(
            interaction,
            "give-money"
        ):

            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

            return

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a 0.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        data["cash"] += cantidad
        data["stats"]["earned"] += cantidad

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "💰 Give Money",
            (
                f"{interaction.user.mention} entregó "
                f"**{money(cantidad)}** a "
                f"{usuario.mention}."
            )
        )

        await interaction.response.send_message(
            f"💰 Se agregaron **{money(cantidad)}** "
            f"a {usuario.mention}."
        )


    # ========================================================
    # REMOVE MONEY
    # ========================================================

    @app_commands.command(
        name="remove-money",
        description="Quita dinero a un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que quitar dinero.",
        cantidad="Cantidad de dinero."
    )
    async def remove_money(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.has_economy_permission(
            interaction,
            "remove-money"
        ):

            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

            return

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a 0.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        removed = min(
            cantidad,
            data["cash"]
        )

        data["cash"] -= removed

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "➖ Remove Money",
            (
                f"{interaction.user.mention} quitó "
                f"**{money(removed)}** a "
                f"{usuario.mention}."
            )
        )

        await interaction.response.send_message(
            f"➖ Se quitaron **{money(removed)}** "
            f"a {usuario.mention}."
        )


    # ========================================================
    # SET MONEY
    # ========================================================

    @app_commands.command(
        name="set-money",
        description="Establece exactamente el dinero de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario.",
        cantidad="Nuevo balance."
    )
    async def set_money(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.has_economy_permission(
            interaction,
            "set-money"
        ):

            await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

            return

        if cantidad < 0:

            await interaction.response.send_message(
                "❌ La cantidad no puede ser negativa.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        old = data["cash"]

        data["cash"] = cantidad

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "⚙️ Set Money",
            (
                f"{interaction.user.mention} cambió el balance de "
                f"{usuario.mention}\n"
                f"Antes: **{money(old)}**\n"
                f"Ahora: **{money(cantidad)}**"
            )
        )

        await interaction.response.send_message(
            f"⚙️ El balance de {usuario.mention} ahora es "
            f"**{money(cantidad)}**."
        )


    # ========================================================
    # RESET MONEY
    # ========================================================

    @app_commands.command(
        name="reset-money",
        description="Reinicia la economía de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario."
    )
    async def reset_money(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member
    ):

        if not self.has_economy_permission(
            interaction,
            "reset-money"
        ):

            await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        data["cash"] = START_MONEY
        data["bank"] = START_BANK
        data["inventory"] = {}

        save_data(self.data)

        await self.economy_log(
            interaction.guild,
            "🔄 Reset Economy",
            f"{usuario.mention} fue reiniciado por {interaction.user.mention}."
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
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.has_economy_permission(
            interaction,
            "add-bank"
        ):

            await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

            return

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ Cantidad inválida.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        data["bank"] += cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Se agregaron **{money(cantidad)}** "
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
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.has_economy_permission(
            interaction,
            "remove-bank"
        ):

            await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

            return

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ Cantidad inválida.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        removed = min(
            cantidad,
            data["bank"]
        )

        data["bank"] -= removed

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Se quitaron **{money(removed)}** "
            f"del banco de {usuario.mention}."
        )


    # ========================================================
    # SET BANK
    # ========================================================

    @app_commands.command(
        name="set-bank",
        description="Establece el banco de un usuario."
    )
    async def set_bank(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.has_economy_permission(
            interaction,
            "set-bank"
        ):

            await interaction.response.send_message(
                "❌ No tenés permiso.",
                ephemeral=True
            )

            return

        if cantidad < 0:

            await interaction.response.send_message(
                "❌ Cantidad inválida.",
                ephemeral=True
            )

            return

        data = self.user_data(
            interaction.guild.id,
            usuario.id
        )

        data["bank"] = cantidad

        save_data(self.data)

        await interaction.response.send_message(
            f"🏦 Banco de {usuario.mention}: "
            f"**{money(cantidad)}**."
        )


    # ========================================================
    # ECONOMY SET
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
        description="Configura qué roles pueden administrar la economía."
    )
    @app_commands.describe(
        accion="Acción que tendrá permitido usar el rol.",
        rol="Rol que podrá utilizar la acción."
    )
    @app_commands.choices(
        accion=economy_actions
    )
    async def economyset(
        self,
        interaction: discord.Interaction,
        accion: app_commands.Choice[str],
        rol: discord.Role
    ):

        if not self.is_owner(interaction):

            await interaction.response.send_message(
                "❌ Solo el dueño del servidor puede configurar la economía.",
                ephemeral=True
            )

            return

        guild = self.guild_data(
            interaction.guild.id
        )

        roles = guild["permissions"].setdefault(
            accion.value,
            []
        )

        if rol.id in roles:

            roles.remove(rol.id)

            action_text = "quitado"

        else:

            roles.append(rol.id)

            action_text = "agregado"

        save_data(self.data)

        await interaction.response.send_message(
            f"⚙️ El rol {rol.mention} fue **{action_text}** "
            f"para `{accion.value}`."
        )


    # ========================================================
    # ECONOMY PERMISSIONS VIEW
    # ========================================================

    @app_commands.command(
        name="economy-permissions",
        description="Muestra los permisos configurados de economía."
    )
    async def economy_permissions(
        self,
        interaction: discord.Interaction
    ):

        if not self.is_owner(interaction):

            await interaction.response.send_message(
                "❌ Solo el dueño puede ver esta configuración.",
                ephemeral=True
            )

            return

        guild = self.guild_data(
            interaction.guild.id
        )

        lines = []

        for action, roles in guild["permissions"].items():

            if roles:

                role_mentions = []

                for role_id in roles:

                    role = interaction.guild.get_role(
                        role_id
                    )

                    if role:
                        role_mentions.append(
                            role.mention
                        )

                roles_text = (
                    ", ".join(role_mentions)
                    if role_mentions
                    else "Sin roles"
                )

            else:

                roles_text = "👑 Administradores"

            lines.append(
                f"**{action}** → {roles_text}"
            )

        embed = discord.Embed(
            title="⚙️ Permisos de economía",
            description="\n".join(lines),
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


    # ========================================================
    # LOG CHANNEL
    # ========================================================

    @app_commands.command(
        name="economy-log",
        description="Configura el canal de logs de economía."
    )
    @app_commands.describe(
        canal="Canal donde se enviarán los logs."
    )
    async def economy_log_channel(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):

        if not self.is_owner(interaction):

            await interaction.response.send_message(
                "❌ Solo el dueño puede configurar esto.",
                ephemeral=True
            )

            return

        guild = self.guild_data(
            interaction.guild.id
        )

        guild["log_channel"] = canal.id

        save_data(self.data)

        await interaction.response.send_message(
            f"📋 Los logs de economía ahora irán a {canal.mention}."
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

        if not message.guild:
            return

        data = self.user_data(
            message.guild.id,
            message.author.id
        )

        data["stats"]["messages"] += 1

        # No guardamos el archivo en cada mensaje.
        # Solo incrementamos en memoria.
        if data["stats"]["messages"] % 10 == 0:
            save_data(self.data)


async def setup(bot):

    await bot.add_cog(
        Economia(bot)
    )