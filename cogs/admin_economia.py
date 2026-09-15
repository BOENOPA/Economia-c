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
RED = discord.Color.from_rgb(220, 60, 70)
GREEN = discord.Color.from_rgb(45, 190, 110)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "economia.json"
# ============================================================
# UTILIDADES
# ============================================================
def cargar_economia():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except (json.JSONDecodeError, OSError):
        return {}
def guardar_economia(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
def obtener_usuario(data, user_id):
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "money": 0
        }
    if not isinstance(data[user_id], dict):
        data[user_id] = {
            "money": 0
        }
    if "money" not in data[user_id]:
        data[user_id]["money"] = 0
    return data[user_id]
# ============================================================
# COG
# ============================================================
class EconomiaAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # ========================================================
    # COMPROBAR DUEÑO
    # ========================================================
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID:
            embed = discord.Embed(
                title="❌ Acceso denegado",
                description="No tenés permiso para utilizar los comandos de administración de economía.",
                color=RED
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return False
        return True
    # ========================================================
    # AGREGAR DINERO
    # ========================================================
    @app_commands.command(
        name="addmoney",
        description="Agrega dinero a la cuenta de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés agregar dinero",
        cantidad="Cantidad de dinero a agregar"
    )
    async def addmoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: app_commands.Range[int, 1, 1_000_000_000]
    ):
        data = cargar_economia()
        cuenta = obtener_usuario(data, usuario.id)
        saldo_anterior = int(cuenta.get("money", 0))
        cuenta["money"] = saldo_anterior + cantidad
        guardar_economia(data)
        embed = discord.Embed(
            title="💰 Dinero agregado",
            description=(
                f"Se agregaron **${cantidad:,}** a {usuario.mention}.\n\n"
                f"**Saldo anterior:** ${saldo_anterior:,}\n"
                f"**Nuevo saldo:** ${cuenta['money']:,}"
            ).replace(",", "."),
            color=GREEN
        )
        embed.set_footer(
            text=f"Operación realizada por {interaction.user}"
        )
        await interaction.response.send_message(embed=embed)
    # ========================================================
    # SACAR DINERO
    # ========================================================
    @app_commands.command(
        name="removemoney",
        description="Quita dinero de la cuenta de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés quitar dinero",
        cantidad="Cantidad de dinero a quitar"
    )
    async def removemoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: app_commands.Range[int, 1, 1_000_000_000]
    ):
        data = cargar_economia()
        cuenta = obtener_usuario(data, usuario.id)
        saldo_anterior = int(cuenta.get("money", 0))
        # No permite saldo negativo
        cantidad_real = min(cantidad, saldo_anterior)
        cuenta["money"] = saldo_anterior - cantidad_real
        guardar_economia(data)
        if cantidad_real == 0:
            embed = discord.Embed(
                title="⚠️ Sin dinero",
                description=(
                    f"{usuario.mention} no tiene dinero para retirar.\n\n"
                    f"**Saldo actual:** $0"
                ),
                color=RED
            )
        else:
            embed = discord.Embed(
                title="💸 Dinero retirado",
                description=(
                    f"Se quitaron **${cantidad_real:,}** a {usuario.mention}.\n\n"
                    f"**Saldo anterior:** ${saldo_anterior:,}\n"
                    f"**Nuevo saldo:** ${cuenta['money']:,}"
                ).replace(",", "."),
                color=PURPLE
            )
        embed.set_footer(
            text=f"Operación realizada por {interaction.user}"
        )
        await interaction.response.send_message(embed=embed)
# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(EconomiaAdmin(bot))