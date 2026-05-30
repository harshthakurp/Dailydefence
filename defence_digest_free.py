"""
DEFENCE DEC — YouTube Content Intelligence Brief
Fetches real defence news + searches YouTube for exact matching video clips
Uses: Google News RSS (free) + YouTube Data API v3 (free 10k units/day)
"""

import smtplib, urllib.request, urllib.parse, xml.etree.ElementTree as ET
import datetime, html, re, time, random, os, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── SETTINGS ──────────────────────────────────────────────────
RECIPIENT_EMAIL  = "defencedec@gmail.com"
SENDER_EMAIL     = "manmahow@gmail.com"
GMAIL_APP_PASS   = os.environ.get("GMAIL_APP_PASS", "myzs tqyb zhei mdnq")
YOUTUBE_API_KEY  = os.environ.get("YOUTUBE_API_KEY", "AIzaSyA-7VPKRc5FiUntEcW5rX9nUq4Ro2gqOBw")

# ── VIRAL KEYWORDS (score engine) ─────────────────────────────
VIRAL_KEYWORDS = {
    "hypersonic":10,"mach 5":10,"mach 10":10,"oreshnik":10,"sarmat":10,
    "rs-28":10,"hwasong":10,"icbm":9,"slbm":9,"trident":8,"minuteman":8,
    "tomahawk":8,"f-35":9,"f-22":9,"b-21":10,"ngad":10,"gcap":9,"fcas":9,
    "nuclear":9,"warhead":9,"ballistic":8,"stealth":8,"drone swarm":10,
    "loitering":8,"kamikaze":9,"shahed":9,"lancet":8,"submarine":8,
    "ssbn":9,"ssn":8,"carrier killer":10,"anti-satellite":10,"asat":10,
    "directed energy":10,"laser weapon":10,"railgun":9,"electronic warfare":8,
    "cyber attack":8,"nightmare":10,"game changer":10,"revolutionary":9,
    "first ever":9,"unprecedented":9,"secret":8,"leaked":10,"classified":9,
    "revealed":8,"destroyed":8,"intercepted":8,"vs":8,"beats":8,
    "russia":7,"china":7,"nato":7,"ukraine":8,"taiwan":9,"iran":8,
    "north korea":9,"india":7,"israel":8,"pentagon":6,
}

# ── RSS FEEDS ─────────────────────────────────────────────────
RSS_FEEDS = [
    {"tag":"🚀 Missiles & Hypersonics",   "color":"#ff4444",
     "url":"https://news.google.com/rss/search?q=missile+hypersonic+ICBM+ballistic&hl=en&gl=US&ceid=US:en"},
    {"tag":"⚓ Naval & Submarines",        "color":"#00aaff",
     "url":"https://news.google.com/rss/search?q=submarine+SSBN+navy+naval+warship&hl=en&gl=US&ceid=US:en"},
    {"tag":"✈️ Jets & Stealth Aircraft",  "color":"#00d4ff",
     "url":"https://news.google.com/rss/search?q=fighter+jet+stealth+F-35+NGAD+air+force&hl=en&gl=US&ceid=US:en"},
    {"tag":"🎯 Weapons & Drones",         "color":"#ffaa00",
     "url":"https://news.google.com/rss/search?q=weapon+system+military+drone+loitering+munition&hl=en&gl=US&ceid=US:en"},
    {"tag":"🤖 Drone Warfare & AI",       "color":"#ff8800",
     "url":"https://news.google.com/rss/search?q=drone+swarm+UAV+autonomous+weapon+AI+military&hl=en&gl=US&ceid=US:en"},
    {"tag":"🛰️ Space & Cyber Warfare",   "color":"#aa44ff",
     "url":"https://news.google.com/rss/search?q=space+warfare+ASAT+cyber+military+satellite&hl=en&gl=US&ceid=US:en"},
    {"tag":"⚔️ East vs West",            "color":"#ff2266",
     "url":"https://news.google.com/rss/search?q=Russia+China+USA+NATO+military+capability&hl=en&gl=US&ceid=US:en"},
    {"tag":"🌍 Global Defence Intel",    "color":"#44ff88",
     "url":"https://news.google.com/rss/search?q=pentagon+defence+ministry+military+contract&hl=en&gl=US&ceid=US:en"},
]

# ══════════════════════════════════════════════════════════════
# YOUTUBE SEARCH — exact clips per topic
# ══════════════════════════════════════════════════════════════

