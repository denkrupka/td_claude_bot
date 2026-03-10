"""
Twoja Decyzja Telegram Bot — handles leads from Web App calculator.
"""
import json
import logging
import urllib.request
import urllib.parse

BOT_TOKEN = "8310300457:AAEcbE-P6H0UzIhaHFedR1SzJH0p5KgLNDo"
WEBAPP_URL = "https://denkrupka.github.io/td_claude_bot/"
ADMIN_CHAT_ID = 326628865
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


def api(method, data=None):
    url = f"{API_URL}/{method}"
    payload = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def handle_update(update):
    msg = update.get("message")
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    user = msg.get("from", {})
    username = user.get("username", "")
    first_name = user.get("first_name", "")

    # Web App data received (lead from calculator)
    web_app_data = msg.get("web_app_data")
    if web_app_data:
        try:
            data = json.loads(web_app_data["data"])
            result_text = data.get("text", "No data")
            total = data.get("total", 0)
            name = data.get("name", "")
            phone = data.get("phone", "")

            # Forward to admin
            admin_msg = (
                f"🆕 НОВЫЙ ЛИД из калькулятора!\n"
                f"👤 {name or first_name}\n"
                f"📞 {phone or '—'}\n"
                f"🔗 @{username or '—'} (Chat ID: {chat_id})\n\n"
                f"{result_text}"
            )
            api("sendMessage", {"chat_id": ADMIN_CHAT_ID, "text": admin_msg})

            # Confirm to user
            api("sendMessage", {
                "chat_id": chat_id,
                "text": (
                    "✅ <b>Дякуємо за заявку!</b>\n\n"
                    "Наш менеджер зв'яжеться з вами найближчим часом.\n\n"
                    "📞 +48 459 569 035\n"
                    "📍 Poznan, ul. Stanisława Taczaka 24/301\n\n"
                    "Також ми допомагаємо з:\n"
                    "🔹 Карта побиту\n"
                    "🔹 Легалізація перебування\n"
                    "🔹 Заміна водійських прав\n"
                    "🔹 Дозволи на роботу\n\n"
                    "Натисніть кнопку нижче, щоб розрахувати ще раз 👇"
                ),
                "parse_mode": "HTML",
                "reply_markup": {
                    "inline_keyboard": [[{
                        "text": "📊 Калькулятор послуг",
                        "web_app": {"url": WEBAPP_URL}
                    }]]
                }
            })
        except Exception as e:
            log.error(f"Error parsing web_app_data: {e}")
        return

    if text == "/start":
        welcome = (
            "👋 <b>Вітаємо в Twoja Decyzja!</b>\n\n"
            "🏢 Бухгалтерія для бізнесу в Польщі:\n"
            "• JDG (ФОП) — від 250 zł/міс\n"
            "• Sp. z o.o. (ТОВ) — від 450 zł/міс\n\n"
            "📍 Poznan, ul. Stanisława Taczaka 24/301\n"
            "📞 +48 459 569 035\n\n"
            "Також допомагаємо з:\n"
            "🔹 Карта побиту та легалізація\n"
            "🔹 Заміна прав + оцифрування\n"
            "🔹 Дозволи на роботу іноземців\n\n"
            "👇 <b>Розрахуйте вартість послуг за 1 хвилину:</b>"
        )
        api("sendMessage", {
            "chat_id": chat_id,
            "text": welcome,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [[{
                    "text": "📊 Калькулятор послуг",
                    "web_app": {"url": WEBAPP_URL}
                }], [{
                    "text": "📞 Зателефонувати",
                    "url": "tel:+48459569035"
                }, {
                    "text": "💬 Telegram",
                    "url": "https://t.me/twoja_decyzja"
                }]]
            }
        })
        return

    # Default
    api("sendMessage", {
        "chat_id": chat_id,
        "text": "Натисніть /start щоб відкрити калькулятор послуг 📊",
        "reply_markup": {
            "inline_keyboard": [[{
                "text": "📊 Калькулятор",
                "web_app": {"url": WEBAPP_URL}
            }]]
        }
    })


def setup_bot():
    api("setChatMenuButton", {
        "menu_button": {
            "type": "web_app",
            "text": "Kalkulator",
            "web_app": {"url": WEBAPP_URL}
        }
    })
    api("setMyCommands", {
        "commands": [
            {"command": "start", "description": "Open price calculator"}
        ]
    })
    log.info("Bot configured.")


def run_polling():
    setup_bot()
    log.info("Bot started in polling mode...")
    offset = 0
    while True:
        try:
            result = api("getUpdates", {"offset": offset, "timeout": 30})
            for update in result.get("result", []):
                offset = update["update_id"] + 1
                try:
                    handle_update(update)
                except Exception as e:
                    log.error(f"Error handling update: {e}")
        except KeyboardInterrupt:
            log.info("Bot stopped.")
            break
        except Exception as e:
            log.error(f"Polling error: {e}")
            import time
            time.sleep(5)


if __name__ == "__main__":
    run_polling()
