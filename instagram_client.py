import json
import os
import re
import tempfile
from datetime import datetime
from curl_cffi import requests
import urllib.parse

class InstagramClient:
    def __init__(self, sessionid='', csrftoken=''):
        self.sessionid = sessionid
        self.csrftoken = csrftoken or ''
        self._logged_in = bool(sessionid)
        # ds_user_id is the first segment of sessionid before %3A (URL-encoded :)
        raw = sessionid
        if '%3A' in raw:
            raw = urllib.parse.unquote(raw)
        self.ds_user_id = raw.split(':')[0] if ':' in raw else ''

    def login(self, sessionid, csrftoken=''):
        self.sessionid = sessionid
        self.csrftoken = csrftoken or ''
        self._logged_in = True
        return True

    def is_logged_in(self):
        return self._logged_in

    def _headers(self):
        h = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
        }
        if self.csrftoken:
            h['X-CSRFToken'] = self.csrftoken
        return h

    def _cookies(self):
        c = {}
        if self.sessionid:
            c['sessionid'] = self.sessionid
        if self.csrftoken:
            c['csrftoken'] = self.csrftoken
        return c

    def _request(self, url, **kwargs):
        return requests.get(
            url,
            headers=self._headers(),
            cookies=self._cookies(),
            impersonate='chrome',
            **kwargs
        )

    def search_users(self, query, count=30):
        url = f'https://i.instagram.com/api/v1/users/search/?q={query}&count={min(count, 50)}'
        try:
            r = self._request(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                users = data.get('users', []) or data.get('accounts', []) or []
                results = []
                for u in users[:count]:
                    results.append({
                        'username': u.get('username', ''),
                        'full_name': u.get('full_name', ''),
                        'followers': u.get('follower_count', 0),
                        'profile_pic_url': u.get('profile_pic_url', ''),
                        'is_verified': u.get('is_verified', False),
                        'is_private': u.get('is_private', False),
                        'pk': u.get('pk', ''),
                    })
                return results
        except:
            pass
        return []

    def get_user_info(self, username):
        url = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
        try:
            r = self._request(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                user = data.get('data', {}).get('user', {})
                return self._format_profile(user)
        except:
            pass

        # Fallback: scrape public page
        try:
            r2 = requests.get(
                f'https://www.instagram.com/{username}/',
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept': 'text/html',
                },
                impersonate='chrome',
                timeout=15
            )
            if r2.status_code == 200:
                return self._scrape_public_profile(username, r2.text)
        except:
            pass

        return {'error': 'Profil bilgisi alinamadi'}

    def _format_profile(self, user):
        return {
            'username': user.get('username', ''),
            'full_name': user.get('full_name', ''),
            'biography': user.get('biography', ''),
            'followers': user.get('edge_followed_by', {}).get('count', 0),
            'following': user.get('edge_follow', {}).get('count', 0),
            'media_count': user.get('edge_owner_to_timeline_media', {}).get('count', 0),
            'is_private': user.get('is_private', False),
            'is_verified': user.get('is_verified', False),
            'profile_pic_url': user.get('profile_pic_url_hd', '') or user.get('profile_pic_url', ''),
            'external_url': user.get('external_url', ''),
        }

    def _scrape_public_profile(self, username, html):
        followers = 0
        following = 0
        posts = 0

        m = re.search(r'"edge_followed_by":\{"count":(\d+)\}', html)
        if m:
            followers = int(m.group(1))

        m = re.search(r'"edge_follow":\{"count":(\d+)\}', html)
        if m:
            following = int(m.group(1))

        m = re.search(r'"edge_owner_to_timeline_media":\{"count":(\d+)', html)
        if m:
            posts = int(m.group(1))

        name_match = re.search(r'<meta property="og:description" content="([^"]*)"', html)
        name_text = name_match.group(1) if name_match else ''

        return {
            'username': username,
            'full_name': '',
            'biography': name_text,
            'followers': followers,
            'following': following,
            'media_count': posts,
            'is_private': False,
            'is_verified': False,
            'profile_pic_url': '',
            'external_url': '',
        }

    def _resolve_user_id(self, username):
        url = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
        try:
            r = self._request(url, timeout=15)
            if r.status_code == 200:
                return r.json().get('data', {}).get('user', {}).get('id', '')
        except:
            pass
        return ''

    def get_user_posts(self, username, count=30):
        uid = self._resolve_user_id(username)
        if not uid:
            return []
        url = f'https://i.instagram.com/api/v1/feed/user/{uid}/?count={min(count, 50)}'
        try:
            r = self._request(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                items = data.get('items', [])
                posts = []
                for item in items[:count]:
                    caption = ''
                    if item.get('caption'):
                        caption = item['caption'].get('text', '')
                    posts.append({
                        'id': item.get('id', ''),
                        'code': item.get('code', ''),
                        'caption': (caption or '')[:500],
                        'likes': item.get('like_count', 0),
                        'comments': item.get('comment_count', 0),
                        'date': datetime.fromtimestamp(item.get('taken_at', 0)).isoformat(),
                        'date_ts': item.get('taken_at', 0),
                        'is_video': item.get('media_type') == 2,
                        'video_duration': item.get('video_duration', 0),
                        'display_url': item.get('image_versions2', {}).get('candidates', [{}])[0].get('url', ''),
                        'thumbnail_url': item.get('image_versions2', {}).get('candidates', [{}])[-1].get('url', ''),
                    })
                return posts
        except:
            pass
        return []

    def get_analytics(self, username, count=50):
        info = self.get_user_info(username)
        if 'error' in info:
            return info
        posts = self.get_user_posts(username, count=min(count, 200))

        if not posts:
            return {**info, 'posts': [], 'summary': {
                'total_posts': 0, 'total_likes': 0, 'total_comments': 0,
                'avg_likes': 0, 'avg_comments': 0, 'engagement_rate': 0,
            }}

        total_likes = sum(p.get('likes', 0) for p in posts)
        total_comments = sum(p.get('comments', 0) for p in posts)
        total_engagement = total_likes + total_comments
        avg_likes = total_likes // len(posts) if posts else 0
        avg_comments = total_comments // len(posts) if posts else 0
        followers = info.get('followers', 1)
        engagement_rate = round((total_engagement / max(1, followers)) * 100, 2)

        videos = [p for p in posts if p.get('is_video')]
        images = [p for p in posts if not p.get('is_video')]

        def avg_of(lst, key):
            if not lst: return 0
            return sum(v.get(key, 0) for v in lst) // len(lst)

        format_analysis = {
            'short': {'count': len(images), 'avg_likes': avg_of(images, 'likes'), 'avg_comments': avg_of(images, 'comments')},
            'video': {'count': len(videos), 'avg_likes': avg_of(videos, 'likes'), 'avg_comments': avg_of(videos, 'comments')},
        }

        by_likes = sorted(posts, key=lambda p: p.get('likes', 0), reverse=True)
        by_comments = sorted(posts, key=lambda p: p.get('comments', 0), reverse=True)
        by_low = sorted(posts, key=lambda p: p.get('likes', 0))

        hashtag_stats = {}
        for p in posts:
            caption = p.get('caption', '') or ''
            for tag in set(re.findall(r'#(\w+)', caption)):
                if tag not in hashtag_stats:
                    hashtag_stats[tag] = {'count': 0, 'total_likes': 0, 'total_comments': 0}
                hashtag_stats[tag]['count'] += 1
                hashtag_stats[tag]['total_likes'] += p.get('likes', 0)
                hashtag_stats[tag]['total_comments'] += p.get('comments', 0)
        top_tags = sorted(hashtag_stats.items(), key=lambda x: x[1]['total_likes'], reverse=True)[:10]

        return {
            'profile': info,
            'posts': posts,
            'summary': {
                'total_posts': len(posts),
                'total_likes': total_likes,
                'total_comments': total_comments,
                'avg_likes': avg_likes,
                'avg_comments': avg_comments,
                'engagement_rate': engagement_rate,
                'video_count': len(videos),
                'image_count': len(images),
            },
            'format_analysis': format_analysis,
            'best_by_likes': by_likes[:5],
            'best_by_comments': by_comments[:5],
            'worst_posts': by_low[:5],
            'top_tags': [{'tag': t, **s} for t, s in top_tags],
        }
