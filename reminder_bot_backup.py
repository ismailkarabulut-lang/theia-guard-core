import json
import os
import re
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

REMINDERS_FILE = Path("reminders.json")
COGNITIVE_LOG_FILE = Path("cognitive_log.json")

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

def api_call(token, method, data=None):
    url = "https://api.telegram.org/bot" + token + "/" + method
    if data:
        resp = requests.post(url, json=data, timeout=10)
    else:
        resp = requests.get(url, timeout=10)
    return resp.json()

def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return []
    return []

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def normalize(text):
    text = text.lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = text.replace("ç", "c").replace("Ç", "c")
    text = text.replace("ş", "s").replace("Ş", "s")
    text = text.replace("ğ", "g").replace("Ğ", "g")
    text = text.replace("ö", "o").replace("Ö", "o")
    text = text.replace("ü", "u").replace("Ü", "u")
    return text

def find_similar_topics(log, new_topic):
    new_words = set(normalize(new_topic).split())
    matches = []
    for entry in log:
        existing_words = set(normalize(entry["topic"]).split())
        if len(new_words) > 0 and len(existing_words) > 0:
            overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
            if overlap > 0.4:
                matches.append(entry)
    return matches

def process_cognitive_log(token, chat_id, text):
    content = text[4:].strip()
    if not content:
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Format: !log konu #heyecan 5"})
        return

    emotion = "notr"
    intensity = 3
    topic = content

    # His etiketi bul
    emotions = ["heyecan", "merak", "kaygi", "ofke", "sevinc", "uzgu", "rahatlama", "notr = "#" + emo
        if tag in normalize(topic):
            emotion = emo
            topic = topic.replace(tag, "").replace("#" + emo, "").strip()
            break

    # Sayı"]
    for emo in emotions:
        tag etiketi bul
    m = re.search(r"#(\d)", content)
    if m:
        intensity = int(m.group(1))
        if intensity < 1: intensity = 1
        if intensity > 5: intensity = 5
        topic = re.sub(r"#\d", "", topic).strip()

    topic = re.sub(r"\s+", " ", topic).strip(" -–—,;:.")
    if not topic:
        topic = "Genel"

    log = load_json(COGNITIVE_LOG_FILE)
    similar = find_similar_topics(log, topic)
    count = len(similar) + 1

    entry = {
        "id": len(log) + 1,
        "chat_id": int(chat_id),
        "topic": topic,
        "emotion": emotion,
        "intensity": intensity,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action_taken": False
    }
    log.append(entry)
    save_json(COGNITIVE_LOG_FILE, log)

    msg = "Kaydedildi\n"
    msg += "Konu: " + topic + "\n"
    msg += "His: " + emotion + " (" + str(intensity) + "/5)\n"
    msg += "Zaman: " + entry["timestamp"][:16]

    if len(similar) >= 1:
        prev = similar[-1]
        msg += "\n\nBu konu " + str(count) + ". kez gundeme geldi\n"
        msg += "Onceki: " + prev["emotion"] + " (" + str(prev["intensity"]) + ")\n"
        msg += "Simdi: " + emotion + " (" + str(intensity) + ")\n"
        if intensity < prev["intensity"]:
            msg += "Enerji duseyor\n"

        if count >= 3:
            no_action = all(not e.get("action_taken", False) for e in similar)
            if no_action:
                first = similar[0]
                msg += "\nTERSINE HAFIZA UYARISI\n"
                msg += '"' + topic + '" konusu ' + str(count) + " kez gundeme geldi\n"
                msg += "ama aksiyona donusmedi\n"
                msg += "Ilk: " + first["timestamp"][:10] + " " + first["emotion"] + " (" + str(first["intensity"]) + ")\n"
                msg += "Son: " + entry["timestamp"][:10] + " " + emotion + " (" + str(intensity) + ")\n"
                msg += "\nYa harekete gec ya birak"

    api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": msg})

def process_weekly_summary(token, chat_id):
    log = load_json(COGNITIVE_LOG_FILE)
    now = datetime.now()
    week_ago = now - timedelta(days=7)

    weekly = []
    for entry in log:
        try:
            t = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
            if t >= week_ago:
                weekly.append(entry)
        except:
            pass

    if not weekly:
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Bu hafta hic kayit yok"})
        return

    topics = {}
    for e in weekly:
        t = e["topic"]
        if t not in topics:
            topics[t] = []
        topics[t].append(e)

    emotion_counts = {}
    for e in weekly:
        emo = e["emotion"]
        if emo not in emotion_counts:
            emotion_counts[emo] = 0
        emotion_counts[emo] += 1

    dominant = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)

    reverses = []
    for topic_name, entries in topics.items():
        if len(entries) >= 2:
            action_taken = any(e.get("action_taken", False) for e in entries)
            if not action_taken:
                reverses.append((topic_name, len(entries)))

    decisions = sum(1 for e in weekly if e.get("action_taken", False))
    total = len(weekly)

    msg = "HAFTALIK BILISEL OZET\n"
    msg += week_ago.strftime("%d.%m") + " - " + now.strftime("%d.%m.%Y") + "\n"
    msg += "=" * 30 + "\n\n"

    msg += "Aktif Konular:\n"
    for topic_name, entries in topics.items():
        intensities = [e["intensity"] for e in entries]
        trend = ""
        if len(intensities) >= 2:
            if intensities[-1] < intensities[0]:
                trend = " (enerji dusuyor)"
            elif intensities[-1] > intensities[0]:
                trend = " (enerji artiyor)"
        msg += "  - " + topic_name + " (" + str(len(entries)) + " kayit)" + trend + "\n"

    msg += "\nDuygusal Pattern:\n"
    for emo, count in dominant:
        msg += "  " + emo + ": " + str(count) + "\n"

    if reverses:
        msg += "\nTERSINE HAFIZA:\n"
        for topic_name, count in reverses:
            msg += "  - " + topic_name + " - " + str(count) + " kez aksiyon yok\n"

    msg += "\nSinyal/Gurultu:\n"
    msg += "  Kayit: " + str(total) + "\n"
    msg += "  Karar: " + str(decisions) + "\n"
    noise = total - decisions
    msg += "  Gurultu: " + str(noise) + "\n"
    if total > 0:
        ratio = int((decisions / total) * 100)
        msg += "  Karar orani: %" + str(ratio) + "\n"
        if ratio < 30:
            msg += "\nKarar orani dusuk - daha cok uret daha az dusun"

    api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": msg})

