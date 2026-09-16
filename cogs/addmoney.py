import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

OWNER_ID = 1460867297500594266

PURPLE = discord.Color.from_rgb(115, 55, 210)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "economia.json"


# ============================================================
# ARCHIVO DE ECONOMÍA
# ============================================================

def ensure_data_file():
    """
    Se asegura de que exista data/economia.json.

    No intenta crear la carpeta data si ya existe.
    Esto evita el FileExistsError de Render.
    """

    if DATA_DIR.exists():
        if not DATA_DIR.is_dir():
            raise RuntimeError(
                f"❌ '{DATA_DIR}' existe pero NO es una carpeta. "
                "Renombrá/eliminá ese archivo llamado 'data' en GitHub."
            )
    else:
        DATA_DIR.mkdir(parents=True)

    if not DATA_FILE.exists():
        DATA_FILE.write_text(
            "{}",
            encoding="utf-8"
        )


def load_data():
    ensure_data_file()

    try:
        with DATA_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            data = {}

        return data

    except json.JSONDecodeError:
        print("[ADDMONEY] ⚠️ economia.json tiene JSON inválido.")
        return {}

    except OSError as error:
        print(
            f"[ADDMONEY] ❌ Error leyendo economia.json: {error}"
        )
        return {}


def save_data(data):
    ensure_data_file()

    temp_file = DATA_FILE.with_suffix(".tmp")

    with temp_file.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    temp_file.replace(DATA_FILE)


# ============================================================
# DATOS DEL USUARIO
# ============================================================

def get_user_data(data, user_id, guild_id=None):
    """
    Detecta automáticamente varias estructuras posibles
    de economia.json.

    Soporta:

    1.
    {
        "guilds": {
            "GUILD_ID": {
                "users": {
                    "USER_ID": {
                        "money": 1000
                    }
                }
            }
        }
    }

    2.
    {
        "GUILD_ID": {
            "users": {
                "USER_ID": {
                    "money": 1000
                }
            }
        }
    }

    3.
    {
        "GUILD_ID": {
            "USER_ID": {
                "money": 1000
            }
        }
    }

    4.
    {
        "users": {
            "USER_ID": {
                "money": 1000
            }
        }
    }

    5.
    {
        "USER_ID": {
            "money": 1000
        }
    }
    """

    user_id = str(user_id)

    # --------------------------------------------------------
    # Estructura guilds -> guild -> users -> user
    # --------------------------------------------------------

    if isinstance(data.get("guilds"), dict):

        guilds = data["guilds"]

        if guild_id is not None:
            guild_key = str(guild_id)

            if guild_key not in guilds:
                guilds[guild_key] = {
                    "users": {}
                }

            guild_data = guilds[guild_key]

            if not isinstance(guild_data, dict):
                guild_data = {
                    "users": {}
                }
                guilds[guild_key] = guild_data

            if not isinstance(
                guild_data.get("users"),
                dict
            ):
                guild_data["users"] = {}

            users = guild_data["users"]

            if user_id not in users:
                users[user_id] = {
                    "money": 1000
                }

            if not isinstance(
                users[user_id],
                dict
            ):
                users[user_id] = {
                    "money": 1000
                }

            users[user_id].setdefault(
                "money",
                1000
            )

            return users[user_id]

    # --------------------------------------------------------
    # Estructura guild -> users -> user
    # --------------------------------------------------------

    if guild_id is not None:

        guild_key = str(guild_id)

        if guild_key in data:

            guild_data = data[guild_key]

            if isinstance(guild_data, dict):

                if isinstance(
                    guild_data.get("users"),
                    dict
                ):

                    users = guild_data["users"]

                    if user_id not in users:
                        users[user_id] = {
                            "money": 1000
                        }

                    if not isinstance(
                        users[user_id],
                        dict
                    ):
                        users[user_id] = {
                            "money": 1000
                        }

                    users[user_id].setdefault(
                        "money",
                        1000
                    )

                    return users[user_id]

                # ------------------------------------------------
                # Estructura guild -> user
                # ------------------------------------------------

                if user_id in guild_data:

                    if not isinstance(
                        guild_data[user_id],
                        dict
                    ):
                        guild_data[user_id] = {
                            "money": 1000
                        }

                    guild_data[user_id].setdefault(
                        "money",
                        1000
                    )

                    return guild_data[user_id]

                guild_data[user_id] = {
                    "money": 1000
                }

                return guild_data[user_id]

    # --------------------------------------------------------
    # Estructura users -> user
    # --------------------------------------------------------

    if isinstance(
        data.get("users"),
        dict
    ):

        users = data["users"]

        if user_id not in users:
            users[user_id] = {
                "money": 1000
            }

        if not isinstance(
            users[user_id],
            dict
        ):
            users[user_id] = {
                "money": 1000
            }

        users[user_id].setdefault(
            "money",
            1000
        )

        return users[user_id]

    # --------------------------------------------------------
    # Estructura user -> datos
    # --------------------------------------------------------

    if user_id not in data:
        data[user_id] = {
            "money": 1000
        }

    if not isinstance(
        data[user_id],
        dict
    ):
        data[user_id] = {
            "money": 1000
        }

    data[user_id].setdefault(
        "money",
        1000
    )

    return data[user_id]


# ============================================================
# FORMATO DE DINERO
# ============================================================

def format_money(amount):
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        amount = 0

    return f"${amount:,}".replace(",", ".")


# ============================================================
# COG
# ============================================================