def search_youtube_clips(query: str, max_results: int = 3) -> list:
    """Search YouTube for real video clips matching the query.
    Returns list of {title, url, channel, views, thumb}"""
    if not YOUTUBE_API_KEY:
        return []
    try:
        # Step 1: search
        search_url = (
            "https://www.googleapis.com/youtube/v3/search?"
            + urllib.parse.urlencode({
                "part":       "snippet",
                "q":          query + " military defence",
                "type":       "video",
                "maxResults": max_results + 3,
                "order":      "relevance",
                "videoDuration": "medium",
                "key":        YOUTUBE_API_KEY,
            })
        )
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        if "items" not in data or not data["items"]:
            return []

        video_ids = [item["id"]["videoId"] for item in data["items"]
                     if item.get("id", {}).get("videoId")]

        if not video_ids:
            return []

        # Step 2: get view counts
        stats_url = (
            "https://www.googleapis.com/youtube/v3/videos?"
            + urllib.parse.urlencode({
                "part": "statistics,snippet",
                "id":   ",".join(video_ids),
                "key":  YOUTUBE_API_KEY,
            })
        )
        req2 = urllib.request.Request(stats_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=10) as r2:
            stats_data = json.loads(r2.read())

        clips = []
        for item in stats_data.get("items", []):
            vid_id  = item["id"]
            title   = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            views   = int(item["statistics"].get("viewCount", 0))
            thumb   = item["snippet"]["thumbnails"].get("medium", {}).get("url", "")
            clips.append({
                "title":   title,
                "url":     f"https://www.youtube.com/watch?v={vid_id}",
                "channel": channel,
                "views":   views,
                "thumb":   thumb,
            })

        # Sort by views descending, return top N
        clips.sort(key=lambda x: x["views"], reverse=True)
        return clips[:max_results]

    except Exception as e:
        print(f"    ⚠️ YouTube search error: {e}")
        return []


