"""
╔══════════════════════════════════════════════════════════════════╗
║       🛡️  DEFENCE DEC — YOUTUBE CONTENT INTELLIGENCE BRIEF     ║
║  Upgraded: Viral Score + Media Clips + Multi-Source RSS          ║
║  Zero cost. Pure Python stdlib. Replaces defence_digest_free.py  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import smtplib, urllib.request, xml.etree.ElementTree as ET
import datetime, html, re, time, random, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ╔══════════════════════════════════════════════════════════════╗
# ║                    🔧  YOUR SETTINGS                        ║
# ╚══════════════════════════════════════════════════════════════╝
RECIPIENT_EMAIL = "defencedec@gmail.com"
SENDER_EMAIL    = "defencedec@gmail.com"
GMAIL_APP_PASS  = os.environ.get("GMAIL_APP_PASS", "uscc ugea lcbi zdmj")

# ╔══════════════════════════════════════════════════════════════╗
# ║         🎬  MEDIA CLIP SOURCES (per topic type)             ║
# ╚══════════════════════════════════════════════════════════════╝
# Each topic maps to direct searchable clip sources
MEDIA_SOURCES = {
    "missile": [
        ("DVIDS – Missile Tests",        "https://www.dvidshub.net/search/#q=missile+test&view=grid&type=video"),
        ("Missile Defense Agency YT",    "https://www.youtube.com/@MissileDefenseAgency/videos"),
        ("Raytheon – Missiles",          "https://www.youtube.com/@RaytheonTechnologies/search?query=missile"),
        ("DARPA Hypersonic",             "https://www.youtube.com/@DARPA/search?query=hypersonic"),
        ("Russian MoD Telegram",         "https://t.me/mod_russia"),
    ],
    "naval": [
        ("DVIDS – Naval",                "https://www.dvidshub.net/search/#q=submarine+navy&view=grid&type=video"),
        ("US Navy Official YT",          "https://www.youtube.com/@USNavy/videos"),
        ("Naval News YT",                "https://www.youtube.com/@NavalNews/videos"),
        ("USNI News",                    "https://news.usni.org/category/video"),
        ("HI Sutton – Submarines",       "https://www.youtube.com/@CovertShores/videos"),
    ],
    "aircraft": [
        ("DVIDS – Air Force",            "https://www.dvidshub.net/search/#q=fighter+jet+stealth&view=grid&type=video"),
        ("US Air Force YT",              "https://www.youtube.com/@usairforce/videos"),
        ("Lockheed Martin – F35",        "https://www.youtube.com/@LockheedMartinVideos/search?query=F-35"),
        ("Northrop Grumman – B21",       "https://www.youtube.com/@northropgrumman/search?query=B-21"),
        ("The War Zone Clips",           "https://www.thedrive.com/the-war-zone"),
    ],
    "weapons": [
        ("DVIDS – Weapons Systems",      "https://www.dvidshub.net/search/#q=weapon+system&view=grid&type=video"),
        ("Raytheon Weapons",             "https://www.youtube.com/@RaytheonTechnologies/videos"),
        ("BAE Systems YT",               "https://www.youtube.com/@BAESystems/videos"),
        ("Boeing Defence",               "https://www.youtube.com/@Boeing/search?query=defence"),
        ("WarMonitor Telegram",          "https://t.me/WarMonitor3"),
    ],
    "drone": [
        ("DVIDS – Drones/UAV",           "https://www.dvidshub.net/search/#q=drone+UAV&view=grid&type=video"),
        ("DARPA Drone Programs",         "https://www.youtube.com/@DARPA/search?query=drone"),
        ("Ukraine Drone Footage",        "https://t.me/UkraineNow"),
        ("General Atomics – MQ-9",       "https://www.youtube.com/@GeneralAtomicsAeronautical/videos"),
        ("Oryx Equipment Losses",        "https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html"),
    ],
    "space": [
        ("DVIDS – Space Force",          "https://www.dvidshub.net/search/#q=space+force&view=grid&type=video"),
        ("US Space Force YT",            "https://www.youtube.com/@USSpaceForce/videos"),
        ("Space News",                   "https://spacenews.com/section/military-space/"),
        ("Northrop – Space",             "https://www.youtube.com/@northropgrumman/search?query=space"),
        ("CSIS Missile Threat DB",       "https://missilethreat.csis.org/"),
    ],
    "geopolitical": [
        ("RAND Corporation",             "https://www.rand.org/topics/military-technology.html"),
        ("IISS Military Balance",        "https://www.iiss.org/research/defence-and-military-analysis/"),
        ("SIPRI Arms Data",              "https://www.sipri.org/databases/armstransfers"),
        ("CSIS Analysis",               "https://www.csis.org/programs/international-security-program"),
        ("Breaking Defense",             "https://breakingdefense.com/"),
    ],
}

# ╔══════════════════════════════════════════════════════════════╗
# ║    🔥  VIRAL KEYWORDS — used to score each story            ║
# ╚══════════════════════════════════════════════════════════════╝
VIRAL_KEYWORDS = {
    # Weapon names that historically go viral on defence channels
    "hypersonic":       10, "mach 5":           10, "mach 10":          10,
    "oreshnik":         10, "sarmat":            10, "rs-28":            10,
    "hwasong":          10, "icbm":               9, "slbm":              9,
    "trident":           8, "minuteman":          8, "tomahawk":          8,
    "f-35":              9, "f-22":               9, "b-21":             10,
    "ngad":             10, "gcap":               9, "fcas":              9,
    "nuclear":           9, "warhead":            9, "ballistic":         8,
    "stealth":           8, "drone swarm":       10, "loitering":         8,
    "kamikaze":          9, "shahed":             9, "lancet":            8,
    "submarine":         8, "ssbn":               9, "ssn":               8,
    "carrier killer":   10, "anti-satellite":    10, "asat":             10,
    "directed energy":  10, "laser weapon":      10, "railgun":           9,
    "ew":                7, "electronic warfare": 8, "cyber attack":      8,
    # Trigger words that boost engagement
    "nightmare":        10, "game changer":      10, "revolutionary":     9,
    "first ever":        9, "unprecedented":      9, "secret":            8,
    "leaked":           10, "classified":         9, "revealed":          8,
    "destroyed":         8, "intercepted":        8, "failed":            7,
    "test":              6, "launched":           7, "deployed":          7,
    "vs":                8, "versus":             8, "compared":          7,
    "beats":             8, "outperforms":        8, "dominates":         8,
    # Countries that drive East vs West engagement
    "russia":            7, "china":              7, "usa":               6,
    "nato":              7, "ukraine":            8, "taiwan":            9,
    "iran":              8, "north korea":        9, "india":             7,
    "pakistan":          7, "israel":             8, "pentagon":          6,
}

# ╔══════════════════════════════════════════════════════════════╗
# ║              📡  RSS FEED SOURCES                           ║
# ╚══════════════════════════════════════════════════════════════╝
RSS_FEEDS = [
    # Missiles & Hypersonics
    {
        "tag": "🚀 Missiles & Hypersonics", "color": "#ff4444", "media_key": "missile",
        "url": "https://news.google.com/rss/search?q=missile+hypersonic+ICBM+ballistic&hl=en&gl=US&ceid=US:en",
    },
    # Naval
    {
        "tag": "⚓ Naval & Submarines", "color": "#00aaff", "media_key": "naval",
        "url": "https://news.google.com/rss/search?q=submarine+SSBN+navy+naval+warship&hl=en&gl=US&ceid=US:en",
    },
    # Fighter Jets
    {
        "tag": "✈️ Jets & Stealth Aircraft", "color": "#00d4ff", "media_key": "aircraft",
        "url": "https://news.google.com/rss/search?q=fighter+jet+stealth+F-35+NGAD+air+force&hl=en&gl=US&ceid=US:en",
    },
    # Weapons Systems
    {
        "tag": "🎯 Weapons & Drones", "color": "#ffaa00", "media_key": "weapons",
        "url": "https://news.google.com/rss/search?q=weapon+system+military+drone+loitering+munition&hl=en&gl=US&ceid=US:en",
    },
    # Drone Warfare
    {
        "tag": "🤖 Drone Warfare & AI", "color": "#ff8800", "media_key": "drone",
        "url": "https://news.google.com/rss/search?q=drone+swarm+UAV+autonomous+weapon+AI+military&hl=en&gl=US&ceid=US:en",
    },
    # Space & Cyber
    {
        "tag": "🛰️ Space & Cyber Warfare", "color": "#aa44ff", "media_key": "space",
        "url": "https://news.google.com/rss/search?q=space+warfare+ASAT+cyber+military+satellite&hl=en&gl=US&ceid=US:en",
    },
    # East vs West
    {
        "tag": "⚔️ East vs West", "color": "#ff2266", "media_key": "geopolitical",
        "url": "https://news.google.com/rss/search?q=Russia+China+USA+NATO+military+capability+comparison&hl=en&gl=US&ceid=US:en",
    },
    # Breaking Defence
    {
        "tag": "🌍 Global Defence Intel", "color": "#44ff88", "media_key": "geopolitical",
        "url": "https://news.google.com/rss/search?q=pentagon+defence+ministry+military+contract+billion&hl=en&gl=US&ceid=US:en",
    },
]

# ══════════════════════════════════════════════════════════════
# VIRAL SCORE ENGINE
# ══════════════════════════════════════════════════════════════

def compute_viral_score(title: str, desc: str) -> int:
    """Score a story 0-100 based on viral keyword matches."""
    text = (title + " " + desc).lower()
    score = 0
    matched = []
    for keyword, weight in VIRAL_KEYWORDS.items():
        if keyword in text:
            score += weight
            matched.append(keyword)
    # Bonus: multiple high-value keywords = exponential interest
    if len(matched) >= 4:
        score += 15
    elif len(matched) >= 2:
        score += 8
    return min(score, 100)


def viral_label(score: int) -> tuple:
    """Return (label, color, emoji) based on viral score."""
    if score >= 70:
        return "VIRAL POTENTIAL", "#ff2244", "🔥🔥🔥"
    elif score >= 50:
        return "HIGH INTEREST",   "#ff8800", "🔥🔥"
    elif score >= 30:
        return "WORTH COVERING",  "#ffcc00", "🔥"
    else:
        return "MONITOR",         "#44aa88", "📌"


# ══════════════════════════════════════════════════════════════
# RSS FETCHING
# ══════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_rss(url: str, max_items: int = 6) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read()
        root = ET.fromstring(raw)
        items = root.findall(".//item")
        results = []
        for item in items[:max_items]:
            title = clean_text(item.findtext("title", ""))
            link  = item.findtext("link", "#")
            desc  = clean_text(item.findtext("description", ""))
            pub   = item.findtext("pubDate", "")
            title = re.sub(r"\s+-\s+[^-]{2,40}$", "", title).strip()
            if title and len(title) > 10:
                results.append({
                    "title": title,
                    "link":  link,
                    "desc":  desc[:280] + "…" if len(desc) > 280 else desc,
                    "pub":   pub,
                })
        return results
    except Exception as e:
        print(f"  ⚠️  Feed error: {e}")
        return []


def fetch_all_topics() -> list:
    print("📡 Fetching & scoring defence topics...")
    all_topics = []

    for feed in RSS_FEEDS:
        print(f"  → {feed['tag']} ...", end=" ", flush=True)
        items = fetch_rss(feed["url"], max_items=6)

        if items:
            # Score all items and pick highest scoring one
            scored = []
            for item in items:
                score = compute_viral_score(item["title"], item["desc"])
                scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            best_score, best_item = scored[0]

            all_topics.append({
                "tag":        feed["tag"],
                "color":      feed["color"],
                "media_key":  feed["media_key"],
                "title":      best_item["title"],
                "link":       best_item["link"],
                "desc":       best_item["desc"],
                "pub":        best_item["pub"],
                "score":      best_score,
                "all_scored": scored[:3],  # top 3 for bonus topics section
            })
            label, lcolor, emoji = viral_label(best_score)
            print(f"{emoji} Score:{best_score} — '{best_item['title'][:45]}...'")
        else:
            print("❌ No items")

        time.sleep(random.uniform(0.4, 0.9))

    # Sort all topics by viral score — highest first
    all_topics.sort(key=lambda x: x["score"], reverse=True)
    return all_topics


# ══════════════════════════════════════════════════════════════
# HTML EMAIL BUILDER
# ══════════════════════════════════════════════════════════════

def format_pubdate(raw: str) -> str:
    if not raw:
        return datetime.date.today().strftime("%b %d, %Y")
    try:
        dt = datetime.datetime.strptime(raw.strip()[:25], "%a, %d %b %Y %H:%M:%S")
        return dt.strftime("%b %d · %H:%M UTC")
    except:
        return raw[:25]


def build_score_bar(score: int, color: str) -> str:
    pct = min(score, 100)
    label, lcolor, emoji = viral_label(score)
    return f"""
