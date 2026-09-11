import asyncio
import random

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# CONFIGURACIÓN
# ============================================================

PURPLE = discord.Color.from_rgb(115, 55, 210)

MAX_BET = 100000

GAME_TIMEOUT = 180

# Blackjack natural:
# devuelve apuesta + 1.5x de ganancia = 2.5x total
BLACKJACK_MULTIPLIER = 2.5

# Victoria normal:
# devuelve apuesta + 1x de ganancia = 2x total
NORMAL_WIN_MULTIPLIER = 2

# Dealer se planta en 17
DEALER_STAND_VALUE = 17


# ============================================================
# CARTAS
# ============================================================

SUITS = (
    "♠",
    "♥",
    "♦",
    "♣"
)

RANKS = (
    "A",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "J",
    "Q",
    "K"
)


# ============================================================
# CARTAS UNICODE
# ============================================================

UNICODE_CARDS = {

    # ESPADAS
    ("A", "♠"): "🂡",
    ("2", "♠"): "🂢",
    ("3", "♠"): "🂣",
    ("4", "♠"): "🂤",
    ("5", "♠"): "🂥",
    ("6", "♠"): "🂦",
    ("7", "♠"): "🂧",
    ("8", "♠"): "🂨",
    ("9", "♠"): "🂩",
    ("10", "♠"): "🂪",
    ("J", "♠"): "🂫",
    ("Q", "♠"): "🂭",
    ("K", "♠"): "🂮",

    # CORAZONES
    ("A", "♥"): "🂱",
    ("2", "♥"): "🂲",
    ("3", "♥"): "🂳",
    ("4", "♥"): "🂴",
    ("5", "♥"): "🂵",
    ("6", "♥"): "🂶",
    ("7", "♥"): "🂷",
    ("8", "♥"): "🂸",
    ("9", "♥"): "🂹",
    ("10", "♥"): "🂺",
    ("J", "♥"): "🂻",
    ("Q", "♥"): "🂽",
    ("K", "♥"): "🂾",

    # DIAMANTES
    ("A", "♦"): "🃁",
    ("2", "♦"): "🃂",
    ("3", "♦"): "🃃",
    ("4", "♦"): "🃄",
    ("5", "♦"): "🃅",
    ("6", "♦"): "🃆",
    ("7", "♦"): "🃇",
    ("8", "♦"): "🃈",
    ("9", "♦"): "🃉",
    ("10", "♦"): "🃊",
    ("J", "♦"): "🃋",
    ("Q", "♦"): "🃍",
    ("K", "♦"): "🃎",

    # TREBOLES
    ("A", "♣"): "🃑",
    ("2", "♣"): "🃒",
    ("3", "♣"): "🃓",
    ("4", "♣"): "🃔",
    ("5", "♣"): "🃕",
    ("6", "♣"): "🃖",
    ("7", "♣"): "🃗",
    ("8", "♣"): "🃘",
    ("9", "♣"): "🃙",
    ("10", "♣"): "🃚",
    ("J", "♣"): "🃛",
    ("Q", "♣"): "🃝",
    ("K", "♣"): "🃞",
}


# ============================================================
# UTILIDADES
# ============================================================

def create_deck():
    deck = [
        (rank, suit)
        for suit in SUITS
        for rank in RANKS
    ]

    random.shuffle(deck)

    return deck


def card_value(card):

    rank = card[0]

    if rank in ("J", "Q", "K"):
        return 10

    if rank == "A":
        return 11

    return int(rank)


def hand_value(hand):

    total = 0
    aces = 0

    for card in hand:

        total += card_value(card)

        if card[0] == "A":
            aces += 1

    while total > 21 and aces > 0:

        total -= 10
        aces -= 1

    return total


def is_blackjack(hand):

    return (
        len(hand) == 2
        and hand_value(hand) == 21
    )


def is_bust(hand):

    return hand_value(hand) > 21


