import asyncio
import logging
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import escape
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)
TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {9216132946}
DB_PATH = Path("data/p2p_capital.db")
REVIEWS_URL = "https://t.me/"
SUPPORT_USERNAME = "Dimonch1x"
MENU_IMAGE = Path(__file__).parent / "assets" / "menu_banner.png"
PREMIUM_EMOJI_IDS = {
    "⭐": "5438496463044752972",
    "💎": "5427168083074628963",
    "💱": "5402186569006210455",
    "📊": "5231200819986047254",
    "🎧": "5251203410396458957",
    "🔐": "5296369303661067030",
    "📦": "5334544901428229844",
    "📋": "5305265301917549162",
    "⚙️": "5341715473882955310",
    "🌐": "5447410659077661506",
    "🟢": "5449683594425410231",
    "🔵": "5447183459602669338",
    "✍️": "5467538555158943525",
    "⚠️": "5274099962655816924",
    "🔴": "5210952531676504517",
    "🧾": "5206607081334906820",
    "✅": "5210956306952758910",
    "💬": "5443038326535759644",
    "⛔": "5260293700088511294",
    "🆕": "5282843764451195532",
    "🔔": "5458603043203327669",
    "💠": "5427168083074628963",
    "👤": "5461117441612462242",
    "✉️": "5253742260054409879",
    "✖️": "5210952531676504517",
    "📈": "5244837092042750681",
    "👥": "5461117441612462242",
    "🔄": "5386367538735104399",
    "💰": "5409048419211682843",
    "🕒": "5386367538735104399",
    "🔧": "5361741454685256344",
    "🏠": "5416041192905265756",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("p2p-capital")

LANGS = {
    "ru": {
        "welcome": "⭐ <b>P2P CAPITAL</b>  <code>PREMIUM</code>\n<blockquote>Добро пожаловать в P2P-сервис заявок.</blockquote>\n💎 <b>Быстрый доступ к обменным заявкам</b>\nВыберите нужный раздел:",
        "buy_sell": "💱 Купить / Продать", "rates": "📊 Курсы", "stock": "📦 Наличие",
        "my_orders": "📋 Мои заявки", "support": "🎧 Поддержка", "reviews": "⭐ Отзывы",
        "settings": "⚙️ Настройки", "language": "🌐 Язык",
        "choose_lang": "🌐 <b>Выберите язык интерфейса</b>",
        "choose_direction": "💱 <b>Выберите направление</b>",
        "buy": "🟢 Купить", "sell": "🔵 Продать", "choose_asset": "Выберите актив:",
        "amount": "✍️ Введите количество <b>{asset}</b>.\n\nНапример: <code>25</code> или <code>12.5</code>",
        "bad_amount": "⚠️ Введите корректное число больше нуля.",
        "no_stock": "🔴 <b>Сейчас {asset} нет в наличии.</b>\n\nПокупка этого актива временно недоступна. Попробуйте позже или обратитесь к менеджеру: @{manager}",
        "not_enough": "⚠️ <b>Недостаточно актива в наличии.</b>\nЗапрошено: <b>{requested} {asset}</b>\nДоступно: <b>{available} {asset}</b>\n\nВведите другое количество или отмените заявку.",
        "limit": "⚠️ Превышен лимит {direction}: <b>{limit} UAH</b>.\nУменьшите сумму заявки и попробуйте снова.",
        "confirm": "🧾 <b>ПРОВЕРЬТЕ ЗАЯВКУ</b>\n\n<b>Направление:</b> {direction}\n<b>Актив:</b> {asset}\n<b>Количество:</b> {amount} {asset}\n<b>Курс:</b> {rate} UAH\n<b>Ориентировочная сумма:</b> {total} UAH\n\n<blockquote>Это предварительная заявка. Сделка не считается подтверждённой до ответа оператора.</blockquote>",
        "created": "✅ <b>Заявка #{id} отправлена администратору.</b>\n\nОператор свяжется с вами в Telegram. Не отправляйте пароли, коды подтверждения или приватные ключи.",
        "cancel": "Заявка отменена.", "confirm_btn": "✅ Отправить заявку",
        "no_orders": "У вас пока нет заявок.", "status": "Статус",
        "stock_empty": "Наличие пока не указано администратором.",
        "support_prompt": "💬 Напишите сообщение. Оно будет отправлено администратору вместе с вашим Telegram-профилем.",
        "support_sent": "✅ Сообщение отправлено администратору. Ваш ID обращения: #{id}.",
        "admin_only": "⛔ Эта функция доступна только администратору.",
        "admin": "🔐 Админ-панель", "admin_orders": "📋 Последние заявки",
        "admin_rates": "📊 Изменить курс", "admin_stock": "📦 Изменить наличие",
        "admin_limits": "⚖️ Лимиты покупки / продажи",
        "enter_limits": "Отправьте одну строку для изменения лимита:\n<code>BUY 10000</code> или <code>SELL 20000</code>\n\nСумма указывается в UAH. Текущие лимиты можно менять отдельно.",
        "limits_saved": "✅ Лимит {direction} установлен: <b>{limit} UAH</b>.",
        "enter_rate": "Отправьте одной строкой:\n<code>USDT 45 43</code>\nили <code>GRAM 66 61</code>\n\nФормат: АКТИВ КУРС_ПОКУПКИ КУРС_ПРОДАЖИ",
        "rate_saved": "✅ Курсы обновлены.",
        "enter_stock": "Отправьте одной строкой:\n<code>USDT 1500</code>\nили <code>GRAM 25000</code>\n\nУкажите 0, чтобы отключить покупку актива.",
        "stock_saved": "✅ Наличие обновлено.",
        "support_contact": "Менеджер: @{name}",
        "reviews_text": "⭐ Открыть канал отзывов:",
        "language_saved": "✅ Язык сохранён.",
        "demo_notice": "⚠️ <b>Важно:</b> бот принимает заявки и передаёт их оператору. Он не принимает платежи и не выполняет переводы.",
        "admin_home": "🔐 <b>P2P CAPITAL · ADMIN</b>\n\nВыберите действие:",
        "admin_new": "🆕 <b>НОВАЯ ЗАЯВКА #{id}</b>",
        "admin_ticket": "🎧 <b>НОВОЕ ОБРАЩЕНИЕ #{id}</b>",
        "admin_reply_usage": "Ответить клиенту: <code>/reply USER_ID текст сообщения</code>\n\nID клиента и username указаны в уведомлении.",
        "reply_ok": "✅ Сообщение отправлено пользователю.",
        "reply_fail": "Не удалось отправить сообщение. Проверьте Telegram ID и то, что пользователь запускал бота.",
        "status_help": "Использование: <code>/status ORDER_ID NEW|ACCEPTED|PROCESSING|COMPLETED|CANCELLED|REJECTED</code>",
        "status_updated": "✅ Статус заявки #{id} изменён на <b>{status}</b>.",
        "user_status": "🔔 Статус вашей заявки <b>#{id}</b> изменён: <b>{status}</b>.",
        "empty_orders": "Заявок пока нет.",
    },
    "uk": {
        "welcome": "⭐ <b>P2P CAPITAL</b>  <code>PREMIUM</code>\n<blockquote>Вітаємо у P2P-сервісі заявок.</blockquote>\n💎 <b>Швидкий доступ до заявок на обмін</b>\nОберіть потрібний розділ:",
        "buy_sell": "💱 Купити / Продати", "rates": "📊 Курси", "stock": "📦 Наявність",
        "my_orders": "📋 Мої заявки", "support": "🎧 Підтримка", "reviews": "⭐ Відгуки",
        "settings": "⚙️ Налаштування", "language": "🌐 Мова",
        "choose_lang": "🌐 <b>Оберіть мову інтерфейсу</b>",
        "choose_direction": "💱 <b>Оберіть напрямок</b>",
        "buy": "🟢 Купити", "sell": "🔵 Продати", "choose_asset": "Оберіть актив:",
        "amount": "✍️ Введіть кількість <b>{asset}</b>.\n\nНаприклад: <code>25</code> або <code>12.5</code>",
        "bad_amount": "⚠️ Введіть коректне число більше нуля.",
        "no_stock": "🔴 <b>Зараз {asset} немає в наявності.</b>\n\nКупівля цього активу тимчасово недоступна. Спробуйте пізніше або зверніться до менеджера: @{manager}",
        "not_enough": "⚠️ <b>Недостатньо активу в наявності.</b>\nЗапитано: <b>{requested} {asset}</b>\nДоступно: <b>{available} {asset}</b>\n\nВведіть іншу кількість або скасуйте заявку.",
        "limit": "⚠️ Перевищено ліміт {direction}: <b>{limit} UAH</b>.\nЗменште суму заявки та спробуйте ще раз.",
        "confirm": "🧾 <b>ПЕРЕВІРТЕ ЗАЯВКУ</b>\n\n<b>Напрямок:</b> {direction}\n<b>Актив:</b> {asset}\n<b>Кількість:</b> {amount} {asset}\n<b>Курс:</b> {rate} UAH\n<b>Орієнтовна сума:</b> {total} UAH\n\n<blockquote>Це попередня заявка. Угода не підтверджена до відповіді оператора.</blockquote>",
        "created": "✅ <b>Заявку #{id} надіслано адміністратору.</b>\n\nОператор зв’яжеться з вами в Telegram. Не надсилайте паролі, коди підтвердження або приватні ключі.",
        "cancel": "Заявку скасовано.", "confirm_btn": "✅ Надіслати заявку",
        "no_orders": "У вас поки немає заявок.", "status": "Статус",
        "stock_empty": "Наявність ще не вказана адміністратором.",
        "support_prompt": "💬 Напишіть повідомлення. Його буде надіслано адміністратору разом із вашим Telegram-профілем.",
        "support_sent": "✅ Повідомлення надіслано адміністратору. ID звернення: #{id}.",
        "admin_only": "⛔ Ця функція доступна лише адміністратору.",
        "admin": "🔐 Адмін-панель", "admin_orders": "📋 Останні заявки",
        "admin_rates": "📊 Змінити курс", "admin_stock": "📦 Змінити наявність",
        "admin_limits": "⚖️ Ліміти купівлі / продажу",
        "enter_limits": "Надішліть один рядок для зміни ліміту:\n<code>BUY 10000</code> або <code>SELL 20000</code>\n\nСума вказується в UAH. Ліміти можна змінювати окремо.",
        "limits_saved": "✅ Ліміт {direction} встановлено: <b>{limit} UAH</b>.",
        "enter_rate": "Надішліть одним рядком:\n<code>USDT 45 43</code>\nабо <code>GRAM 66 61</code>\n\nФормат: АКТИВ КУРС_КУПІВЛІ КУРС_ПРОДАЖУ",
        "rate_saved": "✅ Курси оновлено.",
        "enter_stock": "Надішліть одним рядком:\n<code>USDT 1500</code>\nабо <code>GRAM 25000</code>\n\nВкажіть 0, щоб вимкнути купівлю активу.",
        "stock_saved": "✅ Наявність оновлено.",
        "support_contact": "Менеджер: @{name}",
        "reviews_text": "⭐ Відкрити канал відгуків:",
        "language_saved": "✅ Мову збережено.",
        "demo_notice": "⚠️ <b>Важливо:</b> бот приймає заявки та передає їх оператору. Він не приймає платежі й не виконує перекази.",
        "admin_home": "🔐 <b>P2P CAPITAL · ADMIN</b>\n\nОберіть дію:",
        "admin_new": "🆕 <b>НОВА ЗАЯВКА #{id}</b>",
        "admin_ticket": "🎧 <b>НОВЕ ЗВЕРНЕННЯ #{id}</b>",
        "admin_reply_usage": "Відповісти клієнту: <code>/reply USER_ID текст повідомлення</code>\n\nID клієнта та username вказані в сповіщенні.",
        "reply_ok": "✅ Повідомлення надіслано користувачу.",
        "reply_fail": "Не вдалося надіслати повідомлення. Перевірте Telegram ID і чи запускав користувач бота.",
        "status_help": "Використання: <code>/status ORDER_ID NEW|ACCEPTED|PROCESSING|COMPLETED|CANCELLED|REJECTED</code>",
        "status_updated": "✅ Статус заявки #{id} змінено на <b>{status}</b>.",
        "user_status": "🔔 Статус вашої заявки <b>#{id}</b> змінено: <b>{status}</b>.",
        "empty_orders": "Заявок поки немає.",
    },
    "en": {
        "welcome": "⭐ <b>P2P CAPITAL</b>  <code>PREMIUM</code>\n<blockquote>Welcome to the P2P request service.</blockquote>\n💎 <b>Quick access to exchange requests</b>\nChoose a section:",
        "buy_sell": "💱 Buy / Sell", "rates": "📊 Rates", "stock": "📦 Availability",
        "my_orders": "📋 My requests", "support": "🎧 Support", "reviews": "⭐ Reviews",
        "settings": "⚙️ Settings", "language": "🌐 Language",
        "choose_lang": "🌐 <b>Choose interface language</b>",
        "choose_direction": "💱 <b>Choose direction</b>",
        "buy": "🟢 Buy", "sell": "🔵 Sell", "choose_asset": "Choose an asset:",
        "amount": "✍️ Enter the amount of <b>{asset}</b>.\n\nExample: <code>25</code> or <code>12.5</code>",
        "bad_amount": "⚠️ Enter a valid number greater than zero.",
        "no_stock": "🔴 <b>{asset} is currently unavailable.</b>\n\nBuying this asset is temporarily unavailable. Try again later or contact the manager: @{manager}",
        "not_enough": "⚠️ <b>Insufficient availability.</b>\nRequested: <b>{requested} {asset}</b>\nAvailable: <b>{available} {asset}</b>\n\nEnter a lower amount or cancel.",
        "limit": "⚠️ The {direction} limit was exceeded: <b>{limit} UAH</b>.\nReduce the request amount and try again.",
        "confirm": "🧾 <b>REVIEW YOUR REQUEST</b>\n\n<b>Direction:</b> {direction}\n<b>Asset:</b> {asset}\n<b>Quantity:</b> {amount} {asset}\n<b>Rate:</b> {rate} UAH\n<b>Estimated total:</b> {total} UAH\n\n<blockquote>This is a preliminary request. It is not confirmed until an operator responds.</blockquote>",
        "created": "✅ <b>Request #{id} has been sent to the administrator.</b>\n\nThe operator will contact you on Telegram. Never send passwords, verification codes, or private keys.",
        "cancel": "Request cancelled.", "confirm_btn": "✅ Send request",
        "no_orders": "You have no requests yet.", "status": "Status",
        "stock_empty": "Availability has not been set by an administrator yet.",
        "support_prompt": "💬 Send a message. It will be forwarded to the administrator with your Telegram profile.",
        "support_sent": "✅ Message sent to the administrator. Ticket ID: #{id}.",
        "admin_only": "⛔ This feature is for administrators only.",
        "admin": "🔐 Admin panel", "admin_orders": "📋 Recent requests",
        "admin_rates": "📊 Change rates", "admin_stock": "📦 Change availability",
        "admin_limits": "⚖️ Buy / sell limits",
        "enter_limits": "Send one line to change a limit:\n<code>BUY 10000</code> or <code>SELL 20000</code>\n\nThe amount is in UAH. Each limit can be changed separately.",
        "limits_saved": "✅ {direction} limit set to <b>{limit} UAH</b>.",
        "enter_rate": "Send one line:\n<code>USDT 45 43</code>\nor <code>GRAM 66 61</code>\n\nFormat: ASSET BUY_RATE SELL_RATE",
        "rate_saved": "✅ Rates updated.",
        "enter_stock": "Send one line:\n<code>USDT 1500</code>\nor <code>GRAM 25000</code>\n\nSet 0 to disable buying this asset.",
        "stock_saved": "✅ Availability updated.",
        "support_contact": "Manager: @{name}",
        "reviews_text": "⭐ Open the reviews channel:",
        "language_saved": "✅ Language saved.",
        "demo_notice": "⚠️ <b>Important:</b> this bot collects requests and forwards them to an operator. It does not accept payments or execute transfers.",
        "admin_home": "🔐 <b>P2P CAPITAL · ADMIN</b>\n\nChoose an action:",
        "admin_new": "🆕 <b>NEW REQUEST #{id}</b>",
        "admin_ticket": "🎧 <b>NEW SUPPORT MESSAGE #{id}</b>",
        "admin_reply_usage": "Reply to a client: <code>/reply USER_ID message text</code>\n\nThe user ID and username are shown in the notification.",
        "reply_ok": "✅ Message sent to the user.",
        "reply_fail": "Could not send the message. Check the Telegram ID and whether the user has started the bot.",
        "status_help": "Usage: <code>/status ORDER_ID NEW|ACCEPTED|PROCESSING|COMPLETED|CANCELLED|REJECTED</code>",
        "status_updated": "✅ Request #{id} status changed to <b>{status}</b>.",
        "user_status": "🔔 Your request <b>#{id}</b> status changed: <b>{status}</b>.",
        "empty_orders": "No requests yet.",
    }
}

def premium_text(text: str) -> str:
    """Use configured Telegram custom emoji IDs; fall back to normal Unicode emoji."""
    for fallback, emoji_id in PREMIUM_EMOJI_IDS.items():
        if emoji_id and emoji_id.isdigit():
            text = text.replace(fallback, f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>')
    return text

async def edit_screen(message: Message, text: str, reply_markup=None):
    """Edit a photo-caption menu or a regular text message without sending clutter."""
    text = premium_text(text)
    if message.photo:
        await message.edit_caption(caption=text, reply_markup=reply_markup)
    else:
        await message.edit_text(text, reply_markup=reply_markup)

async def show_main_menu(message: Message, uid: int):
    caption = premium_text(t(uid, "welcome") + "\n\n" + t(uid, "demo_notice"))
    if MENU_IMAGE.exists():
        await message.answer_photo(FSInputFile(MENU_IMAGE), caption=caption, reply_markup=main_kb(uid))
    else:
        await message.answer(caption, reply_markup=main_kb(uid))

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            telegram_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            language TEXT NOT NULL DEFAULT 'ru', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rates(
            asset TEXT PRIMARY KEY, buy_rate TEXT NOT NULL, sell_rate TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS inventory(
            asset TEXT PRIMARY KEY, quantity TEXT NOT NULL DEFAULT '0', enabled INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders(
            id TEXT PRIMARY KEY, telegram_id INTEGER NOT NULL, direction TEXT NOT NULL,
            asset TEXT NOT NULL CHECK(asset IN ('USDT','GRAM')), amount TEXT NOT NULL,
            rate TEXT NOT NULL, total_uah TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'NEW',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tickets(
            id TEXT PRIMARY KEY, telegram_id INTEGER NOT NULL, message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS order_limits(
            direction TEXT PRIMARY KEY CHECK(direction IN ('BUY','SELL')),
            max_uah TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        c.execute("INSERT OR IGNORE INTO order_limits VALUES('BUY','10000',?)", (now(),))
        c.execute("INSERT OR IGNORE INTO order_limits VALUES('SELL','10000',?)", (now(),))
        for asset, buy, sell in [("USDT","45","43"),("GRAM","66","61")]:
            c.execute("INSERT OR IGNORE INTO rates VALUES(?,?,?,?)", (asset,buy,sell,now()))
            c.execute("INSERT OR IGNORE INTO inventory VALUES(?,?,?,?)", (asset,"0",0,now()))

def ensure_user(user):
    with connect() as c:
        c.execute("""INSERT INTO users(telegram_id,username,first_name,language,created_at)
        VALUES(?,?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET
        username=excluded.username, first_name=excluded.first_name""",
        (user.id, user.username, user.first_name, "ru", now()))

def lang(uid):
    with connect() as c:
        row = c.execute("SELECT language FROM users WHERE telegram_id=?", (uid,)).fetchone()
    return row["language"] if row and row["language"] in LANGS else "ru"

def t(uid, key):
    return LANGS[lang(uid)][key]

def fmt_num(value):
    d = Decimal(str(value))
    return format(d.normalize(), "f")

def get_order_limit(direction: str) -> Decimal:
    with connect() as c:
        row = c.execute("SELECT max_uah FROM order_limits WHERE direction=?", (direction,)).fetchone()
    return Decimal(row["max_uah"]) if row else Decimal("0")

def limit_message(uid: int, direction: str, limit: Decimal) -> str:
    direction_label = t(uid, "buy") if direction == "BUY" else t(uid, "sell")
    return t(uid, "limit").format(direction=direction_label, limit=fmt_num(limit))

def user_profile(uid, username, first_name):
    name = f"@{escape(username)}" if username else "username отсутствует"
    first = escape(first_name or "без имени")
    return f"<a href=\"tg://user?id={uid}\">{first}</a> · {name}\n<code>{uid}</code>"

def main_kb(uid):
    L = LANGS[lang(uid)]
    # Telegram inline-button labels accept regular Unicode emoji, but not
    # Premium custom-emoji entities. Premium custom emoji are used in the
    # menu caption; buttons keep matching standard emoji as a safe fallback.
    rows = [
        [(f"💱 {L['buy_sell'].split(' ', 1)[-1]}", "menu:buy_sell"),
         (f"📊 {L['rates'].split(' ', 1)[-1]}", "menu:rates")],
        [(f"📦 {L['stock'].split(' ', 1)[-1]}", "menu:stock"),
         (f"📋 {L['my_orders'].split(' ', 1)[-1]}", "menu:my_orders")],
        [(f"🎧 {L['support'].split(' ', 1)[-1]}", "menu:support"),
         (f"💬 {L['reviews'].split(' ', 1)[-1]}", "menu:reviews")],
        [(f"⚙️ {L['settings'].split(' ', 1)[-1]}", "menu:settings"),
         (f"🌐 {L['language'].split(' ', 1)[-1]}", "menu:language")],
    ]
    if uid in ADMIN_IDS:
        rows.append([(L["admin"], "menu:admin")])
    return ikb(rows)


def ikb(rows):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=data) for label,data in row]
        for row in rows
    ])

class Flow(StatesGroup):
    direction = State()
    asset = State()
    amount = State()
    confirm = State()
    support = State()
    rate = State()
    stock = State()
    limits = State()
    admin_support_reply = State()

def is_state(current, state):
    return current == state.state

async def start(m: Message, state: FSMContext):
    await state.clear()
    ensure_user(m.from_user)
    # /start opens the main menu directly; language is changed in Settings.
    try:
        await m.delete()
    except Exception:
        pass
    await show_main_menu(m, m.from_user.id)

async def choose_language(cq: CallbackQuery):
    selected = cq.data.split(":")[1]
    with connect() as c:
        c.execute("UPDATE users SET language=? WHERE telegram_id=?", (selected,cq.from_user.id))
    await edit_screen(cq.message, LANGS[selected]["welcome"] + "\n\n" + LANGS[selected]["demo_notice"],
                               reply_markup=main_kb(cq.from_user.id))
    await cq.answer(LANGS[selected]["language_saved"])

async def notify_admins(bot: Bot, text: str, reply_markup=None):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup)
        except Exception:
            log.exception("Cannot notify admin %s", admin_id)

async def handle_text(m: Message, state: FSMContext):
    uid = m.from_user.id
    txt = (m.text or "").strip()
    L = LANGS[lang(uid)]
    current = await state.get_state()
    # Remove typed input after receiving it; bot replies and inline controls remain.
    try:
        await m.delete()
    except Exception:
        pass

    if txt in {L["language"], L["settings"]}:
        await m.answer(t(uid,"choose_lang"), reply_markup=ikb([[("🇺🇦 Українська","lang:uk"),("🇷🇺 Русский","lang:ru"),("🇬🇧 English","lang:en")]])); return

    if txt == L["buy_sell"]:
        await state.clear()
        await state.set_state(Flow.direction)
        await m.answer(t(uid,"choose_direction"), reply_markup=ikb([[(L["buy"],"dir:BUY"),(L["sell"],"dir:SELL")],[("⬅️ В меню","menu:home")]])); return

    if txt == L["rates"]:
        with connect() as c:
            rows = c.execute("SELECT * FROM rates ORDER BY asset").fetchall()
        body = "📊 <b>P2P CAPITAL · КУРСЫ</b>\n\n" + "\n\n".join(
            f"💠 <b>{r['asset']}</b>\nПокупка: <b>{r['buy_rate']} UAH</b>\nПродажа: <b>{r['sell_rate']} UAH</b>"
            for r in rows)
        await m.answer(body); return

    if txt == L["stock"]:
        with connect() as c:
            rows = c.execute("SELECT * FROM inventory ORDER BY asset").fetchall()
        body = "📦 <b>P2P CAPITAL · НАЛИЧИЕ</b>\n\n" + "\n\n".join(
            f"💠 <b>{r['asset']}</b>\n" + (f"🟢 Доступно: <b>{r['quantity']} {r['asset']}</b>" if r["enabled"] and Decimal(r["quantity"]) > 0 else "🔴 Сейчас нет в наличии")
            for r in rows)
        await m.answer(body); return

    if txt == L["my_orders"]:
        with connect() as c:
            rows = c.execute("SELECT * FROM orders WHERE telegram_id=? ORDER BY created_at DESC LIMIT 10",(uid,)).fetchall()
        if not rows:
            await m.answer(t(uid,"no_orders")); return
        await m.answer("📋 <b>ВАШИ ЗАЯВКИ</b>\n\n" + "\n\n".join(
            f"#{r['id']} · {r['direction']} {r['amount']} {r['asset']}\n{L['status']}: <b>{r['status']}</b>"
            for r in rows)); return

    if txt == L["support"]:
        await state.set_state(Flow.support)
        await m.answer(t(uid,"support_prompt"), reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]])); return

    if txt == L["reviews"]:
        await m.answer(t(uid,"reviews_text"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Открыть отзывы", url=REVIEWS_URL)]
        ])); return

    if txt == L["admin"] and uid in ADMIN_IDS:
        await m.answer(premium_text(t(uid,"admin_home")), reply_markup=ikb([
            [(L["admin_orders"],"adm:orders")],
            [(L["admin_rates"],"adm:rates"),(L["admin_stock"],"adm:stock")],
            [(L["admin_limits"],"adm:limits")]
        ])); return

    if is_state(current, Flow.amount):
        data = await state.get_data()
        try:
            amount = Decimal(txt.replace(",", "."))
            if not amount.is_finite() or amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            await m.answer(t(uid,"bad_amount")); return

        asset, direction = data["asset"], data["direction"]
        with connect() as c:
            rate_row = c.execute("SELECT * FROM rates WHERE asset=?", (asset,)).fetchone()
            inv = c.execute("SELECT * FROM inventory WHERE asset=?", (asset,)).fetchone()

        if direction == "BUY":
            available = Decimal(inv["quantity"]) if inv and inv["enabled"] else Decimal("0")
            if available <= 0:
                await state.clear()
                await m.answer(t(uid,"no_stock").format(asset=asset,manager=SUPPORT_USERNAME), reply_markup=main_kb(uid)); return
            if amount > available:
                await m.answer(t(uid,"not_enough").format(requested=fmt_num(amount),asset=asset,available=fmt_num(available))); return

        rate = Decimal(rate_row["buy_rate"] if direction == "BUY" else rate_row["sell_rate"])
        if rate <= 0:
            await m.answer("⚠️ Для цього активу курс ще не налаштований адміністратором."); return
        total = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        current_limit = get_order_limit(direction)
        if total > current_limit:
            await m.answer(limit_message(uid, direction, current_limit)); return

        await state.update_data(amount=str(amount), rate=str(rate), total=str(total))
        await state.set_state(Flow.confirm)
        direction_label = L["buy"] if direction == "BUY" else L["sell"]
        await m.answer(t(uid,"confirm").format(direction=direction_label,asset=asset,amount=fmt_num(amount),rate=fmt_num(rate),total=fmt_num(total)),
            reply_markup=ikb([[(t(uid,"confirm_btn"),"order:confirm")],[(t(uid,"cancel"),"order:cancel")],[("⬅️ В меню","menu:home")]])); return

    if is_state(current, Flow.support):
        if not txt:
            await m.answer(t(uid,"support_prompt"), reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]])); return
        ticket_id = uuid.uuid4().hex[:8].upper()
        with connect() as c:
            c.execute("INSERT INTO tickets VALUES(?,?,?,'OPEN',?)",(ticket_id,uid,txt,now()))
        profile = user_profile(uid,m.from_user.username,m.from_user.first_name)
        admin_text = f"{t(uid,'admin_ticket').format(id=ticket_id)}\n\n👤 <b>Клиент:</b> {profile}\n\n💬 <b>Сообщение:</b>\n{escape(txt)}\n\n{t(uid,'admin_reply_usage')}"
        await notify_admins(m.bot,admin_text,reply_markup=ikb([[("✉️ Ответить клиенту",f"supportreply:{ticket_id}:{uid}")]]))
        await state.clear()
        await m.answer(t(uid,"support_sent").format(id=ticket_id), reply_markup=main_kb(uid)); return

    if is_state(current, Flow.admin_support_reply) and uid in ADMIN_IDS:
        data = await state.get_data()
        target = int(data.get("support_target", 0))
        try:
            await m.bot.send_message(target, "💬 <b>Ответ поддержки P2P Capital</b>\n\n" + escape(txt), reply_markup=ikb([[ ("✉️ Ответить поддержке","menu:support") ]]))
            await m.answer("✅ Ответ отправлен клиенту.")
        except Exception:
            await m.answer(t(uid,"reply_fail"))
        await state.clear(); return

    if is_state(current, Flow.rate) and uid in ADMIN_IDS:
        try:
            asset,buy,sell = txt.upper().split()
            if asset not in {"USDT","GRAM"} or Decimal(buy) <= 0 or Decimal(sell) <= 0: raise ValueError
            with connect() as c:
                c.execute("UPDATE rates SET buy_rate=?,sell_rate=?,updated_at=? WHERE asset=?",(buy,sell,now(),asset))
            await state.clear(); await m.answer(t(uid,"rate_saved"), reply_markup=main_kb(uid))
        except Exception:
            await m.answer(t(uid,"enter_rate"))
        return

    if is_state(current, Flow.stock) and uid in ADMIN_IDS:
        try:
            asset,qty = txt.upper().split()
            q = Decimal(qty)
            if asset not in {"USDT","GRAM"} or not q.is_finite() or q < 0: raise ValueError
            with connect() as c:
                c.execute("UPDATE inventory SET quantity=?,enabled=?,updated_at=? WHERE asset=?",(str(q),int(q>0),now(),asset))
            await state.clear(); await m.answer(t(uid,"stock_saved"), reply_markup=main_kb(uid))
        except Exception:
            await m.answer(t(uid,"enter_stock"))
        return

    if is_state(current, Flow.limits) and uid in ADMIN_IDS:
        try:
            direction, raw_limit = txt.upper().split()
            limit = Decimal(raw_limit.replace(",", "."))
            if direction not in {"BUY", "SELL"} or not limit.is_finite() or limit <= 0:
                raise ValueError
            with connect() as c:
                c.execute(
                    "INSERT INTO order_limits(direction,max_uah,updated_at) VALUES(?,?,?) "
                    "ON CONFLICT(direction) DO UPDATE SET max_uah=excluded.max_uah, updated_at=excluded.updated_at",
                    (direction, str(limit), now())
                )
            await state.clear()
            await m.answer(
                t(uid, "limits_saved").format(
                    direction=("покупки" if direction == "BUY" else "продажи") if lang(uid) == "ru"
                    else ("купівлі" if direction == "BUY" else "продажу") if lang(uid) == "uk"
                    else ("buy" if direction == "BUY" else "sell"),
                    limit=fmt_num(limit)
                ),
                reply_markup=main_kb(uid)
            )
        except Exception:
            await m.answer(t(uid, "enter_limits"))
        return

