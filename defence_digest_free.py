"""
╔══════════════════════════════════════════════════════════════╗
║          🛡️  DEFENCE DIGEST — 100% FREE AUTO-EMAILER        ║
║  Fetches real news from Google News RSS → Sends via Gmail    ║
║  Zero paid APIs. Zero cost. Pure Python stdlib only.         ║
╚══════════════════════════════════════════════════════════════╝

REQUIREMENTS:
  - Python 3.6+  (no pip installs needed — all stdlib)
  - Gmail App Password (free — see SETUP_GUIDE.md)

HOW TO RUN:
  python3 defence_digest_free.py

HOW TO SCHEDULE (8 AM IST = 02:30 UTC):
  Cron:    30 2 * * * python3 /path/to/defence_digest_free.py
  Windows: Task Scheduler → Daily 8:00 AM
  Cloud:   PythonAnywhere free tier → Scheduled Task 02:30 UTC
"""

import smtplib
import urllib.request
import xml.etree.ElementTree as ET
import datetime
import html
import re
import time
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ╔══════════════════════════════════════════════════════════════╗
# ║                    🔧  YOUR SETTINGS                        ║
# ╚══════════════════════════════════════════════════════════════╝

RECIPIENT_EMAIL = "defencedec@gmail.com"
SENDER_EMAIL    = "manmahow@gmail.com"   # Your Gmail address
GMAIL_APP_PASS  = "uscc ugea lcbi zdmj"    # Gmail App Password (NOT your login password)
                                            # Get it: Google Account → Security → App Passwords

# ╔══════════════════════════════════════════════════════════════╗
# ║              📡  FREE RSS FEED SOURCES                      ║
# ╚══════════════════════════════════════════════════════════════╝

RSS_FEEDS = [
    {
        "name":  "Defence Technology",
        "url":   "https://news.google.com/rss/search?q=missile+hypersonic+defence+technology&hl=en&gl=US&ceid=US:en",
        "tag":   "🚀 Missiles & Hypersonics",
        "color": "#ff4444",
    },
    {
        "name":  "Naval & Submarines",
        "url":   "https://news.google.com/rss/search?q=submarine+navy+naval+warfare+warship&hl=en&gl=US&ceid=US:en",
        "tag":   "⚓ Naval & Submarines",
        "color": "#00aaff",
    },
    {
        "name":  "Fighter Jets & Aerospace",
        "url":   "https://news.google.com/rss/search?q=fighter+jet+stealth+aircraft+air+force&hl=en&gl=US&ceid=US:en",
        "tag":   "✈️ Jets & Aerospace",
        "color": "#00d4ff",
    },
    {
        "name":  "Weapons Systems",
        "url":   "https://news.google.com/rss/search?q=weapon+system+military+drone+UAV+defence&hl=en&gl=US&ceid=US:en",
        "tag":   "🎯 Weapons & Drones",
        "color": "#ffaa00",
    },
    {
        "name":  "Space & Cyber Warfare",
        "url":   "https://news.google.com/rss/search?q=space+warfare+cyber+military+satellite+defence&hl=en&gl=US&ceid=US:en",
        "tag":   "🛰️ Space & Cyber",
        "color": "#aa44ff",
    },
    {
        "name":  "Global Defence News",
        "url":   "https://news.google.com/rss/search?q=pentagon+NATO+defence+ministry+military+deal&hl=en&gl=US&ceid=US:en",
        "tag":   "🌍 Global Defence",
        "color": "#44ff88",
    },
]