class AddMoney(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        print(
            "[ADDMONEY] ✅ Cog AddMoney cargado."
        )

    # ========================================================
    # PERMISOS
    # ========================================================

    async def check_owner(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != OWNER_ID:

            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ No tenés permiso para usar este comando.",
                    ephemeral=True
                )

            return False

        return True

    # ========================================================
    # ADD MONEY
    # ========================================================

    @app_commands.command(
        name="addmoney",
        description="Agrega dinero a la cuenta de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés agregar dinero.",
        cantidad="Cantidad de dinero a agregar."
    )
    async def addmoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        print(
            f"[ADDMONEY] /addmoney usado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if not await self.check_owner(interaction):
            return

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a **0**.",
                ephemeral=True
            )

            return

        data = load_data()

        guild_id = (
            interaction.guild.id
            if interaction.guild
            else None
        )

        user_data = get_user_data(
            data,
            usuario.id,
            guild_id
        )

        try:
            dinero_anterior = int(
                user_data.get(
                    "money",
                    0
                )
            )
        except (TypeError, ValueError):
            dinero_anterior = 0

        dinero_nuevo = (
            dinero_anterior + cantidad
        )

        user_data["money"] = dinero_nuevo

        save_data(data)

        print(
            f"[ADDMONEY] ✅ "
            f"{usuario} recibió {cantidad}. "
            f"Saldo: {dinero_nuevo}"
        )

        embed = discord.Embed(
            title="💰 Dinero agregado",
            color=PURPLE
        )

        embed.description = (
            f"Se agregaron **{format_money(cantidad)}** "
            f"a la cuenta de {usuario.mention}."
        )

        embed.add_field(
            name="Saldo anterior",
            value=(
                f"**{format_money(dinero_anterior)}**"
            ),
            inline=True
        )

        embed.add_field(
            name="Saldo actual",
            value=(
                f"**{format_money(dinero_nuevo)}**"
            ),
            inline=True
        )

        embed.set_footer(
            text=f"Administrado por {interaction.user}"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # REMOVE MONEY
    # ========================================================

    @app_commands.command(
        name="removemoney",
        description="Quita dinero de la cuenta de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés quitar dinero.",
        cantidad="Cantidad de dinero a quitar."
    )
    async def removemoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        print(
            f"[ADDMONEY] /removemoney usado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if not await self.check_owner(interaction):
            return

        if cantidad <= 0:

            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a **0**.",
                ephemeral=True
            )

            return

        data = load_data()

        guild_id = (
            interaction.guild.id
            if interaction.guild
            else None
        )

        user_data = get_user_data(
            data,
            usuario.id,
            guild_id
        )

        try:
            dinero_anterior = int(
                user_data.get(
                    "money",
                    0
                )
            )
        except (TypeError, ValueError):
            dinero_anterior = 0

        dinero_nuevo = max(
            0,
            dinero_anterior - cantidad
        )

        dinero_quitado = (
            dinero_anterior - dinero_nuevo
        )

        user_data["money"] = dinero_nuevo

        save_data(data)

        print(
            f"[ADDMONEY] ✅ "
            f"{usuario} perdió {dinero_quitado}. "
            f"Saldo: {dinero_nuevo}"
        )

        embed = discord.Embed(
            title="💸 Dinero retirado",
            color=PURPLE
        )

        embed.description = (
            f"Se quitaron **{format_money(dinero_quitado)}** "
            f"de la cuenta de {usuario.mention}."
        )

        embed.add_field(
            name="Saldo anterior",
            value=(
                f"**{format_money(dinero_anterior)}**"
            ),
            inline=True
        )

        embed.add_field(
            name="Saldo actual",
            value=(
                f"**{format_money(dinero_nuevo)}**"
            ),
            inline=True
        )

        embed.set_footer(
            text=f"Administrado por {interaction.user}"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # SET MONEY
    # ========================================================

    @app_commands.command(
        name="setmoney",
        description="Establece exactamente el dinero de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés modificar.",
        cantidad="Nuevo saldo."
    )
    async def setmoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: int
    ):

        print(
            f"[ADDMONEY] /setmoney usado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if not await self.check_owner(interaction):
            return

        if cantidad < 0:

            await interaction.response.send_message(
                "❌ La cantidad no puede ser negativa.",
                ephemeral=True
            )

            return

        data = load_data()

        guild_id = (
            interaction.guild.id
            if interaction.guild
            else None
        )

        user_data = get_user_data(
            data,
            usuario.id,
            guild_id
        )

        try:
            dinero_anterior = int(
                user_data.get(
                    "money",
                    0
                )
            )
        except (TypeError, ValueError):
            dinero_anterior = 0

        user_data["money"] = cantidad

        save_data(data)

        print(
            f"[ADDMONEY] ✅ "
            f"{usuario} ahora tiene {cantidad}"
        )

        embed = discord.Embed(
            title="💰 Saldo actualizado",
            color=PURPLE
        )

        embed.description = (
            f"El saldo de {usuario.mention} "
            f"ahora es **{format_money(cantidad)}**."
        )

        embed.add_field(
            name="Saldo anterior",
            value=(
                f"**{format_money(dinero_anterior)}**"
            ),
            inline=True
        )

        embed.add_field(
            name="Nuevo saldo",
            value=(
                f"**{format_money(cantidad)}**"
            ),
            inline=True
        )

        embed.set_footer(
            text=f"Administrado por {interaction.user}"
        )

        await interaction.response.send_message(
            embed=embed
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot: commands.Bot):

    await bot.add_cog(
        AddMoney(bot)
    )

    print(
        "[ADDMONEY] ✅ AddMoney agregado al bot."
    )