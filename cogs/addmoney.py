
import traceback

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

OWNER_ID = 1460867297500594266
PURPLE = discord.Color.from_rgb(115, 55, 210)


# ============================================================
# COG
# ============================================================

class AddMoney(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        print("==============================================")
        print("[ADDMONEY] Cog cargado correctamente.")
        print(f"[ADDMONEY] Usuario autorizado: {OWNER_ID}")
        print("[ADDMONEY] Comandos: addmoney, removemoney, setmoney")
        print("==============================================")


    # ========================================================
    # SEGURIDAD
    # ========================================================

    def is_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID


    # ========================================================
    # ECONOMÍA
    # ========================================================

    def get_economia(self):
        economia = self.bot.get_cog("Economia")

        if economia is None:
            print("[ADDMONEY] ❌ El cog Economia no está cargado.")

        return economia


    # ========================================================
    # FORMATO DE DINERO
    # ========================================================

    def format_money(self, economia, cantidad: int) -> str:
        formatter = getattr(economia, "format_money", None)

        if callable(formatter):
            return str(formatter(cantidad))

        return f"{cantidad:,}".replace(",", ".")


    # ========================================================
    # ERROR GENERAL
    # ========================================================

    async def error_message(
        self,
        interaction: discord.Interaction,
        error: Exception
    ):
        print("[ADDMONEY] ❌ ERROR:")
        traceback.print_exc()

        mensaje = (
            "❌ Ocurrió un error al modificar el dinero.\n"
            "Revisá la consola de Render para ver los detalles."
        )

        if interaction.response.is_done():
            await interaction.followup.send(
                mensaje,
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                mensaje,
                ephemeral=True
            )


    # ========================================================
    # CREAR EMBED
    # ========================================================

    def create_embed(
        self,
        titulo: str,
        usuario: discord.Member,
        descripcion: str
    ):
        embed = discord.Embed(
            title=titulo,
            description=descripcion,
            color=PURPLE
        )

        embed.set_thumbnail(
            url=usuario.display_avatar.url
        )

        embed.set_footer(
            text="Sistema de economía"
        )

        return embed


    # ========================================================
    # /ADDMONEY
    # ========================================================

    @app_commands.command(
        name="addmoney",
        description="Agrega dinero a un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés agregar dinero.",
        cantidad="Cantidad de dinero a agregar."
    )
    async def addmoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: app_commands.Range[int, 1, 1000000000]
    ):
        print(
            f"[ADDMONEY] /addmoney usado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )
            return

        try:
            economia = self.get_economia()

            if economia is None:
                await interaction.response.send_message(
                    "❌ El sistema de economía no está cargado.",
                    ephemeral=True
                )
                return

            data = economia.get_user(usuario.id)

            saldo_anterior = int(data.get("money", 0))
            data["money"] = saldo_anterior + cantidad

            economia.save_data()

            nuevo_saldo = data["money"]

            embed = self.create_embed(
                "💰・DINERO AGREGADO",
                usuario,
                (
                    f"👤 Usuario: {usuario.mention}\n\n"
                    f"💵 Agregado: **${self.format_money(economia, cantidad)}**\n\n"
                    f"💰 Nuevo saldo: **${self.format_money(economia, nuevo_saldo)}**"
                )
            )

            await interaction.response.send_message(embed=embed)

            print(
                f"[ADDMONEY] ✅ +${cantidad} para {usuario.id} | "
                f"Saldo: ${nuevo_saldo}"
            )

        except Exception as error:
            await self.error_message(interaction, error)


    # ========================================================
    # /REMOVEMONEY
    # ========================================================

    @app_commands.command(
        name="removemoney",
        description="Quita dinero a un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés quitar dinero.",
        cantidad="Cantidad de dinero a quitar."
    )
    async def removemoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: app_commands.Range[int, 1, 1000000000]
    ):
        print(
            f"[REMOVEMONEY] /removemoney usado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )
            return

        try:
            economia = self.get_economia()

            if economia is None:
                await interaction.response.send_message(
                    "❌ El sistema de economía no está cargado.",
                    ephemeral=True
                )
                return

            data = economia.get_user(usuario.id)

            saldo_anterior = int(data.get("money", 0))
            cantidad_real = min(cantidad, saldo_anterior)

            data["money"] = saldo_anterior - cantidad_real

            economia.save_data()

            nuevo_saldo = data["money"]

            embed = self.create_embed(
                "💸・DINERO RETIRADO",
                usuario,
                (
                    f"👤 Usuario: {usuario.mention}\n\n"
                    f"💸 Retirado: **${self.format_money(economia, cantidad_real)}**\n\n"
                    f"💰 Nuevo saldo: **${self.format_money(economia, nuevo_saldo)}**"
                )
            )

            await interaction.response.send_message(embed=embed)

            print(
                f"[REMOVEMONEY] ✅ -${cantidad_real} para {usuario.id} | "
                f"Saldo: ${nuevo_saldo}"
            )

        except Exception as error:
            await self.error_message(interaction, error)


    # ========================================================
    # /SETMONEY
    # ========================================================

    @app_commands.command(
        name="setmoney",
        description="Establece el dinero de un usuario."
    )
    @app_commands.describe(
        usuario="Usuario al que querés establecer el saldo.",
        cantidad="Nuevo saldo."
    )
    async def setmoney(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        cantidad: app_commands.Range[int, 0, 1000000000]
    ):
        print(
            f"[SETMONEY] /setmoney usado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        if not self.is_owner(interaction):
            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )
            return

        try:
            economia = self.get_economia()

            if economia is None:
                await interaction.response.send_message(
                    "❌ El sistema de economía no está cargado.",
                    ephemeral=True
                )
                return

            data = economia.get_user(usuario.id)

            saldo_anterior = int(data.get("money", 0))
            data["money"] = cantidad

            economia.save_data()

            nuevo_saldo = data["money"]

            embed = self.create_embed(
                "💳・SALDO ESTABLECIDO",
                usuario,
                (
                    f"👤 Usuario: {usuario.mention}\n\n"
                    f"💰 Saldo anterior: **${self.format_money(economia, saldo_anterior)}**\n\n"
                    f"💳 Nuevo saldo: **${self.format_money(economia, nuevo_saldo)}**"
                )
            )

            await interaction.response.send_message(embed=embed)

            print(
                f"[SETMONEY] ✅ Saldo de {usuario.id} establecido en "
                f"${nuevo_saldo}"
            )

        except Exception as error:
            await self.error_message(interaction, error)


# ============================================================
# SETUP
# ============================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(AddMoney(bot))
    print("[ADDMONEY] ✅ Comandos administrativos cargados.")