# ══════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Remove HTML tags and decode HTML entities."""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_rss(url: str, max_items: int = 3) -> list:
    """Fetch and parse an RSS feed. Returns list of {title, link, description, pubdate}."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            raw = response.read()

        root = ET.fromstring(raw)
        items = root.findall(".//item")

        results = []
        for item in items[:max_items]:
            title = clean_text(item.findtext("title", "No title"))
            link  = item.findtext("link", "#")
            desc  = clean_text(item.findtext("description", ""))
            pub   = item.findtext("pubDate", "")
            # Remove source tag if appended in Google News titles  (e.g. "... - Reuters")
            title = re.sub(r"\s+-\s+[^-]{2,40}$", "", title).strip()

            if title and len(title) > 10:
                results.append({
                    "title": title,
                    "link":  link,
                    "desc":  desc[:300] + "…" if len(desc) > 300 else desc,
                    "pub":   pub,
                })
        return results

    except Exception as e:
        print(f"  ⚠️  Feed error ({url[:60]}...): {e}")
        return []


def fetch_all_topics() -> list:
    """Fetch one top story from each RSS category. Returns 5-6 topic dicts."""
    print("📡 Fetching live defence news from RSS feeds...")
    topics = []

    for feed in RSS_FEEDS:
        print(f"  → {feed['tag']} ...", end=" ", flush=True)
        items = fetch_rss(feed["url"], max_items=5)

        if items:
            # Pick the most recent / first item
            best = items[0]
            topics.append({
                "tag":   feed["tag"],
                "color": feed["color"],
                "title": best["title"],
                "link":  best["link"],
                "desc":  best["desc"],
                "pub":   best["pub"],
            })
            print(f"✅  '{best['title'][:55]}...'")
        else:
            print("❌  No items fetched")

        time.sleep(random.uniform(0.5, 1.2))  # polite crawl delay

    # Fallback: if <4 topics fetched, add curated static placeholders
    # so the email always has content
    fallback_topics = [
        {
            "tag": "🚀 Missiles & Hypersonics",
            "color": "#ff4444",
            "title": "Global Hypersonic Arms Race Intensifies in 2025",
            "link": "https://www.defensenews.com",
            "desc": "Multiple nations are accelerating hypersonic glide vehicle programs. "
                    "The US, China, and Russia are all testing systems capable of Mach 5+ speeds "
                    "that can evade conventional missile defence systems, reshaping strategic deterrence.",
            "pub": "",
        },
        {
            "tag": "⚓ Naval & Submarines",
            "color": "#00aaff",
            "title": "Next-Gen Nuclear Submarines Enter Service Worldwide",
            "link": "https://news.usni.org",
            "desc": "AUKUS partners and China are commissioning advanced SSBNs with improved "
                    "stealth, longer-range SLBMs, and AI-assisted sonar systems that challenge "
                    "existing anti-submarine warfare doctrine.",
            "pub": "",
        },
        {
            "tag": "✈️ Jets & Aerospace",
            "color": "#00d4ff",
            "title": "6th Generation Fighter Programs Reach Critical Milestones",
            "link": "https://www.thedrive.com/the-war-zone",
            "desc": "The US NGAD, UK-led GCAP, and France-Germany FCAS programs are progressing "
                    "toward prototype flights. These aircraft feature directed energy weapons, "
                    "loyal wingman drone integration, and advanced stealth coatings.",
            "pub": "",
        },
        {
            "tag": "🎯 Weapons & Drones",
            "color": "#ffaa00",
            "title": "AI-Driven Drone Swarms Redefine Battlefield Tactics",
            "link": "https://breakingdefense.com",
            "desc": "Autonomous drone swarms equipped with edge AI are being deployed for ISR "
                    "and strike missions. Ukraine conflict has accelerated adoption, with nations "
                    "investing billions in counter-drone and swarm coordination technologies.",
            "pub": "",
        },
        {
            "tag": "🛰️ Space & Cyber",
            "color": "#aa44ff",
            "title": "Space Domain Becomes the New Battlefield Frontier",
            "link": "https://spacenews.com",
            "desc": "Anti-satellite (ASAT) weapons, orbital debris concerns, and military "
                    "satellite constellations are driving the weaponization of space. "
                    "The US Space Force and counterparts in China and Russia are expanding rapidly.",
            "pub": "",
        },
        {
            "tag": "🌍 Global Defence",
            "color": "#44ff88",
            "title": "Record Global Defence Spending Surpasses $2.4 Trillion",
            "link": "https://www.sipri.org",
            "desc": "SIPRI data shows global military expenditure at an all-time high, led by "
                    "the US, China, and NATO members. India ranks among top spenders, with focus "
                    "on indigenous defence manufacturing under the Aatmanirbhar Bharat initiative.",
            "pub": "",
        },
    ]

    if len(topics) < 4:
        print("  ℹ️  Using curated fallback topics (network may be restricted)")
        return fallback_topics

    return topics[:6]


# ══════════════════════════════════════════════════════════════
# EMAIL BUILDER
# ══════════════════════════════════════════════════════════════

def format_pubdate(raw: str) -> str:
    """Convert RSS pubDate to a readable string."""
    if not raw:
        return datetime.date.today().strftime("%B %d, %Y")
    try:
        # Try common RSS date format: "Mon, 27 May 2026 02:30:00 +0000"
        dt = datetime.datetime.strptime(raw.strip()[:25], "%a, %d %b %Y %H:%M:%S")
        return dt.strftime("%b %d, %Y · %H:%M UTC")
    except Exception:
        return raw[:30]


def build_topic_card(topic: dict, index: int) -> str:
    """Build one styled HTML card for a topic."""
    color  = topic["color"]
    tag    = topic["tag"]
    title  = html.escape(topic["title"])
    desc   = html.escape(topic["desc"])
    link   = topic["link"]
    pub    = format_pubdate(topic.get("pub", ""))

    return f"""
