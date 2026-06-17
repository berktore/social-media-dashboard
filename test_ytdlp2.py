import subprocess, json

# yt-dlp ile TikTok kanal metadata
print("=== Test: yt-dlp channel info ===")
try:
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "-J", "--playlist-items", "1:1",
         "https://www.tiktok.com/@infoyatirim"],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"Top-level keys: {list(data.keys())}")
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool)):
                print(f"  {k}: {v}")
            elif isinstance(v, dict):
                print(f"  {k}: dict[{len(v)} keys] -> {list(v.keys())[:10]}")
            elif isinstance(v, list):
                print(f"  {k}: list[{len(v)}]")
            else:
                print(f"  {k}: {v}")
    else:
        print(f"STDERR: {result.stderr[:500]}")
except Exception as e:
    print(f"HATA: {e}")

print("\n=== Test: yt-dlp flat playlist with channel URL (no --flat-playlist) ===")
try:
    result = subprocess.run(
        ["yt-dlp", "-j", "--playlist-items", "1:1",
         "https://www.tiktok.com/@infoyatirim"],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        for line in result.stdout.strip().split("\n")[:2]:
            if line.strip():
                data = json.loads(line)
                print(f"Keys: {list(data.keys())}")
                for k, v in data.items():
                    if isinstance(v, (str, int, float, bool)):
                        print(f"  {k}: {v}")
                    elif isinstance(v, dict):
                        print(f"  {k}: dict[{len(v)} keys]")
                    elif isinstance(v, list):
                        print(f"  {k}: list[{len(v)}]")
                    else:
                        print(f"  {k}: {v}")
    else:
        print(f"STDERR: {result.stderr[:500]}")
except Exception as e:
    print(f"HATA: {e}")
