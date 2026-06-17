import json, os, sys
from datetime import datetime, timedelta

from twitter_client import TwitterClient
from tiktok_client import TikTokClient
from youtube_client import YouTubeClient

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Clients
cookies_file = "cookies.json"
auth_token = ct0 = None
if os.path.exists(cookies_file):
    with open(cookies_file) as f:
        c = json.load(f)
        auth_token = c.get("auth_token")
        ct0 = c.get("ct0")

client = TwitterClient(auth_token, ct0)
tiktok = TikTokClient()
yt_api_key = os.environ.get("YOUTUBE_API_KEY", "")
if not yt_api_key and os.path.exists("youtube_config.json"):
    with open("youtube_config.json") as f:
        yt_api_key = json.load(f).get("api_key", "")
youtube = YouTubeClient(api_key=yt_api_key)

TWITTER_USER = "infoyatirim"
TIKTOK_USER = "infoyatirim"
YT_CHANNEL_ID = "UC-Il4FpbUEatDuaefVzqh8Q"

print("Collecting data...")


def save(name, data):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {path}")


# --- OVERVIEW ---
overview = {"twitter": None, "tiktok": None, "youtube": None}

if client.is_logged_in():
    try:
        tw_user = client.get_user_info(TWITTER_USER)
        tw_tweets = client.get_user_tweets(TWITTER_USER, count=20)
        total_impressions = sum(int(t.get("view_count", 0) or 0) for t in tw_tweets)
        total_likes = sum(t.get("favorite_count", 0) for t in tw_tweets)
        total_rts = sum(t.get("retweet_count", 0) for t in tw_tweets)
        total_replies = sum(t.get("reply_count", 0) for t in tw_tweets)
        total_engagement = total_likes + total_rts + total_replies
        eng_rate = round((total_engagement / max(1, total_impressions)) * 100, 2)
        overview["twitter"] = {
            "username": tw_user["username"],
            "name": tw_user["name"],
            "followers": tw_user["followers_count"],
            "following": tw_user["following_count"],
            "tweets": tw_user["tweets_count"],
            "follower_growth": tw_user.get("follower_growth", 0),
            "total_impressions": total_impressions,
            "engagement_rate": eng_rate,
            "total_likes": total_likes,
            "total_retweets": total_rts,
            "total_replies": total_replies,
            "profile_image": tw_user.get("profile_image_url", ""),
        }
        save("twitter-profile.json", tw_user)
        save("twitter-tweets.json", tw_tweets)
    except Exception as e:
        print(f"  Twitter error: {e}")

try:
    tt_user = tiktok.get_user_info(TIKTOK_USER)
    if "error" not in tt_user:
        tt_videos = tiktok.get_user_videos(TIKTOK_USER, count=30)
        total_views = sum(v.get("play_count", 0) for v in tt_videos)
        total_likes = sum(v.get("like_count", 0) for v in tt_videos)
        total_comments = sum(v.get("comment_count", 0) for v in tt_videos)
        total_shares = sum(v.get("share_count", 0) for v in tt_videos)
        total_engagement = total_likes + total_comments + total_shares
        eng_rate = round((total_engagement / max(1, total_views)) * 100, 2)
        overview["tiktok"] = {
            "username": tt_user["username"],
            "nickname": tt_user.get("nickname", ""),
            "followers": tt_user["followers"],
            "hearts": tt_user["hearts"],
            "videos": tt_user["videos"],
            "follower_growth": tt_user.get("follower_growth", 0),
            "follower_growth_rate": tt_user.get("follower_growth_rate", 0),
            "total_views": total_views,
            "engagement_rate": eng_rate,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "avatar": tt_user.get("avatar", ""),
        }
except Exception as e:
    print(f"  TikTok overview error: {e}")

try:
    yt_info = youtube.get_channel_info(YT_CHANNEL_ID)
    yt_videos = youtube.get_uploads(YT_CHANNEL_ID, count=30)
    total_views_vids = sum(v.get("view_count", 0) for v in yt_videos)
    total_likes_vids = sum(v.get("like_count", 0) for v in yt_videos)
    total_comments_vids = sum(v.get("comment_count", 0) for v in yt_videos)
    total_engagement_yt = total_likes_vids + total_comments_vids
    eng_rate_yt = round((total_engagement_yt / max(1, total_views_vids)) * 100, 2)
    overview["youtube"] = {
        "channel_id": yt_info["id"],
        "title": yt_info["title"],
        "subscribers": yt_info["subscribers"],
        "total_views": yt_info["total_views"],
        "total_videos": yt_info["total_videos"],
        "subscriber_growth": yt_info.get("subscriber_growth", 0),
        "subscriber_growth_rate": yt_info.get("subscriber_growth_rate", 0),
        "engagement_rate": eng_rate_yt,
        "thumbnail": yt_info.get("thumbnail", ""),
    }
