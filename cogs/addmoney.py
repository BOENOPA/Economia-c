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
# DATOS
# ============================================================
def ensure_data_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")
def load_data():
    ensure_data_file()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            data = {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}
def save_data(data):
    ensure_data_file()
    temp_file = DATA_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )
    temp_file.replace(DATA_FILE)
# ============================================================
# USUARIO
# ============================================================
def get_user_data(data, user_id):
    """
    Busca los datos del usuario independientemente de si
    economia.json usa IDs como strings.
    Si no existe, crea:
    {
        "money": 1000
    }
    """
    user_id = str(user_id)
    # Caso normal:
    if user_id in data:
        user_data = data[user_id]
        if isinstance(user_data, dict):
            user_data.setdefault("money", 1000)
            return user_data
    # Algunos sistemas guardan los usuarios dentro de
    # una clave "users".
    if isinstance(data.get("users"), dict):
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "money": 1000
            }
        user_data = data["users"][user_id]
        if isinstance(user_data, dict):
            user_data.setdefault("money", 1000)
            return user_data
    # Si no existe ninguna estructura conocida,
    # usamos directamente el ID.
    data[user_id] = {
        "money": 1000
    }
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
    # ========================================================
    # VERIFICAR DUEÑO
    # ========================================================
    async def check_owner(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
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
        if not await self.check_owner(interaction):
            return
        if cantidad <= 0:
            await interaction.response.send_message(
                "❌ La cantidad debe ser mayor a **0**.",
                ephemeral=True
            )
            return
        data = load_data()
        user_data = get_user_data(
            data,
            usuario.id
        )
        dinero_anterior = int(
            user_data.get("money", 0)
        )
        dinero_nuevo = dinero_anterior + cantidad
        user_data["money"] = dinero_nuevo
        save_data(data)
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
        data = load_data()
        user_data = get_user_data(
            data,
            usuario.id
        )
        dinero_anterior = int(
            user_data.get("money", 0)
        )
        dinero_nuevo = max(
            0,
            dinero_anterior - cantidad
        )
        dinero_quitado = dinero_anterior - dinero_nuevo
        user_data["money"] = dinero_nuevo
        save_data(data)
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
        data = load_data()
        user_data = get_user_data(
            data,
            usuario.id
        )
        dinero_anterior = int(
            user_data.get("money", 0)
        )
        user_data["money"] = cantidad
        save_data(data)
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
    await bot.add_cog(AddMoney(bot))