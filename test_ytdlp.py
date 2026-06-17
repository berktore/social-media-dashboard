import subprocess, json

# Test 1: yt-dlp to extract user info from TikTok profile
print("=== Test 1: yt-dlp flat playlist ===")
try:
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "-j", "--playlist-items", "1:3",
         "https://www.tiktok.com/@infoyatirim"],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        print(f"Videos found: {len(lines)}")
        for line in lines[:2]:
            item = json.loads(line)
            print(f"  ID: {item.get('id')}")
            print(f"  Title: {item.get('title', '')[:50]}")
            print(f"  View count: {item.get('view_count')}")
    else:
        print(f"STDERR: {result.stderr[:500]}")
except subprocess.TimeoutExpired:
    print("yt-dlp TIMEOUT")
except Exception as e:
    print(f"HATA: {e}")

# Test 2: Try the TikApi-like approach (mobile API)
print("\n=== Test 2: Mobile API approach ===")
try:
    import httpx
    headers = {
        "User-Agent": "com.ss.android.ugc.trill/494 (Linux; U; Android 14; en_US; Pixel 7; Build/UP1A.231005.007; Cronet/58.0.2991.00)",
        "Accept": "application/json",
    }
    r = httpx.get(f"https://www.tiktok.com/api/user/detail/?uniqueId=infoyatirim", headers=headers, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:300]}")
except Exception as e:
    print(f"HATA: {e}")
