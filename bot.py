import os
import asyncio
import threading
import traceback

import discord
from discord.ext import commands
from flask import Flask


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
GUILD_ID = int(os.getenv("GUILD_ID", "1534290216418938891"))

if not TOKEN:
    raise RuntimeError("Falta la variable DISCORD_TOKEN en Render.")


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

    async def setup_hook(self):

    # ========================================================
    # CARGAR TODOS LOS COGS
    # ========================================================

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            extension = f"cogs.{filename[:-3]}"

            try:
                await self.load_extension(extension)
                print(f"✅ Cog cargado: {extension}")
            except Exception:
                print(f"❌ Error cargando: {extension}")
                traceback.print_exc()

    # ========================================================
    # SINCRONIZAR SLASH COMMANDS
    # ========================================================

    try:
        guild = discord.Object(id=GUILD_ID)

        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)

        print(f"✅ {len(synced)} comandos sincronizados.")
    except Exception:
        print("❌ Error sincronizando comandos:")
        traceback.print_exc()

    async def on_ready(self):

        print("=" * 50)
        print(f"🤖 Bot conectado como: {self.user}")
        print(f"🆔 ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print("=" * 50)

        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(
                name="/chikibeibys 💰"
            )
        )


bot = EconomyBot()


# ============================================================
# ARRANQUE
# ============================================================

if __name__ == "__main__":

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    print("🌐 Flask iniciado.")
    print(f"🔌 Puerto: {PORT}")

    bot.run(TOKEN)