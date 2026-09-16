
import discord
from discord.ext import commands
from discord import app_commands

PURPLE = discord.Color.from_rgb(115, 55, 210)


def create_main_embed():
    embed = discord.Embed(
        title="💜・67 Economy",
        description=(
            "Bienvenido al centro de ayuda de **67 Economy**.\n\n"
            "Administrá tu fortuna, jugá, ganá monedas "
            "y competí con toda la comunidad.\n\n"
            "Seleccioná una categoría para ver los comandos."
        ),
        color=PURPLE
    )

    embed.add_field(
        name="💰 Economía",
        value="Dinero, recompensas y saldo.",
        inline=False
    )
    embed.add_field(
        name="🎰 Juegos",
        value="Apuestas y minijuegos.",
        inline=False
    )
    embed.add_field(
        name="💸 Dinero",
        value="Transferencias y banco.",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utilidades",
        value="Herramientas del bot.",
        inline=False
    )

    embed.set_footer(text="67 Economy • Sistema de ayuda")
    return embed


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.select(
        placeholder="Seleccioná una categoría...",
        options=[
            discord.SelectOption(
                label="Economía",
                emoji="💰",
                description="Comandos de economía",
                value="economia"
            ),
            discord.SelectOption(
                label="Juegos",
                emoji="🎰",
                description="Juegos y apuestas",
                value="juegos"
            ),
            discord.SelectOption(
                label="Dinero",
                emoji="💸",
                description="Transferencias y banco",
                value="dinero"
            ),
            discord.SelectOption(
                label="Utilidades",
                emoji="🛠️",
                description="Comandos útiles",
                value="utilidades"
            )
        ]
    )
    async def select_callback(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):
        categoria = select.values[0]

        embeds = {
            "economia": discord.Embed(
                title="💰・Comandos de economía",
                description=(
                    "`/balance` — Consultá tu saldo.\n"
                    "`/daily` — Reclamá tu recompensa diaria.\n"
                    "`/work` — Trabajá para ganar dinero.\n"
                    "`/beg` — Pedí unas monedas.\n"
                    "`/leaderboard` — Ranking de riqueza."
                ),
                color=PURPLE
            ),
            "juegos": discord.Embed(
                title="🎰・Juegos",
                description=(
                    "`/slots` — Tragamonedas.\n"
                    "`/blackjack` — Jugá al blackjack.\n"
                    "`/coinflip` — Cara o cruz.\n"
                    "`/dice` — Tirada de dados."
                ),
                color=PURPLE
            ),
            "dinero": discord.Embed(
                title="💸・Gestión de dinero",
                description=(
                    "`/pay` — Transferí dinero.\n"
                    "`/bank` — Consultá tu banco.\n"
                    "`/deposit` — Depositá dinero.\n"
                    "`/withdraw` — Retirá dinero."
                ),
                color=PURPLE
            ),
            "utilidades": discord.Embed(
                title="🛠️・Utilidades",
                description=(
                    "`/help` — Abrí este menú.\n"
                    "`/profile` — Mirá tu perfil.\n"
                    "`/rank` — Consultá tu posición."
                ),
                color=PURPLE
            )
        }

        embed = embeds[categoria]
        embed.set_footer(text="67 Economy • Sistema de ayuda")

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Inicio",
        emoji="🏠",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def home(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            embed=create_main_embed(),
            view=self
        )


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Mostrá todos los comandos de 67 Economy."
    )
    async def help_command(
        self,
        interaction: discord.Interaction
    ):
        print(
            f"[HELP] Comando ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )

        await interaction.response.send_message(
            embed=create_main_embed(),
            view=HelpView()
        )


async def setup(bot):
    print("[HELP] Cargando cogs.help...")

    await bot.add_cog(HelpCog(bot))

    print("[HELP] ✅ cogs.help cargado correctamente")
