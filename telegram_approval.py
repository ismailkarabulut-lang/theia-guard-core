import json
import os
import time
from datetime import datetime
import requests
from pathlib import Path

# Karargah Dizin Ayarları
BASE_DIR = Path.home() / "Masaüstü" / "theia-guard-core"
APPROVAL_FILE = BASE_DIR / "pending_approval.json"
REMINDERS_FILE = BASE_DIR / "reminders.json"
NOTES_FILE = BASE_DIR / "notes.json"

def load_json(file_path):
    if file_path.exists():
        try:
            return json.loads(file_path.read_text())
        except:
            return None
    return None

def save_json(file_path, data):
    file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def get_env():
    env_path = BASE_DIR / ".env"
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
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        resp = requests.post(url, json=data, timeout=10) if data else requests.get(url, timeout=10)
        return resp.json()
    except:
        return {}

# --- YENİ YETENEK: TELEGRAM'DAN GELEN MESAJI DİNLE ---
def handle_incoming_message(token, update, chat_id):
    message = update.get("message", {})
    text = message.get("text", "")
    sender_chat_id = str(message.get("chat", {}).get("id", ""))

    if text.startswith("/not "):
        note_content = text.replace("/not ", "").strip()
        notes = load_json(NOTES_FILE) or []
        new_note = {
            "id": len(notes) + 1,
            "text": note_content,
            "timestamp": datetime.now().isoformat()
        }
        notes.append(new_note)
        save_json(NOTES_FILE, notes)
        api_call(token, "sendMessage", {"chat_id": sender_chat_id, "text": "✅ Not THEIA hafızasına işlendi Kaptan."})

    elif text == "/start":
        api_call(token, "sendMessage", {"chat_id": sender_chat_id, "text": f"🚀 THEIA Guard Core Aktif!\nChat ID: {sender_chat_id}\n\nKomutlar:\n/not [mesaj] - Hafızaya not ekler."})

# --- HATIRLATICI VE ONAY SİSTEMİ ---
def check_reminders(token, chat_id):
    if not chat_id: return
    reminders = load_json(REMINDERS_FILE) or []
    updated = False
    now = datetime.now()
    for r in reminders:
        if r.get("status") == "active":
            try:
                r_time = datetime.fromisoformat(r["timestamp"])
                if now >= r_time:
                    msg = f"🔔 **THEIA HATIRLATICI**\n{'-'*20}\n{r.get('text', 'İçerik yok')}"
                    api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": msg, "parse_mode": "Markdown"})
                    r["status"] = "notified"
                    updated = True
            except: continue
    if updated: save_json(REMINDERS_FILE, reminders)

def handle_callback(token, update):
    callback = update.get("callback_query", {})
    if not callback: return
    data, msg = callback.get("data", ""), callback.get("message", {})
    approval = load_json(APPROVAL_FILE)
    if approval and approval.get("status") == "sent":
        res = "APPROVED" if data == "approve" else "DENIED"
        icon = "✅ ONAYLANDI" if data == "approve" else "❌ REDDEDİLDİ"
        approval["status"] = res
        save_json(APPROVAL_FILE, approval)
        api_call(token, "editMessageText", {"chat_id": msg["chat"]["id"], "message_id": msg["message_id"], "text": f"{msg['text']}\n\n{icon}"})

def send_approval_request(token, chat_id):
    approval = load_json(APPROVAL_FILE)
    if not approval or approval.get("status") != "pending": return
    text = f"🛡️ **THEIA GUARD ONAY**\nKomut: `{approval.get('command')}`\nRisk: {approval.get('risk_level')}"
    kb = {"inline_keyboard": [[{"text": "Onay ✅", "callback_data": "approve"},{"text": "Red ✅", "callback_data": "deny"}]]}
    if api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": text, "reply_markup": kb, "parse_mode": "Markdown"}).get("ok"):
        approval["status"] = "sent"
        save_json(APPROVAL_FILE, approval)

def bot_loop():
    token, chat_id = get_env()
    print("🚀 THEIA Guard Core Aktif! Dinleme moduna geçildi...")
    offset = 0
    while True:
        try:
            updates = api_call(token, "getUpdates", {"offset": offset, "timeout": 5}).get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update: handle_incoming_message(token, update, chat_id)
                if "callback_query" in update: handle_callback(token, update)
            if chat_id:
                send_approval_request(token, chat_id)
                check_reminders(token, chat_id)
        except: pass
        time.sleep(2)

if __name__ == "__main__":
    bot_loop()
