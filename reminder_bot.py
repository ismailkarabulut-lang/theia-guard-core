import json,re,time,requests
from datetime import datetime,timedelta
from pathlib import Path
RF=Path("reminders.json")
CL=Path("cognitive_log.json")
def ge():
 e=Path(".env");t="";c=""
 if e.exists():
  for l in e.read_text().splitlines():
   if l.startswith("TELEGRAM_BOT_TOKEN="):t=l.split("=",1)[1].strip()
   elif l.startswith("TELEGRAM_CHAT_ID="):c=l.split("=",1)[1].strip()
 return t,c
def ac(t,m,d=None):
 u="https://api.telegram.org/bot"+t+"/"+m
 if d:return requests.post(u,json=d,timeout=10).json()
 return requests.get(u,timeout=10).json()
def lj(p):
 if p.exists():
  try:return json.loads(p.read_text())
  except:return []
 return []
def sj(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False))
def n(t):
 t=t.lower()
 for a,b in[("\u0131","i"),("\u0130","i"),("\u00e7","c"),("\u00c7","c"),("\u015f","s"),("\u015e","s"),("\u011f","g"),("\u011e","g"),("\u00f6","o"),("\u00d6","o"),("\u00fc","u"),("\u00dc","u")]:t=t.replace(a,b)
 return t
def fs(log,nt):
 nw=set(n(nt).split());m=[]
 for e in log:
  ew=set(n(e["topic"]).split())
  if nw and ew and len(nw&ew)/max(len(nw),len(ew))>0.4:m.append(e)
 return m
