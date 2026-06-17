import subprocess, json, re

print("=== Test 1: yt-dlp with impersonation ===")
try:
    result = subprocess.run(
        ["yt-dlp", "--impersonate", "chrome:131", "-j", "--playlist-items", "1:2",
         "https://www.tiktok.com/@infoyatirim"],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        print(f"Videos: {len(lines)}")
        for line in lines[:2]:
            v = json.loads(line)
            print(f"  ID={v.get('id')}, views={v.get('view_count')}, likes={v.get('like_count')}")
            print(f"  Duration={v.get('duration')}")
            print(f"  Keys: {[k for k in v.keys() if not k.startswith('_')][:15]}")
    else:
        print(f"STDERR[:500]: {result.stderr[:500]}")
except Exception as e:
    print(f"HATA: {e}")

print("\n=== Test 2: yt-dlp --write-info-json (full metadata) ===")
try:
    import tempfile, os
    tmpdir = tempfile.mkdtemp()
    result = subprocess.run(
        ["yt-dlp", "--impersonate", "chrome:131", "--write-info-json", "--skip-download",
         "--playlist-items", "1:1", "-o", os.path.join(tmpdir, "%(id)s"),
         "https://www.tiktok.com/@infoyatirim"],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        # Find the JSON file
        files = os.listdir(tmpdir)
        json_files = [f for f in files if f.endswith(".json")]
        print(f"Files created: {json_files}")
        for jf in json_files:
            with open(os.path.join(tmpdir, jf)) as f:
                info = json.load(f)
                print(f"Top keys: {list(info.keys())}")
                # Check for channel/subscriber info
                for k in ["channel", "channel_id", "channel_follower_count", "channel_url", "uploader", "uploader_id", "repost_count"]:
                    if k in info:
                        print(f"  {k}: {info[k]}")
    else:
        print(f"STDERR[:500]: {result.stderr[:500]}")
except Exception as e:
    print(f"HATA: {e}")
