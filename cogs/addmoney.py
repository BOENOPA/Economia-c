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
# ARCHIVO DE DATOS
# ============================================================
def ensure_data_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(
            "{}",
            encoding="utf-8"
        )
def load_data():
    ensure_data_file()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            print("[ADDMONEY] economia.json no contiene un objeto válido.")
            return {}
        return data
    except json.JSONDecodeError as error:
        print(f"[ADDMONEY] ❌ JSON inválido: {error}")
        return {}
    except OSError as error:
        print(f"[ADDMONEY] ❌ Error leyendo economia.json: {error}")
        return {}
def save_data(data):
    ensure_data_file()
    temp_file = DATA_FILE.with_suffix(".tmp")
    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )
        temp_file.replace(DATA_FILE)
        print("[ADDMONEY] ✅ economia.json guardado correctamente.")
    except OSError as error:
        print(f"[ADDMONEY] ❌ Error guardando economia.json: {error}")
        raise
# ============================================================
# OBTENER USUARIO
# ============================================================
def get_user_data(data, guild_id, user_id):
    """
    Busca al usuario intentando mantener la estructura existente.
    Soporta:
    1.
    {
        "users": {
            "USER_ID": {
                "money": 1000
            }
        }
    }
    2.
    {
        "USER_ID": {
            "money": 1000
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
    """
    guild_id = str(guild_id)
    user_id = str(user_id)
    # ========================================================
    # ESTRUCTURA: guilds -> guild_id -> users -> user_id
    # ========================================================
    if isinstance(data.get("guilds"), dict):
        guilds = data["guilds"]
        if guild_id in guilds:
            guild_data = guilds[guild_id]
            if isinstance(guild_data, dict):
                users = guild_data.setdefault(
                    "users",
                    {}
                )
                if not isinstance(users, dict):
                    users = {}
                    guild_data["users"] = users
                user_data = users.setdefault(
                    user_id,
                    {
                        "money": 1000
                    }
                )
                if not isinstance(user_data, dict):
                    user_data = {
                        "money": 1000
                    }
                    users[user_id] = user_data
                user_data.setdefault("money", 1000)
                print(
                    f"[ADDMONEY] 📁 Estructura usada: "
                    f"guilds/{guild_id}/users/{user_id}"
                )
                return user_data
        # Si guild_id todavía no existe
        data["guilds"].setdefault(
            guild_id,
            {
                "users": {}
            }
        )
        guild_data = data["guilds"][guild_id]
        users = guild_data.setdefault(
            "users",
            {}
        )
        user_data = users.setdefault(
            user_id,
            {
                "money": 1000
            }
        )
        user_data.setdefault("money", 1000)
        print(
            f"[ADDMONEY] 📁 Creado: "
            f"guilds/{guild_id}/users/{user_id}"
        )
        return user_data
    # ========================================================
    # ESTRUCTURA: guild_id -> user_id
    # ========================================================
    if guild_id in data and isinstance(data[guild_id], dict):
        guild_data = data[guild_id]
        # Si ya tiene users
        if isinstance(guild_data.get("users"), dict):
            users = guild_data["users"]
            user_data = users.setdefault(
                user_id,
                {
                    "money": 1000
                }
            )
            if not isinstance(user_data, dict):
                user_data = {
                    "money": 1000
                }
                users[user_id] = user_data
            user_data.setdefault("money", 1000)
            print(
                f"[ADDMONEY] 📁 Estructura usada: "
                f"{guild_id}/users/{user_id}"
            )
            return user_data
        # Si directamente contiene usuarios
        if user_id in guild_data:
            user_data = guild_data[user_id]
            if isinstance(user_data, dict):
                user_data.setdefault("money", 1000)
                print(
                    f"[ADDMONEY] 📁 Estructura usada: "
                    f"{guild_id}/{user_id}"
                )
                return user_data
        # Crear usuario dentro del servidor
        guild_data[user_id] = {
            "money": 1000
        }
        print(
            f"[ADDMONEY] 📁 Creado: "
            f"{guild_id}/{user_id}"
        )
        return guild_data[user_id]
    # ========================================================
    # ESTRUCTURA: users -> user_id
    # ========================================================
    if isinstance(data.get("users"), dict):
        users = data["users"]
        user_data = users.setdefault(
            user_id,
            {
                "money": 1000
            }
        )
        if not isinstance(user_data, dict):
            user_data = {
                "money": 1000
            }
            users[user_id] = user_data
        user_data.setdefault("money", 1000)
        print(
            f"[ADDMONEY] 📁 Estructura usada: "
            f"users/{user_id}"
        )
        return user_data
    # ========================================================
    # ESTRUCTURA SIMPLE: user_id
    # ========================================================
    if user_id in data:
        user_data = data[user_id]
        if isinstance(user_data, dict):
            user_data.setdefault(
                "money",
                1000
            )
            print(
                f"[ADDMONEY] 📁 Estructura usada: "
                f"{user_id}"
            )
            return user_data
    # ========================================================
    # CREAR ESTRUCTURA SIMPLE
    # ========================================================
    data[user_id] = {
        "money": 1000
    }
    print(
        f"[ADDMONEY] 📁 Creado usuario: {user_id}"
    )
    return data[user_id]
