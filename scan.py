import json,os,time,urllib.request
coins=json.load(open("coins.json")); ids=",".join(str(v) for v in coins.values())
key=os.environ.get("CMC_API_KEY","").strip()
def get(url,h={}):
    r=urllib.request.Request(url,headers={"User-Agent":"coin-watch",**h})
    return json.load(urllib.request.urlopen(r,timeout=30))
rows=[]
if key:
    src="CoinMarketCap API"
    d=get(f"https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?id={ids}&convert=USD",{"X-CMC_PRO_API_KEY":key})["data"]
    for i,c in d.items():
        q=c["quote"]["USD"]
        rows.append(dict(id=c["id"],sym=c["symbol"],name=c["name"],slug=c["slug"],rank=c.get("cmc_rank"),price=q["price"],p1h=q["percent_change_1h"],p24h=q["percent_change_24h"],p7d=q["percent_change_7d"],mcap=q["market_cap"],vol=q["volume_24h"],volchg=q.get("volume_change_24h")))
else:
    src="fallback (CMC public data, no API key yet)"
    for c in get(f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/quote/latest?id={ids}&convertId=2781")["data"]:
        q=c["quotes"][0]
        rows.append(dict(id=c["id"],sym=c["symbol"],name=c["name"],slug=c["slug"],rank=c.get("rank"),price=q["price"],p1h=q["percentChange1h"],p24h=q["percentChange24h"],p7d=q["percentChange7d"],mcap=q["marketCap"],vol=q["volume24h"],volchg=None))
now=int(time.time())
try: hist=json.load(open("hist.json"))
except Exception: hist={"snaps":[]}
snaps=[s for s in hist["snaps"] if now-s["t"]<26*3600]
old=min(snaps,key=lambda s:abs(now-s["t"]-86400)) if snaps else None
if old and abs(now-old["t"]-86400)>4*3600: old=None
for r in rows:
    r["vr"]=r["vol"]/r["mcap"] if r["mcap"] else None
    o=old["v"].get(str(r["id"])) if old else None
    if r["volchg"] is None and o and o[0]: r["volchg"]=(r["vol"]/o[0]-1)*100
    r["vr_prev"]=(o[0]/o[1]) if o and o[1] else None
    # boom radar score
    s=0;why=[]
    small=r["mcap"] and r["mcap"]<500e6
    if r["vr"] and r["vr"]>0.15: s+=2;why.append("vol/mcap %.0f%%"%(r["vr"]*100))
    elif r["vr"] and r["vr"]>0.07: s+=1;why.append("vol/mcap %.0f%%"%(r["vr"]*100))
    if r["vr_prev"] and r["vr"] and r["vr"]>1.5*r["vr_prev"]: s+=2;why.append("ratio x%.1f vs 24h"%(r["vr"]/r["vr_prev"]))
    if r["volchg"] and r["volchg"]>50: s+=1;why.append("vol +%.0f%%"%r["volchg"])
    if (r["p1h"] or 0)>1.5: s+=1;why.append("1h up")
    if (r["p24h"] or 0)>5: s+=1;why.append("24h up")
    if (r["p7d"] or 0)>10: s+=1;why.append("7d up")
    if not small: s=max(0,s-2)
    r["boom"]=s;r["why"]=why;r["small"]=bool(small)
snaps.append({"t":now,"v":{str(r["id"]):[r["vol"],r["mcap"]] for r in rows}})
json.dump({"snaps":snaps},open("hist.json","w"))
json.dump({"updated":now,"source":src,"coins":rows},open("data.json","w"),indent=0)
print(src,len(rows))