<div style="margin:10px 0 14px 0;">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
    <span style="font-size:10px; font-weight:800; letter-spacing:2px; color:{lcolor};">
      {emoji} {label}
    </span>
    <span style="font-size:11px; font-weight:700; color:{lcolor};">{score}/100</span>
  </div>
  <div style="background:#0d1f35; border-radius:4px; height:5px; overflow:hidden;">
    <div style="width:{pct}%; height:100%; background:linear-gradient(90deg,{color},{lcolor}); border-radius:4px;"></div>
  </div>
</div>"""


def build_media_links(media_key: str) -> str:
    sources = MEDIA_SOURCES.get(media_key, MEDIA_SOURCES["geopolitical"])
    links_html = ""
    for name, url in sources:
        icon = "📹" if "youtube" in url or "YT" in name else "🎬" if "dvidshub" in url else "📡" if "t.me" in url else "🔗"
        links_html += f"""
<a href="{url}" style="
    display:inline-block; margin:3px 4px 3px 0;
    background:#0d1f35; border:1px solid #1e3a5a;
    color:#6ab0d4; font-size:11px; padding:4px 10px;
    border-radius:4px; text-decoration:none;
    white-space:nowrap;
">{icon} {name}</a>"""
    return f"""
<div style="margin-top:12px; padding-top:10px; border-top:1px solid #0d1f35;">
  <p style="font-size:10px; color:#3a5a7a; letter-spacing:2px; text-transform:uppercase; margin:0 0 6px 0;">
    🎬 CLIP SOURCES FOR THIS TOPIC
  </p>
  <div style="line-height:2;">{links_html}</div>
</div>"""