def process_action_mark(token, chat_id, text):
    topic = text[7:].strip()
    if not topic:
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Format: !action konu adi"})
        return

    log = load_json(COGNITIVE_LOG_FILE)
    updated = 0
    for entry in log:
        if normalize(entry["topic"]) == normalize(topic):
            entry["action_taken"] = True
            updated += 1

    if updated > 0:
        save_json(COGNITIVE_LOG_FILE, log)
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": '"' + topic + '" icin ' + str(updated) + " kayit aksiyonlandi"})
    else:
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": '"' + topic + '" bulunamadi'})

def parse_natural_time(text):
    text = normalize(text)
    now = datetime.now()
    target = None
    task = text

    gunler = {"pazartesi": 0, "sali": 1, "carsamba": 2, "persembe": 3, "cuma": 4, "cumartesi": 5, "pazar": 6}

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

    if "yarin" in text:
        target = now + timedelta(days=1)
        task = text.replace("yarin", "").strip()
    elif "bugun" in text:
        target = now
        task = text.replace("bugun", "").strip()
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
            if "sabah" in text:
                target = target.replace(hour=9, minute=0, second=0)
            elif "ogle" in text:
                target = target.replace(hour=12, minute=0, second=0)
            elif "aksam" in text:
                target = target.replace(hour=20, minute=0, second=0)
            else:
                target = target.replace(hour=9, minute=0, second=0)

    task = re.sub(r"saat\s*\d{1,2}[.:]?\d{0,2}", "", task)
    task = re.sub(r"sabah|ogle|aksam", "", task)
    task = re.sub(r"hatirlat", "", task)
    task = task.strip(" -–—,;:.")
    if not task:
        task = "Hatirlatma"

    return target, task

