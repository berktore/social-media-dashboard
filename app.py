import json
import os
import secrets
import tempfile
import time as _time
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from twitter_client import TwitterClient
from tiktok_client import TikTokClient
from youtube_client import YouTubeClient
from instagram_client import InstagramClient

_competitor_cache = {}

def _cache_get(key):
    entry = _competitor_cache.get(key)
    if entry and _time.time() - entry['t'] < 90:
        return entry['data']
    return None

def _cache_set(key, data):
    _competitor_cache[key] = {'data': data, 't': _time.time()}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'socialnexus-2024-sabit-anahtar-degistirme')

USERS = {
    'info': {'password': 'info', 'role': 'admin', 'name': 'Ana Admin'},
    'demo': {'password': 'demo123', 'role': 'user', 'name': 'Demo Kullanici'},
    'takip': {'password': 'takip2024', 'role': 'user', 'name': 'Takip Kullanici'},
}

def _check_login(username, password):
    user = USERS.get(username)
    if user and user['password'] == password:
        return user
    return None

tiktok = TikTokClient()
yt_api_key = os.environ.get('YOUTUBE_API_KEY', '')
if not yt_api_key and os.path.exists('youtube_config.json'):
    with open('youtube_config.json') as f:
        yt_api_key = json.load(f).get('api_key', '')
youtube = YouTubeClient(api_key=yt_api_key)

instagram = InstagramClient()
ig_sessionid = os.environ.get('INSTAGRAM_SESSIONID', '1513274915%3ARP3kd9sI8rDucW%3A14%3AAYhNpZC3fSs90obrh7VE6gCLIGKQQNyLVLI21yaIfjY')
if ig_sessionid:
    instagram.login(ig_sessionid)

def _get_twitter_client():
    try:
        auth_token = session.get('twitter_auth_token') if session else None
    except RuntimeError:
        auth_token = None
    if not auth_token:
        auth_token = os.environ.get('TWITTER_AUTH_TOKEN') or None
    try:
        ct0 = session.get('twitter_ct0') if session else None
    except RuntimeError:
        ct0 = None
    if not ct0:
        ct0 = os.environ.get('TWITTER_CT0') or None
    if not auth_token and os.path.exists("cookies.json"):
        with open("cookies.json") as f:
            c = json.load(f)
            auth_token = c.get("auth_token")
            ct0 = c.get("ct0")
    if not auth_token and os.path.exists(os.path.join(tempfile.gettempdir(), "twitter_creds.json")):
        try:
            with open(os.path.join(tempfile.gettempdir(), "twitter_creds.json")) as f:
                c = json.load(f)
                auth_token = c.get("auth_token") or auth_token
                ct0 = c.get("ct0") or ct0
        except (OSError, IOError, json.JSONDecodeError):
            pass
    return TwitterClient(auth_token, ct0)

client = _get_twitter_client()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = _check_login(username, password)
        if user:
            session["logged_in"] = True
            session["username"] = username
            session["role"] = user['role']
            session["display_name"] = user['name']
            return redirect(url_for("index"))
        return render_template("login.html", error="Hatali kullanici adi veya sifre!")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    logged_in = 'logged_in' in session
    return jsonify({"logged_in": logged_in, "twitter_ready": client.is_logged_in()})


@app.before_request
def _reload_twitter_client():
    global client
    try:
        fresh = _get_twitter_client()
        if fresh.auth_token != client.auth_token or fresh.ct0 != client.ct0:
            client = fresh
    except Exception:
        if not client.is_logged_in():
            client = _get_twitter_client()


@app.route("/api/login", methods=["POST"])
@login_required
def api_login():
    data = request.json
    if not data or not data.get("auth_token") or not data.get("ct0"):
        return jsonify({"success": False, "error": "auth_token ve ct0 degerleri gerekli"})
    try:
        tmp_creds = os.path.join(tempfile.gettempdir(), "twitter_creds.json")
        try:
            with open(tmp_creds, "w") as f:
                json.dump(data, f)
        except (OSError, PermissionError):
            pass
        try:
            with open("cookies.json", "w") as f:
                json.dump(data, f)
        except (OSError, PermissionError):
            pass
        client.login(data["auth_token"], data["ct0"])
        session['twitter_auth_token'] = data["auth_token"]
        session['twitter_ct0'] = data["ct0"]
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/debug")
@login_required
def api_debug():
    from twitter_client import TwitterClient
    import inspect
    has_twitter_session = bool(session.get('twitter_auth_token'))
    client_creds = {"auth_token": client.auth_token[:8] + "..." if client.auth_token else None,
                    "ct0": client.ct0[:8] + "..." if client.ct0 else None,
                    "logged_in": client.is_logged_in(),
                    "instance_id": id(client)}
    try:
        fresh = _get_twitter_client()
        fresh_creds = {"auth_token": fresh.auth_token[:8] + "..." if fresh.auth_token else None,
                       "ct0": fresh.ct0[:8] + "..." if fresh.ct0 else None,
                       "logged_in": fresh.is_logged_in(),
                       "instance_id": id(fresh)}
    except Exception as e:
        fresh_creds = {"error": str(e)}
    return jsonify({
        "session_twitter_auth_token": has_twitter_session,
        "session_keys": list(session.keys()),
        "client": client_creds,
        "fresh_client": fresh_creds,
        "cookies_json_exists": os.path.exists("cookies.json"),
        "tmp_creds_exists": os.path.exists(os.path.join(tempfile.gettempdir(), "twitter_creds.json")),
        "env_has_twitter_auth_token": "TWITTER_AUTH_TOKEN" in os.environ,
        "env_has_twitter_ct0": "TWITTER_CT0" in os.environ,
    })


@app.route("/api/user/<username>")
@login_required
def api_user(username):
    try:
        user = client.get_user_info(username)
        return jsonify(user)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/user/<username>/tweets")
@login_required
def api_user_tweets(username):
    count = request.args.get("count", 20, type=int)
    try:
        tweets = client.get_user_tweets(username, count=count)
        return jsonify(tweets)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/search")
@login_required
def api_search():
    query = request.args.get("q", "")
    count = request.args.get("count", 20, type=int)
    try:
        tweets = client.search_tweets(query, count=count)
        return jsonify(tweets)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/trends")
@login_required
def api_trends():
    try:
        trends = client.get_trends()
        return jsonify(trends)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/user/<username>/similar")
@login_required
def api_similar(username):
    count = request.args.get("count", 20, type=int)
    try:
        users = client.get_similar_accounts(username, count=count)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/user/<username>/followers")
@login_required
def api_followers(username):
    count = request.args.get("count", 20, type=int)
    try:
        users = client.get_followers(username, count=count)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/user/<username>/following")
@login_required
def api_following(username):
    count = request.args.get("count", 20, type=int)
    try:
        users = client.get_following(username, count=count)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)})


# TikTok Endpoints
@app.route("/api/tiktok/<username>")
@login_required
def api_tiktok_user(username):
    try:
        user = tiktok.get_user_info(username)
        return jsonify(user)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/tiktok/<username>/videos")
@login_required
def api_tiktok_videos(username):
    count = request.args.get("count", 30, type=int)
    try:
        videos = tiktok.get_user_videos(username, count=count)
        return jsonify(videos)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/tiktok/<username>/analytics")