def build_topic_card(topic: dict, index: int) -> str:
    color   = topic["color"]
    tag     = topic["tag"]
    title   = html.escape(topic["title"])
    desc    = html.escape(topic["desc"])
    link    = topic["link"]
    pub     = format_pubdate(topic.get("pub", ""))
    score   = topic["score"]
    score_bar  = build_score_bar(score, color)
    media_html = build_media_links(topic["media_key"])

    rank_badge = ""
    if index == 1:
        rank_badge = f'<span style="background:#ff2244; color:#fff; font-size:10px; font-weight:800; padding:2px 8px; border-radius:3px; margin-left:8px;">🔥 TOP PICK</span>'

    return f"""
<div style="
    background:linear-gradient(135deg,#0d1421 0%,#111827 100%);
    border:1px solid #1e3050;
    border-left:4px solid {color};
    border-radius:8px;
    margin:0 0 22px 0;
    padding:20px 22px;
    font-family:'Segoe UI',Arial,sans-serif;
">
  <!-- Header row -->
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
    <span style="background:{color}22; color:{color}; font-size:10px; font-weight:700;
        letter-spacing:2px; text-transform:uppercase; padding:3px 10px;
        border-radius:20px; border:1px solid {color}44;">{tag}</span>
    <span style="color:#3a5a7a; font-size:11px; font-weight:700;">#{index:02d} {rank_badge}</span>
  </div>

  <!-- Viral score bar -->
  {score_bar}

  <!-- Headline -->
  <h2 style="font-size:16px; font-weight:700; color:#e8f0f8; line-height:1.4; margin:0 0 8px 0;">
    {title}
  </h2>

  <!-- Description -->
  <p style="font-size:13px; color:#8aa8c0; line-height:1.7; margin:0 0 12px 0;">{desc}</p>

  <!-- Read more + date -->
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:0;">
    <a href="{link}" style="
        background:{color}; color:#000; font-size:10px; font-weight:800;
        letter-spacing:1.5px; text-transform:uppercase; padding:6px 14px;
        border-radius:4px; text-decoration:none; display:inline-block;">
      READ FULL STORY →
    </a>
    <span style="color:#2a4a6a; font-size:11px;">{pub}</span>
  </div>

  <!-- Media clip sources -->
  {media_html}
</div>"""


