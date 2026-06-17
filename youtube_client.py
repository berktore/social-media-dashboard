import httpx
import json
import os
import tempfile
from datetime import datetime, timedelta


class YouTubeClient:
    """YouTube Data API v3 + YouTube Analytics API v2 client."""

    BASE_URL = 'https://www.googleapis.com/youtube/v3'
    ANALYTICS_URL = 'https://youtubeanalytics.googleapis.com/v2'

    def __init__(self, api_key=None, access_token=None):
        self.api_key = api_key
        self.access_token = access_token
        self.client = httpx.Client(follow_redirects=True, timeout=30.0)
        tmp = tempfile.gettempdir()
        self.history_file = os.path.join(tmp, 'youtube_history.json')

    def _api_get(self, url, params=None):
        if params is None:
            params = {}
        if self.api_key:
            params['key'] = self.api_key
        headers = {}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        resp = self.client.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            raise Exception(f'YouTube API hatasi: HTTP {resp.status_code} - {resp.text[:200]}')
        return resp.json()

    def _analytics_get(self, params):
        headers = {}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        resp = self.client.get(self.ANALYTICS_URL, params=params, headers=headers)
        if resp.status_code != 200:
            return None
        return resp.json()

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file) as f:
                return json.load(f)
        return {}

    def _save_history(self, channel_id, data):
        history = self._load_history()
        now = datetime.now().isoformat()
        if channel_id not in history:
            history[channel_id] = []
        if history[channel_id] and history[channel_id][-1]['date'][:10] == now[:10]:
            history[channel_id][-1] = {'date': now, **data}
        else:
            history[channel_id].append({'date': now, **data})
        history[channel_id] = history[channel_id][-365:]
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except (OSError, IOError):
            pass
        return history[channel_id]

    def get_channel_info(self, channel_id):
        """Kanal bilgilerini ve istatistiklerini cek."""
        data = self._api_get(f'{self.BASE_URL}/channels', {
            'part': 'snippet,contentDetails,statistics,brandingSettings',
            'id': channel_id,
        })
        if not data.get('items'):
            raise Exception('Kanal bulunamadi')
        ch = data['items'][0]
        snippet = ch.get('snippet', {})
        stats = ch.get('statistics', {})
        content = ch.get('contentDetails', {})

        subscriber_count = int(stats.get('subscriberCount', 0))
        view_count = int(stats.get('viewCount', 0))
        video_count = int(stats.get('videoCount', 0))
        hidden_subs = stats.get('hiddenSubscriberCount', False)

        # Takipci gecmisini kaydet
        history = self._save_history(channel_id, {
            'subscribers': subscriber_count,
            'views': view_count,
            'videos': video_count,
        })

        prev_subs = subscriber_count
        prev_views = view_count
        if len(history) >= 2:
            prev_subs = history[-2].get('subscribers', subscriber_count)
            prev_views = history[-2].get('views', view_count)

        return {
            'id': ch['id'],
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'banner': ch.get('brandingSettings', {}).get('image', {}).get('bannerExternalUrl', ''),
            'published_at': snippet.get('publishedAt', ''),
            'country': snippet.get('country', ''),
            'language': snippet.get('defaultLanguage', ''),
            'subscribers': subscriber_count,
            'subscribers_hidden': hidden_subs,
            'total_views': view_count,
            'total_videos': video_count,
            'uploads_playlist': content.get('relatedPlaylists', {}).get('uploads', ''),
            'subscriber_growth': subscriber_count - prev_subs,
            'subscriber_growth_rate': round(((subscriber_count - prev_subs) / max(1, prev_subs)) * 100, 2),
            'view_growth': view_count - prev_views,
            'history': history[-30:],
        }

    def get_channel_by_username(self, username):
        """Kullanici adindan kanal bilgisi cek."""
        data = self._api_get(f'{self.BASE_URL}/channels', {
            'part': 'snippet,contentDetails,statistics,brandingSettings',
            'forUsername': username,
        })
        if not data.get('items'):
            raise Exception('Kanal bulunamadi')
        return self.get_channel_info(data['items'][0]['id'])

    def get_channel_search(self, query):
        """Kanal ara."""
        data = self._api_get(f'{self.BASE_URL}/search', {
            'part': 'snippet',
            'q': query,
            'type': 'channel',
            'maxResults': 5,
        })
        results = []
        for item in data.get('items', []):
            snippet = item.get('snippet', {})
            results.append({
                'id': item.get('id', {}).get('channelId', ''),
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'thumbnail': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
            })
        return results

    def get_uploads(self, channel_id, count=30):
        """Kanal yuklemelerini cek."""
        # Uploads playlist ID'sini bul
        ch_data = self._api_get(f'{self.BASE_URL}/channels', {
            'part': 'contentDetails',
            'id': channel_id,
        })
        if not ch_data.get('items'):
            return []
        uploads_id = ch_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Playlist videolarini cek
        pl_data = self._api_get(f'{self.BASE_URL}/playlistItems', {
            'part': 'snippet',
            'playlistId': uploads_id,
            'maxResults': min(count, 50),
        })

        video_ids = []
        for item in pl_data.get('items', []):
            vid = item.get('snippet', {}).get('resourceId', {}).get('videoId', '')
            if vid:
                video_ids.append(vid)

        if not video_ids:
            return []

        # Video detaylarini cek
        vids_data = self._api_get(f'{self.BASE_URL}/videos', {
            'part': 'snippet,statistics,contentDetails',
            'id': ','.join(video_ids),
            'maxResults': min(count, 50),
        })

        videos = []
        for item in vids_data.get('items', []):
            snippet = item.get('snippet', {})
            stats = item.get('statistics', {})
            content = item.get('contentDetails', {})

            # Suresi parse et (PT1H2M3S -> saniye)
            duration_str = content.get('duration', 'PT0S')
            dur_sec = self._parse_duration(duration_str)

            videos.append({
                'id': item['id'],
                'title': snippet.get('title', ''),
                'description': snippet.get('description', '')[:200],
                'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'published_at': snippet.get('publishedAt', ''),
                'category_id': snippet.get('categoryId', ''),
                'tags': snippet.get('tags', []),
                'duration': dur_sec,
                'duration_str': duration_str,
                'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0)),
                'favorite_count': int(stats.get('favoriteCount', 0)),
            })

        return videos

    def get_analytics(self, channel_id, days=30):
        """YouTube Analytics API'dan detayli veri cek (OAuth gerekli)."""
        if not self.access_token:
            return None

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        base_params = {
            'ids': f'channel=={channel_id}',
            'startDate': start_date,
            'endDate': end_date,
        }

        result = {}

        # Temel metrikler
        data = self._analytics_get({
            **base_params,
            'metrics': 'views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares',
            'dimensions': 'day',
            'sort': 'day',
        })
        if data and 'rows' in data:
            rows = data['rows']
            result['daily'] = [{
                'date': r[0],
                'views': r[1],
                'watch_time_min': r[2],
                'avg_duration': r[3],
                'avg_view_pct': r[4],
                'subs_gained': r[5],
                'subs_lost': r[6],
                'likes': r[7],
                'comments': r[8],
                'shares': r[9],
            } for r in rows]
            # Toplamlar
            result['totals'] = {
                'views': sum(r[1] for r in rows),
                'watch_time_min': round(sum(r[2] for r in rows), 1),
                'avg_duration': round(sum(r[3] for r in rows) / len(rows), 1) if rows else 0,
                'avg_view_pct': round(sum(r[4] for r in rows) / len(rows), 1) if rows else 0,
                'subs_gained': sum(r[5] for r in rows),
                'subs_lost': sum(r[6] for r in rows),
                'likes': sum(r[7] for r in rows),
                'comments': sum(r[8] for r in rows),
                'shares': sum(r[9] for r in rows),
            }

        # Trafik kaynaklari
        traffic = self._analytics_get({
            **base_params,
            'metrics': 'views,estimatedMinutesWatched',
            'dimensions': 'insightTrafficSourceType',
            'sort': '-views',
        })
        if traffic and 'rows' in traffic:
            result['traffic_sources'] = [{'source': r[0], 'views': r[1], 'watch_time': r[2]} for r in traffic['rows']]

        # Izleyici profili - yas
        age_data = self._analytics_get({
            **base_params,
            'metrics': 'viewerPercentage',
            'dimensions': 'ageGroup',
        })
        if age_data and 'rows' in age_data:
            result['age_demographics'] = [{'age_group': r[0], 'percentage': r[1]} for r in age_data['rows']]

        # Izleyici profili - cinsiyet
        gender_data = self._analytics_get({
            **base_params,
            'metrics': 'viewerPercentage',
            'dimensions': 'gender',
        })
        if gender_data and 'rows' in gender_data:
            result['gender_demographics'] = [{'gender': r[0], 'percentage': r[1]} for r in gender_data['rows']]

        # Lokasyon
        country_data = self._analytics_get({
            **base_params,
            'metrics': 'views,estimatedMinutesWatched',
            'dimensions': 'country',
            'sort': '-views',
            'maxResults': 10,
        })
        if country_data and 'rows' in country_data:
            result['countries'] = [{'country': r[0], 'views': r[1], 'watch_time': r[2]} for r in country_data['rows']]

        # CTR (tiklanma orani) - bu genellikle YouTube Studio'dan gelir, API'da sinirlidir
        # Tahmini CTR: likes+comments+shares / views
        if result.get('totals'):
            t = result['totals']
            total_engagement = t.get('likes', 0) + t.get('comments', 0) + t.get('shares', 0)
            t['estimated_ctr'] = round((total_engagement / max(1, t['views'])) * 100, 2)

        return result

    @staticmethod
    def _parse_duration(iso_duration):
        """PT1H2M3S formatini saniyeye cevir."""
        import re
        m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
        if not m:
            return 0
        hours = int(m.group(1) or 0)
        minutes = int(m.group(2) or 0)
        seconds = int(m.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
