"""
Twoja Decyzja Telegram Bot
Handles Web App data and provides the calculator button.
"""
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse

BOT_TOKEN = "8310300457:AAEcbE-P6H0UzIhaHFedR1SzJH0p5KgLNDo"
WEBAPP_URL = "https://denkrupka.github.io/td_claude_bot/"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)


def api(method, data=None):
    """Call Telegram Bot API."""
    url = f"{API_URL}/{method}"
    payload = json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def handle_update(update):
    """Process a single update from Telegram."""
    # /start command
    msg = update.get("message")
    if msg:
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # Web App data received
        web_app_data = msg.get("web_app_data")
        if web_app_data:
            try:
                data = json.loads(web_app_data["data"])
                result_text = data.get("text", "No data")
                api("sendMessage", {
                    "chat_id": chat_id,
                    "text": result_text,
                    "parse_mode": "HTML",
                })
            except Exception as e:
                log.error(f"Error parsing web_app_data: {e}")
                api("sendMessage", {
                    "chat_id": chat_id,
                    "text": "Ошибка обработки данных. Попробуйте ещё раз.",
                })
            return

        if text == "/start":
            welcome = (
                "👋 <b>Добро пожаловать в Twoja Decyzja!</b>\n\n"
                "Рассчитайте стоимость бухгалтерских услуг "
                "с помощью нашего калькулятора.\n\n"
                "Нажмите кнопку ниже 👇"
            )
            api("sendMessage", {
                "chat_id": chat_id,
                "text": welcome,
                "parse_mode": "HTML",
                "reply_markup": {
                    "inline_keyboard": [[{
                        "text": "📊 Калькулятор услуг",
                        "web_app": {"url": WEBAPP_URL}
                    }]]
                }
            })
            return

        # Default reply
        api("sendMessage", {
            "chat_id": chat_id,
            "text": "Нажмите /start чтобы открыть калькулятор.",
        })


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        self.send_response(200)
        self.end_headers()
        try:
            update = json.loads(body)
            handle_update(update)
        except Exception as e:
            log.error(f"Error: {e}")

    def log_message(self, format, *args):
        pass  # Suppress default logging


def setup_bot():
    """Set menu button and commands."""
    # Set Web App as menu button
    api("setChatMenuButton", {
        "menu_button": {
            "type": "web_app",
            "text": "📊 Калькулятор",
            "web_app": {"url": WEBAPP_URL}
        }
    })
    # Set commands
    api("setMyCommands", {
        "commands": [
            {"command": "start", "description": "Запустить калькулятор услуг"}
        ]
    })
    log.info("Bot menu button and commands configured.")


def run_polling():
    """Simple long-polling mode (no webhook needed)."""
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