def build_bonus_topics_section(all_topics: list) -> str:
    """Build a compact section showing runner-up stories from each category."""
    rows = ""
    for topic in all_topics:
        extras = topic.get("all_scored", [])[1:3]  # items 2 and 3
        for score, item in extras:
            if score < 15:
                continue
            label, lcolor, emoji = viral_label(score)
            t = html.escape(item["title"][:80]) + ("…" if len(item["title"]) > 80 else "")
            rows += f"""
<tr>
  <td style="padding:7px 10px; border-bottom:1px solid #0d1f35; font-size:12px; color:#7090a8; width:60px; text-align:center;">
    <span style="color:{lcolor}; font-weight:700;">{score}</span>
  </td>
  <td style="padding:7px 10px; border-bottom:1px solid #0d1f35;">
    <a href="{item['link']}" style="color:#6ab0d4; font-size:12px; text-decoration:none; line-height:1.5;">{t}</a>
  </td>
  <td style="padding:7px 10px; border-bottom:1px solid #0d1f35; font-size:10px; color:{lcolor}; white-space:nowrap;">
    {emoji} {label}
  </td>
</tr>"""

    if not rows:
        return ""

    return f"""
<div style="margin:0 0 22px 0; padding:18px 22px;
    background:#080e1a; border:1px solid #1a2a3a; border-radius:8px;">
  <p style="font-size:11px; letter-spacing:3px; text-transform:uppercase;
      color:#3a5a7a; margin:0 0 12px 0; font-weight:700;">
    📋 ADDITIONAL TOPICS TO MONITOR
  </p>
  <table style="width:100%; border-collapse:collapse;">
    <tr style="background:#0d1421;">
      <th style="padding:6px 10px; font-size:10px; color:#2a4a6a; text-align:center; letter-spacing:1px;">SCORE</th>
      <th style="padding:6px 10px; font-size:10px; color:#2a4a6a; text-align:left; letter-spacing:1px;">STORY</th>
      <th style="padding:6px 10px; font-size:10px; color:#2a4a6a; text-align:left; letter-spacing:1px;">RATING</th>
    </tr>
    {rows}
  </table>
</div>"""


