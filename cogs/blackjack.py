import random
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
# ============================================================
# CONFIG
# ============================================================
PURPLE = discord.Color.from_rgb(115, 55, 210)
MAX_BET = 100000
# Tiempo máximo de una partida sin interacción
GAME_TIMEOUT = 180
# Blackjack natural = 3:2
BLACKJACK_MULTIPLIER = 2.5
# Victoria normal = 1:1
NORMAL_WIN_MULTIPLIER = 2
# ============================================================
# CARTAS
# ============================================================
SUITS = {
    "♠": "♠",
    "♥": "♥",
    "♦": "♦",
    "♣": "♣"
}
RANKS = [
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
]
# ============================================================
# UTILIDADES
# ============================================================
def create_deck():
    """
    Crea un mazo estándar de 52 cartas.
    """
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append((rank, suit))
    random.shuffle(deck)
    return deck
def card_value(card):
    """
    Valor básico de una carta.
    """
    rank = card[0]
    if rank in ("J", "Q", "K"):
        return 10
    if rank == "A":
        return 11
    return int(rank)
def hand_value(hand):
    """
    Calcula el valor de una mano teniendo
    en cuenta correctamente los Ases.
    """
    total = 0
    aces = 0
    for card in hand:
        rank = card[0]
        total += card_value(card)
        if rank == "A":
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
    """
    Ejemplo:
    🂡
    """
    rank, suit = card
    # Cartas visuales Unicode
    unicode_cards = {
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
    return unicode_cards.get(
        (rank, suit),
        f"`{rank}{suit}`"
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
# BLACKJACK VIEW
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
        # PEDIR
        hit = discord.ui.Button(
            label="Pedir",
            emoji="🃏",
            style=discord.ButtonStyle.primary,
            custom_id="blackjack_hit"
        )
        hit.callback = self.hit_callback
        self.add_item(hit)
        # PLANTARSE
        stand = discord.ui.Button(
            label="Plantarse",
            emoji="✋",
            style=discord.ButtonStyle.secondary,
            custom_id="blackjack_stand"
        )
        stand.callback = self.stand_callback
        self.add_item(stand)
        # DOBLAR
        if self.game.can_double():
            double = discord.ui.Button(
                label="Doblar",
                emoji="💰",
                style=discord.ButtonStyle.success,
                custom_id="blackjack_double"
            )
            double.callback = self.double_callback
            self.add_item(double)
        # SEPARAR
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
        if self.game.current_bust():
            self.stop()
            self.game.finish_loss(
                reason="bust"
            )
            await interaction.edit_original_response(
                embed=self.game.build_result_embed(),
                view=None
            )
            return
        # Si llegó a 21, plantarse automáticamente
        if self.game.current_value() == 21:
            self.stop()
            await self.game.finish_round()
            await interaction.edit_original_response(
                embed=self.game.build_result_embed(),
                view=None
            )
            return
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
        self.stop()
        if self.game.current_bust():
            self.game.finish_loss(
                reason="bust"
            )
        else:
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
                "❌ No podés separar esta mano.",
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
        # Si estamos jugando la segunda mano,
        # el sistema continúa normalmente.
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
        self.doubled = False
        # Mano inicial
        hand = [
            self.deck.pop(),
            self.deck.pop()
        ]
        self.hands.append({
            "cards": hand,
            "bet": bet,
            "finished": False,
            "bust": False,
            "blackjack": False
        })
        # Dealer
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
        economy = self.cog.bot.get_cog(
            "Economia"
        )
        return economy
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
        if economy is not None:
            economy.save_data(
                economy.data
            )
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
        return self.current_hand()["cards"]
    def current_value(self):
        return hand_value(
            self.current_cards()
        )
    def current_bust(self):
        return is_bust(
            self.current_cards()
        )
    # ========================================================
    # HIT
    # ========================================================
    def hit(self):
        self.current_hand()["cards"].append(
            self.deck.pop()
        )
    # ========================================================
    # DOUBLE
    # ========================================================
    def can_double(self):
        hand = self.current_hand()
        return (
            len(hand["cards"]) == 2
            and not hand["finished"]
            and not self.doubled
            and not self.split_used
        )
    def double_bet(self):
        hand = self.current_hand()
        amount = hand["bet"]
        if not self.remove_money(amount):
            return False
        hand["bet"] *= 2
        self.doubled = True
        return True
    # ========================================================
    # SPLIT
    # ========================================================
    def can_split(self):
        if self.split_used:
            return False
        hand = self.current_hand()
        cards = hand["cards"]
        if len(cards) != 2:
            return False
        if cards[0][0] != cards[1][0]:
            return False
        user = self.get_user()
        if user is None:
            return False
        return user["cash"] >= hand["bet"]
    def split_hand(self):
        if not self.can_split():
            return False
        original = self.current_hand()
        if not self.remove_money(
            original["bet"]
        ):
            return False
        card_one = original["cards"][0]
        card_two = original["cards"][1]
        original["cards"] = [
            card_one,
            self.deck.pop()
        ]
        second = {
            "cards": [
                card_two,
                self.deck.pop()
            ],
            "bet": original["bet"],
            "finished": False,
            "bust": False,
            "blackjack": False
        }
        self.hands.append(
            second
        )
        self.split_used = True
        self.current_hand_index = 0
        return True
    # ========================================================
    # TERMINAR MANO
    # ========================================================
    def finish_current_hand(self):
        self.current_hand()["finished"] = True
    def next_hand(self):
        self.current_hand()["finished"] = True
        for index, hand in enumerate(
            self.hands
        ):
            if not hand["finished"]:
                self.current_hand_index = index
                self.doubled = False
                return True
        return False
    # ========================================================
    # RESULTADO
    # ========================================================
    async def finish_round(self):
        # Si todavía quedan manos
        if self.next_hand():
            return
        # Dealer juega
        await self.dealer_play()
        self.finished = True
        self.calculate_results()
        self.save()
    def finish_loss(
        self,
        reason=None
    ):
        for hand in self.hands:
            hand["finished"] = True
            if is_bust(
                hand["cards"]
            ):
                hand["bust"] = True
        self.finished = True
        user = self.get_user()
        if user is not None:
            user["stats"]["games_played"] += 1
            user["stats"]["games_lost"] += 1
        self.save()
    # ========================================================
    # DEALER
    # ========================================================
    async def dealer_play(self):
        # Dealer roba hasta 17
        while hand_value(
            self.dealer
        ) < 17:
            await asyncio.sleep(
                0.35
            )
            self.dealer.append(
                self.deck.pop()
            )
    # ========================================================
    # CALCULAR RESULTADOS
    # ========================================================
    def calculate_results(self):
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
                and not self.split_used
            )
            # BUST
            if player_value > 21:
                hand["result"] = "loss"
                user["stats"]["games_lost"] += 1
                continue
            # BLACKJACK
            if player_blackjack:
                if dealer_blackjack:
                    hand["result"] = "push"
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
            # Dealer blackjack
            if dealer_blackjack:
                hand["result"] = "loss"
                user["stats"]["games_lost"] += 1
                continue
            # Dealer bust
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
            # Player mayor
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
            # Empate
            elif player_value == dealer_value:
                self.add_money(
                    hand["bet"]
                )
                hand["result"] = "push"
            # Dealer gana
            else:
                hand["result"] = "loss"
                user["stats"]["games_lost"] += 1
    # ========================================================
    # EMBED DURANTE PARTIDA
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
        dealer_hidden = "🂠"
        embed = discord.Embed(
            title="🃏 Blackjack",
            description=(
                f"### 👤 {self.interaction.user.display_name}\n"
                f"{player_cards}\n"
                f"**Valor:** `{player_value}`\n\n"
                f"### 🤵 Dealer\n"
                f"{dealer_visible} {dealer_hidden}\n"
                f"**Valor:** `?`\n\n"
                f"💰 **Apuesta:** "
                f"`{format_money(hand['bet'])}`"
            ),
            color=PURPLE
        )
        if len(self.hands) > 1:
            embed.add_field(
                name="🔀 Manos",
                value=(
                    f"Mano **{self.current_hand_index + 1}** "
                    f"de **{len(self.hands)}**"
                ),
                inline=False
            )
        embed.set_footer(
            text="Pedir una carta o plantarte cuando quieras."
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
            f"### 🤵 Dealer\n"
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
                    "🃏 **BLACKJACK — Ganaste 3:2**"
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
                    f"{result_text}\n\n"
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
            f"\n\n💵 **Balance:** "
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
# COG
# ============================================================
class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Una partida por usuario
        self.active_games = {}
        # Lock para evitar apuestas simultáneas
        self.locks = {}
        print(
            "✅ Cog de Blackjack cargado correctamente."
        )
    # ========================================================
    # LOCK
    # ========================================================
    def get_lock(
        self,
        user_id
    ):
        if user_id not in self.locks:
            self.locks[user_id] = asyncio.Lock()
        return self.locks[user_id]
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
        if interaction.guild is None:
            return await interaction.response.send_message(
                "❌ Este comando solo funciona dentro de un servidor.",
                ephemeral=True
            )
        user_id = interaction.user.id
        # ====================================================
        # VALIDACIONES
        # ====================================================
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
        if user_id in self.active_games:
            return await interaction.response.send_message(
                "❌ Ya tenés una partida de Blackjack activa.",
                ephemeral=True
            )
        # ====================================================
        # ECONOMÍA
        # ====================================================
        economy = self.bot.get_cog(
            "Economia"
        )
        if economy is None:
            return await interaction.response.send_message(
                "❌ El sistema de economía no está cargado.",
                ephemeral=True
            )
        user = economy.get_user_data(
            interaction.guild.id,
            user_id
        )
        if apuesta > user["cash"]:
            return await interaction.response.send_message(
                "❌ No tenés suficiente dinero.",
                ephemeral=True
            )
        # ====================================================
        # LOCK
        # ====================================================
        lock = self.get_lock(
            user_id
        )
        if lock.locked():
            return await interaction.response.send_message(
                "⏳ Ya estás iniciando otra partida.",
                ephemeral=True
            )
        async with lock:
            if user_id in self.active_games:
                return await interaction.response.send_message(
                    "❌ Ya tenés una partida activa.",
                    ephemeral=True
                )
            # Sacar apuesta inmediatamente
            user["cash"] -= apuesta
            user["stats"]["money_spent"] += apuesta
            economy.save_data(
                economy.data
            )
            # =================================================
            # CREAR PARTIDA
            # =================================================
            game = BlackjackGame(
                self,
                interaction,
                apuesta
            )
            self.active_games[
                user_id
            ] = game
            # =================================================
            # BLACKJACK INICIAL
            # =================================================
            player_blackjack = is_blackjack(
                game.current_cards()
            )
            dealer_blackjack = is_blackjack(
                game.dealer
            )
            if player_blackjack or dealer_blackjack:
                game.finished = True
                game.calculate_results()
                economy.save_data(
                    economy.data
                )
                self.active_games.pop(
                    user_id,
                    None
                )
                return await interaction.response.send_message(
                    embed=game.build_result_embed()
                )
            # =================================================
            # PARTIDA NORMAL
            # =================================================
            view = BlackjackView(
                game
            )
            await interaction.response.send_message(
                embed=game.build_game_embed(),
                view=view
            )
            # Esperar hasta timeout
            await view.wait()
            # Si expiró
            if not game.finished:
                game.finished = True
                # Devolver la apuesta
                # para evitar que quede dinero bloqueado
                economy_user = economy.get_user_data(
                    interaction.guild.id,
                    user_id
                )
                economy_user["cash"] += (
                    game.current_hand()["bet"]
                )
                economy.save_data(
                    economy.data
                )
                try:
                    await interaction.edit_original_response(
                        embed=discord.Embed(
                            title="🃏 Blackjack",
                            description=(
                                "⏰ **La partida expiró.**\n\n"
                                "Tu apuesta fue devuelta porque "
                                "no hubo ninguna interacción durante "
                                f"**{GAME_TIMEOUT} segundos**.\n\n"
                                f"💰 Devuelto: "
                                f"**{format_money(game.current_hand()['bet'])}**"
                            ),
                            color=PURPLE
                        ),
                        view=None
                    )
                except discord.HTTPException:
                    pass
            self.active_games.pop(
                user_id,
                None
            )
# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(
        Blackjack(bot)
    )