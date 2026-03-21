import json
import os
import re
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

REMINDERS_FILE = Path("reminders.json")

def get_env():
    env_path = Path(".env")
    token = ""
    chat_id = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("TELEGRAM_CHAT_ID="):
                chat_id = line.split("=", 1)[1].strip()
    return token, chat_id

def load_reminders():
    if REMINDERS_FILE.exists():
        try:
            return json.loads(REMINDERS_FILE.read_text())
        except:
            return []
    return []

def save_reminders(reminders):
    REMINDERS_FILE.write_text(json.dumps(reminders, indent=2, ensure_ascii=False))

def api_call(token, method, data=None):
    url = "https://api.telegram.org/bot" + token + "/" + method
    if data:
        resp = requests.post(url, json=data, timeout=10)
    else:
        resp = requests.get(url, timeout=10)
    return resp.json()

def parse_natural_time(text):
    text = text.lower().strip()
    now = datetime.now()
    target = None
    task = text

    gunler = {
        "pazartesi": 0, "sal": 1, "carsamba": 2, "çarşamba": 2,
        "persembe": 3, "perşembe": 3, "cuma": 4,
        "cumartesi": 5, "pazar": 6
    }

    # "2 saat sonra" / "30 dakika sonra"
    m = re.search(r"(\d+)\s*(saat|dakika|dk)\s*(sonra)", text)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        if unit == "saat":
            target = now + timedelta(hours=amount)
        else:
            target = now + timedelta(minutes=amount)
        task = re.sub(r"\d+\s*(saat|dakika|dk)\s*sonra", "", text).strip()
        return target, task

    # "yarın"
    if "yarın" in text or "yarin" in text:
        target = now + timedelta(days=1)
        task = text.replace("yarın", "").replace("yarin", "").strip()

    # "bugün"
    elif "bugün" in text or "bugun" in text:
        target = now
        task = text.replace("bugün", "").replace("bugun", "").strip()

    # Gün isimleri
    else:
        for gun_adi, gun_index in gunler.items():
            if gun_adi in text:
                days_ahead = (gun_index - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target = now + timedelta(days=days_ahead)
                task = text.replace(gun_adi, "").strip()
                break

    if target is None:
        # Tarih formatı: 25.03.2026 veya 25/03
        m = re.search(r"(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?", text)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else now.year
            try:
                target = datetime(year, month, day)
                task = re.sub(r"\d{1,2}[./]\d{1,2}(?:[./]\d{4})?", "", text).strip()
            except:
                pass

    if target is None:
        return None, text

    # Saat bul
    m = re.search(r"(\d{1,2})[.:](\d{2})", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        target = target.replace(hour=hour, minute=minute, second=0)
    else:
        m = re.search(r"saat\s*(\d{1,2})", text)
        if m:
            hour = int(m.group(1))
            target = target.replace(hour=hour, minute=0, second=0)
        else:
            # Sabah/öğle/akşam
            if "sabah" in text:
                target = target.replace(hour=9, minute=0, second=0)
            elif "öğle" in text or "ogle" in text:
                target = target.replace(hour=12, minute=0, second=0)
            elif "akşam" in text or "aksam" in text:
                target = target.replace(hour=20, minute=0, second=0)
            else:
                target = target.replace(hour=9, minute=0, second=0)

    # Temizle
    task = re.sub(r"saat\s*\d{1,2}[.:]?\d{0,2}", "", task)
    task = re.sub(r"sabah|öğle|akşam|ogle|aksam", "", task)
    task = re.sub(r"hatırlat|hatirlat|hatırlatma|hatirlatma", "", task)
    task = re.sub(r"^\s*ve\s+|\s+ve\s*$", "", task)
    task = task.strip(" -–—,;:.")

    if not task:
        task = "Hatırlatma"

    return target, task

def add_reminder(chat_id, text):
    target_time, task = parse_natural_time(text)
    if target_time is None:
        return None, "Zaman algılanamadı. Örnek: 'yarın saat 14'te toplantı hatırlat'"

    if target_time < datetime.now():
        return None, "Geçmiş bir zamana hatırlatıcı eklenemez."

    reminders = load_reminders()
    reminder = {
        "id": len(reminders) + 1,
        "chat_id": int(chat_id),
        "task": task,
        "datetime": target_time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    reminders.append(reminder)
    save_reminders(reminders)

    formatted_time = target_time.strftime("%d %B %H:%M")
    return reminder, formatted_time

def check_and_send_reminders(token):
    reminders = load_reminders()
    now = datetime.now()
    updated = False

    for r in reminders:
        if r["status"] != "active":
            continue
        r_time = datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
        if now >= r_time:
            msg = "\u23f0 HATIRLATICI\n" + "=" * 25 + "\n"
            msg += r["task"] + "\n"
            msg += "\nZaman: " + r_time.strftime("%d.%m.%Y %H:%M")
            api_call(token, "sendMessage", {
                "chat_id": r["chat_id"],
                "text": msg
            })
            r["status"] = "sent"
            updated = True

    if updated:
        save_reminders(reminders)

def list_reminders(chat_id):
    reminders = load_reminders()
    active = [r for r in reminders if r["status"] == "active" and r["chat_id"] == int(chat_id)]
    if not active:
        return "Aktif hatırlatıcı yok."
    msg = "Aktif Hatırlatıcılar\n" + "=" * 25 + "\n"
    for r in active:
        r_time = datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
        msg += "#" + str(r["id"]) + " - " + r["task"] + "\n"
        msg += "   " + r_time.strftime("%d.%m.%Y %H:%M") + "\n\n"
    return msg

def delete_reminder(reminder_id):
    reminders = load_reminders()
    for r in reminders:
        if r["id"] == reminder_id and r["status"] == "active":
            r["status"] = "deleted"
            save_reminders(reminders)
            return True
    return False

def handle_message(token, update):
    message = update.get("message", {})
    text = message.get("text", "").strip()
    chat_id = str(message["chat"]["id"])

    if not text:
        return

    if text == "/start" or text == "/help":
        help_msg = "THEIA Hatırlatıcı\n" + "=" * 25 + "\n\n"
        help_msg += "Doğal dil ile hatırlatıcı ekle:\n"
        help_msg += "  'yarın saat 14'te toplantı hatırlat'\n"
        help_msg += "  '2 saat sonra su iç'\n"
        help_msg += "  'pazartesi 10:00 standup'\n"
        help_msg += "  'bugün akşam 8'de Netflix'\n\n"
        help_msg += "Komutlar:\n"
        help_msg += "  /list - Tüm hatırlatıcıları göster\n"
        help_msg += "  /delete ID - Hatırlatıcı sil\n"
        help_msg += "  /help - Bu mesaj"
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": help_msg})
        return

    if text == "/list":
        msg = list_reminders(chat_id)
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": msg})
        return

    if text.startswith("/delete"):
        parts = text.split()
        if len(parts) > 1:
            try:
                rid = int(parts[1])
                if delete_reminder(rid):
                    api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Hatırlatıcı #" + str(rid) + " silindi."})
                else:
                    api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Hatırlatıcı bulunamadı."})
            except:
                api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Geçersiz ID. /list ile kontrol et."})
        return

    # Normal mesaj - hatırlatıcı olarak işle
    reminder, info = add_reminder(chat_id, text)
    if reminder:
        msg = "Hatırlatıcı eklendi!\n"
        msg += "Görev: " + reminder["task"] + "\n"
        msg += "Zaman: " + info
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": msg})
    else:
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": info})

def main():
    token, chat_id = get_env()
    if not token:
        print("HATA: TELEGRAM_BOT_TOKEN bulunamadi!")
        return
    print("THEIA Hatilatici Bot aktif!")
    print("Chat ID: " + (chat_id if chat_id else "Henuz baglanmadi"))

    offset = 0
    while True:
        try:
            result = api_call(token, "getUpdates", {"offset": offset, "timeout": 5})
            updates = result.get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(token, update)

            # Zamanı gelen hatırlatıcıları gönder
            check_and_send_reminders(token)

        except Exception as e:
            print("Hata: " + str(e))
        time.sleep(2)

if __name__ == "__main__":
    main()