@login_required
def api_tiktok_analytics(username):
    try:
        profile = tiktok.get_user_info(username)
        if 'error' in profile:
            return jsonify(profile)
        videos = tiktok.get_user_videos(username, count=200) or []

        # --- Tarih araligi filtresi ---
        from_date = request.args.get('from', '')
        to_date = request.args.get('to', '')
        if from_date or to_date:
            from_ts = int(datetime.strptime(from_date, '%Y-%m-%d').timestamp()) if from_date else 0
            to_ts = int(datetime.strptime(to_date, '%Y-%m-%d').timestamp()) + 86399 if to_date else 9999999999
            videos = [v for v in videos if from_ts <= v.get('created_at', 0) <= to_ts]

        # --- Takipci gecmisi (filtrlenebilir) ---
        history = profile.get('history', [])
        follower_history_filtered = history
        if from_date or to_date:
            fh_from = from_date if from_date else '2000-01-01'
            fh_to = to_date if to_date else '2099-12-31'
            follower_history_filtered = [
                h for h in history
                if fh_from <= h.get('date', '')[:10] <= fh_to
            ]

        # Takipci artisi hesapla
        follower_growth_data = None
        if len(follower_history_filtered) >= 2:
            first = follower_history_filtered[0]
            last = follower_history_filtered[-1]
            net_growth = last.get('followers', 0) - first.get('followers', 0)
            first_date = first.get('date', '')[:10]
            last_date = last.get('date', '')[:10]
            follower_growth_data = {
                'start_followers': first.get('followers', 0),
                'end_followers': last.get('followers', 0),
                'net_growth': net_growth,
                'growth_rate': round((net_growth / max(1, first.get('followers', 1))) * 100, 2),
                'start_date': first_date,
                'end_date': last_date,
                'history': follower_history_filtered,
            }

        # --- Temel metrikler ---
        total_views = sum(v.get('play_count', 0) for v in videos)
        total_likes = sum(v.get('like_count', 0) for v in videos)
        total_comments = sum(v.get('comment_count', 0) for v in videos)
        total_shares = sum(v.get('share_count', 0) for v in videos)
        total_saves = sum(v.get('save_count', 0) for v in videos)
        total_engagement = total_likes + total_comments + total_shares + total_saves
        avg_views = total_views // len(videos) if videos else 0
        avg_likes = total_likes // len(videos) if videos else 0
        avg_comments = total_comments // len(videos) if videos else 0
        avg_shares = total_shares // len(videos) if videos else 0
        avg_saves = total_saves // len(videos) if videos else 0
        engagement_rate = round((total_engagement / total_views * 100), 2) if total_views > 0 else 0

        # --- Izlenme kalitesi ---
        avg_duration = sum(v.get('duration', 0) for v in videos) / len(videos) if videos else 0
        total_duration = sum(v.get('duration', 1) for v in videos)
        avg_view_per_second = total_views / max(1, total_duration)
        followers = profile.get('followers', 1)
        rewatch_rate = round(min(100, (avg_views / max(1, followers)) * 100), 1)

        # --- Sure bazli analiz ---
        short = [v for v in videos if v.get('duration', 0) <= 15]
        medium = [v for v in videos if 15 < v.get('duration', 0) <= 60]
        long = [v for v in videos if v.get('duration', 0) > 60]

        def avg_of(lst, key):
            if not lst:
                return 0
            return sum(v.get(key, 0) for v in lst) // len(lst)

        def eng_rate(lst):
            if not lst:
                return 0
            t = sum(v.get('play_count', 0) for v in lst)
            e = sum(v.get('like_count', 0) + v.get('comment_count', 0) + v.get('share_count', 0) for v in lst)
            return round((e / max(1, t)) * 100, 2)

        format_analysis = {
            'short': {'count': len(short), 'avg_views': avg_of(short, 'play_count'), 'avg_likes': avg_of(short, 'like_count'), 'avg_eng_rate': eng_rate(short)},
            'medium': {'count': len(medium), 'avg_views': avg_of(medium, 'play_count'), 'avg_likes': avg_of(medium, 'like_count'), 'avg_eng_rate': eng_rate(medium)},
            'long': {'count': len(long), 'avg_views': avg_of(long, 'play_count'), 'avg_likes': avg_of(long, 'like_count'), 'avg_eng_rate': eng_rate(long)},
        }

        # --- En iyi ve en kotu videolar ---
        by_views = sorted(videos, key=lambda v: v.get('play_count', 0), reverse=True)
        by_engagement = sorted(videos, key=lambda v: (v.get('like_count', 0) + v.get('comment_count', 0) + v.get('share_count', 0)), reverse=True)
        by_low = sorted(videos, key=lambda v: v.get('play_count', 0))

        # --- Hashtag analizi ---
        hashtag_stats = {}
        for v in videos:
            for tag in v.get('hashtags', []):
                if tag not in hashtag_stats:
                    hashtag_stats[tag] = {'count': 0, 'total_views': 0, 'total_likes': 0}
                hashtag_stats[tag]['count'] += 1
                hashtag_stats[tag]['total_views'] += v.get('play_count', 0)
                hashtag_stats[tag]['total_likes'] += v.get('like_count', 0)
        top_hashtags = sorted(hashtag_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)[:10]

        return jsonify({
            'profile': profile,
            'follower_growth': follower_growth_data,
            'summary': {
                'total_videos': len(videos),
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'total_shares': total_shares,
                'total_saves': total_saves,
                'avg_views': avg_views,
                'avg_likes': avg_likes,
                'avg_comments': avg_comments,
                'avg_shares': avg_shares,
                'avg_saves': avg_saves,
                'engagement_rate': engagement_rate,
            },
            'view_quality': {
                'avg_duration': round(avg_duration, 1),
                'avg_view_per_second': round(avg_view_per_second, 1),
                'rewatch_rate': rewatch_rate,
            },
            'format_analysis': format_analysis,
            'best_by_views': by_views[:5],
            'best_by_engagement': by_engagement[:5],
            'worst_videos': by_low[:5],
            'top_hashtags': [{'tag': t, **s} for t, s in top_hashtags],
            'all_videos': videos,
        })
    except Exception as e:
        return jsonify({'error': str(e)})


# ==================== INSTAGRAM ====================

@app.route("/api/instagram/login", methods=["POST"])
@login_required
def api_instagram_login():
    data = request.json
    if not data or not data.get("sessionid"):
        return jsonify({"success": False, "error": "sessionid degeri gerekli"})
    try:
        sessionid = data["sessionid"]
        csrftoken = data.get("csrftoken", "")
        instagram.login(sessionid, csrftoken)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/instagram/<username>")
@login_required
def api_instagram_user(username):
    try:
        data = instagram.get_user_info(username)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/instagram/<username>/posts")
@login_required
def api_instagram_posts(username):
    count = request.args.get("count", 30, type=int)
    try:
        posts = instagram.get_user_posts(username, count=count)
        return jsonify(posts)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/instagram/<username>/analytics")
@login_required
def api_instagram_analytics(username):
    count = request.args.get("count", 50, type=int)
    try:
        analytics = instagram.get_analytics(username, count=count)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({"error": str(e)})


# ==================== YOUTUBE ====================

@app.route("/api/youtube/search")
@login_required
def api_youtube_search():
    q = request.args.get('q', '')
    try:
        results = youtube.get_channel_search(q)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route("/api/youtube/channel/<channel_id>")
@login_required
def api_youtube_channel(channel_id):
    try:
        info = youtube.get_channel_info(channel_id)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route("/api/youtube/channel/<channel_id>/videos")
@login_required
def api_youtube_videos(channel_id):
    count = request.args.get('count', 30, type=int)
    try:
        videos = youtube.get_uploads(channel_id, count=count)
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route("/api/youtube/channel/<channel_id>/analytics")
@login_required
def api_youtube_analytics(channel_id):
    days = request.args.get('days', 30, type=int)
    try:
        info = youtube.get_channel_info(channel_id)
        if 'error' in info:
            return jsonify(info)
        videos = youtube.get_uploads(channel_id, count=200)

        # Tarih filtresi: son N gun
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        filtered_videos = [v for v in videos if v.get('published_at', '') and
                           datetime.strptime(v['published_at'], '%Y-%m-%dT%H:%M:%SZ').timestamp() >= cutoff]

        # Eger filtrelenmis video yoksa hepsini kullan
        if not filtered_videos:
            filtered_videos = videos

        # Video bazli hesaplamalar (filtrelenmis videolardan)
        total_views = sum(v.get('view_count', 0) for v in filtered_videos)
        total_likes = sum(v.get('like_count', 0) for v in filtered_videos)
        total_comments = sum(v.get('comment_count', 0) for v in filtered_videos)
        total_duration = sum(v.get('duration', 0) for v in filtered_videos)
        avg_duration = total_duration / len(filtered_videos) if filtered_videos else 0

        # Sure bazli analiz
        short = [v for v in filtered_videos if v.get('duration', 0) <= 60]
        medium = [v for v in filtered_videos if 60 < v.get('duration', 0) <= 600]
        long = [v for v in filtered_videos if v.get('duration', 0) > 600]

        def avg_of(lst, key):
            if not lst:
                return 0
            return sum(v.get(key, 0) for v in lst) // len(lst)

        # En iyi ve en kotu videolar
        by_views = sorted(filtered_videos, key=lambda v: v.get('view_count', 0), reverse=True)
        by_likes = sorted(filtered_videos, key=lambda v: v.get('like_count', 0), reverse=True)
        by_comments = sorted(filtered_videos, key=lambda v: v.get('comment_count', 0), reverse=True)
        by_low = sorted(filtered_videos, key=lambda v: v.get('view_count', 0))

        # Tag analizi
        tag_stats = {}
        for v in filtered_videos:
            for tag in v.get('tags', [])[:5]:
                if tag not in tag_stats:
                    tag_stats[tag] = {'count': 0, 'total_views': 0}
                tag_stats[tag]['count'] += 1
                tag_stats[tag]['total_views'] += v.get('view_count', 0)
        top_tags = sorted(tag_stats.items(), key=lambda x: x[1]['total_views'], reverse=True)[:10]

        return jsonify({
            'channel': info,
            'days': days,
            'filtered_count': len(filtered_videos),
            'summary': {
                'total_videos': info.get('total_videos', len(videos)),
                'total_views': info.get('total_views', total_views),
                'total_subscribers': info.get('subscribers', 0),
                'subscriber_growth': info.get('subscriber_growth', 0),
                'subscriber_growth_rate': info.get('subscriber_growth_rate', 0),
                'fetched_videos': len(filtered_videos),
                'avg_views': total_views // len(filtered_videos) if filtered_videos else 0,
                'avg_likes': total_likes // len(filtered_videos) if filtered_videos else 0,
                'avg_comments': total_comments // len(filtered_videos) if filtered_videos else 0,
                'avg_duration_sec': round(avg_duration, 1),
            },
            'duration_analysis': {
                'short': {'count': len(short), 'avg_views': avg_of(short, 'view_count'), 'avg_likes': avg_of(short, 'like_count')},
                'medium': {'count': len(medium), 'avg_views': avg_of(medium, 'view_count'), 'avg_likes': avg_of(medium, 'like_count')},
                'long': {'count': len(long), 'avg_views': avg_of(long, 'view_count'), 'avg_likes': avg_of(long, 'like_count')},
            },
            'best_by_views': by_views[:5],
            'best_by_likes': by_likes[:5],
            'best_by_comments': by_comments[:5],
            'worst_videos': by_low[:5],
            'top_tags': [{'tag': t, **s} for t, s in top_tags],
            'all_videos': filtered_videos,
        })
    except Exception as e:
        return jsonify({'error': str(e)})


