"""Best-effort public FC27 catalog updater. Never accesses EA accounts."""
import concurrent.futures
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, robotparser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

BASE="https://fcdata.io"
URL=BASE+"/objectives"
ROOT=Path(__file__).resolve().parent
PATH=ROOT/"catalog.json"
LINK_RE=re.compile(r"^/objectives/(\d+)-[a-z0-9-]+/?$",re.I)
DATE_RE=re.compile(r"(\d{1,2}\s+[A-Za-z]+\s+20\d{2},?\s+\d{1,2}:\d{2})")
STATUS_RE=re.compile(r"\b(Active|Expired|Coming Soon)\s+(Campaigns|Seasonal|Foundations|Mastery|Milestones|Live Events|FC Pro|Evolutions|Other)\b",re.I)
def txt(tag):
    return " ".join(tag.stripped_strings) if tag else ""
def fetch(url):
    req=request.Request(url,headers={"User-Agent":"FC27ObjectiveHub/4.0 (public fan tracker)","Accept":"text/html"})
    with request.urlopen(req,timeout=22) as r:
        if r.status!=200 or "html" not in r.headers.get("Content-Type","").lower():raise ValueError("Source response not HTML 200")
        return r.read(3000000).decode("utf-8","replace")
def expiry(raw):
    m=DATE_RE.search(raw)
    if not m:return ""
    for fmt in ("%d %b %Y %H:%M","%d %B %Y %H:%M"):
        try:return datetime.strptime(m.group(1).replace(",",""),fmt).strftime("%Y-%m-%dT%H:%M")
        except ValueError:pass
    return ""
def category(raw,name):
    if name.lower()=="daily objectives":return "Daily"
    if name.lower() in ("weekly objectives","weekly rush points"):return "Weekly"
    return {"campaigns":"Campaign","seasonal":"Season","foundations":"Foundations","mastery":"Mastery","milestones":"Milestones","live events":"Live Events","fc pro":"FC Pro","evolutions":"Evolutions"}.get(raw.lower(),"Other")
def listing(html):
    s=BeautifulSoup(html,"html.parser")
    reported=re.search(r"\b(\d+)\s+active groups\b",txt(s),re.I)
    seen=set();groups=[]
    for h in s.select("h2"):
        a=next((a for a in h.select("a[href]") if LINK_RE.match(urlparse(urljoin(BASE,a["href"])).path)),None)
        if not a:continue
        url=urljoin(BASE,a["href"]);mid=LINK_RE.match(urlparse(url).path).group(1)
        if mid in seen:continue
        seen.add(mid);name=txt(a).strip()
        card=h.parent
        for parent in h.parents:
            if parent.name in ("html","body"):break
            summary=txt(parent)
            if len(summary)>3500 or len(parent.find_all("h2"))>1:continue
            if "tasks" in summary.lower() and ("Group rewards" in summary or "No fixed expiry" in summary):
                card=parent;break
        content=txt(card)
        m=STATUS_RE.search(content[:210])
        if not m:
            for previous in h.find_all_previous(string=True,limit=45):
                st=str(previous).strip()
                m=STATUS_RE.search(st)
                if m or len(st)>120:break
        if not m or m.group(1).lower()!="active":continue
        hint=re.search(r"\b(\d{1,3})\s+tasks?\b",content,re.I)
        reward=re.search(r"Group rewards\s*(.*?)\s*(?:View tasks and rewards|$)",content,re.I)
        groups.append({"sourceKey":"fcdata:"+mid,"sourceUrl":url,"title":name[:140],"category":category(m.group(2),name),
          "expires":expiry(content),"reward":reward.group(1).strip()[:150] if reward else "",
          "countHint":int(hint.group(1)) if hint else 0,"tasks":[],"detailStatus":"unavailable"})
    return groups,int(reported.group(1)) if reported else None
def infer(name,description):
    full=(name+" "+description).lower()
    modes=[label for word,label in (("squad battles","Squad Battles"),("division rivals","Rivals"),("champions","Champions"),("rush","Rush"),("friendlies","Friendlies"),("live events","Live Events")) if word in full]
    mode=modes[0] if len(set(modes))==1 else "Any"
    metric="custom";target=1
    patterns=[("matches",r"\b(?:play|complete)\s+(\d+)\s+matches?\b"),("wins",r"\bwin\s+(\d+)\s+matches?\b"),("goals",r"\bscore\s+(\d+)\s+goals?\b"),("assists",r"\b(?:record|make)\s+(\d+)\s+assists?\b")]
    for kind,pat in patterns:
        m=re.search(pat,full)
        if m:metric=kind;target=int(m.group(1));break
    if re.search(r"\b(?:in|during)\s+(?:one|1)\s+match\b",full) and ("score" in full or "assist" in full):metric="custom";target=1
    return {"description":name[:180],"metric":metric,"target":max(1,min(1000000,target)),"mode":mode,"rule":description[:180]}
