import urllib.request, json, sys

# Fetch the actual TikTok analytics data
req = urllib.request.Request("http://localhost:5001/api/tiktok/infoyatirim/analytics")
r = urllib.request.urlopen(req, timeout=30)
data = json.loads(r.read())

if "error" in data:
    print("API ERROR:", data["error"])
    sys.exit(1)

print("=== ALL KEYS ===")
for k, v in data.items():
    if isinstance(v, list):
        print(f"  {k}: list[{len(v)}]")
    elif isinstance(v, dict):
        print(f"  {k}: dict[{len(v)} keys] -> {list(v.keys())}")
    elif v is None:
        print(f"  {k}: None")
    else:
        print(f"  {k}: {type(v).__name__} = {v}")

print("\n=== TESTING ALL TEMPLATE LITERALS ===")

# Simulate what renderTikTokAll does
profile = data.get("profile", {})
follower_growth = data.get("follower_growth")
summary = data.get("summary", {})
view_quality = data.get("view_quality", {})
format_analysis = data.get("format_analysis", {})
best_by_views = data.get("best_by_views", [])
best_by_engagement = data.get("best_by_engagement", [])
worst_videos = data.get("worst_videos", [])
top_hashtags = data.get("top_hashtags", [])
all_videos = data.get("all_videos", [])

errors = []

# Test 1: Profile cards
try:
    growth = profile.get("follower_growth", 0)
    growthRate = profile.get("follower_growth_rate", 0)
    growthText = ("+" + str(growth)) if growth >= 0 else str(growth)
    print(f"  Test 1 (profile cards): OK - {profile.get('followers')} followers, growth={growth}")
except Exception as e:
    errors.append(f"Test 1 (profile cards): {e}")

# Test 2: Follower growth
try:
    if follower_growth and follower_growth.get("history") and len(follower_growth["history"]) >= 2:
        hist = follower_growth["history"]
        maxF = max(h.get("followers", 0) for h in hist)
        minF = min(h.get("followers", 0) for h in hist)
        rangeV = maxF - minF or 1
        print(f"  Test 2a (follower growth chart): OK - {len(hist)} points, range={rangeV}")
    else:
        print(f"  Test 2b (follower growth fallback): OK - using profile.followers={profile.get('followers')}")
except Exception as e:
    errors.append(f"Test 2 (follower growth): {e}")

# Test 3: View quality
try:
    avg_duration = view_quality.get("avg_duration", 0)
    avg_view_per_second = view_quality.get("avg_view_per_second", 0)
    rewatch_rate = view_quality.get("rewatch_rate", 0)
    duration_str = f"{int(avg_duration // 60)}:{int(avg_duration % 60):02d}"
    print(f"  Test 3 (view quality): OK - duration={avg_duration}s, avg_vps={avg_view_per_second}, rewatch={rewatch_rate}%")
except Exception as e:
    errors.append(f"Test 3 (view quality): {e}")

# Test 4: Engagement
try:
    total_likes = summary.get("total_likes", 0)
    avg_likes = summary.get("avg_likes", 0)
    total_comments = summary.get("total_comments", 0)
    avg_comments = summary.get("avg_comments", 0)
    total_shares = summary.get("total_shares", 0)
    avg_shares = summary.get("avg_shares", 0)
    total_saves = summary.get("total_saves", 0)
    engagement_rate = summary.get("engagement_rate", 0)
    print(f"  Test 4 (engagement): OK - likes={total_likes}, comments={total_comments}, shares={total_shares}, er={engagement_rate}%")
except Exception as e:
    errors.append(f"Test 4 (engagement): {e}")

# Test 5: Video rankings (renderList)
try:
    def renderList(title, icon, color, items):
        result = ""
        for i, v in enumerate(items):
            desc = v.get("desc", "") or "Aciklama yok"
            play_count = v.get("play_count", 0)
            like_count = v.get("like_count", 0)
            comment_count = v.get("comment_count", 0)
            result += f"  #{i+1}: {desc[:30]}... play={play_count} like={like_count}"
        return result

    top5_views = best_by_views[:5]
    top5_eng = best_by_engagement[:5]
    print(f"  Test 5 (rankings): OK - top views={len(top5_views)}, top eng={len(top5_eng)}")
except Exception as e:
    errors.append(f"Test 5 (rankings): {e}")

# Test 6: Format analysis
try:
    for key in ["short", "medium", "long"]:
        d = format_analysis.get(key, {})
        count = d.get("count", 0)
        avg_views = d.get("avg_views", 0)
        avg_likes = d.get("avg_likes", 0)
        avg_eng_rate = d.get("avg_eng_rate", 0)
    print(f"  Test 6 (formats): OK - short={format_analysis.get('short',{}).get('count')}, medium={format_analysis.get('medium',{}).get('count')}, long={format_analysis.get('long',{}).get('count')}")
except Exception as e:
    errors.append(f"Test 6 (formats): {e}")

# Test 7: Hashtags
try:
    for h in top_hashtags:
        tag = h.get("tag", "")
        count = h.get("count", 0)
        total_views = h.get("total_views", 0)
    print(f"  Test 7 (hashtags): OK - {len(top_hashtags)} hashtags, first={top_hashtags[0].get('tag') if top_hashtags else 'none'}")
except Exception as e:
    errors.append(f"Test 7 (hashtags): {e}")

# Test 8: All videos table
try:
    for v in all_videos:
        eng = (v.get("like_count") or 0) + (v.get("comment_count") or 0) + (v.get("share_count") or 0) + (v.get("save_count") or 0)
        engRate = (eng / v["play_count"] * 100) if v.get("play_count", 0) > 0 else 0
        duration = v.get("duration", 0)
        dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "-"
        created = v.get("created_at", 0)
        import datetime
        if created:
            dt = datetime.datetime.fromtimestamp(created)
            date_str = dt.strftime("%d %b %Y")
    print(f"  Test 8 (videos table): OK - {len(all_videos)} videos")
except Exception as e:
    errors.append(f"Test 8 (videos table): {e}")

print(f"\n=== ERRORS: {len(errors)} ===")
for e in errors:
    print(f"  ERROR: {e}")

if not errors:
    print("ALL TESTS PASSED - no template literal errors")
    print("\n=== INVESTIGATING NON-OBVIOUS ISSUES ===")
    # Check for special chars in description
    for i, v in enumerate(all_videos[:3]):
        desc = v.get("desc", "")
        if "${" in desc or "`" in desc:
            print(f"  WARNING: Video {i} has special chars in desc!")
        print(f"  Video {i}: desc[:50]={desc[:50]}")
    
    # Check profile description special chars
    prof_desc = profile.get("description", "")
    if "${" in prof_desc or "`" in prof_desc:
        print(f"  WARNING: profile.description has special chars!")
    print(f"  profile.description[:80]='{prof_desc[:80]}'")
    
    # Check avatar URL
    avatar = profile.get("avatar", "")
    print(f"  avatar[:60]='{avatar[:60]}'")
    
    # Check any None values in video fields
    for i, v in enumerate(all_videos):
        for field in ["play_count", "like_count", "comment_count", "share_count", "save_count", "duration", "created_at"]:
            if v.get(field) is None:
                print(f"  Video {i}: {field} is None!")
