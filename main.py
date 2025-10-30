import os
import random
import tempfile
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# -------------------------
# Configuration
# -------------------------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = "@XSENSE_I"
OWNER_HANDLE = "@PyL1nx"
SIGNATURE = "🔹 Bot by @PyL1nx | Powered by Sensei 💖"

INLINE_CHAT_THRESHOLD = 500
MAX_SAFE_GENERATE = 200000
AUTOTRIM_LENGTH = 3800

GENERATED_PANS_FILE = "generated_pans.txt"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# -------------------------
# Persistence helpers
# -------------------------
def load_generated_pans():
    pans = set()
    if os.path.exists(GENERATED_PANS_FILE):
        try:
            with open(GENERATED_PANS_FILE, "r") as fh:
                for line in fh:
                    p = line.strip()
                    if p:
                        pans.add(p)
        except Exception:
            return set()
    return pans

def append_generated_pans(new_pans):
    try:
        with open(GENERATED_PANS_FILE, "a") as fh:
            for pan in new_pans:
                fh.write(str(pan) + "\n")
    except Exception:
        pass

GENERATED_PANS = load_generated_pans()

# -------------------------
# Utility Functions
# -------------------------
def random_digits_string(length):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def calc_luhn_check_digit(partial):
    digits = [int(d) for d in partial]
    digits.append(0)
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
        if d > 9:
            d -= 9
        checksum += d
    return str((10 - checksum % 10) % 10)

def generate_luhn_pan_from_prefix(prefix, total_length=16, max_attempts=2000):
    prefix = ''.join(ch for ch in str(prefix) if ch.isdigit())
    if not prefix:
        prefix = str(random.choice([3, 4, 5]))
    if len(prefix) >= total_length:
        prefix = prefix[: total_length - 1]

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        base = prefix
        while len(base) < total_length - 1:
            base += str(random.randint(0, 9))
        check = calc_luhn_check_digit(base)
        pan = base + check
        if pan not in GENERATED_PANS:
            GENERATED_PANS.add(pan)
            append_generated_pans([pan])
            return pan
    raise RuntimeError("Could not generate a unique PAN after many attempts. Reduce count or clear history.")

def generate_unique_luhn_pan_any(total_length=16, max_attempts=2000):
    return generate_luhn_pan_from_prefix(str(random.choice([3, 4, 5])), total_length, max_attempts=max_attempts)

def generate_luhn_card_from_bin(bin_prefix, total_length=16):
    return generate_luhn_pan_from_prefix(bin_prefix, total_length)

def random_card_pan(prefix=None, total_length=16):
    if prefix:
        pan = str(prefix)
    else:
        pan = str(random.choice([4, 5, 3]))
    while len(pan) < total_length:
        pan += str(random.randint(0, 9))
    return pan

def generate_to_file(count, prefix=None, total_length=16, luhn=True):
    fd, path = tempfile.mkstemp(prefix="dump_", suffix=".txt")
    os.close(fd)
    generated = []
    with open(path, "w") as f:
        for _ in range(count):
            pan = generate_luhn_pan_from_prefix(prefix if prefix else str(random.choice([4, 5, 3])), total_length)
            month = str(random.randint(1, 12)).zfill(2)
            year = str(random.randint(2025, 2035))
            cvv_len = 4 if total_length == 15 else 3
            cvv = str(random.randint(0, (10 ** cvv_len) - 1)).zfill(cvv_len)
            line = f"{pan}|{month}|{year}|{cvv}\n"
            f.write(line)
            generated.append(pan)
    return path

# -------------------------
# UI & Texts (HTML-safe)
# -------------------------
def join_channel_markup():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
        InlineKeyboardButton("💳 Generate Cards", callback_data="show_gen"),
        InlineKeyboardButton("📄 About", callback_data="about"),
    )
    return markup

WELCOME_TEXT = (
    "💎 <b>Welcome to Sensei Premium CC Generator Bot 💳</b>\n\n"
    "This bot generates <b>Luhn-valid</b> dummy cards for testing & study purposes only.\n\n"
    "🔥 <b>Features:</b>\n"
    "• Full-card generation (Luhn applied and uniqueness enforced)\n"
    "• BIN-based full cards (Luhn applied)\n"
    "• Random 6-digit dummy BINs (no PAN when using /randbin)\n"
    "• Amex (15-digit) supported\n\n"
    "📖 <b>Example:</b>\n"
    "/gen 10             - generate 10 Luhn-valid full cards\n"
    "/gen 10 4539        - generate 10 Luhn-valid cards starting with 4539\n"
    "/genbin 100 453968  - generate 100 cards starting with BIN 453968 (Luhn applied)\n"
    "/randbin 500 45     - 500 dummy 6-digit BINs starting with 45\n\n"
    f"{SIGNATURE}"
)

HELP_TEXT = (
    "🧠 <b>Commands Guide:</b>\n\n"
    "/gen &lt;count&gt; [prefix]       - Generate full Luhn-valid cards (prefix optional)\n"
    "/genbin &lt;count&gt; &lt;bin&gt;   - Generate full Luhn-valid cards from BIN (6+ digits)\n"
    "/randbin &lt;count&gt; [prefix]    - Generate dummy 6-digit BINs (prefix optional)\n"
    "/about - About the bot\n\n"
    "⚙️ Large outputs are sent as .txt file. All generated PANs are stored to avoid repeats."
)

