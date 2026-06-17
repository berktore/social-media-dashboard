import subprocess, re, json, httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.tiktok.com/",
}
FALLBACK = "1%7CkvsogcLtZ9xPJKgsR5-9Bs-tOb-WEHfq05jj5AyJwJk%7C1781271623%7Cc80bdd2ff9ac511e6ca8ba27b265bcda133006bcf73e7f4c5e5fc3c30071aae2"

print("=== TEST 1: curl.exe ttwid ===")
try:
    result = subprocess.run(
        ["curl.exe", "-s", "-D", "-", "--compressed", "https://www.tiktok.com/@test",
         "-H", "User-Agent: " + HEADERS["User-Agent"], "-H", "Accept: text/html"],
        capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
    )
    match = re.search(r"ttwid=([^;]+)", result.stdout)
    if match:
        print(f"ttwid OK: {match.group(1)[:40]}...")
        ttwid = match.group(1)
    else:
        print("ttwid NOT FOUND")
        print("Headers:", result.stdout[:600])
except Exception as e:
    print(f"curl HATA: {e}")
    ttwid = None

if not ttwid:
    ttwid = FALLBACK

print("\n=== TEST 2: Fallback ttwid ile profil ===")
try:
    client = httpx.Client(headers=HEADERS, cookies={"ttwid": ttwid}, follow_redirects=True, timeout=15.0)
    resp = client.get("https://www.tiktok.com/@infoyatirim")
    html = resp.text
    if "__UNIVERSAL_DATA_FOR_REHYDRATION__" in html:
        print("UNIVERSAL_DATA found!")
        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html)
        if match:
            data = json.loads(match.group(1))
            user_info = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {})
            stats = user_info.get("stats", {})
            user = user_info.get("user", {})
            print(f"Username: {user.get('uniqueId')}")
            print(f"Followers: {stats.get('followerCount')}")
            print(f"Videos: {stats.get('videoCount')}")
    else:
        print("UNIVERSAL_DATA NOT FOUND")
        print(f"Status: {resp.status_code}, Body len: {len(html)}")
        if resp.status_code != 200:
            print(f"Body[:500]: {html[:500]}")
    client.close()
except Exception as e:
    print(f"Profil HATASI: {e}")

print("\n=== TEST 3: Flask API via httpx ===")
try:
    import urllib.request
    req = urllib.request.Request("http://localhost:5001/api/tiktok/infoyatirim/analytics")
    r = urllib.request.urlopen(req, timeout=30)
    data = json.loads(r.read())
    if "error" in data:
        print(f"API Error: {data['error']}")
    else:
        print(f"API OK! Keys: {list(data.keys())}")
        print(f"  profile: {data.get('profile', {}).get('followers')} followers")
        print(f"  videos: {len(data.get('all_videos', []))}")
        print(f"  view_quality: {data.get('view_quality')}")
except Exception as e:
    print(f"Flask API HATASI: {e}")
