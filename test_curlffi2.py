from curl_cffi import requests
import json, re

for i in range(3):
    print(f"=== Attempt {i+1} ===")
    try:
        resp = requests.get(
            "https://www.tiktok.com/@infoyatirim",
            impersonate="chrome131",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
            timeout=15
        )
        print(f"  Status: {resp.status_code}, Size: {len(resp.text)}")
        if "__UNIVERSAL_DATA_FOR_REHYDRATION__" in resp.text:
            print("  SUCCESS! UNIVERSAL_DATA found")
            match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', resp.text)
            if match:
                data = json.loads(match.group(1))
                ui = data.get("__DEFAULT_SCOPE__",{}).get("webapp.user-detail",{}).get("userInfo",{})
                if ui:
                    print(f"  Followers: {ui.get('stats',{}).get('followerCount')}")
        elif "captcha" in resp.text.lower():
            print("  CAPTCHA page")
            print(f"  First 200: {resp.text[:200]}")
        else:
            print(f"  Unknown page, first 200: {resp.text[:200]}")
    except Exception as e:
        print(f"  HATA: {e}")
