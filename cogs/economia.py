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


# ============================================================
# CARGAR DATOS
# ============================================================

def load_data():

    try:

        if not DATA_FILE.exists():
            return {
                "guilds": {}
            }

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            return {
                "guilds": {}
            }

        data.setdefault(
            "guilds",
            {}
        )

        return data

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError
    ):

        return {
            "guilds": {}
        }


# ============================================================
# GUARDAR DATOS
# ============================================================

def save_data(data):

    try:

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

    return int(
        time.time()
    )


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
     
    class Economia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

        print(
            "✅ Cog de economía cargado correctamente."
        )

    # ============================================================
    # DAR DINERO A UN ROL
    # ============================================================

    @app_commands.command(
        name="give-role-money",
        description="Da dinero a todos los miembros que tengan un rol."
    )
    @app_commands.describe(
        rol="Rol cuyos miembros recibirán el dinero.",
        cantidad="Cantidad de dinero para cada miembro."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def give_role_money(
        self,
        interaction: discord.Interaction,
        rol: discord.Role,
        cantidad: int
    ):
        if cantidad <= 0:
            return await interaction.response.send_message(
                "❌ La cantidad debe ser mayor que **$0**.",
                ephemeral=True
            )

        if rol.is_default():
            return await interaction.response.send_message(
                "❌ No podés seleccionar `@everyone`.",
                ephemeral=True
            )

        await interaction.response.defer()

        count = 0
        total = 0

        for member in rol.members:

            if member.bot:
                continue

            user = self.get_user_data(
                interaction.guild.id,
                member.id
            )

            user["cash"] += cantidad
            user["stats"]["money_earned"] += cantidad

            count += 1
            total += cantidad

        self.save_data(self.data)

        embed = discord.Embed(
            title="💰 Dinero entregado",
            description=(
                f"Se entregaron **${cantidad:,}** a cada miembro "
                f"con el rol {rol.mention}.\n\n"
                f"👥 **Miembros:** `{count}`\n"
                f"💵 **Por persona:** `${cantidad:,}`\n"
                f"💰 **Total entregado:** `${total:,}`"
            ).replace(",", "."),
            color=PURPLE
        )

        embed.set_footer(
            text=f"Ejecutado por {interaction.user.display_name}"
        )

        await interaction.followup.send(
            embed=embed
        )

    # ========================================================
    # GUILD
    # ========================================================

    def get_guild_data(
        self,
        guild_id
    ):

        guild_id = str(
            guild_id
        )

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

        user_id = str(
            user_id
        )

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

        # Dueño siempre puede
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

        # Si no hay rol configurado:
        # solamente Administradores
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

        target = (
            usuario
            or interaction.user
        )

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
    async def daily(
        self,
        interaction
    ):

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

        save_data(
            self.data
        )

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
    async def work(
        self,
        interaction
    ):

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
            "🛒 vendedor"

        ]

        job = random.choice(
            jobs
        )

        amount = random.randint(
            WORK_MIN,
            WORK_MAX
        )

        user["cash"] += amount

        user["work"] = now_value

        user["stats"]["work_claims"] += 1

        user["stats"]["money_earned"] += amount

        save_data(
            self.data
        )

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
    async def beg(
        self,
        interaction
    ):

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

        save_data(
            self.data
        )

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

        save_data(
            self.data
        )

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

        save_data(
            self.data
        )

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

        save_data(
            self.data
        )

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
    async def leaderboard(
        self,
        interaction
    ):

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

            if member:

                name = member.display_name

            else:

                name = f"Usuario {user_id}"

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
    async def profile(
        self,
        interaction,
        usuario: discord.Member | None = None
    ):

        target = (
            usuario
            or interaction.user
        )

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
            value=format_money(
                total
            ),
            inline=False
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
            name="💬 Mensajes",
            value=str(
                stats["messages"]
            ),
            inline=True
        )

        embed.add_field(
            name="🎁 Daily",
            value=str(
                stats["daily_claims"]
            ),
            inline=True
        )

        embed.add_field(
            name="💼 Trabajos",
            value=str(
                stats["work_claims"]
            ),
            inline=True
        )

        embed.add_field(
            name="🎮 Partidas",
            value=str(
                stats["games_played"]
            ),
            inline=True
        )

        embed.add_field(
            name="🏆 Victorias",
            value=str(
                stats["games_won"]
            ),
            inline=True
        )

        embed.add_field(
            name="💀 Derrotas",
            value=str(
                stats["games_lost"]
            ),
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

        user = self.get_user_data(
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

        # JACKPOT
        if (
            result[0]
            == result[1]
            == result[2]
        ):

            winnings = apuesta * 5

            user["cash"] += winnings

            user["stats"]["games_won"] += 1

            user["stats"]["money_earned"] += winnings

            description = (
                "🎉 **¡JACKPOT!**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💰 Ganaste "
                f"**{format_money(winnings)}**."
            )

        # DOS IGUALES
        elif (
            result[0] == result[1]
            or result[1] == result[2]
        ):

            winnings = apuesta * 2

            user["cash"] += winnings

            user["stats"]["games_won"] += 1

            user["stats"]["money_earned"] += winnings

            description = (
                "✨ **¡Ganaste!**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💰 Ganaste "
                f"**{format_money(winnings)}**."
            )

        # PERDER
        else:

            user["cash"] -= apuesta

            user["stats"]["games_lost"] += 1

            user["stats"]["money_spent"] += apuesta

            description = (
                "💀 **Perdiste.**\n\n"
                f"**{' | '.join(result)}**\n\n"
                f"💸 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        save_data(
            self.data
        )

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

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        if apuesta > user["cash"]:

            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        result = random.choice(
            [
                "cara",
                "cruz"
            ]
        )

        user["stats"]["games_played"] += 1

        if result == lado.value:

            user["cash"] += apuesta

            user["stats"]["games_won"] += 1

            user["stats"]["money_earned"] += apuesta

            description = (
                f"🪙 Salió **{result.upper()}**.\n\n"
                f"🎉 Ganaste "
                f"**{format_money(apuesta)}**."
            )

        else:

            user["cash"] -= apuesta

            user["stats"]["games_lost"] += 1

            user["stats"]["money_spent"] += apuesta

            description = (
                f"🪙 Salió **{result.upper()}**.\n\n"
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        save_data(
            self.data
        )

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

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        if apuesta > user["cash"]:

            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        result = random.randint(
            1,
            6
        )

        user["stats"]["games_played"] += 1

        if result == numero:

            winnings = apuesta * 5

            user["cash"] += winnings

            user["stats"]["games_won"] += 1

            user["stats"]["money_earned"] += winnings

            description = (
                f"🎲 Salió **{result}**.\n\n"
                f"🎉 ¡Ganaste "
                f"**{format_money(winnings)}**!"
            )

        else:

            user["cash"] -= apuesta

            user["stats"]["games_lost"] += 1

            user["stats"]["money_spent"] += apuesta

            description = (
                f"🎲 Salió **{result}**.\n\n"
                f"💀 Perdiste "
                f"**{format_money(apuesta)}**."
            )

        save_data(
            self.data
        )

        await interaction.response.send_message(
            description
        )

    
    # ========================================================
    # INVENTORY
    # ========================================================

    @app_commands.command(
        name="inventory",
        description="Muestra tu inventario."
    )
    async def inventory(
        self,
        interaction
    ):

        user = self.get_user_data(
            interaction.guild.id,
            interaction.user.id
        )

        inventory = user[
            "inventory"
        ]

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
    async def shop(
        self,
        interaction
    ):

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

        save_data(
            self.data
        )

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

        save_data(
            self.data
        )

        await interaction.response.send_message(
            f"💰 Vendiste **{item}** "
            f"por **{format_money(price)}**."
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

        if not self.can_manage_money(
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

        user = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        user["cash"] += cantidad

        user["stats"]["money_earned"] += cantidad

        save_data(
            self.data
        )

        await self.send_log(
            interaction.guild,
            "💰 GIVE MONEY",
            (
                f"**Administrador:** "
                f"{interaction.user.mention}\n"
                f"**Usuario:** "
                f"{usuario.mention}\n"
                f"**Cantidad:** "
                f"{format_money(cantidad)}"
            )
        )

        await interaction.response.send_message(
            f"💰 Le diste "
            f"**{format_money(cantidad)}** "
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

        if not self.can_manage_money(
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

        user = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        removed = min(
            cantidad,
            user["cash"]
        )

        user["cash"] -= removed

        save_data(
            self.data
        )

        await self.send_log(
            interaction.guild,
            "💸 REMOVE MONEY",
            (
                f"**Administrador:** "
                f"{interaction.user.mention}\n"
                f"**Usuario:** "
                f"{usuario.mention}\n"
                f"**Cantidad:** "
                f"{format_money(removed)}"
            )
        )

        await interaction.response.send_message(
            f"💸 Le quitaste "
            f"**{format_money(removed)}** "
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

        if not self.can_manage_money(
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

        user = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        old = user["cash"]

        user["cash"] = cantidad

        save_data(
            self.data
        )

        await self.send_log(
            interaction.guild,
            "⚙️ SET MONEY",
            (
                f"**Administrador:** "
                f"{interaction.user.mention}\n"
                f"**Usuario:** "
                f"{usuario.mention}\n"
                f"**Anterior:** "
                f"{format_money(old)}\n"
                f"**Nuevo:** "
                f"{format_money(cantidad)}"
            )
        )

        await interaction.response.send_message(
            f"⚙️ El balance de "
            f"{usuario.mention} ahora es "
            f"**{format_money(cantidad)}**."
        )

    # ========================================================
    # RESET MONEY
    # ========================================================

    @app_commands.command(
        name="reset-money",
        description="Reinicia la economía de un usuario."
    )
    async def reset_money(
        self,
        interaction,
        usuario: discord.Member
    ):

        if not self.can_manage_money(
            interaction,
            "reset-money"
        ):

            return await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

        user = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        user["cash"] = START_MONEY

        user["bank"] = 0

        save_data(
            self.data
        )

        await self.send_log(
            interaction.guild,
            "🔄 RESET MONEY",
            (
                f"**Administrador:** "
                f"{interaction.user.mention}\n"
                f"**Usuario:** "
                f"{usuario.mention}\n"
                f"**Balance inicial:** "
                f"{format_money(START_MONEY)}"
            )
        )

        await interaction.response.send_message(
            f"🔄 Economía de "
            f"{usuario.mention} reiniciada."
        )

    # ========================================================
    # ADD BANK
    # ========================================================

    @app_commands.command(
        name="add-bank",
        description="Agrega dinero al banco."
    )
    async def add_bank(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_manage_money(
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

        user = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        user["bank"] += cantidad

        save_data(
            self.data
        )

        await interaction.response.send_message(
            f"🏦 Agregaste "
            f"**{format_money(cantidad)}** "
            f"al banco de {usuario.mention}."
        )

    # ========================================================
    # REMOVE BANK
    # ========================================================

    @app_commands.command(
        name="remove-bank",
        description="Quita dinero del banco."
    )
    async def remove_bank(
        self,
        interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        if not self.can_manage_money(
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

        user = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        removed = min(
            cantidad,
            user["bank"]
        )

        user["bank"] -= removed

        save_data(
            self.data
        )

        await interaction.response.send_message(
            f"🏦 Quitaste "
            f"**{format_money(removed)}** "
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

        if not self.can_manage_money(
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

        user = self.get_user_data(
            interaction.guild.id,
            usuario.id
        )

        user["bank"] = cantidad

        save_data(
            self.data
        )

        await interaction.response.send_message(
            f"🏦 El banco de "
            f"{usuario.mention} ahora tiene "
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
        description="Configura los permisos de economía."
    )
    @app_commands.describe(
        accion="Acción económica.",
        rol="Rol que podrá usarla."
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
                "❌ Solo el dueño del servidor puede "
                "configurar la economía.",
                ephemeral=True
            )

        guild = self.get_guild_data(
            interaction.guild.id
        )

        roles = guild[
            "permissions"
        ].setdefault(
            accion.value,
            []
        )

        role_id = str(
            rol.id
        )

        if role_id in roles:

            roles.remove(
                role_id
            )

            message = (
                f"🗑️ Se quitó el permiso "
                f"**{accion.value}** de {rol.mention}."
            )

        else:

            roles.append(
                role_id
            )

            message = (
                f"✅ Se otorgó el permiso "
                f"**{accion.value}** a {rol.mention}."
            )

        save_data(
            self.data
        )

        await interaction.response.send_message(
            message
        )

    # ========================================================
    # VER PERMISOS
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
                "❌ Solo el dueño del servidor puede "
                "ver esta configuración.",
                ephemeral=True
            )

        guild = self.get_guild_data(
            interaction.guild.id
        )

        description = ""

        for action, role_ids in guild[
            "permissions"
        ].items():

            if role_ids:

                role_mentions = []

                for role_id in role_ids:

                    role = interaction.guild.get_role(
                        int(role_id)
                    )

                    if role:

                        role_mentions.append(
                            role.mention
                        )

                roles_text = (
                    ", ".join(
                        role_mentions
                    )
                    if role_mentions
                    else "Rol eliminado"
                )

            else:

                roles_text = (
                    "👑 Administradores"
                )

            description += (
                f"**{action}**\n"
                f"{roles_text}\n\n"
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
    # CONFIGURAR LOG
    # ========================================================

    @app_commands.command(
        name="economy-log",
        description="Configura el canal de logs."
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

        guild[
            "log_channel"
        ] = canal.id

        save_data(
            self.data
        )

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

        user[
            "stats"
        ][
            "messages"
        ] += 1

        # Guardar cada 10 mensajes
        if (
            user["stats"]["messages"]
            % 10
            == 0
        ):

            save_data(
                self.data
            )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Economia(bot)
    )