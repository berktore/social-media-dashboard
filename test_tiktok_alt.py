import subprocess, json, httpx, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# 1) oEmbed API
print("=== 1) oEmbed API ===")
try:
    r = httpx.get("https://www.tiktok.com/oembed?url=https://www.tiktok.com/@infoyatirim", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        d = r.json()
        print(f"Keys: {list(d.keys())}")
        for k in ["author_name", "author_url", "title", "thumbnail_url"]:
            print(f"  {k}: {d.get(k)}")
    else:
        print(f"Status: {r.status_code}, Body: {r.text[:200]}")
except Exception as e:
    print(f"HATA: {e}")

# 2) TikTok API /api/user/detail/ with browser headers
print("\n=== 2) TikTok API /api/user/detail/ ===")
for ua_name, ua in [
    ("Chrome Windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
    ("Mobile Android", "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36"),
]:
    try:
        h = {**HEADERS, "User-Agent": ua}
        r = httpx.get(f"https://www.tiktok.com/api/user/detail/?uniqueId=infoyatirim", headers=h, timeout=10)
        if r.status_code == 200 and len(r.text) > 10:
            print(f"  [{ua_name}] Status 200, len={len(r.text)}")
            try:
                d = r.json()
                print(f"    Keys: {list(d.keys())}")
            except:
                print(f"    Not JSON: {r.text[:100]}")
        else:
            print(f"  [{ua_name}] Status {r.status_code}, len={len(r.text)}")
    except Exception as e:
        print(f"  [{ua_name}] HATA: {e}")

# 3) Try with actual browser cookies from curl.exe (just the cookie, no ttwid)
print("\n=== 3) Minimal cookie approach ===")
try:
    result = subprocess.run(
        ["curl.exe", "-s", "-v", "--compressed", "https://www.tiktok.com/@infoyatirim",
         "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
         "-H", "Accept: text/html,application/xhtml+xml",
         "-H", "Accept-Language: en-US,en;q=0.9",
         "-H", "Cache-Control: no-cache",
         "-H", "Pragma: no-cache"],
        capture_output=True, text=True, timeout=15,
        encoding="utf-8", errors="replace"
    )
    if "__UNIVERSAL_DATA_FOR_REHYDRATION__" in result.stdout:
        print("curl.exe BAŞARILI! UNIVERSAL_DATA found!")
        print(f"Page size: {len(result.stdout)}")
        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', result.stdout)
        if match:
            data = json.loads(match.group(1))
            user_info = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {})
            stats = user_info.get("stats", {})
            print(f"Followers: {stats.get('followerCount')}, Videos: {stats.get('videoCount')}")
    else:
        print(f"curl.exe FAILED. Page size: {len(result.stdout)}")
        # Check for captcha
        if "captcha" in result.stdout.lower():
            print("CAPTCHA detected in page")
        print(f"First 500 chars: {result.stdout[:500]}")
except Exception as e:
    print(f"HATA: {e}")

# 4) yt-dlp with verbose to see what it extracts
print("\n=== 4) yt-dlp verbose channel ===")
try:
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "-v", "--playlist-items", "1:1",
         "https://www.tiktok.com/@infoyatirim"],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    stderr_lines = result.stderr.split("\n")
    info_lines = [l for l in stderr_lines if "Extracting URL" in l or "Downloading" in l or "channel" in l.lower()]
    for l in info_lines[:10]:
        print(f"  {l}")
    print(f"  Return code: {result.returncode}")
except Exception as e:
    print(f"HATA: {e}")
