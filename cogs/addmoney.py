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

    def __init__(self, bot):
        self.bot = bot

        print("==============================================")
        print("[ADDMONEY] Cog cargado correctamente.")
        print(f"[ADDMONEY] Usuario autorizado: {OWNER_ID}")
        print("[ADDMONEY] /addmoney")
        print("[ADDMONEY] /removemoney")
        print("[ADDMONEY] /setmoney")
        print("==============================================")


    # ========================================================
    # COMPROBAR SI ES EL DUEÑO AUTORIZADO
    # ========================================================

    def is_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == OWNER_ID


    # ========================================================
    # OBTENER COG DE ECONOMÍA
    # ========================================================

    def get_economia(self):

        economia = self.bot.get_cog("Economia")

        if economia is None:
            print("[ADDMONEY] ❌ No se encontró el cog Economia.")

        return economia


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

        # ----------------------------------------------------
        # SEGURIDAD
        # ----------------------------------------------------

        if not self.is_owner(interaction):

            print(
                f"[ADDMONEY] ❌ ACCESO DENEGADO "
                f"ID={interaction.user.id}"
            )

            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # ECONOMÍA
        # ----------------------------------------------------

        economia = self.get_economia()

        if economia is None:

            await interaction.response.send_message(
                "❌ El sistema de economía no está cargado.",
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # AGREGAR DINERO
        # ----------------------------------------------------

        data = economia.get_user(usuario.id)

        saldo_anterior = data["money"]

        data["money"] += cantidad

        economia.save_data()

        nuevo_saldo = data["money"]


        print(
            f"[ADDMONEY] ✅ +${cantidad} "
            f"para {usuario.id}"
        )

        print(
            f"[ADDMONEY] Saldo anterior: ${saldo_anterior}"
        )

        print(
            f"[ADDMONEY] Nuevo saldo: ${nuevo_saldo}"
        )


        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title="💰・DINERO AGREGADO",
            description=(
                f"👤 Usuario: {usuario.mention}\n\n"
                f"💵 Agregado: "
                f"**${economia.format_money(cantidad)}**\n\n"
                f"💰 Nuevo saldo: "
                f"**${economia.format_money(nuevo_saldo)}**"
            ),
            color=PURPLE
        )

        embed.set_thumbnail(
            url=usuario.display_avatar.url
        )

        embed.set_footer(
            text="Sistema de economía"
        )

        await interaction.response.send_message(
            embed=embed
        )


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


        # ----------------------------------------------------
        # SEGURIDAD
        # ----------------------------------------------------

        if not self.is_owner(interaction):

            print(
                f"[REMOVEMONEY] ❌ ACCESO DENEGADO "
                f"ID={interaction.user.id}"
            )

            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # ECONOMÍA
        # ----------------------------------------------------

        economia = self.get_economia()

        if economia is None:

            await interaction.response.send_message(
                "❌ El sistema de economía no está cargado.",
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # QUITAR DINERO
        # ----------------------------------------------------

        data = economia.get_user(usuario.id)

        saldo_anterior = data["money"]

        cantidad_real = min(
            cantidad,
            data["money"]
        )

        data["money"] -= cantidad_real

        economia.save_data()

        nuevo_saldo = data["money"]


        print(
            f"[REMOVEMONEY] ✅ -${cantidad_real} "
            f"para {usuario.id}"
        )

        print(
            f"[REMOVEMONEY] Saldo anterior: "
            f"${saldo_anterior}"
        )

        print(
            f"[REMOVEMONEY] Nuevo saldo: "
            f"${nuevo_saldo}"
        )


        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title="💸・DINERO RETIRADO",
            description=(
                f"👤 Usuario: {usuario.mention}\n\n"
                f"💸 Retirado: "
                f"**${economia.format_money(cantidad_real)}**\n\n"
                f"💰 Nuevo saldo: "
                f"**${economia.format_money(nuevo_saldo)}**"
            ),
            color=PURPLE
        )

        embed.set_thumbnail(
            url=usuario.display_avatar.url
        )

        embed.set_footer(
            text="Sistema de economía"
        )

        await interaction.response.send_message(
            embed=embed
        )


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


        # ----------------------------------------------------
        # SEGURIDAD
        # ----------------------------------------------------

        if not self.is_owner(interaction):

            print(
                f"[SETMONEY] ❌ ACCESO DENEGADO "
                f"ID={interaction.user.id}"
            )

            await interaction.response.send_message(
                "❌ No tenés permiso para usar este comando.",
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # ECONOMÍA
        # ----------------------------------------------------

        economia = self.get_economia()

        if economia is None:

            await interaction.response.send_message(
                "❌ El sistema de economía no está cargado.",
                ephemeral=True
            )

            return


        # ----------------------------------------------------
        # ESTABLECER DINERO
        # ----------------------------------------------------

        data = economia.get_user(usuario.id)

        saldo_anterior = data["money"]

        data["money"] = cantidad

        economia.save_data()

        nuevo_saldo = data["money"]


        print(
            f"[SETMONEY] ✅ Saldo de {usuario.id} "
            f"establecido en ${cantidad}"
        )

        print(
            f"[SETMONEY] Saldo anterior: "
            f"${saldo_anterior}"
        )

        print(
            f"[SETMONEY] Nuevo saldo: "
            f"${nuevo_saldo}"
        )


        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title="💳・SALDO ESTABLECIDO",
            description=(
                f"👤 Usuario: {usuario.mention}\n\n"
                f"💰 Saldo anterior: "
                f"**${economia.format_money(saldo_anterior)}**\n\n"
                f"💳 Nuevo saldo: "
                f"**${economia.format_money(nuevo_saldo)}**"
            ),
            color=PURPLE
        )

        embed.set_thumbnail(
            url=usuario.display_avatar.url
        )

        embed.set_footer(
            text="Sistema de economía"
        )

        await interaction.response.send_message(
            embed=embed
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        AddMoney(bot)
    )

    print(
        "[ADDMONEY] ✅ Comandos administrativos "
        "cargados correctamente."
    )