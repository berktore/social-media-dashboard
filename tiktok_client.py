import json
import os
import re
import tempfile
from datetime import datetime

try:
    from curl_cffi import requests as _requests
    TIKTOK_IMPERSONATE = "chrome131"
except ImportError:
    import httpx as _requests
    TIKTOK_IMPERSONATE = None

try:
    import yt_dlp
    HAS_YT_DLP = True
except ImportError:
    HAS_YT_DLP = False

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.tiktok.com/',
}


class TikTokClient:
    def __init__(self):
        tmp = tempfile.gettempdir()
        self.history_file = os.path.join(tmp, "tiktok_history.json")

    def _request(self, url, headers=None):
        h = {**HEADERS, **(headers or {})}
        kwargs = {"headers": h, "timeout": 20}
        if TIKTOK_IMPERSONATE:
            kwargs["impersonate"] = TIKTOK_IMPERSONATE
        return _requests.get(url, **kwargs)

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file) as f:
                return json.load(f)
        return {}

    def _save_history(self, username, data):
        history = self._load_history()
        now = datetime.now().isoformat()
        if username not in history:
            history[username] = []
        if history[username] and history[username][-1]['date'][:10] == now[:10]:
            history[username][-1] = {'date': now, **data}
        else:
            history[username].append({'date': now, **data})
        history[username] = history[username][-365:]
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except (OSError, IOError):
            pass
        return history[username]

    def get_user_info(self, username, max_retries=4):
        import time
        for attempt in range(max_retries):
            try:
                resp = self._request(f'https://www.tiktok.com/@{username}')
                html = resp.text

                match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html)
                if not match:
                    if attempt < max_retries - 1:
                        time.sleep(1.5)
                        continue
                    return {'error': 'TikTok captcha — sayfa alinamadi'}

                data = json.loads(match.group(1))
                default_scope = data.get('__DEFAULT_SCOPE__', {})
                user_info = default_scope.get('webapp.user-detail', {}).get('userInfo', {})

                if not user_info:
                    return {'error': 'Kullanici bulunamadi'}

                stats = user_info.get('stats', {})
                stats_v2 = user_info.get('statsV2', {})
                user = user_info.get('user', {})

                follower_count = stats.get('followerCount', 0) or int(stats_v2.get('followerCount', 0) or 0)
                heart_count = stats.get('heartCount', 0) or int(stats_v2.get('heartCount', 0) or 0)
                following_count = stats.get('followingCount', 0) or int(stats_v2.get('followingCount', 0) or 0)
                video_count = stats.get('videoCount', 0) or int(stats_v2.get('videoCount', 0) or 0)
                digg_count = stats.get('diggCount', 0) or int(stats_v2.get('diggCount', 0) or 0)

                history = self._save_history(username, {
                    'followers': follower_count,
                    'following': following_count,
                    'hearts': heart_count,
                    'videos': video_count,
                    'diggs': digg_count,
                })

                prev_followers = follower_count
                prev_hearts = heart_count
                if len(history) >= 2:
                    prev_followers = history[-2].get('followers', follower_count)
                    prev_hearts = history[-2].get('hearts', heart_count)

                growth = follower_count - prev_followers
                growth_rate = round((growth / prev_followers * 100), 2) if prev_followers > 0 else 0

                return {
                    'id': user.get('id', ''),
                    'username': user.get('uniqueId', username),
                    'nickname': user.get('nickname', ''),
                    'avatar': user.get('avatarThumb', ''),
                    'description': user.get('signature', ''),
                    'verified': user.get('verified', False),
                    'private': user.get('privateAccount', False),
                    'followers': follower_count,
                    'following': following_count,
                    'hearts': heart_count,
                    'videos': video_count,
                    'diggs': digg_count,
                    'follower_growth': growth,
                    'follower_growth_rate': growth_rate,
                    'heart_growth': heart_count - prev_hearts,
                    'history': history[-30:],
                }
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1.5)
                    continue
                return {'error': str(e)}

    CACHE_FILE = "tiktok_videos_cache.json"

    def _try_ytdlp(self, username, count):
        if not HAS_YT_DLP:
            return None
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'playlist_items': f'1:{count}',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f'https://www.tiktok.com/@{username}', download=False)
                entries = info.get('entries', [])
            videos = []
            for item in entries:
                if not item:
                    continue
                desc = item.get('description', '') or item.get('title', '')
                hashtags = re.findall(r'#(\w+)', desc)
                thumbs = item.get('thumbnails', [])
                ts = item.get('timestamp', 0)
                if not ts:
                    ud = item.get('upload_date', '')
                    if len(ud) == 8:
                        try:
                            ts = int(datetime.strptime(ud, '%Y%m%d').timestamp())
                        except:
                            ts = 0
                videos.append({
                    'id': item.get('id', ''),
                    'desc': desc,
                    'created_at': ts,
                    'upload_date': item.get('upload_date', ''),
                    'duration': item.get('duration', 0),
                    'play_count': item.get('view_count', 0) or 0,
                    'like_count': item.get('like_count', 0) or 0,
                    'comment_count': item.get('comment_count', 0) or 0,
                    'share_count': item.get('repost_count', 0) or 0,
                    'save_count': item.get('save_count', 0) or 0,
                    'cover': thumbs[0]['url'] if thumbs else '',
                    'music': item.get('track', ''),
                    'hashtags': hashtags,
                    'url': item.get('url', ''),
                })
            return videos
        except Exception:
            return None

    def _save_cache(self, videos):
        if not videos:
            return
        try:
            data = {'timestamp': datetime.now().isoformat(), 'videos': videos}
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (OSError, IOError):
            pass

    def _load_cache(self):
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f).get('videos', [])
        except (OSError, IOError, json.JSONDecodeError):
            pass
        return None

    def _try_api(self, username, count):
        try:
            r = self._request(f'https://www.tiktok.com/@{username}')
            m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
            if not m:
                return None
            data = json.loads(m.group(1))
            sc = data['__DEFAULT_SCOPE__']
            user_info = sc.get('webapp.user-detail', {}).get('userInfo', {})
            sec_uid = user_info.get('user', {}).get('secUid', '')
            if not sec_uid:
                return None

            headers = {
                'Referer': f'https://www.tiktok.com/@{username}',
                'User-Agent': HEADERS['User-Agent'],
            }

            videos = []
            seen_ids = set()
            cursor = 0

            while len(videos) < count:
                r2 = self._request(
                    f'https://www.tiktok.com/api/post/item_list/'
                    f'?aid=1988&secUid={sec_uid}&count={min(30, count - len(videos))}&cursor={cursor}&sourceType=8&type=5',
                    headers=headers,
                )
                r2j = r2.json()
                items = r2j.get('itemList', [])
                if not items:
                    break

                for item in items:
                    vid = item.get('id', '')
                    if vid in seen_ids:
                        continue
                    seen_ids.add(vid)
                    stats = item.get('stats', {})
                    video = item.get('video', {})
                    desc = item.get('desc', '') or ''
                    hashtags = [t.get('name', '') for t in item.get('textExtra', []) if t.get('hashtagName')]
                    videos.append({
                        'id': vid,
                        'desc': desc,
                        'created_at': item.get('createTime', 0),
                        'upload_date': '',
                        'duration': video.get('duration', 0),
                        'play_count': stats.get('playCount', 0) or 0,
                        'like_count': stats.get('diggCount', 0) or 0,
                        'comment_count': stats.get('commentCount', 0) or 0,
                        'share_count': stats.get('shareCount', 0) or 0,
                        'save_count': stats.get('collectCount', 0) or 0,
                        'cover': (video.get('cover', {}) or {}).get('url_list', [''])[0],
                        'music': item.get('music', {}).get('title', ''),
                        'hashtags': hashtags,
                        'url': f'https://www.tiktok.com/@{username}/video/{vid}',
                    })

                has_more = r2j.get('hasMore', False)
                cursor = r2j.get('cursor', 0)
                if not has_more:
                    break

            return videos if videos else None
        except Exception:
            return None

    def get_user_videos(self, username, count=30):
        videos = self._try_ytdlp(username, count)
        if videos is not None and len(videos) > 0:
            self._save_cache(videos)
            return videos
        videos = self._try_api(username, count)
        if videos is not None and len(videos) > 0:
            self._save_cache(videos)
            return videos
        cached = self._load_cache()
        if cached:
            return cached
        return videos or []
