content = open('reminder_bot.py').read()
old = ' msg=update.get("message",{});raw=str(msg["chat"]["id"])\n if not text:return\n tl=n(text)'
new = ' msg=update.get("message",{})\n text=msg.get("text","").strip()\n cid=str(msg["chat"]["id"])\n if not text:return\n tl=n(text)'
if old in content:
    content = content.replace(old, new)
    open('reminder_bot.py', 'w').write(content)
    print("Tamam")
else:
    print("NOT FOUND")