def format_views(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M views"
    elif n >= 1_000:
        return f"{n/1_000:.0f}K views"
    return f"{n} views"


# ══════════════════════════════════════════════════════════════
# VIRAL SCORE
# ══════════════════════════════════════════════════════════════

def compute_viral_score(title: str, desc: str) -> int:
    text = (title + " " + desc).lower()
    score, matched = 0, []
    for kw, w in VIRAL_KEYWORDS.items():
        if kw in text:
            score += w
            matched.append(kw)
    if len(matched) >= 4: score += 15
    elif len(matched) >= 2: score += 8
    return min(score, 100)


def viral_label(score: int) -> tuple:
    if score >= 70: return "VIRAL POTENTIAL", "#ff2244", "🔥🔥🔥"
    elif score >= 50: return "HIGH INTEREST",  "#ff8800", "🔥🔥"
    elif score >= 30: return "WORTH COVERING", "#ffcc00", "🔥"
    return "MONITOR", "#44aa88", "📌"


# ══════════════════════════════════════════════════════════════
# RSS FETCH
# ══════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_rss(url: str, max_items: int = 6) -> list:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            root = ET.fromstring(r.read())
        results = []
        for item in root.findall(".//item")[:max_items]:
            title = re.sub(r"\s+-\s+[^-]{2,40}$", "",
                           clean_text(item.findtext("title", ""))).strip()
            link  = item.findtext("link", "#")
            desc  = clean_text(item.findtext("description", ""))
            pub   = item.findtext("pubDate", "")
            if title and len(title) > 10:
                results.append({
                    "title": title,
                    "link":  link,
                    "desc":  desc[:280] + "…" if len(desc) > 280 else desc,
                    "pub":   pub,
                })
        return results
    except Exception as e:
        print(f"  ⚠️ Feed error: {e}")
        return []


def fetch_all_topics() -> list:
    print("📡 Fetching & scoring defence topics...")
    all_topics = []
    for feed in RSS_FEEDS:
        print(f"  → {feed['tag']} ...", end=" ", flush=True)
        items = fetch_rss(feed["url"])
        if items:
            scored = sorted(
                [(compute_viral_score(i["title"], i["desc"]), i) for i in items],
                key=lambda x: x[0], reverse=True
            )
            best_score, best_item = scored[0]
            _, _, emoji = viral_label(best_score)

            # Search YouTube for exact clips matching this headline
            print(f"{emoji} Score:{best_score} — searching YouTube clips...", end=" ", flush=True)
            clips = search_youtube_clips(best_item["title"])
            print(f"{'✅ ' + str(len(clips)) + ' clips' if clips else '⚠️ no clips'}")

            all_topics.append({
                "tag":        feed["tag"],
                "color":      feed["color"],
                "title":      best_item["title"],
                "link":       best_item["link"],
                "desc":       best_item["desc"],
                "pub":        best_item["pub"],
                "score":      best_score,
                "clips":      clips,
                "all_scored": scored[:3],
            })
        else:
            print("❌ No items")
        time.sleep(random.uniform(0.5, 1.0))

    all_topics.sort(key=lambda x: x["score"], reverse=True)
    return all_topics


# ══════════════════════════════════════════════════════════════
# HTML EMAIL BUILDER
# ══════════════════════════════════════════════════════════════

def format_pubdate(raw: str) -> str:
    if not raw: return datetime.date.today().strftime("%b %d, %Y")
    try:
        dt = datetime.datetime.strptime(raw.strip()[:25], "%a, %d %b %Y %H:%M:%S")
        return dt.strftime("%b %d · %H:%M UTC")
    except: return raw[:25]


def build_score_bar(score: int, color: str) -> str:
    label, lcolor, emoji = viral_label(score)
    return f"""
<div style="margin:8px 0 12px 0;">
  <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
    <span style="font-size:10px;font-weight:800;letter-spacing:2px;color:{lcolor};">{emoji} {label}</span>
    <span style="font-size:11px;font-weight:700;color:{lcolor};">{score}/100</span>
  </div>
  <div style="background:#0d1f35;border-radius:4px;height:5px;">
    <div style="width:{min(score,100)}%;height:100%;background:linear-gradient(90deg,{color},{lcolor});border-radius:4px;"></div>
  </div>
</div>"""


def build_clips_section(clips: list, color: str) -> str:
    if not clips:
        return """
<div style="margin-top:12px;padding:10px 14px;background:#080e1a;
    border:1px solid #1a2a3a;border-radius:6px;">
  <p style="font-size:11px;color:#3a5a7a;margin:0;letter-spacing:1px;">
    🎬 NO VIDEO CLIPS FOUND FOR THIS TOPIC
  </p>
</div>"""

    cards = ""
    for clip in clips:
        title   = html.escape(clip["title"][:70]) + ("…" if len(clip["title"]) > 70 else "")
        channel = html.escape(clip["channel"])
        views   = format_views(clip["views"])
        url     = clip["url"]
        thumb   = clip.get("thumb", "")

        thumb_html = f'<img src="{thumb}" style="width:100%;border-radius:4px;display:block;margin-bottom:8px;" alt="thumbnail"/>' if thumb else ""

        cards += f"""
<div style="flex:1;min-width:160px;max-width:200px;
    background:#080e1a;border:1px solid #1a2a3a;border-radius:6px;
    padding:10px;box-sizing:border-box;">
  {thumb_html}
  <a href="{url}" style="font-size:12px;color:#e0e8f0;text-decoration:none;
      line-height:1.4;display:block;margin-bottom:6px;font-weight:600;">{title}</a>
  <p style="font-size:10px;color:#4a7090;margin:0 0 3px 0;">{channel}</p>
  <p style="font-size:10px;color:{color};margin:0;font-weight:700;">{views}</p>
  <a href="{url}" style="display:inline-block;margin-top:8px;
      background:{color};color:#000;font-size:10px;font-weight:800;
      padding:4px 10px;border-radius:3px;text-decoration:none;
      letter-spacing:1px;">▶ WATCH</a>
</div>"""

    return f"""
<div style="margin-top:12px;padding-top:10px;border-top:1px solid #0d1f35;">
  <p style="font-size:10px;color:#3a5a7a;letter-spacing:2px;
      text-transform:uppercase;margin:0 0 10px 0;font-weight:700;">
    🎬 TOP VIDEO CLIPS FOR THIS TOPIC
  </p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;">{cards}</div>
</div>"""


def build_topic_card(topic: dict, index: int) -> str:
    color   = topic["color"]
    score   = topic["score"]
    title   = html.escape(topic["title"])
    desc    = html.escape(topic["desc"])
    pub     = format_pubdate(topic.get("pub", ""))
    rank    = ' <span style="background:#ff2244;color:#fff;font-size:10px;font-weight:800;padding:2px 8px;border-radius:3px;">🔥 TOP PICK</span>' if index == 1 else ""

    return f"""
<div style="background:linear-gradient(135deg,#0d1421 0%,#111827 100%);
    border:1px solid #1e3050;border-left:4px solid {color};
    border-radius:8px;margin:0 0 22px 0;padding:20px 22px;
    font-family:'Segoe UI',Arial,sans-serif;">
  <div style="display:flex;justify-content:space-between;align-items:center;
      margin-bottom:8px;flex-wrap:wrap;gap:6px;">
    <span style="background:{color}22;color:{color};font-size:10px;font-weight:700;
        letter-spacing:2px;text-transform:uppercase;padding:3px 10px;
        border-radius:20px;border:1px solid {color}44;">{topic['tag']}</span>
    <span style="color:#3a5a7a;font-size:11px;font-weight:700;">#{index:02d}{rank}</span>
  </div>
  {build_score_bar(score, color)}
  <h2 style="font-size:16px;font-weight:700;color:#e8f0f8;line-height:1.4;margin:0 0 8px 0;">{title}</h2>
  <p style="font-size:13px;color:#8aa8c0;line-height:1.7;margin:0 0 12px 0;">{desc}</p>
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <a href="{topic['link']}" style="background:{color};color:#000;font-size:10px;
        font-weight:800;letter-spacing:1.5px;text-transform:uppercase;
        padding:6px 14px;border-radius:4px;text-decoration:none;">READ FULL STORY →</a>
    <span style="color:#2a4a6a;font-size:11px;">{pub}</span>
  </div>
  {build_clips_section(topic.get('clips', []), color)}
</div>"""


def build_full_email(topics: list) -> str:
    today_long  = datetime.date.today().strftime("%A, %B %d, %Y")
    today_short = datetime.date.today().strftime("%b %d, %Y")
    issue_num   = (datetime.date.today() - datetime.date(2025, 1, 1)).days + 1
    top_score   = topics[0]["score"] if topics else 0
    _, top_color, top_emoji = viral_label(top_score)
    cards_html  = "".join(build_topic_card(t, i+1) for i, t in enumerate(topics))

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Defence Dec Intel — {today_short}</title></head>
<body style="margin:0;padding:0;background:#050810;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;background:#0a0f1e;">

  <div style="background:linear-gradient(135deg,#050d1a 0%,#120508 100%);
      padding:32px 40px 24px;border-bottom:2px solid #00d4ff;text-align:center;">
    <p style="font-size:10px;letter-spacing:6px;text-transform:uppercase;
        color:#00d4ff;margin:0 0 10px 0;font-weight:700;">⬡ YOUTUBE CONTENT INTELLIGENCE ⬡</p>
    <h1 style="font-size:34px;font-weight:900;color:#fff;letter-spacing:4px;
        margin:0 0 4px 0;text-shadow:0 0 30px rgba(0,212,255,0.3);">DEFENCE DEC</h1>
    <p style="font-size:11px;color:#4a7090;letter-spacing:3px;text-transform:uppercase;margin:0 0 8px 0;">
      {today_long} · ISSUE #{issue_num:04d}</p>
    <p style="font-size:13px;color:#7090a8;margin:0;font-style:italic;">
      Viral Score · Live News · Exact YouTube Clips · East vs West
    </p>
  </div>

  <div style="background:#060d1a;padding:9px 40px;display:flex;
      justify-content:space-between;flex-wrap:wrap;gap:6px;
      border-bottom:1px solid #0d1f35;font-size:10px;letter-spacing:2px;text-transform:uppercase;">
    <span style="color:#ff4444;font-weight:800;">● LIVE — {len(topics)} TOPICS SCORED</span>
    <span style="color:{top_color};font-weight:700;">{top_emoji} TOP SCORE: {top_score}/100</span>
    <span style="color:#2a4a6a;">REAL YOUTUBE CLIPS INCLUDED</span>
  </div>

  <div style="padding:20px 40px 4px;">
    <p style="font-size:13px;color:#5a7a9a;line-height:1.7;
        border-left:3px solid #1e3050;padding-left:14px;margin:0;">
      Stories ranked by <strong style="color:#00d4ff;">Viral Probability Score</strong>.
      Each topic includes <strong style="color:#00d4ff;">real YouTube video clips</strong>
      found by searching today's exact headline — sorted by view count.
    </p>
  </div>

  <div style="border-top:1px solid #1a2a3a;margin:20px 0 0 0;"></div>

  <div style="padding:16px 40px 24px;">{cards_html}</div>

  <div style="background:#040810;padding:20px 40px;border-top:1px solid #0d1f35;
      text-align:center;font-size:11px;color:#2a4a6a;line-height:2;">
    <p style="margin:0 0 4px 0;">🛡️ <strong style="color:#3a5a7a;">DEFENCE DEC</strong>
      — YouTube Content Intelligence Brief</p>
    <p style="margin:0;font-size:10px;color:#1a3050;">
      Viral scores based on keyword analysis · Video clips via YouTube Data API · For content research only
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
    msg.attach(MIMEText(f"Defence Dec Intel — {today_short}\nView in HTML client.", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    print("📧 Sending via Gmail SMTP...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASS)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Sent → {RECIPIENT_EMAIL}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print(f"  DEFENCE DEC INTEL  |  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    topics = fetch_all_topics()
    if not topics:
        print("No topics fetched.")
        return

    print(f"\n✅ {len(topics)} topics | Top: '{topics[0]['title'][:55]}' Score:{topics[0]['score']}/100\n")
    html_body = build_full_email(topics)
    send_email(html_body, topics)
    print("\n🎉 Done! Check defencedec@gmail.com")
    print("=" * 65)


if __name__ == "__main__":
    main()