def build_full_email(topics: list) -> str:
    today_long  = datetime.date.today().strftime("%A, %B %d, %Y")
    today_short = datetime.date.today().strftime("%b %d, %Y")
    issue_num   = (datetime.date.today() - datetime.date(2025, 1, 1)).days + 1

    cards_html  = "".join(build_topic_card(t, i+1) for i, t in enumerate(topics))
    bonus_html  = build_bonus_topics_section(topics)
    top_score   = topics[0]["score"] if topics else 0
    _, top_color, top_emoji = viral_label(top_score)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Defence Dec Intel — {today_short}</title></head>
<body style="margin:0;padding:0;background:#050810;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;background:#0a0f1e;">

  <!-- HEADER -->
  <div style="background:linear-gradient(135deg,#050d1a 0%,#120508 100%);
      padding:32px 40px 24px;border-bottom:2px solid #00d4ff;text-align:center;">
    <p style="font-size:10px;letter-spacing:6px;text-transform:uppercase;
        color:#00d4ff;margin:0 0 10px 0;font-weight:700;">⬡ YOUTUBE CONTENT INTELLIGENCE ⬡</p>
    <h1 style="font-size:34px;font-weight:900;color:#fff;letter-spacing:4px;
        margin:0 0 4px 0;text-shadow:0 0 30px rgba(0,212,255,0.3);">DEFENCE DEC</h1>
    <p style="font-size:11px;color:#4a7090;letter-spacing:3px;text-transform:uppercase;margin:0 0 8px 0;">
      {today_long} · ISSUE #{issue_num:04d}</p>
    <p style="font-size:13px;color:#7090a8;margin:0;font-style:italic;">
      Viral Score · Topic Intel · Media Clip Sources · East vs West
    </p>
  </div>

  <!-- STATUS BAR -->
  <div style="background:#060d1a;padding:9px 40px;
      display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;
      border-bottom:1px solid #0d1f35;font-size:10px;letter-spacing:2px;text-transform:uppercase;">
    <span style="color:#ff4444;font-weight:800;">● LIVE INTEL — {len(topics)} TOPICS SCORED</span>
    <span style="color:{top_color};font-weight:700;">{top_emoji} TOP SCORE TODAY: {top_score}/100</span>
    <span style="color:#2a4a6a;">CLIP SOURCES INCLUDED</span>
  </div>

  <!-- INTRO -->
  <div style="padding:20px 40px 4px;">
    <p style="font-size:13px;color:#5a7a9a;line-height:1.7;
        border-left:3px solid #1e3050;padding-left:14px;margin:0;">
      Stories ranked by <strong style="color:#00d4ff;">Viral Probability Score</strong> based on
      weapon names, trigger words, and geopolitical tension signals.
      Each topic includes direct links to <strong style="color:#00d4ff;">free footage sources</strong>
      for your next video. Top score = highest YouTube potential today.
    </p>
  </div>

  <div style="border-top:1px solid #1a2a3a;margin:20px 0 0 0;"></div>

  <!-- MAIN TOPIC CARDS -->
  <div style="padding:16px 40px 8px;">{cards_html}</div>

  <!-- BONUS TOPICS TABLE -->
  <div style="padding:0 40px 16px;">{bonus_html}</div>

  <div style="border-top:1px solid #1a2a3a;margin:4px 0;"></div>

  <!-- QUICK REFERENCE: ALL CLIP SOURCES -->
  <div style="padding:20px 40px;">
    <p style="font-size:11px;letter-spacing:3px;text-transform:uppercase;
        color:#3a5a7a;margin:0 0 14px 0;font-weight:700;">
      📚 MASTER CLIP SOURCE DIRECTORY
    </p>
    <table style="width:100%;border-collapse:collapse;font-size:12px;">
      <tr style="background:#0d1421;">
        <th style="padding:6px 10px;color:#2a4a6a;text-align:left;letter-spacing:1px;font-size:10px;">CATEGORY</th>
        <th style="padding:6px 10px;color:#2a4a6a;text-align:left;letter-spacing:1px;font-size:10px;">BEST FREE SOURCE</th>
      </tr>
      <tr><td style="padding:6px 10px;border-bottom:1px solid #0d1f35;color:#7090a8;">🚀 Missiles</td>
          <td style="padding:6px 10px;border-bottom:1px solid #0d1f35;"><a href="https://www.dvidshub.net/search/#q=missile+test&type=video" style="color:#6ab0d4;text-decoration:none;">DVIDS Missile Tests (Public Domain)</a></td></tr>
      <tr><td style="padding:6px 10px;border-bottom:1px solid #0d1f35;color:#7090a8;">⚓ Naval</td>
          <td style="padding:6px 10px;border-bottom:1px solid #0d1f35;"><a href="https://www.youtube.com/@USNavy/videos" style="color:#6ab0d4;text-decoration:none;">US Navy Official YouTube</a></td></tr>
      <tr><td style="padding:6px 10px;border-bottom:1px solid #0d1f35;color:#7090a8;">✈️ Aircraft</td>
          <td style="padding:6px 10px;border-bottom:1px solid #0d1f35;"><a href="https://www.dvidshub.net/search/#q=fighter+jet&type=video" style="color:#6ab0d4;text-decoration:none;">DVIDS Air Force Footage</a></td></tr>
      <tr><td style="padding:6px 10px;border-bottom:1px solid #0d1f35;color:#7090a8;">🤖 Drones</td>
          <td style="padding:6px 10px;border-bottom:1px solid #0d1f35;"><a href="https://t.me/UkraineNow" style="color:#6ab0d4;text-decoration:none;">Ukraine Now Telegram</a></td></tr>
      <tr><td style="padding:6px 10px;border-bottom:1px solid #0d1f35;color:#7090a8;">🛰️ Space/Cyber</td>
          <td style="padding:6px 10px;border-bottom:1px solid #0d1f35;"><a href="https://www.youtube.com/@USSpaceForce/videos" style="color:#6ab0d4;text-decoration:none;">US Space Force YouTube</a></td></tr>
      <tr><td style="padding:6px 10px;border-bottom:1px solid #0d1f35;color:#7090a8;">⚔️ East vs West</td>
          <td style="padding:6px 10px;border-bottom:1px solid #0d1f35;"><a href="https://www.oryxspioenkop.com" style="color:#6ab0d4;text-decoration:none;">Oryx Visual Equipment Database</a></td></tr>
      <tr><td style="padding:6px 10px;color:#7090a8;">🎬 All Military</td>
          <td style="padding:6px 10px;"><a href="https://www.dvidshub.net" style="color:#6ab0d4;text-decoration:none;">DVIDS — Complete US Military Archive (Free)</a></td></tr>
    </table>
  </div>

  <!-- FOOTER -->
  <div style="background:#040810;padding:20px 40px;border-top:1px solid #0d1f35;
      text-align:center;font-size:11px;color:#2a4a6a;line-height:2;">
    <p style="margin:0 0 4px 0;">🛡️ <strong style="color:#3a5a7a;">DEFENCE DEC</strong> — YouTube Content Intelligence Brief</p>
    <p style="margin:0;font-size:10px;color:#1a3050;">
      Viral scores based on keyword analysis · Clip sources are free/public domain · For content research only
    </p>
  </div>