# ==================== OVERVIEW ====================

@app.route("/api/overview")
@login_required
def api_overview():
    result = {
        'twitter': None,
        'tiktok': None,
        'youtube': None,
        'instagram': None,
    }

    # Twitter
    try:
        if client.is_logged_in():
            tw_user = client.get_user_info('infoyatirim')
            tw_tweets = client.get_user_tweets('infoyatirim', count=20)
            total_impressions = sum(int(t.get('view_count', 0) or 0) for t in tw_tweets)
            total_likes = sum(t.get('favorite_count', 0) for t in tw_tweets)
            total_rts = sum(t.get('retweet_count', 0) for t in tw_tweets)
            total_replies = sum(t.get('reply_count', 0) for t in tw_tweets)
            total_engagement = total_likes + total_rts + total_replies
            eng_rate = round((total_engagement / max(1, total_impressions)) * 100, 2)

            result['twitter'] = {
                'username': tw_user['username'],
                'name': tw_user['name'],
                'followers': tw_user['followers_count'],
                'following': tw_user['following_count'],
                'tweets': tw_user['tweets_count'],
                'follower_growth': tw_user.get('follower_growth', 0),
                'total_impressions': total_impressions,
                'engagement_rate': eng_rate,
                'total_likes': total_likes,
                'total_retweets': total_rts,
                'total_replies': total_replies,
                'profile_image': tw_user.get('profile_image_url', ''),
            }
    except Exception:
        pass

    # TikTok
    try:
        tt_user = tiktok.get_user_info('infoyatirim')
        if 'error' not in tt_user:
            tt_videos = tiktok.get_user_videos('infoyatirim', count=30)
            total_views = sum(v.get('play_count', 0) for v in tt_videos)
            total_likes = sum(v.get('like_count', 0) for v in tt_videos)
            total_comments = sum(v.get('comment_count', 0) for v in tt_videos)
            total_shares = sum(v.get('share_count', 0) for v in tt_videos)
            total_engagement = total_likes + total_comments + total_shares
            eng_rate = round((total_engagement / max(1, total_views)) * 100, 2)

            result['tiktok'] = {
                'username': tt_user['username'],
                'nickname': tt_user.get('nickname', ''),
                'followers': tt_user['followers'],
                'hearts': tt_user['hearts'],
                'videos': tt_user['videos'],
                'follower_growth': tt_user.get('follower_growth', 0),
                'follower_growth_rate': tt_user.get('follower_growth_rate', 0),
                'total_views': total_views,
                'engagement_rate': eng_rate,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'avatar': tt_user.get('avatar', ''),
            }
    except Exception:
        pass

    # YouTube
    try:
        yt_channel_id = 'UC-Il4FpbUEatDuaefVzqh8Q'
        yt_info = youtube.get_channel_info(yt_channel_id)
        yt_videos = youtube.get_uploads(yt_channel_id, count=30)
        total_views_vids = sum(v.get('view_count', 0) for v in yt_videos)
        total_likes_vids = sum(v.get('like_count', 0) for v in yt_videos)
        total_comments_vids = sum(v.get('comment_count', 0) for v in yt_videos)
        total_engagement_yt = total_likes_vids + total_comments_vids
        eng_rate_yt = round((total_engagement_yt / max(1, total_views_vids)) * 100, 2)

        result['youtube'] = {
            'channel_id': yt_info['id'],
            'title': yt_info['title'],
            'subscribers': yt_info['subscribers'],
            'total_views': yt_info['total_views'],
            'total_videos': yt_info['total_videos'],
            'subscriber_growth': yt_info.get('subscriber_growth', 0),
            'subscriber_growth_rate': yt_info.get('subscriber_growth_rate', 0),
            'engagement_rate': eng_rate_yt,
            'thumbnail': yt_info.get('thumbnail', ''),
        }
    except Exception:
        pass

    # Instagram
    try:
        if instagram.is_logged_in():
            ig_data = instagram.get_analytics('infoyatirim', count=20)
            if 'error' not in ig_data:
                summary = ig_data.get('summary', {})
                result['instagram'] = {
                    'username': ig_data['profile']['username'],
                    'full_name': ig_data['profile'].get('full_name', ''),
                    'followers': ig_data['profile']['followers'],
                    'following': ig_data['profile']['following'],
                    'media_count': ig_data['profile']['media_count'],
                    'engagement_rate': summary.get('engagement_rate', 0),
                    'total_likes': summary.get('total_likes', 0),
                    'total_comments': summary.get('total_comments', 0),
                    'profile_image': ig_data['profile'].get('profile_pic_url', ''),
                    'follower_growth': 0,
                }
    except Exception:
        pass

    return jsonify(result)


# ==================== RAKIP ANALIZI ====================

@app.route("/api/competitor/search")
@login_required
def api_competitor_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Arama terimi gerekli'})

    results = {'query': query, 'platforms': {}}

    # Twitter
    try:
        if not client.is_logged_in():
            results['platforms']['twitter'] = {'error': 'Giris yapilmamis'}
        else:
            tw = client.get_user_info(query)
            tw_tweets = client.get_user_tweets(query, count=10)
            total_impressions = sum(int(t.get('view_count', 0) or 0) for t in tw_tweets)
            total_likes = sum(t.get('favorite_count', 0) for t in tw_tweets)
            total_rts = sum(t.get('retweet_count', 0) for t in tw_tweets)
            total_eng = total_likes + total_rts
            eng_rate = round((total_eng / max(1, total_impressions)) * 100, 2)

            results['platforms']['twitter'] = {
                'username': tw['username'],
                'name': tw['name'],
                'followers': tw['followers_count'],
                'following': tw['following_count'],
                'tweets': tw['tweets_count'],
                'description': tw.get('description', ''),
                'profile_image': tw.get('profile_image_url', ''),
                'verified': tw.get('verified', False),
                'engagement_rate': eng_rate,
                'total_impressions': total_impressions,
                'total_likes': total_likes,
                'total_retweets': total_rts,
            }
    except Exception as e:
        print(f"[COMPETITOR] Twitter arama hatasi: {e}")
        results['platforms']['twitter'] = {'error': str(e)}

    # TikTok
    try:
        tt = tiktok.get_user_info(query)
        if 'error' in tt:
            results['platforms']['tiktok'] = {'error': tt['error']}
        else:
            tt_videos = tiktok.get_user_videos(query, count=20)
            total_views = sum(v.get('play_count', 0) for v in tt_videos)
            total_likes = sum(v.get('like_count', 0) for v in tt_videos)
            total_comments = sum(v.get('comment_count', 0) for v in tt_videos)
            total_eng = total_likes + total_comments
            eng_rate = round((total_eng / max(1, total_views)) * 100, 2)

            results['platforms']['tiktok'] = {
                'username': tt['username'],
                'nickname': tt.get('nickname', ''),
                'followers': tt['followers'],
                'hearts': tt['hearts'],
                'videos': tt['videos'],
                'description': tt.get('description', ''),
                'avatar': tt.get('avatar', ''),
                'verified': tt.get('verified', False),
                'engagement_rate': eng_rate,
                'total_views': total_views,
                'total_likes': total_likes,
            }
    except Exception as e:
        print(f"[COMPETITOR] TikTok arama hatasi: {e}")
        results['platforms']['tiktok'] = {'error': str(e)}

    # YouTube
    try:
        yt_results = youtube.get_channel_search(query)
        if yt_results:
            ch = yt_results[0]
            ch_info = youtube.get_channel_info(ch['id'])
            yt_videos = youtube.get_uploads(ch['id'], count=20)
            total_views = sum(v.get('view_count', 0) for v in yt_videos)
            total_likes = sum(v.get('like_count', 0) for v in yt_videos)
            total_comments = sum(v.get('comment_count', 0) for v in yt_videos)
            total_eng = total_likes + total_comments
            eng_rate = round((total_eng / max(1, total_views)) * 100, 2)

            results['platforms']['youtube'] = {
                'channel_id': ch_info['id'],
                'title': ch_info['title'],
                'subscribers': ch_info['subscribers'],
                'total_views': ch_info['total_views'],
                'total_videos': ch_info['total_videos'],
                'description': ch_info.get('description', '')[:200],
                'thumbnail': ch_info.get('thumbnail', ''),
                'engagement_rate': eng_rate,
            }
    except Exception:
        pass

    # Instagram
    try:
        if instagram.is_logged_in():
            ig_info = instagram.get_user_info(query)
            if 'error' not in ig_info:
                results['platforms']['instagram'] = {
                    'username': ig_info['username'],
                    'full_name': ig_info.get('full_name', ''),
                    'followers': ig_info['followers'],
                    'following': ig_info['following'],
                    'posts': ig_info['media_count'],
                    'biography': ig_info.get('biography', ''),
                    'profile_pic_url': ig_info.get('profile_pic_url', ''),
                    'is_private': ig_info.get('is_private', False),
                    'is_verified': ig_info.get('is_verified', False),
                }
    except Exception:
        pass

    # LinkedIn - sadece arama linki
    results['platforms']['linkedin'] = {
        'search_url': f'https://www.linkedin.com/search/results/all/?keywords={query}',
        'note': 'LinkedIn API erisimi sinirlidir. Profili icin linke tiklayin.',
    }

    return jsonify(results)