def add_reminder(chat_id, text):
    target_time, task = parse_natural_time(text)
    if target_time is None:
        return None, "Zaman algilanamadi. Ornek: yarin saat 14 toplanti hatirlat"
    if target_time < datetime.now():
        return None, "Gecmis bir zamana hatirlatici eklenemez"

    reminders = load_json(REMINDERS_FILE)
    reminder = {
        "id": len(reminders) + 1,
        "chat_id": int(chat_id),
        "task": task,
        "datetime": target_time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    reminders.append(reminder)
    save_json(REMINDERS_FILE, reminders)
    formatted_time = target_time.strftime("%d %B %H:%M")
    return reminder, formatted_time

def check_and_send_reminders(token):
    reminders = load_json(REMINDERS_FILE)
    now = datetime.now()
    updated = False
    for r in reminders:
        if r["status"] != "active":
            continue
        r_time = datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
        if now >= r_time:
            msg = "HATIRLATICI\n" + "=" * 25 + "\n"
            msg += r["task"] + "\n"
            msg += "\nZaman: " + r_time.strftime("%d.%m.%Y %H:%M")
            api_call(token, "sendMessage", {"chat_id": r["chat_id"], "text": msg})
            r["status"] = "sent"
            updated = True
    if updated:
        save_json(REMINDERS_FILE, reminders)

def list_reminders(chat_id):
    reminders = load_json(REMINDERS_FILE)
    active = [r for r in reminders if r["status"] == "active" and r["chat_id"] == int(chat_id)]
    if not active:
        return "Aktif hatirlatici yok"
    msg = "Aktif Hatirlaticilar\n" + "=" * 25 + "\n"
    for r in active:
        r_time = datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S")
        msg += "#" + str(r["id"]) + " - " + r["task"] + "\n"
        msg += "   " + r_time.strftime("%d.%m.%Y %H:%M") + "\n\n"
    return msg

, reminders)
           def delete_reminder(reminder_id):
    reminders = load_json(REMINDERS_FILE)
    for r in reminders:
        if r["id"] == reminder_id and r["status"] == "active":
            r["status"] = "deleted"
 return True
    return False

def handle_message(token, update):
    message = update.get("message", {})
    raw_text = message.get("text", "")
    text = raw_text.strip()
    chat_id = str(message["chat"]["id"])

    if not text:
        return

    text_lower = text.lower()

    if text_lower == "/start" or text_lower == "/help":
        help_msg = "THEIA Protokolu\n" + "=" * 25 + "\n\n"
        help_msg += "HATIRLATICI:\n"
        help_msg += "  yarin saat 14 toplanti hatirlat\n"
        help_msg += "  2 saat sonra su ic\n\n"
        help_msg += "BILISEL KAYIT:\n"
        help_msg += "  !log yeni fikrim var #heyecan 5\n"
        help_msg += "  !weekly - haftalik ozet\n"
        help_msg += "  !action konu adi - aksiyon\n\n"
        help_msg += "HISLER: heyecan merak kaygi ofke sevinc uzgu rahatlama notr\n\n"
        help_msg += "KOMUTLAR:\n"
        help_msg += "  /list - hatirlaticilari goster\n"
        help_msg += "  /delete ID - hatirlatici sil"
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": help_msg})
        return

    if text_lower == "/list":
        msg = list_reminders(chat_id)
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": msg})
        return

    if text_lower.startswith("/delete"):
        parts = text.split()
        if len(parts) > 1:
            try:
                rid = int(parts[1])
                if delete_reminder(rid):
                    api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Silindi #" + str(rid)})
                else:
                    api_call(token, "sendMessage", {"chat_id": int            save_json(REMINDERS_FILE(chat_id), "text": "Bulunamadi"})
            except:
                api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": "Gecersiz ID"})
        return

    if text_lower.startswith("!log"):
        process_cognitive_log(token, chat_id, text)
        return

    if text_lower.startswith("!weekly"):
        process_weekly_summary(token, chat_id)
        return

    if text_lower.startswith("!action"):
        process_action_mark(token, chat_id, text)
        return

    # Hatirlatıcı olarak işle
    reminder, info = add_reminder(chat_id, text)
    if reminder:
        msg = "Hatirlatici eklendi\n"
        msg += "Gorev: " + reminder["task"] + "\n"
        msg += "Zaman: " + info
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": msg})
    else:
        api_call(token, "sendMessage", {"chat_id": int(chat_id), "text": info})

def main():
    token, chat_id = get_env()
    if not token:
        print("HATA: TELEGRAM_BOT_TOKEN bulunamadi!")
        return
    print("THEIA Protokolu Bot aktif!")
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
            check_and_send_reminders(token)
        except Exception as e:
            print("Hata: " + str(e))
        time.sleep(2)

if __name__ == "__main__":
    main()