def detail(g):
    soup=BeautifulSoup(fetch(g["sourceUrl"]),"html.parser")
    h1=soup.find("h1")
    if not h1 or txt(h1).casefold()!=g["title"].casefold():raise ValueError("Title mismatch")
    h=next((h for h in soup.select("h2") if txt(h).lower().strip()=="tasks"),None)
    if not h:raise ValueError("No Tasks section")
    tasks=[]
    for tag in h.find_all_next(["h2","h3"]):
        if tag.name=="h2":break
        name=txt(tag)
        if not name or len(name)>180:continue
        desc=""
        for sub in tag.next_elements:
            if getattr(sub,"name",None) in ("h2","h3","h4"):break
            if getattr(sub,"name",None)=="p":desc=txt(sub);break
        tasks.append(infer(name,desc or name))
        if len(tasks)>=100:break
    if not tasks or g["countHint"] and len(tasks)!=g["countHint"]:raise ValueError("Task count mismatch")
    reward=g["reward"]
    rs=next((x for x in soup.select("h2") if txt(x).lower().strip()=="group rewards"),None)
    if rs:
        values=[]
        for child in rs.next_elements:
            if getattr(child,"name",None)=="h2":break
            if getattr(child,"name",None) in ("p","li"):
                t=txt(child)
                if t and t not in values and len(t)<160:values.append(t)
        if values:reward=" · ".join(values[:4])[:150]
    sp=re.search(r"([\d,]+)\s*(?:Season points\s*\(SP\)|\bSP\b)",reward,re.I)
    return {**g,"tasks":tasks,"reward":reward,"sp":int(sp.group(1).replace(",","")) if sp else 0,
      "detailStatus":"complete","notes":"Imported from independent FCData. Confirm all restrictions in game."}
def main():
    robots=robotparser.RobotFileParser();robots.set_url(BASE+"/robots.txt");robots.read()
    if not robots.can_fetch("FC27ObjectiveHub",URL):raise RuntimeError("Source disallows automated access")
    groups,reported=listing(fetch(URL))
    if not groups or (reported and len(groups)<reported*.8):raise RuntimeError("Incomplete active listing; refusing to overwrite catalog")
    groups=groups[:120]; old={}
    if PATH.exists():
        previous=json.loads(PATH.read_text("utf-8"))
        old={g["sourceKey"]:g for g in previous.get("groups",[]) if g.get("tasks")}
    def fetch_one(g):
        try:return detail(g)
        except Exception as exc:
            print("WARN",g["sourceKey"],str(exc)[:100])
            prev=old.get(g["sourceKey"],{})
            if prev.get("tasks"):return {**g,"tasks":prev["tasks"],"sp":prev.get("sp",0),"detailStatus":"cached-previous","notes":"Task details from previous successful refresh. Verify in game."}
            return g
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        enriched=list(pool.map(fetch_one,groups))
    new=sum(g["detailStatus"]=="complete" for g in enriched)
    ready=sum(bool(g["tasks"]) for g in enriched)
    if not ready:raise RuntimeError("No verified task details; refusing to overwrite catalog")
    partial=reported is not None and reported!=len(groups) or ready!=len(groups)
    result={"version":2,"source":"FCData public objective pages","sourceUrl":URL,"updatedAt":datetime.now(timezone.utc).isoformat(),
      "sourceMode":"SCHEDULED STATIC UPDATE","live":False,"totalFound":len(groups),"reportedActive":reported,
      "detailCount":new,"skipped":len(groups)-ready,"coverage":"partial" if partial else "complete",
      "warnings":["Independent catalog; may not match every EA in-game objective.","Scheduled snapshot; manual progress only."],
      "groups":enriched}
    PATH.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n","utf-8")
    print("Updated source groups:",len(groups),"with tasks:",ready,"newly detailed:",new)
if __name__=="__main__":
    try:main()
    except Exception as exc:print("SYNC FAILED:",exc,file=sys.stderr);sys.exit(1)
