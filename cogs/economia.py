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

ROB_COOLDOWN = 1800
CRIME_COOLDOWN = 1800
HEIST_COOLDOWN = 3600
FISH_COOLDOWN = 900
HUNT_COOLDOWN = 1200


# ============================================================
# CARGAR DATOS
# ============================================================

def load_data():
    try:
        if not DATA_FILE.exists():
            return {"guilds": {}}

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {"guilds": {}}

        data.setdefault("guilds", {})
        return data

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError
    ):
        return {"guilds": {}}


# ============================================================
# GUARDAR DATOS
# ============================================================

def save_data(data):
    try:
        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

    except OSError as error:
        print(
            f"❌ Error guardando economía: {error}"
        )


# ============================================================
# UTILIDADES
# ============================================================

def current_time():
    return int(time.time())


def format_money(amount):
    return (
        f"${amount:,}"
        .replace(",", ".")
    )


# ============================================================
# COG ECONOMÍA
# ============================================================

class Economia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

        print(
            "✅ Cog de economía cargado correctamente."
        )

    # ========================================================
    # GUARDAR
    # ========================================================

    def save_data(self, data=None):
        if data is None:
            data = self.data

        save_data(data)

    # ========================================================
    # GUILD
    # ========================================================

    def get_guild_data(self, guild_id):

        guild_id = str(guild_id)

        guilds = self.data.setdefault(
            "guilds",
            {}
        )

        if guild_id not in guilds:

            guilds[guild_id] = {
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

        guild = guilds[guild_id]

        guild.setdefault(
            "users",
            {}
        )

        guild.setdefault(
            "permissions",
            {}
        )

        guild.setdefault(
            "log_channel",
            None
        )

        permissions = {
            "give-money": [],
            "remove-money": [],
            "set-money": [],
            "reset-money": [],
            "add-bank": [],
            "remove-bank": [],
            "set-bank": []
        }

        for key, value in permissions.items():

            guild["permissions"].setdefault(
                key,
                value
            )

        return guild

    # ========================================================
    # USER
    # ========================================================

    def get_user_data(
        self,
        guild_id,
        user_id
    ):

        guild = self.get_guild_data(
            guild_id
        )

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

        user.setdefault(
            "cash",
            START_MONEY
        )

        user.setdefault(
            "bank",
            0
        )

        user.setdefault(
            "daily",
            0
        )

        user.setdefault(
            "work",
            0
        )

        user.setdefault(
            "beg",
            0
        )

        user.setdefault(
            "inventory",
            {}
        )

        user.setdefault(
            "stats",
            {}
        )

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

            user["stats"].setdefault(
                key,
                value
            )

        return user

    # ========================================================
    # VALIDAR APUESTA
    # ========================================================

    def validate_bet(
        self,
        user,
        apuesta
    ):

        if apuesta <= 0:
            return "❌ La apuesta debe ser mayor que **$0**."

        if apuesta > MAX_BET:
            return (
                f"❌ La apuesta máxima es "
                f"**{format_money(MAX_BET)}**."
            )

        if apuesta > user["cash"]:
            return "❌ No tenés suficiente dinero."

        return None

    # ========================================================
    # REGISTRAR JUEGO
    # ========================================================

    def game_stats(
        self,
        user,
        won=False,
        lost=False
    ):

        user["stats"]["games_played"] += 1

        if won:
            user["stats"]["games_won"] += 1

        if lost:
            user["stats"]["games_lost"] += 1

    # ========================================================
    # PERMISOS
    # ========================================================

    def can_manage_money(
        self,
        interaction,
        action
    ):

        if interaction.guild is None:
            return False

        member = interaction.user

        if member.id == interaction.guild.owner_id:
            return True

        guild = self.get_guild_data(
            interaction.guild.id
        )

        allowed_roles = guild[
            "permissions"
        ].get(
            action,
            []
        )

        if not allowed_roles:
            return member.guild_permissions.administrator

        member_roles = {
            role.id
            for role in member.roles
        }

        return any(
            int(role_id) in member_roles
            for role_id in allowed_roles
        )

    # ========================================================
    # LOG
    # ========================================================

    async def send_log(
        self,
        guild,
        title,
        description
    ):

        guild_data = self.get_guild_data(
            guild.id
        )

        channel_id = guild_data.get(
            "log_channel"
        )

        if not channel_id:
            return

        channel = guild.get_channel(
            int(channel_id)
        )

        if channel is None:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=PURPLE,
            timestamp=discord.utils.utcnow()
        )

        try:
            await channel.send(
                embed=embed
            )
        except discord.HTTPException:
            pass

    # ========================================================
    # BALANCE
    # ========================================================

    @app_commands.command(
        name="balance",
        description="Muestra tu balance económico."
    )
    @app_commands.describe(
        usuario="Usuario que querés consultar."
    )
    async def balance(
        self,
        interaction,
        usuario: discord.Member | None = None
    ):

        target = usuario or interaction.user

        user = self.get_user_data(
            interaction.guild.id,
            target.id
        )

        total = (
            user["cash"]
            + user["bank"]
        )

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
            value=format_money(
                user["cash"]
            ),
            inline=True
        )

        embed.add_field(
            name="🏦 Banco",
            value=format_money(
                user["bank"]
            ),
            inline=True
        )

        embed.add_field(
            name="💎 Patrimonio",
            value=format_money(
                total
            ),
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
    async def daily(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        now_value = current_time()

        if (
            now_value - user["daily"]
            < DAILY_COOLDOWN
        ):

            remaining = (
                DAILY_COOLDOWN
                - (
                    now_value
                    - user["daily"]
                )
            )

            hours = remaining // 3600
            minutes = (
                remaining % 3600
            ) // 60

            return await interaction.response.send_message(
                f"⏳ Ya reclamaste tu **Daily**.\n"
                f"Podés volver en "
                f"**{hours}h {minutes}m**.",
                ephemeral=True
            )

        amount = random.randint(
            DAILY_MIN,
            DAILY_MAX
        )

        user["cash"] += amount
        user["daily"] = now_value

        user["stats"]["daily_claims"] += 1
        user["stats"]["money_earned"] += amount

        self.save_data()

        embed = discord.Embed(
            title="🎁 Recompensa diaria",
            description=(
                f"Recibiste "
                f"**{format_money(amount)}**.\n\n"
                f"💰 Balance: "
                f"**{format_money(user['cash'])}**"
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
    async def work(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        now_value = current_time()

        if (
            now_value - user["work"]
            < WORK_COOLDOWN
        ):

            remaining = (
                WORK_COOLDOWN
                - (
                    now_value
                    - user["work"]
                )
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"⏳ Ya trabajaste recientemente.\n"
                f"Podés volver en "
                f"**{minutes} minutos**.",
                ephemeral=True
            )

        jobs = [
            "👨‍💻 programador",
            "🚗 delivery",
            "🎨 diseñador",
            "🎥 streamer",
            "🔧 mecánico",
            "📸 fotógrafo",
            "☕ barista",
            "💻 desarrollador",
            "🛒 vendedor",
            "🎧 DJ",
            "🎮 jugador profesional",
            "📱 creador de contenido",
            "🏎️ mecánico de competición",
            "🍔 cocinero",
            "💼 empresario"
        ]

        job = random.choice(jobs)

        amount = random.randint(
            WORK_MIN,
            WORK_MAX
        )

        user["cash"] += amount
        user["work"] = now_value

        user["stats"]["work_claims"] += 1
        user["stats"]["money_earned"] += amount

        self.save_data()

        embed = discord.Embed(
            title="💼 Trabajo",
            description=(
                f"Trabajaste como "
                f"**{job}**.\n\n"
                f"💵 Ganaste "
                f"**{format_money(amount)}**."
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
        description="Pedí dinero."
    )
    async def beg(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        now_value = current_time()

        if (
            now_value - user["beg"]
            < BEG_COOLDOWN
        ):

            remaining = (
                BEG_COOLDOWN
                - (
                    now_value
                    - user["beg"]
                )
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"⏳ Ya pediste dinero.\n"
                f"Esperá **{minutes} minutos**.",
                ephemeral=True
            )

        amount = random.randint(
            BEG_MIN,
            BEG_MAX
        )

        user["cash"] += amount
        user["beg"] = now_value

        user["stats"]["beg_claims"] += 1
        user["stats"]["money_earned"] += amount

        self.save_data()

        await interaction.response.send_message(
            f"🥺 Alguien te dio "
            f"**{format_money(amount)}**."
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
        interaction,
        cantidad: int
    ):

        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        if cantidad > user["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente efectivo.",
                ephemeral=True
            )

        user["cash"] -= cantidad
        user["bank"] += cantidad

        self.save_data()

        await interaction.response.send_message(
            f"🏦 Depositaste "
            f"**{format_money(cantidad)}**."
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
        interaction,
        cantidad: int
    ):

        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que 0.",
                ephemeral=True
            )

        user = self.get_user_data(
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

        self.save_data()

        await interaction.response.send_message(
            f"🏦 Retiraste "
            f"**{format_money(cantidad)}**."
        )

    # ========================================================
    # PAY
    # ========================================================

    @app_commands.command(
        name="pay",
        description="Envía dinero a otro usuario."
    )
    @app_commands.describe(
        usuario="Usuario que recibirá el dinero.",
        cantidad="Cantidad a enviar."
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

        sender = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        receiver = self.get_user_data(
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

        self.save_data()

        await interaction.response.send_message(
            f"💸 Enviaste "
            f"**{format_money(cantidad)}** "
            f"a {usuario.mention}."
        )

    # ========================================================
    # LEADERBOARD
    # ========================================================

    @app_commands.command(
        name="leaderboard",
        description="Muestra el ranking de riqueza."
    )
    async def leaderboard(self, interaction):

        guild = self.get_guild_data(
            interaction.guild.id
        )

        ranking = []

        for user_id, data in guild["users"].items():

            total = (
                data.get("cash", 0)
                + data.get("bank", 0)
            )

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

        description = ""

        medals = {
            1: "🥇",
            2: "🥈",
            3: "🥉"
        }

        for position, (
            user_id,
            money
        ) in enumerate(
            ranking[:10],
            start=1
        ):

            member = interaction.guild.get_member(
                user_id
            )

            name = (
                member.display_name
                if member
                else f"Usuario {user_id}"
            )

            medal = medals.get(
                position,
                f"`#{position}`"
            )

            description += (
                f"{medal} **{name}** "
                f"— **{format_money(money)}**\n"
            )

        if not description:
            description = (
                "Todavía no hay usuarios registrados."
            )

        embed = discord.Embed(
            title="🏆 Ranking económico",
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
    @app_commands.describe(
        usuario="Usuario cuyo perfil querés consultar."
    )
    async def profile(
        self,
        interaction,
        usuario: discord.Member | None = None
    ):

        target = usuario or interaction.user

        user = self.get_user_data(
            interaction.guild.id,
            target.id
        )

        stats = user["stats"]

        total = (
            user["cash"]
            + user["bank"]
        )

        embed = discord.Embed(
            title="👤 Perfil económico",
            color=PURPLE
        )

        embed.set_thumbnail(
            url=target.display_avatar.url
        )

        embed.add_field(
            name="💎 Patrimonio",
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
            name="💬 Mensajes",
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

        embed.add_field(
            name="🏆 Victorias",
            value=str(stats["games_won"]),
            inline=True
        )

        embed.add_field(
            name="💀 Derrotas",
            value=str(stats["games_lost"]),
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
    @app_commands.describe(
        apuesta="Cantidad a apostar."
    )
    async def slots(
        self,
        interaction,
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
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

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if result[0] == result[1] == result[2]:

            winnings = apuesta * 5

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            description = (
                "🎉 **¡JACKPOT!**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💰 Premio: "
                f"**{format_money(winnings)}**"
            )

        elif (
            result[0] == result[1]
            or result[1] == result[2]
        ):

            winnings = apuesta * 2

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            description = (
                "✨ **¡Ganaste!**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💰 Premio: "
                f"**{format_money(winnings)}**"
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                "💀 **Perdiste.**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💸 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        embed = discord.Embed(
            title="🎰 Slots",
            description=description,
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
        description="Apuesta a cara o cruz."
    )
    @app_commands.describe(
        lado="Cara o cruz",
        apuesta="Cantidad a apostar."
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

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        result = random.choice(
            ["cara", "cruz"]
        )

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if result == lado.value:

            winnings = apuesta * 2

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            description = (
                f"🪙 Salió **{result.upper()}**.\n\n"
                f"🎉 Ganaste "
                f"**{format_money(apuesta)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                f"🪙 Salió **{result.upper()}**.\n\n"
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        await interaction.response.send_message(
            description
        )

    # ========================================================
    # DICE
    # ========================================================

    @app_commands.command(
        name="dice",
        description="Apuesta a un número del dado."
    )
    @app_commands.describe(
        numero="Número del 1 al 6.",
        apuesta="Cantidad a apostar."
    )
    async def dice(
        self,
        interaction,
        numero: int,
        apuesta: int
    ):

        if numero < 1 or numero > 6:

            return await interaction.response.send_message(
                "❌ Elegí un número del **1 al 6**.",
                ephemeral=True
            )

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        result = random.randint(1, 6)

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if result == numero:

            winnings = apuesta * 5

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            description = (
                f"🎲 Salió **{result}**.\n\n"
                f"🎉 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                f"🎲 Salió **{result}**.\n\n"
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        await interaction.response.send_message(
            description
        )

    # ========================================================
    # RPS
    # ========================================================

    @app_commands.command(
        name="rps",
        description="Piedra, papel o tijera con apuesta."
    )
    @app_commands.describe(
        opcion="Tu elección.",
        apuesta="Cantidad a apostar."
    )
    @app_commands.choices(
        opcion=[
            app_commands.Choice(
                name="🪨 Piedra",
                value="piedra"
            ),
            app_commands.Choice(
                name="📄 Papel",
                value="papel"
            ),
            app_commands.Choice(
                name="✂️ Tijera",
                value="tijera"
            )
        ]
    )
    async def rps(
        self,
        interaction,
        opcion: app_commands.Choice[str],
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        bot_choice = random.choice(
            ["piedra", "papel", "tijera"]
        )

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if opcion.value == bot_choice:

            user["cash"] += apuesta
            user["stats"]["money_earned"] += apuesta

            result = "🤝 Empate."

        elif (
            (opcion.value == "piedra" and bot_choice == "tijera")
            or
            (opcion.value == "papel" and bot_choice == "piedra")
            or
            (opcion.value == "tijera" and bot_choice == "papel")
        ):

            winnings = apuesta * 2

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            result = (
                f"🎉 Ganaste "
                f"**{format_money(apuesta)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            result = (
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✂️ Piedra, Papel o Tijera",
                description=(
                    f"Vos: **{opcion.value}**\n"
                    f"Bot: **{bot_choice}**\n\n"
                    f"{result}"
                ),
                color=PURPLE
            )
        )

    # ========================================================
    # HIGHER LOWER
    # ========================================================

    @app_commands.command(
        name="higherlower",
        description="Adiviná si el próximo número será mayor o menor."
    )
    @app_commands.describe(
        eleccion="Mayor o menor.",
        apuesta="Cantidad a apostar."
    )
    @app_commands.choices(
        eleccion=[
            app_commands.Choice(
                name="📈 Mayor",
                value="mayor"
            ),
            app_commands.Choice(
                name="📉 Menor",
                value="menor"
            )
        ]
    )
    async def higherlower(
        self,
        interaction,
        eleccion: app_commands.Choice[str],
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        actual = random.randint(1, 100)
        siguiente = random.randint(1, 100)

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        won = (
            eleccion.value == "mayor"
            and siguiente > actual
        ) or (
            eleccion.value == "menor"
            and siguiente < actual
        )

        if siguiente == actual:

            user["cash"] += apuesta
            user["stats"]["money_earned"] += apuesta

            result = "🤝 Salió el mismo número. Apuesta devuelta."

        elif won:

            winnings = apuesta * 2

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            result = (
                f"🎉 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            result = (
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        embed = discord.Embed(
            title="📈 Higher / Lower",
            description=(
                f"🔢 Número: **{actual}**\n"
                f"🎯 Siguiente: **{siguiente}**\n\n"
                f"{result}"
            ),
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # RULETA
    # ========================================================

    @app_commands.command(
        name="roulette",
        description="Apuesta en la ruleta."
    )
    @app_commands.describe(
        tipo="Tipo de apuesta.",
        apuesta="Cantidad a apostar."
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(
                name="🔴 Rojo",
                value="rojo"
            ),
            app_commands.Choice(
                name="⚫ Negro",
                value="negro"
            ),
            app_commands.Choice(
                name="🟢 Verde",
                value="verde"
            ),
            app_commands.Choice(
                name="⚪ Par",
                value="par"
            ),
            app_commands.Choice(
                name="🔵 Impar",
                value="impar"
            )
        ]
    )
    async def roulette(
        self,
        interaction,
        tipo: app_commands.Choice[str],
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        number = random.randint(0, 36)

        if number == 0:
            color = "verde"
        elif number % 2:
            color = "rojo"
        else:
            color = "negro"

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        won = (
            tipo.value == color
            or (
                tipo.value == "par"
                and number != 0
                and number % 2 == 0
            )
            or (
                tipo.value == "impar"
                and number % 2 == 1
            )
        )

        if won:

            multiplier = (
                14
                if tipo.value == "verde"
                else 2
            )

            winnings = apuesta * multiplier

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            result = (
                f"🎉 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            result = (
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        embed = discord.Embed(
            title="🎡 Ruleta",
            description=(
                f"🎯 Número: **{number}**\n"
                f"🎨 Color: **{color.upper()}**\n\n"
                f"{result}"
            ),
            color=PURPLE
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # WHEEL
    # ========================================================

    @app_commands.command(
        name="wheel",
        description="Gira la rueda de premios."
    )
    @app_commands.describe(
        apuesta="Cantidad a apostar."
    )
    async def wheel(
        self,
        interaction,
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        prizes = [
            ("💀 Nada", 0),
            ("😢 Mitad", 0.5),
            ("💰 x1.5", 1.5),
            ("🔥 x2", 2),
            ("💎 x3", 3),
            ("👑 x5", 5)
        ]

        result, multiplier = random.choice(
            prizes
        )

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        winnings = int(
            apuesta * multiplier
        )

        if winnings > 0:

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings

            if winnings > apuesta:
                user["stats"]["games_won"] += 1

            description = (
                f"🎡 Cayó en **{result}**.\n\n"
                f"💰 Recibiste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                f"🎡 Cayó en **{result}**.\n\n"
                "💀 No ganaste nada."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎡 Wheel",
                description=description,
                color=PURPLE
            )
        )

    # ========================================================
    # SCRATCH
    # ========================================================

    @app_commands.command(
        name="scratch",
        description="Rasca un boleto de la suerte."
    )
    @app_commands.describe(
        apuesta="Precio del boleto."
    )
    async def scratch(
        self,
        interaction,
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        multipliers = [
            0,
            0,
            0.5,
            1,
            1,
            2,
            3,
            5,
            10
        ]

        multiplier = random.choice(
            multipliers
        )

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        winnings = int(
            apuesta * multiplier
        )

        if winnings > 0:

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings

            if winnings > aposta:
                user["stats"]["games_won"] += 1

            description = (
                "🎟️ **Boleto revelado**\n\n"
                f"Multiplicador: **x{multiplier:g}**\n"
                f"💰 Premio: **{format_money(winnings)}**"
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                "🎟️ **Boleto revelado**\n\n"
                "💀 No ganaste nada."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎟️ Scratch",
                description=description,
                color=PURPLE
            )
        )

    # ========================================================
    # MINES
    # ========================================================

    @app_commands.command(
        name="mines",
        description="Mines: elegí cuántas minas querés arriesgar."
    )
    @app_commands.describe(
        minas="Cantidad de minas, entre 1 y 10.",
        apuesta="Cantidad a apostar."
    )
    async def mines(
        self,
        interaction,
        minas: int,
        apuesta: int
    ):

        if minas < 1 or minas > 10:

            return await interaction.response.send_message(
                "❌ Las minas deben estar entre **1 y 10**.",
                ephemeral=True
            )

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        # Simulación rápida de una ronda.
        # Más minas = mayor riesgo y mayor premio.

        safe_chance = (25 - minas) / 25

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if random.random() < safe_chance:

            multiplier = 1 + (
                minas * 0.45
            )

            winnings = int(
                apuesta * multiplier
            )

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            description = (
                "💎 **¡Encontraste una zona segura!**\n\n"
                f"💣 Minas: **{minas}**\n"
                f"📈 Multiplicador: **x{multiplier:.2f}**\n\n"
                f"💰 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                "💥 **¡BOOM!**\n\n"
                f"💣 Había **{minas} minas**.\n"
                f"Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="💣 Mines",
                description=description,
                color=PURPLE
            )
        )

    # ========================================================
    # CRASH
    # ========================================================

    @app_commands.command(
        name="crash",
        description="Intentá cobrar antes de que explote."
    )
    @app_commands.describe(
        multiplicador="Multiplicador al que querés retirarte.",
        apuesta="Cantidad a apostar."
    )
    async def crash(
        self,
        interaction,
        multiplicador: float,
        apuesta: int
    ):

        if multiplicador < 1.10 or multiplicador > 20:

            return await interaction.response.send_message(
                "❌ El multiplicador debe estar entre "
                "**1.10x y 20x**.",
                ephemeral=True
            )

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        crash_point = round(
            random.uniform(
                1.01,
                10.00
            ),
            2
        )

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if multiplicador <= crash_point:

            winnings = int(
                apuesta * multiplicador
            )

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            description = (
                f"🚀 El multiplicador llegó a "
                f"**{crash_point:.2f}x**.\n\n"
                f"🎯 Retiraste en **{multiplicador:.2f}x**.\n"
                f"💰 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                f"💥 **CRASH** en "
                f"**{crash_point:.2f}x**.\n\n"
                f"💀 Intentaste retirar en "
                f"**{multiplicador:.2f}x**.\n"
                f"Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🚀 Crash",
                description=description,
                color=PURPLE
            )
        )

    # ========================================================
    # CUPS
    # ========================================================

    @app_commands.command(
        name="cups",
        description="Elegí el vaso que tiene el premio."
    )
    @app_commands.describe(
        vaso="Elegí un vaso.",
        apuesta="Cantidad a apostar."
    )
    @app_commands.choices(
        vaso=[
            app_commands.Choice(
                name="🥤 Vaso 1",
                value="1"
            ),
            app_commands.Choice(
                name="🥤 Vaso 2",
                value="2"
            ),
            app_commands.Choice(
                name="🥤 Vaso 3",
                value="3"
            )
        ]
    )
    async def cups(
        self,
        interaction,
        vaso: app_commands.Choice[str],
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        correct = random.choice(
            ["1", "2", "3"]
        )

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if vaso.value == correct:

            winnings = apuesta * 3

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            description = (
                f"🎯 El premio estaba en el vaso **{correct}**.\n\n"
                f"🎉 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            description = (
                f"❌ El premio estaba en el vaso **{correct}**.\n\n"
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🥤 Cups",
                description=description,
                color=PURPLE
            )
        )

    # ========================================================
    # FISH
    # ========================================================

    @app_commands.command(
        name="fish",
        description="Salí a pescar y conseguí dinero."
    )
    async def fish(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        now = current_time()

        last = user.get(
            "fish",
            0
        )

        if now - last < FISH_COOLDOWN:

            remaining = (
                FISH_COOLDOWN
                - (now - last)
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"🎣 Todavía estás pescando.\n"
                f"Esperá **{minutes} minutos**.",
                ephemeral=True
            )

        catches = [
            ("🐟 Pez común", 100, 300),
            ("🐠 Pez tropical", 250, 600),
            ("🦑 Calamar", 400, 900),
            ("🦈 Tiburón", 800, 1800),
            ("🐋 Ballena", 1500, 4000),
            ("💎 Cofre perdido", 2500, 6000)
        ]

        item, minimum, maximum = random.choice(
            catches
        )

        amount = random.randint(
            minimum,
            maximum
        )

        user["cash"] += amount
        user["fish"] = now

        user["stats"]["money_earned"] += amount

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎣 Pesca",
                description=(
                    f"Encontraste **{item}**.\n\n"
                    f"💰 Ganaste "
                    f"**{format_money(amount)}**."
                ),
                color=PURPLE
            )
        )

    # ========================================================
    # HUNT
    # ========================================================

    @app_commands.command(
        name="hunt",
        description="Salí de cacería."
    )
    async def hunt(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        now = current_time()

        last = user.get(
            "hunt",
            0
        )

        if now - last < HUNT_COOLDOWN:

            remaining = (
                HUNT_COOLDOWN
                - (now - last)
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"🏹 Todavía estás de cacería.\n"
                f"Esperá **{minutes} minutos**.",
                ephemeral=True
            )

        catches = [
            ("🐇 Conejo", 80, 200),
            ("🦌 Ciervo", 250, 600),
            ("🐗 Jabalí", 400, 900),
            ("🐺 Lobo", 600, 1200),
            ("🐻 Oso", 1000, 2200),
            ("💎 Tesoro escondido", 2000, 5000)
        ]

        item, minimum, maximum = random.choice(
            catches
        )

        amount = random.randint(
            minimum,
            maximum
        )

        user["cash"] += amount
        user["hunt"] = now

        user["stats"]["money_earned"] += amount

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🏹 Cacería",
                description=(
                    f"Encontraste **{item}**.\n\n"
                    f"💰 Ganaste "
                    f"**{format_money(amount)}**."
                ),
                color=PURPLE
            )
        )

    # ========================================================
    # ROB
    # ========================================================

    @app_commands.command(
        name="rob",
        description="Intentá robarle dinero a otro usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés robar."
    )
    async def rob(
        self,
        interaction,
        usuario: discord.Member
    ):

        if usuario.bot:
            return await interaction.response.send_message(
                "❌ No podés robarle a un bot.",
                ephemeral=True
            )

        if usuario.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ No podés robarte a vos mismo.",
                ephemeral=True
            )

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        target = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        now = current_time()

        last = user.get(
            "rob",
            0
        )

        if now - last < ROB_COOLDOWN:

            remaining = (
                ROB_COOLDOWN
                - (now - last)
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"🥷 Ya intentaste robar recientemente.\n"
                f"Esperá **{minutes} minutos**.",
                ephemeral=True
            )

        user["rob"] = now

        if target["cash"] < 100:

            self.save_data()

            return await interaction.response.send_message(
                "❌ Ese usuario no tiene suficiente efectivo.",
                ephemeral=True
            )

        success = random.random() < 0.45

        if success:

            amount = random.randint(
                50,
                max(50, min(target["cash"], 1000))
            )

            target["cash"] -= amount
            user["cash"] += amount

            user["stats"]["money_earned"] += amount
            target["stats"]["money_spent"] += amount

            self.save_data()

            await interaction.response.send_message(
                f"🥷 **¡Robo exitoso!**\n\n"
                f"Le sacaste "
                f"**{format_money(amount)}** "
                f"a {usuario.mention}."
            )

        else:

            fine = min(
                user["cash"],
                random.randint(50, 300)
            )

            user["cash"] -= fine
            user["stats"]["money_spent"] += fine

            self.save_data()

            await interaction.response.send_message(
                f"🚨 **Te descubrieron.**\n\n"
                f"Pagaste una multa de "
                f"**{format_money(fine)}**."
            )

    # ========================================================
    # CRIME
    # ========================================================

    @app_commands.command(
        name="crime",
        description="Cometá un crimen y arriesgá tu dinero."
    )
    async def crime(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        now = current_time()

        last = user.get(
            "crime",
            0
        )

        if now - last < CRIME_COOLDOWN:

            remaining = (
                CRIME_COOLDOWN
                - (now - last)
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"🚨 Todavía estás buscado.\n"
                f"Esperá **{minutes} minutos**.",
                ephemeral=True
            )

        user["crime"] = now

        crimes = [
            "robaste un banco",
            "vendiste información secreta",
            "hackeaste una empresa",
            "hiciste un golpe millonario",
            "robaste un camión blindado",
            "participaste de una estafa"
        ]

        crime = random.choice(crimes)

        if random.random() < 0.55:

            amount = random.randint(
                300,
                2500
            )

            user["cash"] += amount

            user["stats"]["money_earned"] += amount

            self.save_data()

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🚨 Crime",
                    description=(
                        f"🔥 **{crime}.**\n\n"
                        f"Salió bien.\n"
                        f"💰 Ganaste "
                        f"**{format_money(amount)}**."
                    ),
                    color=PURPLE
                )
            )

        else:

            fine = min(
                user["cash"],
                random.randint(100, 1000)
            )

            user["cash"] -= fine

            user["stats"]["money_spent"] += fine

            self.save_data()

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🚔 Crime",
                    description=(
                        f"🚨 **{crime}.**\n\n"
                        "La policía te atrapó.\n"
                        f"💸 Multa: "
                        f"**{format_money(fine)}**."
                    ),
                    color=PURPLE
                )
            )

    # ========================================================
    # HEIST
    # ========================================================

    @app_commands.command(
        name="heist",
        description="Intentá hacer un gran atraco."
    )
    async def heist(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        now = current_time()

        last = user.get(
            "heist",
            0
        )

        if now - last < HEIST_COOLDOWN:

            remaining = (
                HEIST_COOLDOWN
                - (now - last)
            )

            minutes = remaining // 60

            return await interaction.response.send_message(
                f"💎 El próximo atraco todavía no está listo.\n"
                f"Esperá **{minutes} minutos**.",
                ephemeral=True
            )

        user["heist"] = now

        if random.random() < 0.35:

            amount = random.randint(
                2500,
                10000
            )

            user["cash"] += amount

            user["stats"]["money_earned"] += amount

            self.save_data()

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="💎 HEIST",
                    description=(
                        "🔥 **¡ATRACO EXITOSO!**\n\n"
                        f"💰 Botín: "
                        f"**{format_money(amount)}**"
                    ),
                    color=PURPLE
                )
            )

        else:

            fine = min(
                user["cash"],
                random.randint(500, 3000)
            )

            user["cash"] -= fine

            user["stats"]["money_spent"] += fine

            self.save_data()

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="🚨 HEIST",
                    description=(
                        "💥 El atraco salió mal.\n\n"
                        f"💸 Perdiste "
                        f"**{format_money(fine)}**."
                    ),
                    color=PURPLE
                )
            )

    # ========================================================
    # HORSE
    # ========================================================

    @app_commands.command(
        name="horse",
        description="Apostá por un caballo."
    )
    @app_commands.describe(
        caballo="Caballo elegido.",
        apuesta="Cantidad a apostar."
    )
    @app_commands.choices(
        caballo=[
            app_commands.Choice(
                name="🐎 Caballo 1",
                value="1"
            ),
            app_commands.Choice(
                name="🐎 Caballo 2",
                value="2"
            ),
            app_commands.Choice(
                name="🐎 Caballo 3",
                value="3"
            ),
            app_commands.Choice(
                name="🐎 Caballo 4",
                value="4"
            ),
            app_commands.Choice(
                name="🐎 Caballo 5",
                value="5"
            )
        ]
    )
    async def horse(
        self,
        interaction,
        caballo: app_commands.Choice[str],
        apuesta: int
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        error = self.validate_bet(
            user,
            apuesta
        )

        if error:
            return await interaction.response.send_message(
                error,
                ephemeral=True
            )

        winner = random.choice(
            ["1", "2", "3", "4", "5"]
        )

        user["cash"] -= apuesta
        user["stats"]["money_spent"] += apuesta

        self.game_stats(user)

        if caballo.value == winner:

            winnings = apuesta * 5

            user["cash"] += winnings
            user["stats"]["money_earned"] += winnings
            user["stats"]["games_won"] += 1

            result = (
                f"🏆 ¡Ganó el caballo **{winner}**!\n\n"
                f"💰 Ganaste "
                f"**{format_money(winnings)}**."
            )

        else:

            user["stats"]["games_lost"] += 1

            result = (
                f"🏆 Ganó el caballo **{winner}**.\n\n"
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🐎 Carrera",
                description=result,
                color=PURPLE
            )
        )

    # ========================================================
    # LOTTERY
    # ========================================================

    @app_commands.command(
        name="lottery",
        description="Comprá un boleto de lotería."
    )
    async def lottery(self, interaction):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        ticket_price = 500

        if user["cash"] < ticket_price:

            return await interaction.response.send_message(
                f"❌ Necesitás "
                f"**{format_money(ticket_price)}** "
                "para comprar un boleto.",
                ephemeral=True
            )

        user["cash"] -= ticket_price
        user["stats"]["money_spent"] += ticket_price

        if random.random() < 0.03:

            prize = random.randint(
                5000,
                25000
            )

            user["cash"] += prize

            user["stats"]["money_earned"] += prize
            user["stats"]["games_won"] += 1

            result = (
                "🎉 **¡GANASTE LA LOTERÍA!**\n\n"
                f"💰 Premio: "
                f"**{format_money(prize)}**"
            )

        else:

            user["stats"]["games_lost"] += 1

            result = (
                "🎟️ Tu número no salió sorteado.\n\n"
                "💀 Esta vez no ganaste."
            )

        self.save_data()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎫 Lotería",
                description=result,
                color=PURPLE
            )
        )

    # ========================================================
    # INVENTORY
    # ========================================================

    @app_commands.command(
        name="inventory",
        description="Muestra tu inventario."
    )
    async def inventory(self, interaction):

        user = self.get_user_data(
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
                "### 🎨 Rol personalizado\n"
                "💰 **$5.000**\n"
                "`custom_role`\n\n"

                "### 💎 VIP\n"
                "💰 **$25.000**\n"
                "`vip`\n\n"

                "### ✨ Boost\n"
                "💰 **$10.000**\n"
                "`boost`"
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
        description="Compra un artículo."
    )
    @app_commands.describe(
        item="Artículo que querés comprar."
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

        user = self.get_user_data(
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
            user["inventory"].get(
                item,
                0
            ) + 1
        )

        user["stats"]["money_spent"] += price

        self.save_data()

        await interaction.response.send_message(
            f"🛒 Compraste **{item}** "
            f"por **{format_money(price)}**."
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

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        amount = user[
            "inventory"
        ].get(
            item,
            0
        )

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

        self.save_data()

        await interaction.response.send_message(
            f"💰 Vendiste **{item}** "
            f"por **{format_money(price)}**."
        )

    
    # ========================================================
    # CONFIGURAR LOG
    # ========================================================

    @app_commands.command(
        name="economy-log",
        description="Configura el canal de logs."
    )
    @app_commands.describe(
        canal="Canal donde se enviarán los logs."
    )
    async def economy_log_command(
        self,
        interaction,
        canal: discord.TextChannel
    ):

        if interaction.guild.owner_id != interaction.user.id:

            return await interaction.response.send_message(
                "❌ Solo el dueño del servidor puede "
                "configurar los logs.",
                ephemeral=True
            )

        guild = self.get_guild_data(
            interaction.guild.id
        )

        guild["log_channel"] = canal.id

        self.save_data()

        await interaction.response.send_message(
            f"✅ Los logs de economía se enviarán en "
            f"{canal.mention}."
        )

    # ========================================================
    # CONTADOR DE MENSAJES
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

        user = self.get_user_data(
            message.guild.id,
            message.author.id
        )

        user["stats"]["messages"] += 1

        if (
            user["stats"]["messages"]
            % 10
            == 0
        ):

            self.save_data()


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Economia(bot)
    )