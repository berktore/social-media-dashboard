from curl_cffi import requests
import json, re

print("=== curl_cffi ile TikTok profil ===")
try:
    resp = requests.get(
        "https://www.tiktok.com/@infoyatirim",
        impersonate="chrome131",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        timeout=15
    )
    print(f"Status: {resp.status_code}")
    print(f"Page size: {len(resp.text)}")
    if "__UNIVERSAL_DATA_FOR_REHYDRATION__" in resp.text:
        print("UNIVERSAL_DATA found!")
        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', resp.text)
        if match:
            data = json.loads(match.group(1))
            user_info = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {})
            stats = user_info.get("stats", {})
            user = user_info.get("user", {})
            print(f"Username: {user.get('uniqueId')}")
            print(f"Nickname: {user.get('nickname')}")
            print(f"Followers: {stats.get('followerCount')}")
            print(f"Following: {stats.get('followingCount')}")
            print(f"Hearts: {stats.get('heartCount')}")
            print(f"Videos: {stats.get('videoCount')}")
    else:
        print("UNIVERSAL_DATA NOT FOUND")
        if "captcha" in resp.text.lower():
            print("CAPTCHA detected!")
        print(f"First 300: {resp.text[:300]}")
except Exception as e:
    print(f"HATA: {e}")

print("\n=== curl_cffi ile TikTok API ===")
try:
    resp = requests.get(
        "https://www.tiktok.com/api/user/detail/?uniqueId=infoyatirim",
        impersonate="chrome131",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://www.tiktok.com/@infoyatirim",
        },
        timeout=15
    )
    print(f"Status: {resp.status_code}, Body len: {len(resp.text)}")
    if resp.text:
        try:
            d = resp.json()
            print(f"Keys: {list(d.keys())}")
            if "user" in d:
                u = d["user"]
                print(f"Followers: {u.get('follower_count')}")
        except:
            print(f"Raw: {resp.text[:200]}")
except Exception as e:
    print(f"HATA: {e}")