def card_text(card):

    return UNICODE_CARDS.get(
        card,
        f"`{card[0]}{card[1]}`"
    )


def cards_text(hand):

    return " ".join(
        card_text(card)
        for card in hand
    )


def format_money(amount):

    return (
        f"${amount:,}"
        .replace(",", ".")
    )


# ============================================================
# GAME
# ============================================================

class BlackjackGame:

    def __init__(
        self,
        cog,
        interaction,
        bet
    ):

        self.cog = cog
        self.interaction = interaction

        self.user_id = interaction.user.id
        self.guild_id = interaction.guild.id

        self.original_bet = bet

        self.deck = create_deck()

        self.dealer = []

        self.hands = []

        self.current_hand_index = 0

        self.finished = False

        self.split_used = False

        self.game_stats_recorded = False

        # ----------------------------------------------------
        # PRIMERA MANO
        # ----------------------------------------------------

        first_hand = {
            "cards": [
                self.deck.pop(),
                self.deck.pop()
            ],
            "bet": bet,
            "finished": False,
            "bust": False,
            "doubled": False,
            "split": False,
            "result": None
        }

        self.hands.append(
            first_hand
        )

        # ----------------------------------------------------
        # DEALER
        # ----------------------------------------------------

        self.dealer.append(
            self.deck.pop()
        )

        self.dealer.append(
            self.deck.pop()
        )

    # ========================================================
    # ECONOMÍA
    # ========================================================

    def economy(self):

        return self.cog.bot.get_cog(
            "Economia"
        )

    def get_user(self):

        economy = self.economy()

        if economy is None:
            return None

        return economy.get_user_data(
            self.guild_id,
            self.user_id
        )

    def save(self):

        economy = self.economy()

        if economy is None:
            return

        # Compatible con tu economía actual
        if hasattr(
            economy,
            "save_data"
        ):

            economy.save_data(
                economy.data
            )

            return

        # Compatibilidad con función global
        try:

            from cogs.economia import save_data

            save_data(
                economy.data
            )

        except Exception as error:

            print(
                f"❌ Error guardando Blackjack: {error}"
            )

    # ========================================================
    # DINERO
    # ========================================================

    def remove_money(
        self,
        amount
    ):

        user = self.get_user()

        if user is None:
            return False

        if user["cash"] < amount:
            return False

        user["cash"] -= amount

        user["stats"]["money_spent"] += amount

        return True

    def add_money(
        self,
        amount
    ):

        user = self.get_user()

        if user is None:
            return

        user["cash"] += amount

        user["stats"]["money_earned"] += amount

    # ========================================================
    # MANO ACTUAL
    # ========================================================

    def current_hand(self):

        return self.hands[
            self.current_hand_index
        ]

    def current_cards(self):

        return self.current_hand()[
            "cards"
        ]

    def current_value(self):

        return hand_value(
            self.current_cards()
        )

    def current_bust(self):

        return is_bust(
            self.current_cards()
        )

    # ========================================================
    # PEDIR
    # ========================================================

    def hit(self):

        self.current_hand()["cards"].append(
            self.deck.pop()
        )

    # ========================================================
    # DOBLAR
    # ========================================================

    def can_double(self):

        hand = self.current_hand()

        return (
            len(hand["cards"]) == 2
            and not hand["finished"]
            and not hand["doubled"]
        )

    def double_bet(self):

        hand = self.current_hand()

        amount = hand["bet"]

        if not self.remove_money(
            amount
        ):
            return False

        hand["bet"] *= 2

        hand["doubled"] = True

        return True

    # ========================================================
    # SEPARAR
    # ========================================================

    def can_split(self):

        if self.split_used:
            return False

        hand = self.current_hand()

        cards = hand["cards"]

        if len(cards) != 2:
            return False

        # Permitimos separar cartas del mismo valor.
        if card_value(cards[0]) != card_value(cards[1]):
            return False

        user = self.get_user()

        if user is None:
            return False

        return user["cash"] >= hand["bet"]

    def split_hand(self):

        if not self.can_split():
            return False

        original = self.current_hand()

        original_bet = original["bet"]

        # Cobrar la segunda apuesta
        if not self.remove_money(
            original_bet
        ):
            return False

        first_card = original["cards"][0]
        second_card = original["cards"][1]

        # Primera mano
        original["cards"] = [
            first_card,
            self.deck.pop()
        ]

        original["split"] = True

        # Segunda mano
        second_hand = {
            "cards": [
                second_card,
                self.deck.pop()
            ],
            "bet": original_bet,
            "finished": False,
            "bust": False,
            "doubled": False,
            "split": True,
            "result": None
        }

        self.hands.append(
            second_hand
        )

        self.split_used = True

        self.current_hand_index = 0

        return True

    # ========================================================
    # MANOS
    # ========================================================

    def finish_current_hand(self):

        hand = self.current_hand()

        hand["finished"] = True

        if is_bust(
            hand["cards"]
        ):
            hand["bust"] = True

    def next_hand(self):

        for index, hand in enumerate(
            self.hands
        ):

            if not hand["finished"]:

                self.current_hand_index = index

                return True

        return False

    def all_hands_finished(self):

        return all(
            hand["finished"]
            for hand in self.hands
        )

    # ========================================================
    # TERMINAR RONDA
    # ========================================================

    async def finish_round(self):

        # ----------------------------------------------------
        # Si hay más manos
        # ----------------------------------------------------

        if not self.all_hands_finished():

            if self.next_hand():

                return False

        # ----------------------------------------------------
        # Dealer juega
        # ----------------------------------------------------

        await self.dealer_play()

        self.finished = True

        self.calculate_results()

        self.save()

        return True

    # ========================================================
    # DEALER
    # ========================================================

    async def dealer_play(self):

        while hand_value(
            self.dealer
        ) < DEALER_STAND_VALUE:

            await asyncio.sleep(
                0.35
            )

            if not self.deck:
                break

            self.dealer.append(
                self.deck.pop()
            )

    # ========================================================
    # RESULTADOS
    # ========================================================

    def calculate_results(self):

        if self.game_stats_recorded:
            return

        self.game_stats_recorded = True

        user = self.get_user()

        if user is None:
            return

        user["stats"]["games_played"] += 1

        dealer_value = hand_value(
            self.dealer
        )

        dealer_blackjack = is_blackjack(
            self.dealer
        )

        dealer_bust = dealer_value > 21

        for hand in self.hands:

            player_value = hand_value(
                hand["cards"]
            )

            player_blackjack = (
                is_blackjack(
                    hand["cards"]
                )
                and not hand["split"]
            )

            # ------------------------------------------------
            # BUST
            # ------------------------------------------------

            if player_value > 21:

                hand["result"] = "loss"

                user["stats"]["games_lost"] += 1

                continue

            # ------------------------------------------------
            # BLACKJACK NATURAL
            # ------------------------------------------------

            if player_blackjack:

                if dealer_blackjack:

                    hand["result"] = "push"

                    self.add_money(
                        hand["bet"]
                    )

                else:

                    payout = int(
                        hand["bet"]
                        * BLACKJACK_MULTIPLIER
                    )

                    self.add_money(
                        payout
                    )

                    hand["result"] = "blackjack"

                    user["stats"]["games_won"] += 1

                continue

            # ------------------------------------------------
            # DEALER BLACKJACK
            # ------------------------------------------------

            if dealer_blackjack:

                hand["result"] = "loss"

                user["stats"]["games_lost"] += 1

                continue

            # ------------------------------------------------
            # DEALER BUST
            # ------------------------------------------------

            if dealer_bust:

                payout = (
                    hand["bet"]
                    * NORMAL_WIN_MULTIPLIER
                )

                self.add_money(
                    payout
                )

                hand["result"] = "win"

                user["stats"]["games_won"] += 1

                continue

            # ------------------------------------------------
            # PLAYER GANA
            # ------------------------------------------------

            if player_value > dealer_value:

                payout = (
                    hand["bet"]
                    * NORMAL_WIN_MULTIPLIER
                )

                self.add_money(
                    payout
                )

                hand["result"] = "win"

                user["stats"]["games_won"] += 1

            # ------------------------------------------------
            # EMPATE
            # ------------------------------------------------

            elif player_value == dealer_value:

                self.add_money(
                    hand["bet"]
                )

                hand["result"] = "push"

            # ------------------------------------------------
            # DEALER GANA
            # ------------------------------------------------

            else:

                hand["result"] = "loss"

                user["stats"]["games_lost"] += 1

    # ========================================================
    # EMBED PARTIDA
    # ========================================================

    def build_game_embed(self):

        hand = self.current_hand()

        player_cards = cards_text(
            hand["cards"]
        )

        player_value = hand_value(
            hand["cards"]
        )

        dealer_visible = card_text(
            self.dealer[0]
        )

        description = (
            f"### 👤 {self.interaction.user.display_name}\n"
            f"{player_cards}\n"
            f"**Valor:** `{player_value}`\n\n"
            f"### 🤵 Dealer\n"
            f"{dealer_visible} 🂠\n"
            f"**Valor:** `?`\n\n"
            f"💰 **Apuesta:** "
            f"`{format_money(hand['bet'])}`"
        )

        if len(self.hands) > 1:

            description += (
                f"\n\n🔀 **Mano "
                f"{self.current_hand_index + 1}"
                f" de {len(self.hands)}**"
            )

        embed = discord.Embed(
            title="🃏 Blackjack",
            description=description,
            color=PURPLE
        )

        embed.set_thumbnail(
            url=self.interaction.user.display_avatar.url
        )

        embed.set_footer(
            text="Pedir una carta, plantarte, doblar o separar."
        )

        return embed

    # ========================================================
    # EMBED FINAL
    # ========================================================

    def build_result_embed(self):

        dealer_cards = cards_text(
            self.dealer
        )

        dealer_value = hand_value(
            self.dealer
        )

        description = (
            "### 🤵 Dealer\n"
            f"{dealer_cards}\n"
            f"**Valor:** `{dealer_value}`\n\n"
        )

        for index, hand in enumerate(
            self.hands,
            start=1
        ):

            cards = cards_text(
                hand["cards"]
            )

            value = hand_value(
                hand["cards"]
            )

            result = hand.get(
                "result",
                "loss"
            )

            if result == "blackjack":

                result_text = (
                    "🃏 **BLACKJACK — 3:2**"
                )

            elif result == "win":

                result_text = (
                    "🎉 **GANASTE**"
                )

            elif result == "push":

                result_text = (
                    "🤝 **EMPATE**"
                )

            else:

                if value > 21:

                    result_text = (
                        "💥 **BUST — PERDISTE**"
                    )

                else:

                    result_text = (
                        "💀 **PERDISTE**"
                    )

            if len(self.hands) > 1:

                description += (
                    f"### 👤 Mano {index}\n"
                    f"{cards}\n"
                    f"**Valor:** `{value}`\n"
                    f"{result_text}\n"
                    f"💰 Apuesta: "
                    f"`{format_money(hand['bet'])}`\n\n"
                )

            else:

                description += (
                    f"### 👤 Vos\n"
                    f"{cards}\n"
                    f"**Valor:** `{value}`\n"
                    f"{result_text}\n\n"
                    f"💰 Apuesta: "
                    f"`{format_money(hand['bet'])}`"
                )

        user = self.get_user()

        balance = (
            user["cash"]
            if user is not None
            else 0
        )

        description += (
            f"\n💵 **Balance:** "
            f"`{format_money(balance)}`"
        )

        embed = discord.Embed(
            title="🃏 Blackjack",
            description=description,
            color=PURPLE
        )

        embed.set_thumbnail(
            url=self.interaction.user.display_avatar.url
        )

        embed.set_footer(
            text="Gracias por jugar."
        )

        return embed