except Exception as e:
    print(f"  YouTube overview error: {e}")

save("overview.json", overview)

# --- TIKTOK ANALYTICS ---
try:
    profile = tiktok.get_user_info(TIKTOK_USER)
    if "error" not in profile:
        videos = tiktok.get_user_videos(TIKTOK_USER, count=50)
        total_views = sum(v.get("play_count", 0) for v in videos)
        total_likes = sum(v.get("like_count", 0) for v in videos)
        total_comments = sum(v.get("comment_count", 0) for v in videos)
        total_shares = sum(v.get("share_count", 0) for v in videos)
        total_saves = sum(v.get("save_count", 0) for v in videos)
        total_engagement = total_likes + total_comments + total_shares + total_saves
        avg_views = total_views // len(videos) if videos else 0
        avg_likes = total_likes // len(videos) if videos else 0
        avg_comments = total_comments // len(videos) if videos else 0
        avg_shares = total_shares // len(videos) if videos else 0
        avg_saves = total_saves // len(videos) if videos else 0
        engagement_rate = round((total_engagement / total_views * 100), 2) if total_views > 0 else 0

        history = profile.get("history", [])
        follower_growth_data = None
        if len(history) >= 2:
            first = history[0]
            last = history[-1]
            net_growth = last.get("followers", 0) - first.get("followers", 0)
            follower_growth_data = {
                "start_followers": first.get("followers", 0),
                "end_followers": last.get("followers", 0),
                "net_growth": net_growth,
                "growth_rate": round((net_growth / max(1, first.get("followers", 1))) * 100, 2),
                "start_date": first.get("date", "")[:10],
                "end_date": last.get("date", "")[:10],
                "history": history,
            }

        avg_duration = sum(v.get("duration", 0) for v in videos) / len(videos) if videos else 0
        total_duration = sum(v.get("duration", 1) for v in videos)
        avg_view_per_second = total_views / max(1, total_duration)
        followers = profile.get("followers", 1)
        rewatch_rate = round(min(100, (avg_views / max(1, followers)) * 100), 1)

        short = [v for v in videos if v.get("duration", 0) <= 15]
        medium = [v for v in videos if 15 < v.get("duration", 0) <= 60]
        long = [v for v in videos if v.get("duration", 0) > 60]

        def avg_of(lst, key):
            if not lst:
                return 0
            return sum(v.get(key, 0) for v in lst) // len(lst)

        def eng_rate(lst):
            if not lst:
                return 0
            t = sum(v.get("play_count", 0) for v in lst)
            e = sum(v.get("like_count", 0) + v.get("comment_count", 0) + v.get("share_count", 0) for v in lst)
            return round((e / max(1, t)) * 100, 2)

        format_analysis = {
            "short": {"count": len(short), "avg_views": avg_of(short, "play_count"), "avg_likes": avg_of(short, "like_count"), "avg_eng_rate": eng_rate(short)},
            "medium": {"count": len(medium), "avg_views": avg_of(medium, "play_count"), "avg_likes": avg_of(medium, "like_count"), "avg_eng_rate": eng_rate(medium)},
            "long": {"count": len(long), "avg_views": avg_of(long, "play_count"), "avg_likes": avg_of(long, "like_count"), "avg_eng_rate": eng_rate(long)},
        }

        by_views = sorted(videos, key=lambda v: v.get("play_count", 0), reverse=True)
        by_engagement = sorted(videos, key=lambda v: (v.get("like_count", 0) + v.get("comment_count", 0) + v.get("share_count", 0)), reverse=True)
        by_low = sorted(videos, key=lambda v: v.get("play_count", 0))

        hashtag_stats = {}
        for v in videos:
            for tag in v.get("hashtags", []):
                if tag not in hashtag_stats:
                    hashtag_stats[tag] = {"count": 0, "total_views": 0, "total_likes": 0}
                hashtag_stats[tag]["count"] += 1
                hashtag_stats[tag]["total_views"] += v.get("play_count", 0)
                hashtag_stats[tag]["total_likes"] += v.get("like_count", 0)
        top_hashtags = sorted(hashtag_stats.items(), key=lambda x: x[1]["total_views"], reverse=True)[:10]

        save("tiktok-analytics.json", {
            "profile": profile,
            "follower_growth": follower_growth_data,
            "summary": {
                "total_videos": len(videos),
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "total_saves": total_saves,
                "avg_views": avg_views,
                "avg_likes": avg_likes,
                "avg_comments": avg_comments,
                "avg_shares": avg_shares,
                "avg_saves": avg_saves,
                "engagement_rate": engagement_rate,
            },
            "view_quality": {
                "avg_duration": round(avg_duration, 1),
                "avg_view_per_second": round(avg_view_per_second, 1),
                "rewatch_rate": rewatch_rate,
            },
            "format_analysis": format_analysis,
            "best_by_views": by_views[:5],
            "best_by_engagement": by_engagement[:5],
            "worst_videos": by_low[:5],
            "top_hashtags": [{"tag": t, **s} for t, s in top_hashtags],
            "all_videos": videos,
        })