</div></body></html>"""


# ══════════════════════════════════════════════════════════════
# EMAIL SENDER
# ══════════════════════════════════════════════════════════════

def send_email(html_body: str, topics: list):
    today_short = datetime.date.today().strftime("%b %d, %Y")
    top_score   = topics[0]["score"] if topics else 0
    _, _, emoji = viral_label(top_score)
    subject = f"🛡️ Defence Dec Intel — {today_short} | Top Score: {top_score}/100 {emoji}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Defence Dec Intel <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(f"Defence Dec Intel — {today_short}\nView in HTML email client.", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    print("📧 Sending via Gmail SMTP...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASS)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Sent → {RECIPIENT_EMAIL} | Subject: {subject}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print(f"  🛡️  DEFENCE DEC INTEL  |  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    topics = fetch_all_topics()
    if not topics:
        print("❌ No topics fetched.")
        return

    print(f"\n✅ {len(topics)} topics fetched & scored")
    print(f"🔥 Top story: '{topics[0]['title'][:60]}' (Score: {topics[0]['score']}/100)\n")

    print("🔨 Building email...")
    html_body = build_full_email(topics)

    print("🚀 Sending...")
    send_email(html_body, topics)

    print("\n🎉 Done! Check defencedec@gmail.com")
    print("=" * 65)


if __name__ == "__main__":
    main()