ABOUT_TEXT = (
    f"👑 <b>Owner:</b> {OWNER_HANDLE}\n"
    f"💬 <b>Channel:</b> {CHANNEL_USERNAME}\n\n"
    f"{SIGNATURE}"
)

# -------------------------
# Command Handlers
# -------------------------

@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=join_channel_markup())

@bot.message_handler(commands=["about"])
def about(message):
    bot.reply_to(message, ABOUT_TEXT)

@bot.message_handler(commands=["gen"])
def gen_cmd(message):
    parts = message.text.split()
    try:
        count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
    except Exception:
        return bot.reply_to(message, "Usage: /gen <count> [prefix]")
    prefix = None
    if len(parts) > 2:
        for p in parts[2:]:
            if p and any(ch.isdigit() for ch in p):
                prefix = p
                break
    total_length = 15 if prefix and (str(prefix).startswith("34") or str(prefix).startswith("37")) else 16
    if count > MAX_SAFE_GENERATE:
        return bot.reply_to(message, "⚠️ Max limit exceeded.")
    if count <= INLINE_CHAT_THRESHOLD:
        lines = []
        try:
            for _ in range(count):
                pan = generate_luhn_pan_from_prefix(prefix if prefix else str(random.choice([4, 5, 3])), total_length)
                month = str(random.randint(1, 12)).zfill(2)
                year = str(random.randint(2025, 2035))
                cvv_len = 4 if total_length == 15 else 3
                cvv = str(random.randint(0, (10 ** cvv_len) - 1)).zfill(cvv_len)
                lines.append(f"{pan}|{month}|{year}|{cvv}")
        except RuntimeError as e:
            return bot.reply_to(message, f"⚠️ Error generating unique cards: {e}")
        text = "\n".join(lines)
        if len(text) > AUTOTRIM_LENGTH:
            text = text[:AUTOTRIM_LENGTH] + "\n...output trimmed..."
        bot.reply_to(message, f"<code>{text}</code>")
    else:
        try:
            path = generate_to_file(count, prefix, total_length, luhn=True)
        except RuntimeError as e:
            return bot.reply_to(message, f"⚠️ Error generating unique cards: {e}")
        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"Here are {count} generated Luhn-valid cards.\n{SIGNATURE}")
        os.remove(path)

@bot.message_handler(commands=["genbin"])
def genbin_cmd(message):
    parts = message.text.split()
    if len(parts) < 3:
        return bot.reply_to(message, "Usage: /genbin <count> <bin>")
    try:
        count = int(parts[1])
    except ValueError:
        return bot.reply_to(message, "Usage: /genbin <count> <bin>")
    bin_prefix = parts[2]
    total_length = 15 if str(bin_prefix).startswith(("34", "37")) else 16
    if count > MAX_SAFE_GENERATE:
        return bot.reply_to(message, "⚠️ Max limit exceeded.")
    if count <= INLINE_CHAT_THRESHOLD:
        cards = []
        try:
            for _ in range(count):
                pan = generate_luhn_pan_from_prefix(bin_prefix, total_length)
                month = str(random.randint(1, 12)).zfill(2)
                year = str(random.randint(2025, 2035))
                cvv_len = 4 if total_length == 15 else 3
                cvv = str(random.randint(0, (10 ** cvv_len) - 1)).zfill(cvv_len)
                cards.append(f"{pan}|{month}|{year}|{cvv}")
        except RuntimeError as e:
            return bot.reply_to(message, f"⚠️ Error generating unique cards: {e}")
        bot.reply_to(message, f"<code>{'\n'.join(cards[:500])}</code>")
    else:
        try:
            path = generate_to_file(count, bin_prefix, total_length, luhn=True)
        except RuntimeError as e:
            return bot.reply_to(message, f"⚠️ Error generating unique cards: {e}")
        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"BIN {bin_prefix} Luhn-valid dump ({count}).\n{SIGNATURE}")
        os.remove(path)

@bot.message_handler(commands=["randbin"])
def randbin_cmd(message):
    parts = message.text.split()
    try:
        count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
    except Exception:
        return bot.reply_to(message, "Usage: /randbin <count> [prefix]")
    prefix = parts[2] if len(parts) > 2 else None

    def make_random_bin(pref=None):
        if pref:
            base = str(pref)
        else:
            base = str(random.choice([3, 4, 5]))
        while len(base) < 6:
            base += str(random.randint(0, 9))
        return base

    bins = [make_random_bin(prefix) for _ in range(count)]
    result = "\n".join(bins[:500])
    if count <= INLINE_CHAT_THRESHOLD:
        bot.reply_to(message, f"<code>{result}</code>")
    else:
        fd, path = tempfile.mkstemp(prefix="bins_", suffix=".txt")
        os.close(fd)
        with open(path, "w") as f:
            f.write(result)
        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f, caption=f"Here are {count} dummy BINs.\n{SIGNATURE}")
        os.remove(path)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "show_gen":
        bot.send_message(call.message.chat.id, HELP_TEXT)
    elif call.data == "about":
        bot.send_message(call.message.chat.id, ABOUT_TEXT)

print("🤖 Bot is running...")
bot.infinity_polling()