<div style="
    background: linear-gradient(135deg, #0d1421 0%, #111827 100%);
    border: 1px solid #1e3050;
    border-left: 4px solid {color};
    border-radius: 8px;
    margin: 0 0 20px 0;
    padding: 20px 24px;
    font-family: 'Segoe UI', Arial, sans-serif;
">
  <!-- Tag + index -->
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
    <span style="
        background:{color}22;
        color:{color};
        font-size:11px;
        font-weight:700;
        letter-spacing:2px;
        text-transform:uppercase;
        padding:3px 10px;
        border-radius:20px;
        border:1px solid {color}44;
    ">{tag}</span>
    <span style="color:#3a5a7a; font-size:11px; font-weight:700;">#{index:02d}</span>
  </div>

  <!-- Headline -->
  <h2 style="
    font-size:17px;
    font-weight:700;
    color:#e8f0f8;
    line-height:1.4;
    margin:0 0 10px 0;
    letter-spacing:0.3px;
  ">{title}</h2>

  <!-- Description -->
  <p style="
    font-size:13px;
    color:#8aa8c0;
    line-height:1.7;
    margin:0 0 14px 0;
  ">{desc}</p>

  <!-- Footer row -->
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
    <a href="{link}" style="
        display:inline-block;
        background:{color};
        color:#000;
        font-size:11px;
        font-weight:800;
        letter-spacing:1.5px;
        text-transform:uppercase;
        padding:6px 16px;
        border-radius:4px;
        text-decoration:none;
    ">READ FULL STORY →</a>
    <span style="color:#2a4a6a; font-size:11px;">{pub}</span>
  </div>
</div>
"""


def build_full_email(topics: list) -> str:
    """Assemble the complete HTML email."""
    today_long  = datetime.date.today().strftime("%A, %B %d, %Y")
    today_short = datetime.date.today().strftime("%b %d, %Y")
    issue_num   = (datetime.date.today() - datetime.date(2025, 1, 1)).days + 1

    # Build all topic cards
    cards_html = ""
    for i, topic in enumerate(topics, start=1):
        cards_html += build_topic_card(topic, i)

    # Divider line
    divider = '<div style="border-top:1px solid #1a2a3a; margin:28px 0;"></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Defence Digest — {today_short}</title>
</head>
<body style="margin:0; padding:0; background:#050810; font-family:'Segoe UI',Arial,sans-serif;">

<div style="max-width:660px; margin:0 auto; background:#0a0f1e;">

  <!--══ HEADER ══-->
  <div style="
    background: linear-gradient(135deg, #050d1a 0%, #120508 100%);
    padding: 36px 40px 28px;
    border-bottom: 2px solid #00d4ff;
    text-align: center;
  ">
    <!-- Top label -->
    <p style="
      font-size:10px; letter-spacing:6px; text-transform:uppercase;
      color:#00d4ff; margin:0 0 12px 0; font-weight:700;
    ">⬡ OPEN-SOURCE INTELLIGENCE BRIEF ⬡</p>

    <!-- Main title -->
    <h1 style="
      font-size:38px; font-weight:900; color:#ffffff;
      letter-spacing:4px; margin:0 0 6px 0; text-transform:uppercase;
      text-shadow: 0 0 30px rgba(0,212,255,0.3);
    ">DEFENCE DIGEST</h1>

    <!-- Date -->
    <p style="font-size:12px; color:#4a7090; letter-spacing:3px; text-transform:uppercase; margin:0 0 10px 0;">
      {today_long}
    </p>

    <!-- Tagline -->
    <p style="font-size:13px; color:#7090a8; margin:0; font-style:italic;">
      Missiles · Naval · Aerospace · Weapons · Space · Cyber Warfare
    </p>
  </div>

  <!--══ STATUS BAR ══-->
  <div style="
    background:#060d1a; padding:10px 40px;
    display:flex; justify-content:space-between;
    border-bottom:1px solid #0d1f35;
    font-size:10px; letter-spacing:2px; text-transform:uppercase;
  ">
    <span style="color:#ff4444; font-weight:800;">
      ● LIVE — {len(topics)} TOPICS TODAY
    </span>
    <span style="color:#2a4a6a;">ISSUE #{issue_num:04d}</span>
    <span style="color:#2a4a6a;">FREE · RSS-POWERED</span>
  </div>

  <!--══ INTRO ══-->
  <div style="padding:24px 40px 4px;">
    <p style="
      font-size:13px; color:#5a7a9a; line-height:1.7;
      border-left:3px solid #1e3050; padding-left:14px; margin:0;
    ">
      Good morning. Here are today's most significant developments across the global
      defence landscape — sourced live from open-source feeds.
      Stay informed. Stay ahead.
    </p>
  </div>

  {divider.replace("28px", "20px")}

  <!--══ TOPIC CARDS ══-->
  <div style="padding:0 40px 8px;">
    {cards_html}
  </div>

  <!--══ DIVIDER ══-->
  {divider}

  <!--══ FOOTER ══-->
  <div style="
    background:#040810; padding:24px 40px;
    border-top:1px solid #0d1f35;
    text-align:center;
    font-size:11px; color:#2a4a6a; line-height:2;
  ">
    <p style="margin:0 0 6px 0;">
      🛡️ <strong style="color:#3a5a7a;">DEFENCE DIGEST</strong>
      — Automated Daily Intelligence Brief
    </p>
    <p style="margin:0 0 6px 0;">
      Powered by <strong style="color:#3a5a7a;">Google News RSS</strong> ·
      Delivered daily at <strong style="color:#3a5a7a;">08:00 IST</strong> ·
      100% Free
    </p>
    <p style="margin:0; font-size:10px; color:#1a3050;">
      Open-source data only. For personal use. To stop: disable your cron/scheduler.
    </p>
  </div>

</div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════
# EMAIL SENDER
# ══════════════════════════════════════════════════════════════

def send_email(html_body: str, topic_count: int):
    """Send the digest via Gmail SMTP (free, uses App Password)."""
    today_short = datetime.date.today().strftime("%b %d, %Y")
    subject = f"🛡️ Defence Digest — {today_short} | {topic_count} Hot Topics"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Defence Digest <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL

    # Plain text fallback
    plain = (
        f"DEFENCE DIGEST — {today_short}\n"
        "Daily Defence & Military Intelligence Brief\n\n"
        "Please view this email in an HTML-capable client.\n"
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    print(f"📧 Connecting to Gmail SMTP...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASS)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

    print(f"✅ Defence Digest sent → {RECIPIENT_EMAIL}")
    print(f"   Subject: {subject}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print(f"  🛡️  DEFENCE DIGEST  |  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Fetch topics
    topics = fetch_all_topics()

    if not topics:
        print("❌ No topics fetched. Check your internet connection.")
        return

    print(f"\n✅ Fetched {len(topics)} topics\n")

    # 2. Build HTML email
    print("🔨 Building email HTML...")
    html_body = build_full_email(topics)

    # 3. Send
    print("🚀 Sending email...")
    send_email(html_body, len(topics))

    print("\n🎉 Done! Check defencedec@gmail.com")
    print("=" * 60)


if __name__ == "__main__":
    main()