# ============================================================
# VIEW
# ============================================================

class BlackjackView(discord.ui.View):

    def __init__(
        self,
        game,
        timeout=GAME_TIMEOUT
    ):

        super().__init__(
            timeout=timeout
        )

        self.game = game

        self.refresh_buttons()

    # ========================================================
    # BOTONES
    # ========================================================

    def refresh_buttons(self):

        self.clear_items()

        # ----------------------------------------------------
        # PEDIR
        # ----------------------------------------------------

        hit = discord.ui.Button(
            label="Pedir",
            emoji="🃏",
            style=discord.ButtonStyle.primary,
            custom_id="blackjack_hit"
        )

        hit.callback = self.hit_callback

        self.add_item(hit)

        # ----------------------------------------------------
        # PLANTARSE
        # ----------------------------------------------------

        stand = discord.ui.Button(
            label="Plantarse",
            emoji="✋",
            style=discord.ButtonStyle.secondary,
            custom_id="blackjack_stand"
        )

        stand.callback = self.stand_callback

        self.add_item(stand)

        # ----------------------------------------------------
        # DOBLAR
        # ----------------------------------------------------

        if self.game.can_double():

            double = discord.ui.Button(
                label="Doblar",
                emoji="💰",
                style=discord.ButtonStyle.success,
                custom_id="blackjack_double"
            )

            double.callback = self.double_callback

            self.add_item(double)

        # ----------------------------------------------------
        # SEPARAR
        # ----------------------------------------------------

        if self.game.can_split():

            split = discord.ui.Button(
                label="Separar",
                emoji="🔀",
                style=discord.ButtonStyle.danger,
                custom_id="blackjack_split"
            )

            split.callback = self.split_callback

            self.add_item(split)

    # ========================================================
    # SEGURIDAD
    # ========================================================

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != self.game.user_id:

            await interaction.response.send_message(
                "❌ Esta partida no es tuya.",
                ephemeral=True
            )

            return False

        return True

    # ========================================================
    # PEDIR
    # ========================================================

    async def hit_callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer()

        self.game.hit()

        # ----------------------------------------------------
        # BUST
        # ----------------------------------------------------

        if self.game.current_bust():

            self.game.finish_current_hand()

            # Si quedan más manos
            if self.game.next_hand():

                self.refresh_buttons()

                await interaction.edit_original_response(
                    embed=self.game.build_game_embed(),
                    view=self
                )

                return

            # No quedan manos
            self.stop()

            await self.game.finish_round()

            await interaction.edit_original_response(
                embed=self.game.build_result_embed(),
                view=None
            )

            return

        # ----------------------------------------------------
        # 21
        # ----------------------------------------------------

        if self.game.current_value() == 21:

            self.game.finish_current_hand()

            if self.game.next_hand():

                self.refresh_buttons()

                await interaction.edit_original_response(
                    embed=self.game.build_game_embed(),
                    view=self
                )

                return

            self.stop()

            await self.game.finish_round()

            await interaction.edit_original_response(
                embed=self.game.build_result_embed(),
                view=None
            )

            return

        # ----------------------------------------------------
        # CONTINUAR
        # ----------------------------------------------------

        self.refresh_buttons()

        await interaction.edit_original_response(
            embed=self.game.build_game_embed(),
            view=self
        )

    # ========================================================
    # PLANTARSE
    # ========================================================

    async def stand_callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer()

        self.game.finish_current_hand()

        # ----------------------------------------------------
        # SIGUIENTE MANO
        # ----------------------------------------------------

        if self.game.next_hand():

            self.refresh_buttons()

            await interaction.edit_original_response(
                embed=self.game.build_game_embed(),
                view=self
            )

            return

        # ----------------------------------------------------
        # FINAL
        # ----------------------------------------------------

        self.stop()

        await self.game.finish_round()

        await interaction.edit_original_response(
            embed=self.game.build_result_embed(),
            view=None
        )

    # ========================================================
    # DOBLAR
    # ========================================================

    async def double_callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer()

        if not self.game.can_double():

            await interaction.followup.send(
                "❌ Ya no podés doblar esta mano.",
                ephemeral=True
            )

            return

        if not self.game.double_bet():

            await interaction.followup.send(
                "❌ No tenés suficiente dinero para doblar.",
                ephemeral=True
            )

            return

        self.game.hit()

        self.game.finish_current_hand()

        # ----------------------------------------------------
        # BUST
        # ----------------------------------------------------

        if self.game.current_bust():

            if self.game.next_hand():

                self.refresh_buttons()

                await interaction.edit_original_response(
                    embed=self.game.build_game_embed(),
                    view=self
                )

                return

            self.stop()

            await self.game.finish_round()

            await interaction.edit_original_response(
                embed=self.game.build_result_embed(),
                view=None
            )

            return

        # ----------------------------------------------------
        # SIGUIENTE MANO
        # ----------------------------------------------------

        if self.game.next_hand():

            self.refresh_buttons()

            await interaction.edit_original_response(
                embed=self.game.build_game_embed(),
                view=self
            )

            return

        # ----------------------------------------------------
        # FINAL
        # ----------------------------------------------------

        self.stop()

        await self.game.finish_round()

        await interaction.edit_original_response(
            embed=self.game.build_result_embed(),
            view=None
        )

    # ========================================================
    # SEPARAR
    # ========================================================

    async def split_callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer()

        if not self.game.can_split():

            await interaction.followup.send(
                "❌ No podés separar estas cartas.",
                ephemeral=True
            )

            return

        if not self.game.split_hand():

            await interaction.followup.send(
                "❌ No tenés suficiente dinero para separar.",
                ephemeral=True
            )

            return

        self.refresh_buttons()

        await interaction.edit_original_response(
            embed=self.game.build_game_embed(),
            view=self
        )

    # ========================================================
    # TIMEOUT
    # ========================================================

    async def on_timeout(self):

        if self.game.finished:
            return

        self.game.finished = True

        # ----------------------------------------------------
        # DEVOLVER TODAS LAS APUESTAS
        # ----------------------------------------------------

        total_refund = 0

        for hand in self.game.hands:

            if not hand["finished"]:

                total_refund += hand["bet"]

        economy = self.game.economy()

        if economy is not None:

            user = economy.get_user_data(
                self.game.guild_id,
                self.game.user_id
            )

            user["cash"] += total_refund

            self.game.save()

        # ----------------------------------------------------
        # MENSAJE
        # ----------------------------------------------------

        try:

            embed = discord.Embed(
                title="🃏 Blackjack",
                description=(
                    "⏰ **La partida expiró.**\n\n"
                    "No hubo ninguna interacción durante "
                    f"**{GAME_TIMEOUT} segundos**.\n\n"
                    f"💰 Apuestas devueltas: "
                    f"**{format_money(total_refund)}**"
                ),
                color=PURPLE
            )

            embed.set_thumbnail(
                url=self.game.interaction.user.display_avatar.url
            )

            await self.game.interaction.edit_original_response(
                embed=embed,
                view=None
            )

        except discord.HTTPException:

            pass