async def callbacks(cq: CallbackQuery, state: FSMContext):
    uid, data = cq.from_user.id, cq.data
    if data.startswith("menu:"):
        action = data.split(":", 1)[1]
        L = LANGS[lang(uid)]
        if action == "home":
            await state.clear()
            await edit_screen(cq.message, t(uid,"welcome") + "\n\n" + t(uid,"demo_notice"), reply_markup=main_kb(uid))
        elif action in {"settings", "language"}:
            await state.clear()
            await edit_screen(cq.message, t(uid,"choose_lang"), reply_markup=ikb([[ ("🇺🇦 Українська","lang:uk"), ("🇷🇺 Русский","lang:ru"), ("🇬🇧 English","lang:en") ], [("⬅️ В меню","menu:home")]]))
        elif action == "buy_sell":
            await state.clear(); await state.set_state(Flow.direction)
            await edit_screen(cq.message, t(uid,"choose_direction"), reply_markup=ikb([[(L["buy"],"dir:BUY"),(L["sell"],"dir:SELL")],[("⬅️ Назад","menu:home")]]))
        elif action == "rates":
            with connect() as c: rows = c.execute("SELECT * FROM rates ORDER BY asset").fetchall()
            body = "📊 <b>P2P CAPITAL · КУРСЫ</b>\n\n" + "\n\n".join(f"💠 <b>{r['asset']}</b>\nПокупка: <b>{r['buy_rate']} UAH</b>\nПродажа: <b>{r['sell_rate']} UAH</b>" for r in rows)
            await edit_screen(cq.message, body, reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]]))
        elif action == "stock":
            with connect() as c: rows = c.execute("SELECT * FROM inventory ORDER BY asset").fetchall()
            body = "📦 <b>P2P CAPITAL · НАЛИЧИЕ</b>\n\n" + "\n\n".join(f"💠 <b>{r['asset']}</b>\n" + (f"🟢 Доступно: <b>{r['quantity']} {r['asset']}</b>" if r["enabled"] and Decimal(r["quantity"]) > 0 else "🔴 Сейчас нет в наличии") for r in rows)
            await edit_screen(cq.message, body, reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]]))
        elif action == "my_orders":
            with connect() as c: rows = c.execute("SELECT * FROM orders WHERE telegram_id=? ORDER BY created_at DESC LIMIT 10",(uid,)).fetchall()
            body = t(uid,"no_orders") if not rows else "📋 <b>ВАШИ ЗАЯВКИ</b>\n\n" + "\n\n".join(f"#{r['id']} · {r['direction']} {r['amount']} {r['asset']}\n{L['status']}: <b>{r['status']}</b>" for r in rows)
            await edit_screen(cq.message, body, reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]]))
        elif action == "support":
            await state.set_state(Flow.support)
            await edit_screen(cq.message, "🎧 <b>ПОДДЕРЖКА P2P CAPITAL</b>\n\n" + t(uid,"support_prompt") + "\n\nВаши сообщения и ответы менеджера будут идти в этой переписке.", reply_markup=ikb([[ ("✖️ Закрыть","support:close") ],[("⬅️ В меню","menu:home")]]))
        elif action == "reviews":
            await edit_screen(cq.message, t(uid,"reviews_text"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⭐ Открыть отзывы",url=REVIEWS_URL)],[InlineKeyboardButton(text="⬅️ В меню",callback_data="menu:home")]]))
        elif action == "admin" and uid in ADMIN_IDS:
            with connect() as c:
                total_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
                new_orders = c.execute("SELECT COUNT(*) FROM orders WHERE status='NEW'").fetchone()[0]
                open_tickets = c.execute("SELECT COUNT(*) FROM tickets WHERE status='OPEN'").fetchone()[0]
                users_total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            dashboard = (
                "🔐 <b>P2P CAPITAL · CONTROL CENTER</b>\n"
                "<i>Панель управления сервисом</i>\n\n"
                "<blockquote>📈 <b>ОБЩАЯ СТАТИСТИКА</b>\n"
                f"👥 Пользователей: <b>{users_total}</b>\n"
                f"📋 Всего заявок: <b>{total_orders}</b>\n"
                f"🆕 Новых заявок: <b>{new_orders}</b>\n"
                f"🎧 Открытых обращений: <b>{open_tickets}</b></blockquote>\n"
                "Выберите нужный инструмент:")
            await edit_screen(cq.message, dashboard, reply_markup=ikb([
                [("📋 Заявки", "adm:orders"), ("🎧 Поддержка", "adm:tickets")],
                [("📊 Курсы", "adm:rates"), ("📦 Остатки", "adm:stock")],
                [("⚖️ Лимиты", "adm:limits")],
                [("🔄 Обновить", "menu:admin")],
                [("⬅️ В главное меню", "menu:home")]
            ]))
        await cq.answer(); return
    if data == "support:close":
        await state.clear()
        await edit_screen(cq.message, t(uid,"welcome") + "\n\n" + t(uid,"demo_notice"), reply_markup=main_kb(uid))
        await cq.answer(); return
    if data.startswith("supportreply:"):
        if uid not in ADMIN_IDS:
            await cq.answer(t(uid,"admin_only"),show_alert=True); return
        _, ticket_id, target = data.split(":",2)
        await state.set_state(Flow.admin_support_reply)
        await state.update_data(support_target=int(target), ticket_id=ticket_id)
        await cq.message.reply("✉️ <b>Режим ответа в поддержку</b>\nОтправьте следующим сообщением текст клиенту. Для выхода используйте /cancel.")
        await cq.answer(); return
    if data.startswith("lang:"):
        await choose_language(cq); return
    if data.startswith("dir:"):
        await state.update_data(direction=data.split(":")[1])
        await state.set_state(Flow.asset)
        await edit_screen(cq.message, t(uid,"choose_asset"), reply_markup=ikb([ [("USDT","asset:USDT"),("GRAM","asset:GRAM")],[("⬅️ В меню","menu:home")] ]))
        await cq.answer(); return
    if data.startswith("asset:"):
        asset = data.split(":")[1]
        if asset not in {"USDT","GRAM"}:
            await cq.answer("Недоступный актив", show_alert=True); return
        data_state = await state.get_data()
        if data_state.get("direction") == "BUY":
            with connect() as c:
                inv = c.execute("SELECT * FROM inventory WHERE asset=?", (asset,)).fetchone()
            if not inv or not inv["enabled"] or Decimal(inv["quantity"]) <= 0:
                await state.clear()
                await edit_screen(cq.message, t(uid,"no_stock").format(asset=asset,manager=SUPPORT_USERNAME), reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]]))
                await cq.answer(); return
        await state.update_data(asset=asset)
        await state.set_state(Flow.amount)
        await edit_screen(cq.message, t(uid,"amount").format(asset=asset), reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]]))
        await cq.answer(); return
    if data == "order:cancel":
        await state.clear()
        await edit_screen(cq.message, t(uid,"cancel"), reply_markup=main_kb(uid))
        await cq.answer(); return
    if data == "order:confirm":
        d = await state.get_data()
        if not d or "asset" not in d:
            await cq.answer("Заявка устарела. Начните заново.", show_alert=True); return
        order_id = uuid.uuid4().hex[:10].upper()
        # Recheck inventory and limits at confirmation time to avoid stale availability.
        with connect() as c:
            if d["direction"] == "BUY":
                inv = c.execute("SELECT * FROM inventory WHERE asset=?", (d["asset"],)).fetchone()
                available = Decimal(inv["quantity"]) if inv and inv["enabled"] else Decimal("0")
                if Decimal(d["amount"]) > available or available <= 0:
                    await edit_screen(cq.message, t(uid,"no_stock").format(asset=d["asset"],manager=SUPPORT_USERNAME), reply_markup=ikb([[ ("⬅️ В меню","menu:home") ]]))
                    await state.clear(); await cq.answer(); return
            current_limit = get_order_limit(d["direction"])
            if Decimal(d["total"]) > current_limit:
                await edit_screen(cq.message, limit_message(uid, d["direction"], current_limit), reply_markup=main_kb(uid))
                await state.clear(); await cq.answer(); return
            c.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?)",
                (order_id,uid,d["direction"],d["asset"],d["amount"],d["rate"],d["total"],"NEW",now()))
        user = cq.from_user
        profile = user_profile(uid,user.username,user.first_name)
        admin_text = (
            f"{t(uid,'admin_new').format(id=order_id)}\n\n"
            f"👤 <b>Клиент:</b> {profile}\n"
            f"🔄 <b>Направление:</b> {escape(d['direction'])}\n"
            f"💠 <b>Актив:</b> {d['asset']}\n"
            f"📦 <b>Количество:</b> {escape(d['amount'])} {d['asset']}\n"
            f"📊 <b>Курс:</b> {escape(d['rate'])} UAH\n"
            f"💰 <b>Сумма:</b> {escape(d['total'])} UAH\n"
            f"🕒 <b>Время:</b> {now()}\n\n"
            f"✉️ Чтобы написать клиенту: <code>/reply {uid} текст</code>\n"
            f"🔧 Чтобы изменить статус: <code>/status {order_id} ACCEPTED</code>"
        )
        await notify_admins(cq.bot,admin_text,reply_markup=ikb([[(f"✉️ Открыть чат с клиентом","contact:"+str(uid))]]))
        await state.clear()
        await edit_screen(cq.message, t(uid,"created").format(id=order_id))
        await cq.answer(); return
    if data.startswith("contact:"):
        if uid not in ADMIN_IDS:
            await cq.answer(t(uid,"admin_only"),show_alert=True); return
        target = data.split(":")[1]
        await cq.answer("Откройте профиль клиента или используйте /reply USER_ID текст.",show_alert=True)
        return
    if data.startswith("adm:"):
        if uid not in ADMIN_IDS:
            await cq.answer(t(uid,"admin_only"),show_alert=True); return
        action = data.split(":")[1]
        if action == "tickets":
            with connect() as c:
                rows = c.execute("SELECT id,telegram_id,message,status,created_at FROM tickets ORDER BY created_at DESC LIMIT 15").fetchall()
            body = "🎧 <b>ОБРАЩЕНИЯ В ПОДДЕРЖКУ</b>\n\n" + ("\n\n".join(
                f"<b>#{r['id']}</b> · <code>{r['telegram_id']}</code> · {r['status']}\n{escape(r['message'][:500])}"
                for r in rows) or "Новых обращений пока нет.")
            await edit_screen(cq.message, body, reply_markup=ikb([[ ("⬅️ В админ-панель", "menu:admin") ], [("🏠 В главное меню", "menu:home")]]))
        elif action == "orders":
            with connect() as c:
                rows = c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 15").fetchall()
            body = "\n\n".join(f"#{r['id']} · user <code>{r['telegram_id']}</code>\n{r['direction']} {r['amount']} {r['asset']} · {r['total_uah']} UAH\n<b>{r['status']}</b>\n<code>/reply {r['telegram_id']} Ваше сообщение</code>" for r in rows) or t(uid,"empty_orders")
            await edit_screen(cq.message, "📋 <b>ПОСЛЕДНИЕ ЗАЯВКИ</b>\n\n"+body, reply_markup=ikb([[ ("⬅️ В админ-панель","menu:admin") ], [("🏠 В главное меню","menu:home")]]))
        elif action == "rates":
            await state.set_state(Flow.rate); await edit_screen(cq.message, t(uid,"enter_rate"), reply_markup=ikb([[ ("⬅️ В админ-панель","menu:admin") ], [("🏠 В главное меню","menu:home")]]))
        elif action == "stock":
            await state.set_state(Flow.stock); await edit_screen(cq.message, t(uid,"enter_stock"), reply_markup=ikb([[ ("⬅️ В админ-панель","menu:admin") ], [("🏠 В главное меню","menu:home")]]))
        elif action == "limits":
            if uid not in ADMIN_IDS:
                await cq.answer(t(uid,"admin_only"), show_alert=True); return
            buy_limit = get_order_limit("BUY")
            sell_limit = get_order_limit("SELL")
            body = (
                "⚖️ <b>ЛИМИТЫ ЗАЯВОК</b>\n\n"
                f"🟢 Покупка: <b>{fmt_num(buy_limit)} UAH</b>\n"
                f"🔵 Продажа: <b>{fmt_num(sell_limit)} UAH</b>\n\n"
                + t(uid, "enter_limits")
            )
            await state.set_state(Flow.limits)
            await edit_screen(cq.message, body, reply_markup=ikb([[("⬅️ В админ-панель","menu:admin")]]))
        await cq.answer(); return