def dl(tc,cid,text):
 content=text[4:].strip()
 if not content:ac(tc,"sendMessage",{"chat_id":int(cid),"text":"Format: !log konu #heyecan 5"});return
 emo="notr";inten=3;topic=content
 for e in ["heyecan","merak","kaygi","ofke","sevinc","uzgu","rahatlama","notr"]:
  tg="#"+e
  if tg in n(topic):
   emo=e;idx=n(topic).find(tg);ot=topic[idx:idx+len(tg)];topic=topic.replace(ot,"").strip();break
 m=re.search(r"#(\d)",content)
 if m:inten=max(1,min(5,int(m.group(1))));topic=re.sub(r"#\d","",topic).strip()
 topic=re.sub(r"\s+"," ",topic).strip(" -\u2013\u2014,;:.")
 if not topic:topic="Genel"
 log=lj(CL);sim=fs(log,topic);cnt=len(sim)+1
 entry={"id":len(log)+1,"chat_id":int(cid),"topic":topic,"emotion":emo,"intensity":inten,"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"action_taken":False}
 log.append(entry);sj(CL,log)
 msg="Kaydedildi\nKonu: "+topic+"\nHis: "+emo+" ("+str(inten)+"/5)\nZaman: "+entry["timestamp"][:16]
 if len(sim)>=1:
  prev=sim[-1];msg+="\n\nBu konu "+str(cnt)+". kez gundeme geldi\nOnceki: "+prev["emotion"]+" ("+str(prev["intensity"])+")\nSimdi: "+emo+" ("+str(inten)+")"
  if inten<prev["intensity"]:msg+="\nEnerji duseyor"
  if cnt>=3 and all(not e.get("action_taken",False) for e in sim):msg+="\n\nTERSINE HAFIZA UYARISI\n"+topic+" konusu "+str(cnt)+" kez gundeme geldi\nama aksiyona donusmedi\nYa harekete gec ya birak"
 ac(tc,"sendMessage",{"chat_id":int(cid),"text":msg})
def dw(tc,cid):
 log=lj(CL);now=datetime.now();wk=now-timedelta(days=7);weekly=[]
 for e in log:
  try:
   if datetime.strptime(e["timestamp"],"%Y-%m-%d %H:%M:%S")>=wk:weekly.append(e)
  except:pass
 if not weekly:ac(tc,"sendMessage",{"chat_id":int(cid),"text":"Bu hafta hic kayit yok"});return
 topics={}
 for e in weekly:
  t=e["topic"]
  if t not in topics:topics[t]=[]
  topics[t].append(e)
 ec={}
 for e in weekly:
  em=e["emotion"]
  if em not in ec:ec[em]=0
  ec[em]+=1
 dom=sorted(ec.items(),key=lambda x:x[1],reverse=True)
 rev=[(tn,len(en)) for tn,en in topics.items() if len(en)>=2 and not any(e.get("action_taken",False) for e in en)]
 dec=sum(1 for e in weekly if e.get("action_taken",False));tot=len(weekly)
 msg="HAFTALIK BILISEL OZET\n"+wk.strftime("%d.%m")+" - "+now.strftime("%d.%m.%Y")+"\n"+"="*30+"\n\nAktif Konular:\n"
 for tn,en in topics.items():
  ints=[e["intensity"] for e in en];tr=""
  if len(ints)>=2:
   if ints[-1]<ints[0]:tr=" (enerji dusuyor)"
   elif ints[-1]>ints[0]:tr=" (enerji artiyor)"
  msg+="  - "+tn+" ("+str(len(en))+" kayit)"+tr+"\n"
 msg+="\nDuygusal Pattern:\n"
 for em,c in dom:msg+="  "+em+": "+str(c)+"\n"
 if rev:
  msg+="\nTERSINE HAFIZA:\n"
  for tn,c in rev:msg+="  - "+tn+" - "+str(c)+" kez aksiyon yok\n"
 msg+="\nSinyal/Gurultu:\n  Kayit: "+str(tot)+"\n  Karar: "+str(dec)+"\n  Gurultu: "+str(tot-dec)
 if tot>0:
  r=int((dec/tot)*100);msg+="\n  Karar orani: %"+str(r)
  if r<30:msg+="\n\nKarar orani dusuk - daha cok uret daha az dusun"
 ac(tc,"sendMessage",{"chat_id":int(cid),"text":msg})
def da(tc,cid,text):
 topic=text[7:].strip()
 if not topic:ac(tc,"sendMessage",{"chat_id":int(cid),"text":"Format: !action konu adi"});return
 log=lj(CL);upd=0
 for e in log:
  if n(e["topic"])==n(topic):e["action_taken"]=True;upd+=1
 if upd>0:sj(CL,log);ac(tc,"sendMessage",{"chat_id":int(cid),"text":topic+" icin "+str(upd)+" kayit aksiyonlandi"})
 else:ac(tc,"sendMessage",{"chat_id":int(cid),"text":topic+" bulunamadi"})
def pt(text):
 text=n(text);now=datetime.now();target=None;task=text
 days={"pazartesi":0,"sali":1,"carsamba":2,"persembe":3,"cuma":4,"cumartesi":5,"pazar":6}
 m=re.search(r"(\d+)\s*(saat|dakika|dk)\s*(sonra)",text)
 if m:
  a2=int(m.group(1));u=m.group(2)
  target=now+(timedelta(hours=a2) if u=="saat" else timedelta(minutes=a2))
  task=re.sub(r"\d+\s*(saat|dakika|dk)\s*sonra","",text).strip()
  return target,task
 if "yarin" in text:target=now+timedelta(days=1);task=text.replace("yarin","").strip()
 elif "bugun" in text:target=now;task=text.replace("bugun","").strip()
 else:
  for ga,gi in days.items():
   if ga in text:
    d=(gi-now.weekday())%7
    if d==0:d=7
    target=now+timedelta(days=d);task=text.replace(ga,"").strip();break
 if target is None:
  m=re.search(r"(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?",text)
  if m:
   try:target=datetime(int(m.group(3) or now.year),int(m.group(2)),int(m.group(1)));task=re.sub(r"\d{1,2}[./]\d{1,2}(?:[./]\d{4})?","",text).strip()
   except:pass
 if target is None:return None,text
 m=re.search(r"(\d{1,2})[.:](\d{2})",text)
 if m:target=target.replace(hour=int(m.group(1)),minute=int(m.group(2)),second=0)
 else:
  m=re.search(r"saat\s*(\d{1,2})",text)
  if m:target=target.replace(hour=int(m.group(1)),minute=0,second=0)
  elif "sabah" in text:target=target.replace(hour=9,minute=0,second=0)
  elif "ogle" in text:target=target.replace(hour=12,minute=0,second=0)
  elif "aksam" in text:target=target.replace(hour=20,minute=0,second=0)
  else:target=target.replace(hour=9,minute=0,second=0)
 task=re.sub(r"saat\s*\d{1,2}[.:]?\d{0,2}","",task)
 task=re.sub(r"sabah|ogle|aksam","",task)
 task=re.sub(r"hatirlat","",task)
 task=task.strip(" -\u2013\u2014,;:.")
 if not task:task="Hatirlatma"
 return target,task
def ar(cid,text):
 tt,task=pt(text)
 if tt is None:return None,"Zaman algilanamadi. Ornek: yarin saat 14 toplanti hatirlat"
 if tt<datetime.now():return None,"Gecmis zamana hatirlatici eklenemez"
 rems=lj(RF)
 r={"id":len(rems)+1,"chat_id":int(cid),"task":task,"datetime":tt.strftime("%Y-%m-%d %H:%M:%S"),"status":"active","created":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
 rems.append(r);sj(RF,rems)
 return r,tt.strftime("%d %B %H:%M")
def cr(tc):
 rems=lj(RF);now=datetime.now();upd=False
 for r in rems:
  if r["status"]!="active":continue
  rt=datetime.strptime(r["datetime"],"%Y-%m-%d %H:%M:%S")
  if now>=rt:
   ac(tc,"sendMessage",{"chat_id":r["chat_id"],"text":"HATIRLATICI\n"+"="*25+"\n"+r["task"]+"\n\nZaman: "+rt.strftime("%d.%m.%Y %H:%M")})
   r["status"]="sent";upd=True
 if upd:sj(RF,rems)
def lr(cid):
 rems=lj(RF);active=[r for r in rems if r["status"]=="active" and r["chat_id"]==int(cid)]
 if not active:return "Aktif hatirlatici yok"
 msg="Aktif Hatirlaticilar\n"+"="*25+"\n"
 for r in active:
  rt=datetime.strptime(r["datetime"],"%Y-%m-%d %H:%M:%S")
  msg+="#"+str(r["id"])+" - "+r["task"]+"\n   "+rt.strftime("%d.%m.%Y %H:%M")+"\n\n"
 return msg
def dr(rid):
 rems=lj(RF)
 for r in rems:
  if r["id"]==rid and r["status"]=="active":r["status"]="deleted";sj(RF,rems);return True
 return False
def hm(tc,update):
 msg=update.get("message",{})
 text=msg.get("text","").strip()
 cid=str(msg["chat"]["id"])
 if not text:return
 tl=n(text)
 if tl in ("/start","/help"):
  h="THEIA Protokolu\n"+"="*25+"\n\nHATIRLATICI:\n  yarin saat 14 toplanti hatirlat\n  2 saat sonra su ic\n\nBILISEL KAYIT:\n  !log yeni fikrim var #heyecan 5\n  !weekly - haftalik ozet\n  !action konu adi\n\nHISLER: heyecan merak kaygi ofke sevinc uzgu rahatlama notr\n\nKOMUTLAR:\n  /list - hatirlaticilari goster\n  /delete ID - hatirlatici sil"
  ac(tc,"sendMessage",{"chat_id":int(cid),"text":h});return
 if tl=="/list":ac(tc,"sendMessage",{"chat_id":int(cid),"text":lr(cid)});return
 if tl.startswith("/delete"):
  p=text.split()
  if len(p)>1:
   try:
    rid=int(p[1])
    if dr(rid):ac(tc,"sendMessage",{"chat_id":int(cid),"text":"Silindi #"+str(rid)})
    else:ac(tc,"sendMessage",{"chat_id":int(cid),"text":"Bulunamadi"})
   except:ac(tc,"sendMessage",{"chat_id":int(cid),"text":"Gecersiz ID"})
  return
 if tl.startswith("!log"):dl(tc,cid,text);return
 if tl.startswith("!weekly"):dw(tc,cid);return
 if tl.startswith("!action"):da(tc,cid,text);return
 r,info=ar(cid,text)
 if r:ac(tc,"sendMessage",{"chat_id":int(cid),"text":"Hatirlatici eklendi\nGorev: "+r["task"]+"\nZaman: "+info})
 else:ac(tc,"sendMessage",{"chat_id":int(cid),"text":info})
def main():
 tc,cid=ge()
 if not tc:print("HATA: TELEGRAM_BOT_TOKEN bulunamadi!");return
 print("THEIA Protokolu Bot aktif!")
 offset=0
 while True:
  try:
   result=ac(tc,"getUpdates",{"offset":offset,"timeout":5})
   for u in result.get("result",[]):
    offset=u["update_id"]+1
    if "message" in u:hm(tc,u)
   cr(tc)
  except Exception as e:print("Hata: "+str(e))
  time.sleep(2)
if __name__=="__main__":main()