except Exception as e:
    print(f"  TikTok analytics error: {e}")

# --- YOUTUBE ANALYTICS ---
try:
    yt_info = youtube.get_channel_info(YT_CHANNEL_ID)
    videos = youtube.get_uploads(YT_CHANNEL_ID, count=50)
    filtered_videos = videos

    total_views = sum(v.get("view_count", 0) for v in filtered_videos)
    total_likes = sum(v.get("like_count", 0) for v in filtered_videos)
    total_comments = sum(v.get("comment_count", 0) for v in filtered_videos)
    total_duration = sum(v.get("duration", 0) for v in filtered_videos)
    avg_duration = total_duration / len(filtered_videos) if filtered_videos else 0

    short = [v for v in filtered_videos if v.get("duration", 0) <= 60]
    medium = [v for v in filtered_videos if 60 < v.get("duration", 0) <= 600]
    long = [v for v in filtered_videos if v.get("duration", 0) > 600]

    def avg_of(lst, key):
        if not lst:
            return 0
        return sum(v.get(key, 0) for v in lst) // len(lst)

    by_views = sorted(filtered_videos, key=lambda v: v.get("view_count", 0), reverse=True)
    by_likes = sorted(filtered_videos, key=lambda v: v.get("like_count", 0), reverse=True)
    by_comments = sorted(filtered_videos, key=lambda v: v.get("comment_count", 0), reverse=True)
    by_low = sorted(filtered_videos, key=lambda v: v.get("view_count", 0))

    tag_stats = {}
    for v in filtered_videos:
        for tag in v.get("tags", [])[:5]:
            if tag not in tag_stats:
                tag_stats[tag] = {"count": 0, "total_views": 0}
            tag_stats[tag]["count"] += 1
            tag_stats[tag]["total_views"] += v.get("view_count", 0)
    top_tags = sorted(tag_stats.items(), key=lambda x: x[1]["total_views"], reverse=True)[:10]

    save("youtube-analytics.json", {
        "channel": yt_info,
        "days": 30,
        "filtered_count": len(filtered_videos),
        "summary": {
            "total_videos": yt_info.get("total_videos", len(videos)),
            "total_views": yt_info.get("total_views", total_views),
            "total_subscribers": yt_info.get("subscribers", 0),
            "subscriber_growth": yt_info.get("subscriber_growth", 0),
            "subscriber_growth_rate": yt_info.get("subscriber_growth_rate", 0),
            "fetched_videos": len(filtered_videos),
            "avg_views": total_views // len(filtered_videos) if filtered_videos else 0,
            "avg_likes": total_likes // len(filtered_videos) if filtered_videos else 0,
            "avg_comments": total_comments // len(filtered_videos) if filtered_videos else 0,
            "avg_duration_sec": round(avg_duration, 1),
        },
        "duration_analysis": {
            "short": {"count": len(short), "avg_views": avg_of(short, "view_count"), "avg_likes": avg_of(short, "like_count")},
            "medium": {"count": len(medium), "avg_views": avg_of(medium, "view_count"), "avg_likes": avg_of(medium, "like_count")},
            "long": {"count": len(long), "avg_views": avg_of(long, "view_count"), "avg_likes": avg_of(long, "like_count")},
        },
        "best_by_views": by_views[:5],
        "best_by_likes": by_likes[:5],
        "best_by_comments": by_comments[:5],
        "worst_videos": by_low[:5],
        "top_tags": [{"tag": t, **s} for t, s in top_tags],
        "all_videos": filtered_videos,
    })
