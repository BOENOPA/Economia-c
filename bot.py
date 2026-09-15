import os
import threading
import traceback

import discord
from discord.ext import commands
from flask import Flask


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

PORT = int(
    os.getenv(
        "PORT",
        "10000"
    )
)

GUILD_ID = int(
    os.getenv(
        "GUILD_ID",
        "1534290216418938891"
    )
)


if not TOKEN:
    raise RuntimeError(
        "❌ Falta la variable DISCORD_TOKEN en Render."
    )


# ============================================================
# FLASK - RENDER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Economy Bot online ✅"


@app.route("/health")
def health():
    return "OK", 200


def run_flask():

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True


# ============================================================
# BOT
# ============================================================

class EconomyBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )


    # ========================================================
    # CARGAR COGS
    # ========================================================

    async def setup_hook(self):

        # ----------------------------------------------------
        # ECONOMÍA
        # ----------------------------------------------------

        try:

            await self.load_extension(
                "cogs.economia"
            )

            print(
                "✅ Cog de economía cargado."
            )

        except Exception:

            print(
                "❌ Error cargando cogs.economia:"
            )

            traceback.print_exc()


        # ----------------------------------------------------
        # BLACKJACK
        # ----------------------------------------------------

        try:

            await self.load_extension(
                "cogs.blackjack"
            )

            print(
                "✅ Cog de Blackjack cargado."
            )

        except Exception:

            print(
                "❌ Error cargando cogs.blackjack:"
            )

            traceback.print_exc()


        # ----------------------------------------------------
        # ADMINISTRACIÓN DE DINERO
        # ----------------------------------------------------

        try:

            await self.load_extension(
                "cogs.addmoney"
            )

            print(
                "✅ Cog de administración de dinero cargado."
            )

        except Exception:

            print(
                "❌ Error cargando cogs.addmoney:"
            )

            traceback.print_exc()


        # ----------------------------------------------------
        # SINCRONIZAR SLASH COMMANDS
        # ----------------------------------------------------

        try:

            guild = discord.Object(
                id=GUILD_ID
            )


            # Copiar comandos globales al servidor
            self.tree.copy_global_to(
                guild=guild
            )


            # Sincronizar instantáneamente
            synced = await self.tree.sync(
                guild=guild
            )


            print(
                "=============================================="
            )

            print(
                f"✅ {len(synced)} comandos sincronizados."
            )

            print(
                f"🆔 Servidor: {GUILD_ID}"
            )

            print(
                "=============================================="
            )


            # Mostrar comandos sincronizados
            for command in synced:

                print(
                    f"   └─ /{command.name}"
                )


        except Exception:

            print(
                "❌ Error sincronizando comandos:"
            )

            traceback.print_exc()


    # ========================================================
    # READY
    # ========================================================

    async def on_ready(self):

        print(
            "======================================================="
        )

        print(
            f"🤖 Bot conectado como: {self.user}"
        )

        print(
            f"🆔 ID: {self.user.id}"
        )

        print(
            f"🌐 Servidores: {len(self.guilds)}"
        )

        print(
            "======================================================="
        )


        # ----------------------------------------------------
        # PRESENCIA
        # ----------------------------------------------------

        try:

            await self.change_presence(

                status=discord.Status.online,

                activity=discord.Game(
                    name="/chikibeibys 💰"
                )

            )

        except Exception:

            print(
                "⚠️ No se pudo cambiar la presencia."
            )


# ============================================================
# CREAR BOT
# ============================================================

bot = EconomyBot()


# ============================================================
# ARRANQUE
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # FLASK
    # --------------------------------------------------------

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    print(
        "🌐 Flask iniciado."
    )

    print(
        f"🔌 Puerto: {PORT}"
    )


    # --------------------------------------------------------
    # DISCORD
    # --------------------------------------------------------

    print(
        "🤖 Iniciando bot de Discord..."
    )

    bot.run(
        TOKEN
    )