# ============================================================
# COG
# ============================================================

class Blackjack(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        # Una partida por usuario y servidor
        self.active_games = {}

        # Evita dos partidas simultáneas
        self.locks = {}

        print(
            "✅ Cog de Blackjack cargado correctamente."
        )

    # ========================================================
    # LOCK
    # ========================================================

    def get_lock(
        self,
        guild_id,
        user_id
    ):

        key = (
            guild_id,
            user_id
        )

        if key not in self.locks:

            self.locks[key] = asyncio.Lock()

        return self.locks[key]

    # ========================================================
    # COMANDO
    # ========================================================

    @app_commands.command(
        name="blackjack",
        description="Juega una partida de Blackjack."
    )
    @app_commands.describe(
        apuesta="Cantidad de dinero que querés apostar."
    )
    async def blackjack(
        self,
        interaction: discord.Interaction,
        apuesta: int
    ):

        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------

        if interaction.guild is None:

            return await interaction.response.send_message(
                "❌ Este comando solo funciona dentro de un servidor.",
                ephemeral=True
            )

        guild_id = interaction.guild.id

        user_id = interaction.user.id

        key = (
            guild_id,
            user_id
        )

        # ----------------------------------------------------
        # APUESTA
        # ----------------------------------------------------

        if apuesta <= 0:

            return await interaction.response.send_message(
                "❌ La apuesta debe ser mayor que **$0**.",
                ephemeral=True
            )

        if apuesta > MAX_BET:

            return await interaction.response.send_message(
                f"❌ La apuesta máxima es "
                f"**{format_money(MAX_BET)}**.",
                ephemeral=True
            )

        # ----------------------------------------------------
        # ECONOMÍA
        # ----------------------------------------------------

        economy = self.bot.get_cog(
            "Economia"
        )

        if economy is None:

            return await interaction.response.send_message(
                "❌ El sistema de economía no está cargado.",
                ephemeral=True
            )

        user = economy.get_user_data(
            guild_id,
            user_id
        )

        if apuesta > user["cash"]:

            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )

        # ----------------------------------------------------
        # PARTIDA ACTIVA
        # ----------------------------------------------------

        if key in self.active_games:

            return await interaction.response.send_message(
                "❌ Ya tenés una partida de Blackjack activa.",
                ephemeral=True
            )

        # ----------------------------------------------------
        # LOCK
        # ----------------------------------------------------

        lock = self.get_lock(
            guild_id,
            user_id
        )

        if lock.locked():

            return await interaction.response.send_message(
                "⏳ Ya estás iniciando otra partida.",
                ephemeral=True
            )

        async with lock:

            if key in self.active_games:

                return await interaction.response.send_message(
                    "❌ Ya tenés una partida activa.",
                    ephemeral=True
                )

            # ------------------------------------------------
            # COBRAR APUESTA
            # ------------------------------------------------

            user["cash"] -= apuesta

            user["stats"]["money_spent"] += apuesta

            economy.save_data(
                economy.data
            ) if hasattr(
                economy,
                "save_data"
            ) else None

            # ------------------------------------------------
            # CREAR PARTIDA
            # ------------------------------------------------

            game = BlackjackGame(
                self,
                interaction,
                apuesta
            )

            self.active_games[key] = game

            # ------------------------------------------------
            # BLACKJACK NATURAL
            # ------------------------------------------------

            player_blackjack = is_blackjack(
                game.current_cards()
            )

            dealer_blackjack = is_blackjack(
                game.dealer
            )

            if (
                player_blackjack
                or dealer_blackjack
            ):

                game.finished = True

                game.calculate_results()

                game.save()

                self.active_games.pop(
                    key,
                    None
                )

                return await interaction.response.send_message(
                    embed=game.build_result_embed()
                )

            # ------------------------------------------------
            # PARTIDA
            # ------------------------------------------------

            view = BlackjackView(
                game
            )

            await interaction.response.send_message(
                embed=game.build_game_embed(),
                view=view
            )

        # ----------------------------------------------------
        # ESPERAR TIMEOUT
        # ----------------------------------------------------

        await view.wait()

        self.active_games.pop(
            key,
            None
        )


# ============================================================
# SETUP
# ============================================================

async def setup(bot):

    await bot.add_cog(
        Blackjack(bot)
    )