async def admin_reply(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        await m.answer(t(m.from_user.id,"admin_only")); return
    parts = (m.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await m.answer(t(m.from_user.id,"admin_reply_usage")); return
    target = int(parts[1])
    message = parts[2]
    try:
        await m.bot.send_message(target, "💬 <b>Сообщение от менеджера P2P Capital</b>\n\n" + escape(message))
        await m.answer(t(m.from_user.id,"reply_ok"))
    except Exception:
        await m.answer(t(m.from_user.id,"reply_fail"))

async def admin_status(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        await m.answer(t(m.from_user.id,"admin_only")); return
    parts = (m.text or "").split(maxsplit=2)
    if len(parts) != 3:
        await m.answer(t(m.from_user.id,"status_help")); return
    order_id, status = parts[1], parts[2].upper()
    allowed = {"NEW","ACCEPTED","PROCESSING","COMPLETED","CANCELLED","REJECTED"}
    if status not in allowed:
        await m.answer(t(m.from_user.id,"status_help")); return
    with connect() as c:
        row = c.execute("SELECT telegram_id FROM orders WHERE id=?",(order_id,)).fetchone()
        if not row:
            await m.answer("Заявка не найдена."); return
        c.execute("UPDATE orders SET status=? WHERE id=?",(status,order_id))
    await m.answer(t(m.from_user.id,"status_updated").format(id=order_id,status=status))
    try:
        await m.bot.send_message(row["telegram_id"],t(row["telegram_id"],"user_status").format(id=order_id,status=status))
    except Exception:
        log.exception("Could not notify user about status")

async def cancel_command(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Действие отменено.", reply_markup=main_kb(m.from_user.id))

async def main():
    if not TOKEN or TOKEN == "PASTE_TELEGRAM_BOT_TOKEN":
        raise RuntimeError("Укажи BOT_TOKEN в переменных окружения (Environment Variables)")
    init_db()
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.message.register(start, CommandStart())
    dp.message.register(admin_status, Command("status"))
    dp.message.register(cancel_command, Command("cancel"))
    dp.message.register(admin_reply, Command("reply"))
    dp.message.register(handle_text, F.text)
    dp.callback_query.register(callbacks)
    log.info("P2P Capital bot started (request-only mode)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
