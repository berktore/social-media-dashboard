import json
import os
import re
import subprocess
from datetime import datetime

from curl_cffi import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.tiktok.com/',
}


class TikTokClient:
    def __init__(self):
        self.history_file = "tiktok_history.json"

    def _request(self, url, headers=None):
        h = {**HEADERS, **(headers or {})}
        return requests.get(url, impersonate="chrome131", headers=h, timeout=20)

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
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
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

    def get_user_videos(self, username, count=30):
        try:
            cmd = [
                'yt-dlp', '--flat-playlist', '-j',
                '--playlist-items', f'1:{count}',
                f'https://www.tiktok.com/@{username}',
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=60, encoding='utf-8', errors='replace',
            )

            if result.returncode != 0:
                return []

            videos = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    desc = item.get('description', '') or item.get('title', '')
                    upload_date = item.get('upload_date', '')
                    timestamp = item.get('timestamp', 0)
                    duration = item.get('duration', 0)

                    hashtags = re.findall(r'#(\w+)', desc)

                    thumbs = item.get('thumbnails', [])
                    cover = thumbs[0]['url'] if thumbs else ''

                    videos.append({
                        'id': item.get('id', ''),
                        'desc': desc,
                        'created_at': timestamp,
                        'upload_date': upload_date,
                        'duration': duration,
                        'play_count': item.get('view_count', 0) or 0,
                        'like_count': item.get('like_count', 0) or 0,
                        'comment_count': item.get('comment_count', 0) or 0,
                        'share_count': item.get('repost_count', 0) or 0,
                        'save_count': item.get('save_count', 0) or 0,
                        'cover': cover,
                        'music': item.get('track', ''),
                        'hashtags': hashtags,
                        'url': item.get('url', ''),
                    })
                except json.JSONDecodeError:
                    continue

            return videos
        except subprocess.TimeoutExpired:
            return []
        except FileNotFoundError:
            return []
        except Exception:
            return []