except Exception as e:
    print(f"  YouTube analytics error: {e}")

# --- COMPETITOR / INFLUENCER (pre-generated for common queries) ---
KNOWN_FINANCE_TWITTER = {
    "borsa": ["infoyatirim", "borsadabugun", "borsa_gunluk", "forex_borsa", "yatirimteknik", "borsa_yatirimci", "traborsa"],
    "yatirim": ["infoyatirim", "bigaborsa", "burak_kc", "yatirimciakademi", "yatirimteknik"],
    "ekonomi": ["infoyatirim", "bloombegthd", "ekonomi_sektoru", "dunyaekonomi", "piyasalar_gunluk"],
    "finans": ["infoyatirim", "bigaborsa", "finans_sektoru", "bankaborsa", "yatirimciakademi"],
}

KNOWN_FINANCE_TIKTOK = {
    "borsa": ["borsaefe", "yatirimsepeti", "borsailkAdimlar", "borsaogren", "borsayatirim", "finansbank", "borsa_gunluk", "yatirimciakademi"],
    "yatirim": ["yatirimsepeti", "yatirimciadam", "yatirimnedir", "finansbank", "borsaefe"],
    "ekonomi": ["ekonomidogrular", "piyasalar", "dunyaekonomi", "finansbank"],
    "finans": ["finansbank", "finansbank_tr", "ziraatbankasi", "borsaefe"],
}

# Generate competitor data for common queries
competitors = {}
for tag in KNOWN_FINANCE_TWITTER:
    competitors[tag] = {"query": tag, "platforms": {}}
    try:
        if client.is_logged_in():
            for uname in KNOWN_FINANCE_TWITTER[tag][:3]:
                try:
                    p = client.get_user_info(uname)
                    competitors[tag].setdefault("platforms", {})["twitter_" + uname] = {
                        "username": p["username"], "name": p["name"],
                        "followers": p["followers_count"], "tweets": p["tweets_count"],
                        "profile_image": p.get("profile_image_url", ""),
                    }
                except:
                    pass
    except:
        pass
    for uname in KNOWN_FINANCE_TIKTOK.get(tag, [])[:3]:
        try:
            p = tiktok.get_user_info(uname)
            if "error" not in p:
                competitors[tag].setdefault("platforms", {})["tiktok_" + uname] = {
                    "username": p["username"], "nickname": p.get("nickname", ""),
                    "followers": p["followers"],
                    "avatar": p.get("avatar", ""),
                }
        except:
            pass
save("competitors.json", competitors)

# Generate influencer data
def build_influencer_list(query_tag, twitter_users, tiktok_users):
    infs = []
    seen = set()
    for uname in twitter_users[:10]:
        try:
            if client.is_logged_in():
                p = client.get_user_info(uname)
                k = uname.lower()
                if k not in seen:
                    seen.add(k)
                    infs.append({
                        "username": uname, "name": p.get("name", uname),
                        "source": "twitter",
                        "platforms": {
                            "twitter": {"username": uname, "followers": p.get("followers_count", 0)}
                        }
                    })
        except:
            pass
    for uname in tiktok_users[:10]:
        try:
            p = tiktok.get_user_info(uname)
            k = uname.lower()
            if k not in seen and "error" not in p:
                seen.add(k)
                infs.append({
                    "username": uname, "name": p.get("nickname", uname),
                    "source": "tiktok",
                    "platforms": {
                        "tiktok": {"username": uname, "followers": p.get("followers", 0), "nickname": p.get("nickname", "")}
                    }
                })
        except:
            pass
    return sorted(infs, key=lambda x: len(x.get("platforms", {})), reverse=True)

influencers = {}
for tag, tw_users in KNOWN_FINANCE_TWITTER.items():
    tt_users = KNOWN_FINANCE_TIKTOK.get(tag, [])
    influencers[tag] = {"query": tag, "influencers": build_influencer_list(tag, tw_users, tt_users)}
save("influencers.json", influencers)

# Also generate YouTube search pre-cache
yt_search_cache = {}
for term in ["infoyatirim", "info yatirim", "borsa", "yatirim", "ekonomi", "finans"]:
    try:
        results = youtube.get_channel_search(term)
        yt_search_cache[term] = results[:5]
    except:
        yt_search_cache[term] = []
save("youtube-search-cache.json", yt_search_cache)

print("Done! All data saved to data/")