# ============================================================
# DINERO
# ============================================================
def get_money(user_data):
    try:
        return int(user_data.get("money", 0))
    except (TypeError, ValueError):
        user_data["money"] = 0
        return 0
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
        print("[ADDMONEY] Cog iniciado correctamente.")
    # ========================================================
    # COMPROBAR DUEÑO
    # ========================================================
    async def check_owner(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )
            print(
                f"[ADDMONEY] 🚫 Acceso rechazado: "
                f"{interaction.user} ({interaction.user.id})"
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
        if not await self.check_owner(interaction):
            return
        if cantidad <= 0:
            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a **0**.",
                ephemeral=True
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solamente funciona dentro de un servidor.",
                ephemeral=True
            )
            return
        print(
            f"[ADDMONEY] 💰 /addmoney ejecutado | "
            f"Admin: {interaction.user} | "
            f"Usuario: {usuario} | "
            f"Cantidad: {cantidad}"
        )
        data = load_data()
        user_data = get_user_data(
            data,
            interaction.guild.id,
            usuario.id
        )
        dinero_anterior = get_money(user_data)
        dinero_nuevo = dinero_anterior + cantidad
        user_data["money"] = dinero_nuevo
        save_data(data)
        print(
            f"[ADDMONEY] ✅ {usuario} pasó de "
            f"{dinero_anterior} a {dinero_nuevo}"
        )
        embed = discord.Embed(
            title="💰 Dinero agregado",
            description=(
                f"Se agregaron **{format_money(cantidad)}** "
                f"a la cuenta de {usuario.mention}."
            ),
            color=PURPLE
        )
        embed.add_field(
            name="Saldo anterior",
            value=f"**{format_money(dinero_anterior)}**",
            inline=True
        )
        embed.add_field(
            name="Saldo actual",
            value=f"**{format_money(dinero_nuevo)}**",
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
        if not await self.check_owner(interaction):
            return
        if cantidad <= 0:
            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a **0**.",
                ephemeral=True
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solamente funciona dentro de un servidor.",
                ephemeral=True
            )
            return
        print(
            f"[ADDMONEY] 💸 /removemoney ejecutado | "
            f"Usuario: {usuario} | "
            f"Cantidad: {cantidad}"
        )
        data = load_data()
        user_data = get_user_data(
            data,
            interaction.guild.id,
            usuario.id
        )
        dinero_anterior = get_money(user_data)
        dinero_nuevo = max(
            0,
            dinero_anterior - cantidad
        )
        dinero_quitado = dinero_anterior - dinero_nuevo
        user_data["money"] = dinero_nuevo
        save_data(data)
        embed = discord.Embed(
            title="💸 Dinero retirado",
            description=(
                f"Se quitaron **{format_money(dinero_quitado)}** "
                f"de la cuenta de {usuario.mention}."
            ),
            color=PURPLE
        )
        embed.add_field(
            name="Saldo anterior",
            value=f"**{format_money(dinero_anterior)}**",
            inline=True
        )
        embed.add_field(
            name="Saldo actual",
            value=f"**{format_money(dinero_nuevo)}**",
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
        if not await self.check_owner(interaction):
            return
        if cantidad < 0:
            await interaction.response.send_message(
                "❌ La cantidad no puede ser negativa.",
                ephemeral=True
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Este comando solamente funciona dentro de un servidor.",
                ephemeral=True
            )
            return
        print(
            f"[ADDMONEY] 💰 /setmoney ejecutado | "
            f"Usuario: {usuario} | "
            f"Cantidad: {cantidad}"
        )
        data = load_data()
        user_data = get_user_data(
            data,
            interaction.guild.id,
            usuario.id
        )
        dinero_anterior = get_money(user_data)
        user_data["money"] = cantidad
        save_data(data)
        embed = discord.Embed(
            title="💰 Saldo actualizado",
            description=(
                f"El saldo de {usuario.mention} "
                f"ahora es **{format_money(cantidad)}**."
            ),
            color=PURPLE
        )
        embed.add_field(
            name="Saldo anterior",
            value=f"**{format_money(dinero_anterior)}**",
            inline=True
        )
        embed.add_field(
            name="Nuevo saldo",
            value=f"**{format_money(cantidad)}**",
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
    print("[ADDMONEY] ✅ Cog cargado correctamente.")