def _snapshot_follower(key, count):
    now_str = datetime.now(timezone.utc).isoformat()
    data = _get_history_session()
    if key not in data:
        data[key] = []
    entry = {'date': now_str, 'followers': count}
    # ayni gun varsa guncelle, yoksa ekle
    today = now_str[:10]
    found = False
    for i, h in enumerate(data[key]):
        if h['date'][:10] == today:
            data[key][i] = entry
            found = True
            break
    if not found:
        data[key].append(entry)
    if len(data[key]) > 30:
        data[key] = data[key][-30:]
    _set_history_session(data)

@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/api/competitor/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route("/api/competitor/<platform>/<username>")
@login_required
def api_competitor_detail(platform, username):
    """Tek bir platform icin detayli veri cek. ?days=30 ile tarih filtrele."""
    days = request.args.get('days', 30, type=int)
    cache_key = f"{platform}:{username}:{days}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)

    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()

        def parse_ts(item):
            fields = ('created_at', 'published_at', 'taken_at', 'date_ts', 'createTime')
            raw = 0
            for f in fields:
                val = item.get(f)
                if val:
                    raw = val
                    break
            if isinstance(raw, (int, float)):
                if raw > 1e12:
                    return raw / 1000
                return raw
            if isinstance(raw, str):
                s = raw.strip()
                fmts = ('%a %b %d %H:%M:%S %z %Y', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S%z')
                for fmt in fmts:
                    try:
                        return datetime.strptime(s, fmt).timestamp()
                    except: pass
            return 0

        if platform == 'twitter':
            if not client.is_logged_in():
                return jsonify({'error': 'Twitter giris yapilmamis'})
            user = client.get_user_info(username)
            tweets = client.get_user_tweets(username, count=50)
            tweets = [t for t in tweets if parse_ts(t) >= cutoff]

            total_impressions = sum(int(t.get('view_count', 0) or 0) for t in tweets)
            total_likes = sum(t.get('favorite_count', 0) for t in tweets)
            total_rts = sum(t.get('retweet_count', 0) for t in tweets)
            total_replies = sum(t.get('reply_count', 0) for t in tweets)
            total_eng = total_likes + total_rts + total_replies
            eng_rate = round((total_eng / max(1, total_impressions)) * 100, 2)

            original = [t for t in tweets if not t.get('is_retweet') and not t.get('text', '').startswith('RT')]
            retweets = [t for t in tweets if t.get('is_retweet') or t.get('text', '').startswith('RT')]
            with_media = [t for t in tweets if t.get('media')]

            data = {
                'profile': user,
                'tweets': tweets,
                'analytics': {
                    'total_impressions': total_impressions,
                    'total_likes': total_likes,
                    'total_retweets': total_rts,
                    'total_replies': total_replies,
                    'engagement_rate': eng_rate,
                    'avg_impressions': total_impressions // len(tweets) if tweets else 0,
                    'original_count': len(original),
                    'retweet_count': len(retweets),
                    'media_count': len(with_media),
                },
                'best_tweets': sorted(tweets, key=lambda t: int(t.get('view_count', 0) or 0), reverse=True)[:5],
            }
            _snapshot_follower(f"twitter:{user['username']}", user.get('followers_count', 0))
            _cache_set(cache_key, data)
            return jsonify(data)

        elif platform == 'tiktok':
            user = tiktok.get_user_info(username)
            if 'error' in user:
                return jsonify(user)
            videos = tiktok.get_user_videos(username, count=100)
            videos = [v for v in videos if parse_ts(v) >= cutoff]

            total_views = sum(v.get('play_count', 0) for v in videos)
            total_likes = sum(v.get('like_count', 0) for v in videos)
            total_comments = sum(v.get('comment_count', 0) for v in videos)
            total_shares = sum(v.get('share_count', 0) for v in videos)
            total_eng = total_likes + total_comments + total_shares
            eng_rate = round((total_eng / max(1, total_views)) * 100, 2)

            short = [v for v in videos if v.get('duration', 0) <= 15]
            medium = [v for v in videos if 15 < v.get('duration', 0) <= 60]
            long = [v for v in videos if v.get('duration', 0) > 60]

            def avg_of(lst, key):
                if not lst: return 0
                return sum(v.get(key, 0) for v in lst) // len(lst)

            data = {
                'profile': user,
                'videos': videos,
                'analytics': {
                    'total_views': total_views,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'total_shares': total_shares,
                    'engagement_rate': eng_rate,
                    'avg_views': total_views // len(videos) if videos else 0,
                },
                'format_analysis': {
                    'short': {'count': len(short), 'avg_views': avg_of(short, 'play_count'), 'avg_likes': avg_of(short, 'like_count')},
                    'medium': {'count': len(medium), 'avg_views': avg_of(medium, 'play_count'), 'avg_likes': avg_of(medium, 'like_count')},
                    'long': {'count': len(long), 'avg_views': avg_of(long, 'play_count'), 'avg_likes': avg_of(long, 'like_count')},
                },
                'best_videos': sorted(videos, key=lambda v: v.get('play_count', 0), reverse=True)[:5],
            }
            _snapshot_follower(f"tiktok:{user['username']}", user.get('followers', 0))
            _cache_set(cache_key, data)
            return jsonify(data)

        elif platform == 'youtube':
            ch_info = youtube.get_channel_info(username)
            videos = youtube.get_uploads(username, count=100)
            videos = [v for v in videos if parse_ts(v) >= cutoff]

            total_views = sum(v.get('view_count', 0) for v in videos)
            total_likes = sum(v.get('like_count', 0) for v in videos)
            total_comments = sum(v.get('comment_count', 0) for v in videos)
            total_eng = total_likes + total_comments
            eng_rate = round((total_eng / max(1, total_views)) * 100, 2)

            data = {
                'channel': ch_info,
                'videos': videos,
                'analytics': {
                    'total_views': total_views,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'engagement_rate': eng_rate,
                    'avg_views': total_views // len(videos) if videos else 0,
                    'avg_likes': total_likes // len(videos) if videos else 0,
                },
                'best_videos': sorted(videos, key=lambda v: v.get('view_count', 0), reverse=True)[:5],
            }
            _snapshot_follower(f"youtube:{ch_info.get('id', username)}", ch_info.get('subscribers', 0))
            _cache_set(cache_key, data)
            return jsonify(data)

        elif platform == 'instagram':
            analytics = instagram.get_analytics(username, count=100)
            if 'error' in analytics:
                return jsonify(analytics)
            posts = analytics.get('posts', [])
            posts = [p for p in posts if parse_ts(p) >= cutoff]
            analytics['posts'] = posts
            analytics['count'] = len(posts)
            if posts:
                analytics['avg_likes'] = sum(p.get('likes', 0) for p in posts) // len(posts)
                analytics['avg_comments'] = sum(p.get('comments', 0) for p in posts) // len(posts)
            profile = analytics.get('profile', {})
            _snapshot_follower(f"instagram:{profile.get('username', username)}", profile.get('followers', 0))
            _cache_set(cache_key, analytics)
            return jsonify(analytics)

        else:
            return jsonify({'error': f'{platform} desteklenmiyor'})
    except Exception as e:
        return jsonify({'error': str(e)})


# ==================== WATCHLIST ====================
_watchlists = {}

@app.route("/api/watchlist", methods=["GET"])
@login_required
def api_watchlist_get():
    user = session.get('username', 'default')
    items = _watchlists.get(user, [])
    return jsonify({'items': items})

@app.route("/api/watchlist", methods=["POST"])
@login_required
def api_watchlist_add():
    data = request.json
    if not data or not data.get('platform') or not data.get('username'):
        return jsonify({'error': 'platform ve username gerekli'}), 400
    user = session.get('username', 'default')
    if user not in _watchlists:
        _watchlists[user] = []
    new_item = {
        'id': secrets.token_hex(6),
        'platform': data['platform'],
        'username': data['username'],
        'name': data.get('name', data['username']),
        'added_at': datetime.now(timezone.utc).isoformat(),
        'last_follower_count': data.get('last_follower_count', 0),
    }
    _watchlists[user].append(new_item)
    return jsonify({'success': True, 'item': new_item})

@app.route("/api/watchlist/<item_id>", methods=["DELETE"])
@login_required
def api_watchlist_remove(item_id):
    user = session.get('username', 'default')
    items = _watchlists.get(user, [])
    _watchlists[user] = [i for i in items if i.get('id') != item_id]
    return jsonify({'success': True})


# ==================== SIDE-BY-SIDE COMPARE ====================
_compare_cache = {}

@app.route("/api/competitor/compare", methods=["POST"])
@login_required
def api_competitor_compare():
    data = request.json
    entities = data.get('entities', [])
    if not entities:
        return jsonify({'error': 'Karsilastirilacak hesap listesi gerekli'}), 400
    if len(entities) < 2:
        return jsonify({'error': 'En az 2 hesap gerekli'}), 400

    results = []
    for entity in entities:
        platform = entity.get('platform', '').lower()
        username = entity.get('username', '').lower().strip()
        if not platform or not username:
            continue

        cache_key = f"cmp:{platform}:{username}"
        cached = _compare_cache.get(cache_key)
        if cached and _time.time() - cached['t'] < 300:
            results.append(cached['data'])
            continue

        entry = {'platform': platform, 'username': username, 'error': None}
        try:
            if platform == 'twitter':
                if client.is_logged_in():
                    u = client.get_user_info(username)
                    tw_tweets = client.get_user_tweets(username, count=20)
                    imp = sum(int(t.get('view_count', 0) or 0) for t in tw_tweets)
                    likes = sum(t.get('favorite_count', 0) for t in tw_tweets)
                    eng_rate = round((likes / max(1, imp)) * 100, 2) if imp else 0
                    entry.update({
                        'name': u.get('name', username), 'followers': u.get('followers_count', 0),
                        'following': u.get('following_count', 0), 'tweets': u.get('tweets_count', 0),
                        'engagement_rate': eng_rate, 'profile_image': u.get('profile_image_url', ''),
                        'total_impressions': imp, 'total_likes': likes,
                    })
                else:
                    entry['error'] = 'Twitter giris yapilmamis'
            elif platform == 'tiktok':
                u = tiktok.get_user_info(username)
                if 'error' not in u:
                    tt_videos = tiktok.get_user_videos(username, count=20)
                    v = sum(v.get('play_count', 0) for v in tt_videos)
                    l = sum(v.get('like_count', 0) for v in tt_videos)
                    er = round((l / max(1, v)) * 100, 2) if v else 0
                    entry.update({
                        'name': u.get('nickname', username), 'followers': u.get('followers', 0),
                        'hearts': u.get('hearts', 0), 'videos': u.get('videos', 0),
                        'engagement_rate': er, 'avatar': u.get('avatar', ''),
                        'total_views': v, 'total_likes': l,
                    })
                else:
                    entry['error'] = u['error']
            elif platform == 'youtube':
                yt_search = youtube.get_channel_search(username)
                if yt_search:
                    ch = youtube.get_channel_info(yt_search[0]['id'])
                    yt_v = youtube.get_uploads(yt_search[0]['id'], count=20)
                    vi = sum(v.get('view_count', 0) for v in yt_v)
                    li = sum(v.get('like_count', 0) for v in yt_v)
                    er = round((li / max(1, vi)) * 100, 2) if vi else 0
                    entry.update({
                        'name': ch.get('title', username), 'followers': ch.get('subscribers', 0),
                        'total_views': ch.get('total_views', 0), 'videos': ch.get('total_videos', 0),
                        'engagement_rate': er, 'thumbnail': ch.get('thumbnail', ''),
                    })
                else:
                    entry['error'] = 'Kanal bulunamadi'
            elif platform == 'instagram':
                ig_info = instagram.get_user_info(username)
                if 'error' not in ig_info:
                    ig_posts = []
                    try:
                        analytics = instagram.get_analytics(username, count=50)
                        ig_posts = analytics.get('posts', [])
                    except Exception:
                        try:
                            ig_posts = instagram.get_user_posts(username, count=50)
                        except Exception:
                            pass
                    ig_views = sum(p.get('likes', 0) for p in ig_posts) * 3
                    ig_likes = sum(p.get('likes', 0) for p in ig_posts)
                    ig_comments = sum(p.get('comments', 0) for p in ig_posts)
                    ig_eng = ig_likes + ig_comments
                    ig_er = round((ig_eng / max(1, ig_info.get('followers', 1))) * 100, 2)

                    entry.update({
                        'name': ig_info.get('full_name', username), 'followers': ig_info.get('followers', 0),
                        'following': ig_info.get('following', 0), 'posts': ig_info.get('media_count', 0),
                        'profile_pic': ig_info.get('profile_pic_url', ''),
                        'total_likes': ig_likes, 'total_views': ig_views,
                        'engagement_rate': ig_er,
                    })
                else:
                    entry['error'] = ig_info['error']
        except Exception as e:
            entry['error'] = str(e)

        _compare_cache[cache_key] = {'data': entry, 't': _time.time()}
        results.append(entry)

    return jsonify({'comparison': results})


# ==================== HASHTAG INTELLIGENCE ====================
@app.route("/api/hashtag/analytics")
@login_required
def api_hashtag_analytics():
    query = request.args.get('q', '').strip()
    platform = request.args.get('platform', 'tiktok').lower()
    if not query:
        return jsonify({'error': 'Hashtag sorgusu gerekli'})

    result = {'hashtag': query, 'platform': platform, 'analytics': []}

    if platform == 'tiktok':
        try:
            # En cok etkilesim alan videolardan hashtag analizi
            search_videos = tiktok.get_user_videos(query, count=100) if query else []
            if not search_videos:
                result['note'] = 'Kullanici bulunamadi, hashtag trend verisi gosterilemiyor'
            else:
                hashtag_map = {}
                for v in search_videos:
                    for tag in v.get('hashtags', []):
                        if tag not in hashtag_map:
                            hashtag_map[tag] = {'count': 0, 'total_views': 0, 'total_likes': 0, 'total_comments': 0}
                        hashtag_map[tag]['count'] += 1
                        hashtag_map[tag]['total_views'] += v.get('play_count', 0)
                        hashtag_map[tag]['total_likes'] += v.get('like_count', 0)
                        hashtag_map[tag]['total_comments'] += v.get('comment_count', 0)

                sorted_tags = sorted(hashtag_map.items(), key=lambda x: x[1]['total_views'], reverse=True)[:20]
                for tag, stats in sorted_tags:
                    avg_eng = round((stats['total_likes'] + stats['total_comments']) / max(1, stats['count']), 1)
                    result['analytics'].append({
                        'tag': tag, 'frequency': stats['count'],
                        'total_views': stats['total_views'], 'total_likes': stats['total_likes'],
                        'total_comments': stats['total_comments'], 'avg_engagement': avg_eng,
                    })
        except Exception as e:
            result['error'] = str(e)

    elif platform == 'instagram':
        try:
            ig_posts = instagram.get_user_posts(query, count=100) if query else []
            if not ig_posts:
                result['note'] = 'Instagram kullanicisi bulunamadi'
            else:
                hashtag_map = {}
                for p in ig_posts:
                    caption = p.get('caption', '') or ''
                    tags = [t.strip('#').lower() for t in caption.split() if t.startswith('#')]
                    for tag in tags:
                        if tag not in hashtag_map:
                            hashtag_map[tag] = {'count': 0, 'total_likes': 0, 'total_comments': 0}
                        hashtag_map[tag]['count'] += 1
                        hashtag_map[tag]['total_likes'] += p.get('likes', 0)
                        hashtag_map[tag]['total_comments'] += p.get('comments', 0)

                sorted_tags = sorted(hashtag_map.items(), key=lambda x: x[1]['total_likes'], reverse=True)[:20]
                for tag, stats in sorted_tags:
                    avg_eng = round((stats['total_likes'] + stats['total_comments']) / max(1, stats['count']), 1)
                    result['analytics'].append({
                        'tag': tag, 'frequency': stats['count'],
                        'total_likes': stats['total_likes'], 'total_comments': stats['total_comments'],
                        'avg_engagement': avg_eng,
                    })
        except Exception as e:
            result['error'] = str(e)

    elif platform == 'twitter':
        try:
            if not client.is_logged_in():
                result['error'] = 'Twitter giris yapilmamis'
            else:
                tw_posts = client.get_user_tweets(query, count=200)
                if not tw_posts:
                    result['note'] = 'Kullanici tweetleri bulunamadi'
                else:
                    hashtag_map = {}
                    for t in tw_posts:
                        text = t.get('text', '') or ''
                        tags = [t.strip('#').lower() for t in text.split() if t.startswith('#')]
                        for tag in tags:
                            if tag not in hashtag_map:
                                hashtag_map[tag] = {'count': 0, 'total_views': 0, 'total_likes': 0, 'total_retweets': 0}
                            hashtag_map[tag]['count'] += 1
                            hashtag_map[tag]['total_views'] += int(t.get('view_count', 0) or 0)
                            hashtag_map[tag]['total_likes'] += t.get('favorite_count', 0)
                            hashtag_map[tag]['total_retweets'] += t.get('retweet_count', 0)

                    sorted_tags = sorted(hashtag_map.items(), key=lambda x: x[1]['total_views'], reverse=True)[:20]
                    for tag, stats in sorted_tags:
                        avg_eng = round((stats['total_likes'] + stats['total_retweets']) / max(1, stats['count']), 1)
                        result['analytics'].append({
                            'tag': tag, 'frequency': stats['count'],
                            'total_views': stats['total_views'], 'total_likes': stats['total_likes'],
                            'total_retweets': stats['total_retweets'], 'avg_engagement': avg_eng,
                        })
        except Exception as e:
            result['error'] = str(e)

    return jsonify(result)


# ==================== CSV EXPORT ====================
@app.route("/api/competitor/<platform>/<username>/export")
@login_required
def api_competitor_export(platform, username):
    from io import StringIO
    import csv as csv_module

    days = request.args.get('days', 30, type=int)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()

    rows = []
    headers = []
    filename = f"{platform}_{username}_export.csv"

    try:
        if platform == 'twitter':
            if not client.is_logged_in():
                return jsonify({'error': 'Twitter giris yapilmamis'}), 400
            tweets = client.get_user_tweets(username, count=200)
            headers = ['Tarih', 'Metin', 'Gosterim', 'Begeni', 'RT', 'Yanit', 'Tur']
            for t in tweets:
                ts = t.get('created_at', '')
                rows.append([
                    str(ts), t.get('text', '')[:200].replace('\n', ' '),
                    t.get('view_count', 0), t.get('favorite_count', 0),
                    t.get('retweet_count', 0), t.get('reply_count', 0),
                    'RT' if t.get('is_retweet') else 'Original',
                ])
        elif platform == 'tiktok':
            videos = tiktok.get_user_videos(username, count=200)
            headers = ['Tarih', 'Aciklama', 'Izlenme', 'Begeni', 'Yorum', 'Paylasim', 'Sure']
            for v in videos:
                rows.append([
                    str(v.get('created_at', '')), (v.get('desc', '') or '')[:200].replace('\n', ' '),
                    v.get('play_count', 0), v.get('like_count', 0),
                    v.get('comment_count', 0), v.get('share_count', 0),
                    v.get('duration', 0),
                ])
        elif platform == 'youtube':
            ch_videos = youtube.get_uploads(username, count=200)
            headers = ['Tarih', 'Baslik', 'Izlenme', 'Begeni', 'Yorum', 'Sure']
            for v in ch_videos:
                rows.append([
                    v.get('published_at', ''), v.get('title', '')[:200].replace('\n', ' '),
                    v.get('view_count', 0), v.get('like_count', 0),
                    v.get('comment_count', 0), v.get('duration', 0),
                ])
        elif platform == 'instagram':
            ig_posts = instagram.get_user_posts(username, count=200) if instagram.is_logged_in() else []
            headers = ['Tarih', 'Aciklama', 'Begeni', 'Yorum', 'Tur']
            for p in ig_posts:
                rows.append([
                    str(p.get('date_ts', '')), (p.get('caption', '') or '')[:200].replace('\n', ' '),
                    p.get('likes', 0), p.get('comments', 0),
                    'Video' if p.get('is_video') else 'Foto',
                ])
        else:
            return jsonify({'error': f'{platform} desteklenmiyor'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    output = StringIO()
    writer = csv_module.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    csv_content = output.getvalue()
    output.close()

    from flask import Response
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


# ==================== FOLLOWER HISTORY SNAPSHOT ====================

def _get_history_session():
    return session.get('follower_history', {})

def _set_history_session(data):
    session['follower_history'] = data
    session.modified = True

def _fetch_live_followers(platform, username):
    try:
        if platform == 'twitter':
            if client.is_logged_in():
                u = client.get_user_info(username)
                return u.get('followers_count', 0)
        elif platform == 'tiktok':
            u = tiktok.get_user_info(username)
            if 'error' not in u:
                return u.get('followers', 0)
        elif platform == 'youtube':
            ch = youtube.get_channel_info(username)
            return ch.get('subscribers', 0)
        elif platform == 'instagram':
            info = instagram.get_user_info(username)
            if 'error' not in info:
                return info.get('followers', 0)
    except Exception:
        pass
    return None

@app.route("/api/history/<platform>/<username>")
@login_required
def api_follower_history(platform, username):
    """Takipci degisim gecmisini dondurur (son 30 gun) + canli snapshot"""
    key = f"{platform}:{username}"
    data = _get_history_session()
    history = data.get(key, [])

    # Canli veriyi cek - ayni yontemleri competitor detail gibi kullan
    live_count = None
    try:
        if platform == 'twitter':
            if client.is_logged_in():
                u = client.get_user_info(username)
                live_count = u.get('followers_count', 0)
        elif platform == 'tiktok':
            u = tiktok.get_user_info(username)
            if 'error' not in u:
                live_count = u.get('followers', 0)
        elif platform == 'youtube':
            ch = youtube.get_channel_info(username)
            live_count = ch.get('subscribers', 0)
        elif platform == 'instagram':
            info = instagram.get_user_info(username)
            if 'error' not in info:
                live_count = info.get('followers', 0)
    except Exception:
        pass

    if live_count is not None:
        _snapshot_follower(key, live_count)
        data = _get_history_session()
        history = data.get(key, [])

    if not history and live_count is None:
        return jsonify({'platform': platform, 'username': username, 'history': [], 'error': 'canli_veri_yok'})

    if not history and live_count is not None:
        return jsonify({'platform': platform, 'username': username, 'history': [{'date': datetime.now(timezone.utc).isoformat(), 'followers': live_count}]})

    return jsonify({'platform': platform, 'username': username, 'history': history})


@app.route("/api/trend/<platform>/<username>")
@login_required
def api_trend_analysis(platform, username):
    """Son 30 gunluk trend analizi: frekans, etkilesim, buyume ivmesi"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).timestamp()
    prior_cutoff = (datetime.now(timezone.utc) - timedelta(days=60)).timestamp()

    def parse_ts(item):
        fields = ('created_at', 'published_at', 'taken_at', 'date_ts', 'createTime')
        raw = 0
        for f in fields:
            val = item.get(f)
            if val: raw = val; break
        if isinstance(raw, (int, float)):
            return raw / 1000 if raw > 1e12 else raw
        if isinstance(raw, str):
            for fmt in ('%a %b %d %H:%M:%S %z %Y', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S%z'):
                try: return datetime.strptime(raw.strip(), fmt).timestamp()
                except: pass
        return 0

    result = {'platform': platform, 'username': username, 'trends': {}}

    try:
        if platform == 'twitter':
            if not client.is_logged_in():
                return jsonify({'error': 'Twitter giris yapilmamis'})
            tweets = client.get_user_tweets(username, count=50)
            tweets_30 = [t for t in tweets if parse_ts(t) >= cutoff]
            tweets_60 = [t for t in tweets if cutoff > parse_ts(t) >= prior_cutoff]

            def freq(items): return round(len(items) / 30, 1)
            def eng(items):
                imp = sum(int(t.get('view_count', 0) or 0) for t in items) or 1
                like = sum(t.get('favorite_count', 0) for t in items)
                return round((like / imp) * 100, 2)

            f30 = freq(tweets_30); f60 = freq(tweets_60)
            e30 = eng(tweets_30); e60 = eng(tweets_60)
            result['trends']['posting_frequency'] = {'current': f30, 'previous': f60, 'change': round(f30 - f60, 1)}
            result['trends']['engagement'] = {'current': e30, 'previous': e60, 'change': round(e30 - e60, 2)}
            if tweets_30:
                dates = sorted(set(datetime.fromtimestamp(parse_ts(t)).strftime('%Y-%m-%d') for t in tweets_30 if parse_ts(t)))
                result['trends']['active_days'] = len(dates)
                result['trends']['daily_cadence'] = round(len(tweets_30) / max(1, len(dates)), 1)

        elif platform == 'tiktok':
            user = tiktok.get_user_info(username)
            if 'error' in user:
                return jsonify(user)
            videos = tiktok.get_user_videos(username, count=200)
            v30 = [v for v in videos if parse_ts(v) >= cutoff]
            v60 = [v for v in videos if cutoff > parse_ts(v) >= prior_cutoff]

            def freq_v(items): return round(len(items) / 30, 1)
            def eng_v(items):
                views = sum(v.get('play_count', 0) for v in items) or 1
                likes = sum(v.get('like_count', 0) for v in items)
                return round((likes / views) * 100, 2)
            def avg_views(items):
                return sum(v.get('play_count', 0) for v in items) // max(1, len(items))

            f30 = freq_v(v30); f60 = freq_v(v60)
            e30 = eng_v(v30); e60 = eng_v(v60)
            av30 = avg_views(v30); av60 = avg_views(v60)
            result['trends']['posting_frequency'] = {'current': f30, 'previous': f60, 'change': round(f30 - f60, 1)}
            result['trends']['engagement'] = {'current': e30, 'previous': e60, 'change': round(e30 - e60, 2)}
            result['trends']['avg_views'] = {'current': av30, 'previous': av60, 'change': round(av30 - av60, 1)}
            if v30:
                dates = sorted(set(datetime.fromtimestamp(parse_ts(v)).strftime('%Y-%m-%d') for v in v30 if parse_ts(v)))
                result['trends']['active_days'] = len(dates)

        elif platform == 'youtube':
            ch = youtube.get_channel_info(username)
            videos = youtube.get_uploads(username, count=200)
            v30 = [v for v in videos if parse_ts(v) >= cutoff]
            v60 = [v for v in videos if cutoff > parse_ts(v) >= prior_cutoff]

            def freq_v(items): return round(len(items) / 30, 1)
            def eng_v(items):
                views = sum(v.get('view_count', 0) for v in items) or 1
                likes = sum(v.get('like_count', 0) for v in items)
                return round((likes / views) * 100, 2)

            f30 = freq_v(v30); f60 = freq_v(v60)
            e30 = eng_v(v30); e60 = eng_v(v60)
            result['trends']['posting_frequency'] = {'current': f30, 'previous': f60, 'change': round(f30 - f60, 1)}
            result['trends']['engagement'] = {'current': e30, 'previous': e60, 'change': round(e30 - e60, 2)}
            if v30:
                dates = sorted(set(datetime.fromtimestamp(parse_ts(v)).strftime('%Y-%m-%d') for v in v30 if parse_ts(v)))
                result['trends']['active_days'] = len(dates)

        elif platform == 'instagram':
            info = instagram.get_user_info(username)
            if 'error' in info:
                return jsonify(info)
            try:
                analytics = instagram.get_analytics(username, count=100)
                posts = analytics.get('posts', [])
            except:
                posts = instagram.get_user_posts(username, count=100) if instagram.is_logged_in() else []
            p30 = [p for p in posts if parse_ts(p) >= cutoff]
            p60 = [p for p in posts if cutoff > parse_ts(p) >= prior_cutoff]

            def freq_p(items): return round(len(items) / 30, 1)
            def eng_p(items):
                likes = sum(p.get('likes', 0) for p in items)
                return round(likes / max(1, len(items)), 1)

            f30 = freq_p(p30); f60 = freq_p(p60)
            e30 = eng_p(p30); e60 = eng_p(p60)
            result['trends']['posting_frequency'] = {'current': f30, 'previous': f60, 'change': round(f30 - f60, 1)}
            result['trends']['avg_likes'] = {'current': e30, 'previous': e60, 'change': round(e30 - e60, 1)}
            if p30:
                dates = sorted(set(datetime.fromtimestamp(parse_ts(p)).strftime('%Y-%m-%d') for p in p30 if parse_ts(p)))
                result['trends']['active_days'] = len(dates)

    except Exception as e:
        return jsonify({'error': str(e)})

    return jsonify(result)


@app.route("/api/influencer/search")
@login_required
def api_influencer_search():
    """Belirli bir konuda icerik ureten influencer'lari ara - genis hashtag tabanli."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Arama terimi gerekli'})

    results = {'query': query, 'influencers': []}
    seen_keys = set()

    def add_inf(key, name, platforms, source):
        k = key.lower().strip()
        if k in seen_keys: return False
        seen_keys.add(k)
        total_followers = 0
        for p in platforms.values():
            total_followers += p.get('followers', 0) or p.get('subscribers', 0) or 0
        results['influencers'].append({
            'username': key,
            'name': name or key,
            'platforms': platforms,
            'source': source,
            'total_followers': total_followers,
        })
        return True

    # ========== TUM HASHTAGLAR ==========
    ALL_HASHTAGS = [
        '#borsa', '#yatirim', '#hisse', '#hissesenedi', '#bist', '#bist100',
        '#abdborasalari', '#wallstreet', '#s&p500', '#nasdaq', '#dowjones',
        '#yatirimfonu', '#temettu', '#portfoy', '#teknikanaliz', '#trade',
        '#forex', '#kripto', '#altin', '#dolar', '#ekonomi', '#finans',
        '#fon', '#broker', '#komisyon', '#viop', '#vadeli', '#swap',
        '#emeklilikfonu', '#bireyselemeklilik', '#bes', '#endeks',
        '#faiz', '#enflasyon', '#merkezbankasi', '#fed', '#tcmb',
        '#karlilik', '#buysell', '#al-sat', '#gunlukborsa',
        '#finansalokuryazarlik', '#borsaistanbul',
        '#abdpiyasaları', '#usamarkets', '#investing',
    ]

    # Kullanicinin aradigi kelimeyle ilgili hashtaglari bul
    query_lower = query.lower()
    query_words = set(query_lower.split())
    selected_tags = [t for t in ALL_HASHTAGS if any(w in t.lower() for w in query_words)]
    if not selected_tags:
        selected_tags = ALL_HASHTAGS[:20]

    # ========== TWITTER DETAYLI ARAMA ==========
    twitter_user_scores = {}  # username -> gorulme sikligi
    twitter_user_info = {}    # username -> {name, followers}

    if client.is_logged_in():
        # 1. Tum hashtag'lerde ara, kullanicilari topla
        for tag in selected_tags:
            try:
                tweets = client.search_tweets(tag[1:], count=40)
                for t in tweets:
                    u = t.get('user')
                    if u and u.get('username'):
                        uname = u['username'].lower()
                        twitter_user_scores[uname] = twitter_user_scores.get(uname, 0) + 1
                        # Kullanici ismini tweet'ten al
                        if uname not in twitter_user_info:
                            twitter_user_info[uname] = {
                                'username': u['username'],
                                'name': u.get('name', u['username']),
                                'followers': 0,
                            }
            except Exception:
                pass

        # 2. En cok gorulen 80 kullanicinin profilini cek
        ranked = sorted(twitter_user_scores.items(), key=lambda x: -x[1])
        fetched = 0
        for uname_lower, score in ranked:
            if fetched >= 80:
                break
            info = twitter_user_info.get(uname_lower, {})
            username = info.get('username', uname_lower)
            display_name = info.get('name', username)
            try:
                profile = client.get_user_info(username)
                follower_count = profile.get('followers_count', 0)
                twitter_user_info[uname_lower]['followers'] = follower_count
                # Sadece 500+ takipcisi olanlari ekle
                if follower_count >= 500:
                    add_inf(username, profile.get('name', display_name), {
                        'twitter': {
                            'username': username,
                            'followers': follower_count,
                            'best_tweet': '',
                            'total_views': 0,
                            'total_likes': 0,
                        }
                    }, 'twitter')
                    fetched += 1
            except Exception:
                # Rate limit vs - score'u dusuk olanlari atla
                if score < 2:
                    continue
                # Rate limit vurduysa hic profile cekemeyenleri tweet bilgisiyle ekle
                if score >= 3:
                    add_inf(username, display_name, {
                        'twitter': {
                            'username': username,
                            'followers': 0,
                            'best_tweet': '',
                            'total_views': 0,
                            'total_likes': 0,
                        }
                    }, 'twitter')
                    fetched += 1

    # ========== YOUTUBE ARAMA ==========
    try:
        for yt_query in selected_tags[:8]:
            try:
                yt_channels = youtube.get_channel_search(yt_query[1:] if yt_query.startswith('#') else yt_query)
                for ch in yt_channels[:10]:
                    cid = ch.get('id', '')
                    if not cid: continue
                    try:
                        ch_info = youtube.get_channel_info(cid)
                        title = ch_info.get('title', '')
                        subs = ch_info.get('subscribers', 0)
                        if subs < 500:
                            continue
                        key = f"yt:{cid}"
                        if add_inf(key, title, {
                            'youtube': {
                                'channel_id': cid,
                                'title': title,
                                'subscribers': subs,
                                'thumbnail': ch_info.get('thumbnail', ''),
                            }
                        }, 'youtube'):
                            pass
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception:
        pass

    # ========== INSTAGRAM ARAMA ==========
    KNOWN_FINANCE_INSTAGRAM = {
        'borsa': ['caglasekerc', 'borsa_ogreniyorum', 'borsa.egitim', 'borsa_uzmani', 'borsa.takip', 'borsaistanbul_', 'borsa_analiz', 'borsa_hisse', 'borsa_yatirim', 'hisse_senedi'],
        'yatirim': ['caglasekerc', 'destinasaccilarli', 'temettuhocam', 'yatirimtavsiyem', 'yatirim_gunlugum', 'yatirimci_akademi', 'finans_yatirim', 'yatirim.firsatlari', 'yatirimportfoyu', 'yatirimtavsiyeleri'],
        'temettu': ['temettuhocam', 'temettuyatirimi', 'temettuhisseleri', 'temettu_gunlugu', 'temettuportfoyu'],
        'finans': ['finansdersleri', 'finansal_okuryazarlik', 'finans.ve.ekonomi', 'finans.egitim', 'kisiselfinans', 'finansrehberi'],
        'ekonomi': ['ekonomianaliz', 'ekonomi_gunlugu', 'turkiyeekonomisi', 'ekonomi_takip', 'ekonomi.ve.finans'],
        'hisse senedi': ['caglasekerc', 'hisse_senedi_analiz', 'hisseanaliz', 'hisseler', 'hissesenedi_yatirimi', 'temettuhocam'],
        'portfoy': ['portfoyanaliz', 'portfoy_gunlugum', 'portfoyum', 'portfoy_takip'],
        'kripto': ['kripto_paraanaliz', 'kriptopara_rehber', 'bitcoin_turkiye', 'kripto_gunluk'],
        'altin': ['altinfiyatlari', 'altin_gunluk', 'altin_piyasa', 'gramaltin_analiz'],
        'abd borsa': ['wallstreet_turk', 'abd_piyasalari', 'sp500_tr', 'nasdaq_turkiye', 'amerikanborsasi'],
        'yatirim fonu': ['yatirimfonu_takip', 'fonanaliz', 'yatirimfonlari', 'emeklilikfonu'],
        'viop': ['viop_analiz', 'viop_istanbul', 'vadeli_islemler'],
        'dolar': ['dolarkuru_takip', 'dolar_analiz', 'kuranaliz', 'doviz_gunluk'],
    }

    ig_search_profiles = {}
    ig_search_results = set()

    # 1. Instagram API ile hashtag search (login gerektirir)
    if instagram.is_logged_in():
        for ig_tag in selected_tags[:15]:
            try:
                ig_users = instagram.search_users(ig_tag[1:], count=20)
                for u in ig_users:
                    uname = u.get('username', '').lower()
                    if not uname: continue
                    followers = u.get('followers', 0)
                    ig_search_results.add(uname)
                    if uname not in ig_search_profiles or followers > ig_search_profiles[uname].get('followers', 0):
                        ig_search_profiles[uname] = {
                            'username': uname,
                            'name': u.get('full_name', uname),
                            'followers': followers,
                            'profile_pic_url': u.get('profile_pic_url', ''),
                        }
            except Exception:
                pass

    # 2. Bilinen kullanicilari ekle (login olsa da olmasa da)
    ig_direct_users = set()
    for tag, users in KNOWN_FINANCE_INSTAGRAM.items():
        if tag in query_lower or any(word in query_lower for word in tag.split()):
            ig_direct_users.update(users)
    if not ig_direct_users:
        for users in KNOWN_FINANCE_INSTAGRAM.values():
            ig_direct_users.update(users)
    ig_direct_users = set(list(ig_direct_users)[:50])

    for uname in ig_direct_users:
        uname_lower = uname.lower().strip()
        # Zaten search'ten geldiyse atla
        if uname_lower in ig_search_profiles:
            ig_search_results.add(uname_lower)
            continue
        ig_search_results.add(uname_lower)
        # follower sayisini ogrenmek icin profile bak
        followers = 0
        profile_name = uname
        if instagram.is_logged_in():
            try:
                info = instagram.get_user_info(uname)
                if 'error' not in info:
                    followers = info.get('followers', 0)
                    profile_name = info.get('full_name', uname)
            except Exception:
                pass
        ig_search_profiles[uname_lower] = {
            'username': uname,
            'name': profile_name,
            'followers': followers,
        }

    for uname in ig_search_results:
        if uname in seen_keys:
            continue
        profile = ig_search_profiles.get(uname, {})
        followers = profile.get('followers', 0)
        if followers >= 500:
            add_inf(uname, profile.get('name', uname), {
                'instagram': {
                    'username': uname,
                    'followers': followers,
                    'total_posts': 0,
                    'total_likes': 0,
                }
            }, 'instagram')
        elif uname in {u.lower().strip() for u in ig_direct_users}:
            add_inf(uname, profile.get('name', uname), {
                'instagram': {
                    'username': uname,
                    'followers': followers,
                    'total_posts': 0,
                    'total_likes': 0,
                }
            }, 'instagram')

    # ========== TIKTOK ARAMA ==========
    KNOWN_FINANCE_TIKTOK = {
        'borsa': ['borsaefe', 'yatirimsepeti', 'borsailkAdimlar', 'borsaogren', 'borsayatirim', 'finansbank', 'borsa_gunluk', 'yatirimciakademi', 'borsaanaliz', 'hissebul'],
        'yatirim': ['yatirimsepeti', 'yatirimciadam', 'yatirimnedir', 'finansbank', 'borsaefe', 'yatirim_rehberi', 'yatirim_tavsiye', 'parayatirimci'],
        'hisse senedi': ['borsaefe', 'hissebul', 'borsa_analiz', 'borsayatirim', 'yatirimciakademi'],
        'ekonomi': ['ekonomidogrular', 'piyasalar', 'dunyaekonomi', 'finansbank'],
        'finans': ['finansbank', 'finansbank_tr', 'ziraatbankasi', 'borsaefe', 'finans_analiz'],
        'kripto': ['binance_tr', 'btcturk', 'kriptopara_tr', 'bitlocom', 'kriptoakademi'],
        'altin': ['gramaltin', 'ceyrekaltin', 'altinfiyat', 'borsaefe', 'altin_piyasa'],
        'dolar': ['dolarkuru', 'dovizkuru', 'usdtry', 'borsaefe', 'kur_analiz'],
        'temettu': ['temettu_gunluk', 'temettu_ytd'],
        'portfoy': ['portfoy_analiz', 'portfoy_izle'],
        'abd borsa': ['sp500tr', 'wallstreetturk', 'abdborasalari', 'nasdaqtr'],
        'yatirim fonu': ['fonanaliz', 'yatirimfonu', 'fonportfoy'],
    }

    tt_direct_users = set()
    for tag, users in KNOWN_FINANCE_TIKTOK.items():
        if tag in query_lower or any(word in query_lower for word in tag.split()):
            tt_direct_users.update(users)

    if not tt_direct_users:
        for users in KNOWN_FINANCE_TIKTOK.values():
            tt_direct_users.update(users)
    tt_direct_users = set(list(tt_direct_users)[:35])

    for username in tt_direct_users:
        if username.lower() in seen_keys:
            continue
        try:
            info = tiktok.get_user_info(username)
            if 'error' not in info:
                followers = info.get('followers', 0)
                if followers >= 500:
                    tiktok_platform = {
                        'username': username,
                        'nickname': info.get('nickname', ''),
                        'followers': followers,
                        'total_views': info.get('hearts', 0),
                        'total_likes': 0,
                        'best_video': '',
                        'avatar': info.get('avatar', ''),
                    }
                    add_inf(username, info.get('nickname', username), {'tiktok': tiktok_platform}, 'tiktok')
        except Exception:
            pass

    # ========== SIRALA VE FILTRELE ==========
    results['influencers'].sort(key=lambda x: -x.get('total_followers', 0))
    results['influencers'] = results['influencers'][:80]

    return jsonify(results)


if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(debug=debug_mode, port=int(os.environ.get('PORT', 5001)))
