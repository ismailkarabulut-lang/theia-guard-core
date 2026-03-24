import json
import os
import time
import threading
import requests
from pathlib import Path

APPROVAL_FILE = Path("pending_approval.json")

def load_approval():
    if APPROVAL_FILE.exists():
        try:
            return json.loads(APPROVAL_FILE.read_text())
        except:
            return None
    return None

def save_approval(data):
    APPROVAL_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def get_env():
    env_path = Path(".env")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("TELEGRAM_CHAT_ID="):
                chat_id = line.split("=", 1)[1].strip()
    return token, chat_id

def api_call(token, method, data=None):
    url = "https://api.telegram.org/bot" + token + "/" + method
    if data:
        resp = requests.post(url, json=data, timeout=10)
    else:
        resp = requests.get(url, timeout=10)
    return resp.json()

def handle_start(token, update):
    message = update.get("message", {})
    text = message.get("text", "")
    if text == "/start":
        chat_id = str(message["chat"]["id"])
        env_path = Path(".env")
        lines = []
        if env_path.exists():
            lines = env_path.read_text().splitlines()
        found = False
        new_lines = []
        for line in lines:
            if line.startswith("TELEGRAM_CHAT_ID="):
                new_lines.append("TELEGRAM_CHAT_ID=" + chat_id)
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append("TELEGRAM_CHAT_ID=" + chat_id)
        env_path.write_text("\n".join(new_lines) + "\n")
        api_call(token, "sendMessage", {
            "chat_id": int(chat_id),
            "text": "THEIA Guard baglandi!\nChat ID: " + chat_id
        })
        return chat_id
    return None

def handle_callback(token, update):
    callback = update.get("callback_query", {})
    if not callback:
        return
    data = callback.get("data", "")
    callback_id = callback.get("id", "")
    message = callback.get("message", {})
    message_id = message.get("message_id", 0)
    chat_id = message.get("chat", {}).get("id", 0)
    approval = load_approval()
    if approval and approval.get("status") == "sent":
        if data == "approve":
            approval["status"] = "approved"
            icon = "ONAYLANDI"
        else:
            approval["status"] = "denied"
            icon = "REDDEDILDI"
        save_approval(approval)
        old_text = message.get("text", "")
        api_call(token, "editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": old_text + "\n\n" + icon
        })
        api_call(token, "answerCallbackQuery", {
            "callback_query_id": callback_id,
            "text": icon
        })
    else:
        api_call(token, "answerCallbackQuery", {
            "callback_query_id": callback_id,
            "text": "Bu istek zaten islenmis."
        })

def send_approval_request(token, chat_id):
    approval = load_approval()
    if not approval or approval.get("status") != "pending":
        return False
    risk = approval.get("risk_level", "unknown")
    command = approval.get("command", "unknown")
    risk_labels = {"medium": "SARI - Orta Risk", "high": "KIRMIZI - Yuksek Risk"}
    label = risk_labels.get(risk, "Risk: " + risk.upper())
    text = "THEIA GUARD ONAY TALEBI\n" + "=" * 30 + "\n"
    text += "Risk: " + label + "\n"
    text += "Komut: " + command + "\n"
    text += "\nBu komutu onayliyor musunuz?"
    keyboard = {"inline_keyboard": [[
        {"text": "Onayla", "callback_data": "approve"},
        {"text": "Reddet", "callback_data": "deny"}
    ]]}
    result = api_call(token, "sendMessage", {
        "chat_id": int(chat_id),
        "text": text,
        "reply_markup": keyboard
    })
    if result.get("ok"):
        approval["status"] = "sent"
        save_approval(approval)
        return True
    return False

def bot_loop():
    token, chat_id = get_env()
    if not token:
        print("HATA: TELEGRAM_BOT_TOKEN bulunamadi!")
        return
    print("THEIA Guard Telegram Bot aktif!")
    print("Chat ID: " + (chat_id if chat_id else "Henuz baglanmadi - Telegramda /start yazin"))
    print("")
    offset = 0
    while True:
        try:
            result = api_call(token, "getUpdates", {"offset": offset, "timeout": 5})
            updates = result.get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    new_chat = handle_start(token, update)
                    if new_chat:
                        chat_id = new_chat
                if "callback_query" in update:
                    handle_callback(token, update)
            if chat_id:
                send_approval_request(token, chat_id)
        except Exception as e:
            print("Bot hatasi: " + str(e))
        time.sleep(1)

def main():
    bot_loop()

if __name__ == "__main__":
    main()
