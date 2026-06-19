import json
import os
import secrets
import tempfile
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from twitter_client import TwitterClient
from tiktok_client import TikTokClient
from youtube_client import YouTubeClient
from instagram_client import InstagramClient

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'socialnexus-2024-sabit-anahtar-degistirme')

USERNAME = 'info'
PASSWORD_HASH = generate_password_hash('info')

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
        if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
            session["logged_in"] = True
            session["username"] = username
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


@app.route("/api/competitor/<platform>/<username>")
@login_required
def api_competitor_detail(platform, username):
    """Tek bir platform icin detayli veri cek. ?days=30 ile tarih filtrele."""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff = (datetime.utcnow() - timedelta(days=days)).timestamp()

        def parse_ts(item):
            ts = item.get('created_at') or item.get('published_at') or 0
            if isinstance(ts, (int, float)):
                return ts
            if isinstance(ts, str):
                for fmt in ('%a %b %d %H:%M:%S %z %Y', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ'):
                    try:
                        from datetime import datetime as dt2
                        return dt2.strptime(ts.rstrip('Z'), fmt.replace('%z', '').replace('%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S')).timestamp()
                    except: pass
            return 0

        if platform == 'twitter':
            if not client.is_logged_in():
                return jsonify({'error': 'Twitter giris yapilmamis'})
            user = client.get_user_info(username)
            tweets = client.get_user_tweets(username, count=100)
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

            return jsonify({
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
            })

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

            return jsonify({
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
            })

        elif platform == 'youtube':
            ch_info = youtube.get_channel_info(username)
            videos = youtube.get_uploads(username, count=100)
            videos = [v for v in videos if parse_ts(v) >= cutoff]

            total_views = sum(v.get('view_count', 0) for v in videos)
            total_likes = sum(v.get('like_count', 0) for v in videos)
            total_comments = sum(v.get('comment_count', 0) for v in videos)
            total_eng = total_likes + total_comments
            eng_rate = round((total_eng / max(1, total_views)) * 100, 2)

            return jsonify({
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
            })

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
            return jsonify(analytics)

        else:
            return jsonify({'error': f'{platform} desteklenmiyor'})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route("/api/influencer/search")
@login_required
def api_influencer_search():
    """Belirli bir konuda icerik ureten influencer'lari ara."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Arama terimi gerekli'})

    results = {'query': query, 'influencers': []}
    seen_usernames = set()  # Tekrarlari onle

    # Twitter - onceden taninmis finans hesaplarini ara + search dene
    KNOWN_FINANCE_TWITTER = {
        'borsa': ['infoyatirim', 'borsadabugun', 'borsa_gunluk', 'forex_borsa', 'yatirimteknik', 'borsa_yatirimci', 'traborsa'],
        'yatirim': ['infoyatirim', 'bigaborsa', 'burak_kc', 'yatirimciakademi', 'yatirimteknik'],
        'hisse senedi': ['infoyatirim', 'borsadabugun', 'borsa_gunluk', 'hisse_yorum', 'borsaanalizci'],
        'ekonomi': ['infoyatirim', 'bloombegthd', 'ekonomi_sektoru', 'dunyaekonomi', 'piyasalar_gunluk'],
        'finans': ['infoyatirim', 'bigaborsa', 'finans_sektoru', 'bankaborsa', 'yatirimciakademi'],
        'kripto': ['kriptoakademi', 'bitlocom', 'kriptopara_tr', 'kripto_borsa', 'cryptotr'],
        'forex': ['infoyatirim', 'forexbilgi', 'forexpiyasa', 'forex_trader', 'forex_yatirim'],
        'viop': ['infoyatirim', 'viopsyorum', 'borsa_viop', 'vadeliislemler'],
        'bist': ['infoyatirim', 'borsadabugun', 'borsa_gunluk', 'bist_yatirim', 'xu100'],
        'altin': ['infoyatirim', 'altin_fiyatlari', 'altin_yorum', 'ceyrek_altin', 'gram_altin'],
        'dolar': ['infoyatirim', 'dolar_tl', 'kur_yorum', 'doviz_analiz', 'usdtry'],
        'fintech': ['infoyatirim', 'finansal_teknoloji', 'fintech_tr', 'dijital_bankacilik'],
    }

    query_lower = query.lower()
    search_usernames = set()
    for tag, usernames in KNOWN_FINANCE_TWITTER.items():
        if tag in query_lower or any(word in query_lower for word in tag.split()):
            search_usernames.update(usernames)

    # Eger eslesme yoksa genel arama yap
    if not search_usernames:
        search_usernames = {'infoyatirim', 'borsadabugun', 'bigaborsa', 'yatirimciakademi', 'traborsa', 'borsa_gunluk'}

    # Twitter search ile ek kullanici bul
    try:
        if client.is_logged_in():
            tweets = client.search_tweets(query, count=30)
            for t in tweets:
                u = t.get('user')
                if u and u.get('username'):
                    search_usernames.add(u['username'])
    except Exception:
        pass

    # Her kullanici icin profil bilgisi cek
    try:
        if client.is_logged_in():
            for username in list(search_usernames)[:15]:
                if username.lower() in seen_usernames:
                    continue
                seen_usernames.add(username.lower())
                try:
                    profile = client.get_user_info(username)
                    results['influencers'].append({
                        'username': username,
                        'name': profile.get('name', username),
                        'platforms': {
                            'twitter': {
                                'username': username,
                                'followers': profile.get('followers_count', 0),
                                'best_tweet': '',
                                'total_views': 0,
                                'total_likes': 0,
                            }
                        },
                        'source': 'twitter',
                    })
                except Exception:
                    # Profil alinamazsa bile listeye ekle
                    results['influencers'].append({
                        'username': username,
                        'name': username,
                        'platforms': {
                            'twitter': {
                                'username': username,
                                'followers': 0,
                                'best_tweet': '',
                                'total_views': 0,
                                'total_likes': 0,
                            }
                        },
                        'source': 'twitter',
                    })
    except Exception as e:
        print(f"[INFLUENCER] Twitter arama hatasi: {e}")

    # YouTube - kanal ara
    try:
        yt_channels = youtube.get_channel_search(query)
        for ch in yt_channels[:10]:
            cid = ch.get('id', '')
            if not cid:
                continue
            try:
                ch_info = youtube.get_channel_info(cid)
                username_key = ch_info['title'].lower().replace(' ', '')
                if username_key in seen_usernames:
                    continue
                seen_usernames.add(username_key)

                # Mevcut influencer ile eslestir mi?
                matched = False
                for inf in results['influencers']:
                    inf_name = inf['name'].lower().replace(' ', '')
                    if inf_name and (inf_name in ch_info['title'].lower() or ch_info['title'].lower() in inf_name):
                        inf['platforms']['youtube'] = {
                            'channel_id': cid,
                            'title': ch_info['title'],
                            'subscribers': ch_info['subscribers'],
                            'thumbnail': ch_info['thumbnail'],
                        }
                        matched = True
                        break

                if not matched:
                    results['influencers'].append({
                        'username': cid,
                        'name': ch_info['title'],
                        'platforms': {
                            'youtube': {
                                'channel_id': cid,
                                'title': ch_info['title'],
                                'subscribers': ch_info['subscribers'],
                                'thumbnail': ch_info['thumbnail'],
                            }
                        },
                        'source': 'youtube',
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"[INFLUENCER] YouTube arama hatasi: {e}")

    # TikTok - bilinen finans hesaplarini dogrudan cek
    KNOWN_FINANCE_TIKTOK = {
        'borsa': ['borsaefe', 'yatirimsepeti', 'borsailkAdimlar', 'borsaogren', 'borsayatirim', 'finansbank', 'borsa_gunluk', 'yatirimciakademi'],
        'yatirim': ['yatirimsepeti', 'yatirimciadam', 'yatirimnedir', 'finansbank', 'borsaefe'],
        'hisse senedi': ['borsaefe', 'hissebul', 'borsa_analiz', 'borsayatirim', 'yatirimciakademi'],
        'ekonomi': ['ekonomidogrular', 'piyasalar', 'dunyaekonomi', 'finansbank'],
        'finans': ['finansbank', 'finansbank_tr', 'ziraatbankasi', 'borsaefe'],
        'kripto': ['binance_tr', 'btcturk', 'kriptopara_tr', 'bitlocom'],
        'altin': ['gramaltin', 'ceyrekaltin', 'altinfiyat', 'borsaefe'],
        'dolar': ['dolarkuru', 'dovizkuru', 'usdtry', 'borsaefe'],
    }

    tt_direct_users = set()
    for tag, users in KNOWN_FINANCE_TIKTOK.items():
        if tag in query_lower or any(word in query_lower for word in tag.split()):
            tt_direct_users.update(users)

    # Eger eslesme yoksa genel liste
    if not tt_direct_users:
        tt_direct_users = {'borsaefe', 'yatirimsepeti', 'borsailkAdimlar', 'finansbank', 'yatirimciakademi'}

    # TikTok hesaplarini dogrudan cek
    tt_users = {}
    for username in list(tt_direct_users)[:12]:
        if username.lower() in seen_usernames:
            continue
        try:
            info = tiktok.get_user_info(username)
            if 'error' not in info:
                tt_users[username] = {
                    'username': username,
                    'nickname': info.get('nickname', ''),
                    'followers': info.get('followers', 0),
                    'hearts': info.get('hearts', 0),
                    'videos': info.get('videos', 0),
                    'avatar': info.get('avatar', ''),
                    'verified': info.get('verified', False),
                }
        except Exception:
            pass

    # TikTok kullanicilarini ekle
    for username, ud in tt_users.items():
        if username.lower() in seen_usernames:
            continue
        seen_usernames.add(username.lower())

        # Mevcut influencer ile eslestir mi?
        matched = False
        for inf in results['influencers']:
            inf_name = inf['name'].lower().replace(' ', '')
            nick = ud.get('nickname', '').lower().replace(' ', '')
            if inf_name and (inf_name in username.lower() or username.lower() in inf_name or (nick and inf_name in nick)):
                inf['platforms']['tiktok'] = {
                    'username': username,
                    'nickname': ud.get('nickname', ''),
                    'followers': ud.get('followers', 0),
                    'total_views': ud.get('hearts', 0),
                    'total_likes': 0,
                    'best_video': '',
                }
                matched = True
                break

        if not matched:
            results['influencers'].append({
                'username': username,
                'name': ud.get('nickname', '') or username,
                'platforms': {
                    'tiktok': {
                        'username': username,
                        'nickname': ud.get('nickname', ''),
                        'followers': ud.get('followers', 0),
                        'total_views': ud.get('hearts', 0),
                        'total_likes': 0,
                        'best_video': '',
                    }
                },
                'source': 'tiktok',
            })

    # Siralama: cok platformlu olanlar ustte
    results['influencers'].sort(key=lambda x: len(x.get('platforms', {})), reverse=True)

    return jsonify(results)


if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(debug=debug_mode, port=int(os.environ.get('PORT', 5001)))
