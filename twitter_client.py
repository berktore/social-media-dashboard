import httpx
import json
import os
from datetime import datetime


class TwitterClient:
    def __init__(self, auth_token=None, ct0=None):
        self.auth_token = auth_token
        self.ct0 = ct0
        self._logged_in = False
        self.client = None
        self.history_file = "follower_history.json"

        if auth_token and ct0:
            self._init_client()

    def _init_client(self):
        self.client = httpx.Client(
            cookies={'auth_token': self.auth_token, 'ct0': self.ct0},
            headers={
                'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                'x-csrf-token': self.ct0,
                'x-twitter-active-user': 'yes',
                'x-twitter-client-language': 'tr',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            },
            follow_redirects=True,
            timeout=30.0
        )
        self._logged_in = True

    def login(self, auth_token, ct0):
        self.auth_token = auth_token
        self.ct0 = ct0
        self._init_client()

    def is_logged_in(self):
        return self._logged_in

    def _graphql_get(self, url, variables, features):
        params = {'variables': json.dumps(variables), 'features': json.dumps(features)}
        resp = self.client.get(url, params=params)
        if resp.status_code == 429:
            raise Exception("Twitter API rate limit asimina ulasildi. Biraz bekleyip tekrar deneyin.")
        if resp.status_code != 200:
            raise Exception(f"Twitter API hatasi: HTTP {resp.status_code}")
        try:
            return resp.json()
        except ValueError:
            raise Exception("Twitter API gecersiz JSON dondurdu")

    def _load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file) as f:
                return json.load(f)
        return {}

    def _save_history(self, username, follower_count):
        history = self._load_history()
        now = datetime.now().isoformat()
        if username not in history:
            history[username] = []
        # Ayni gunde kaydetme
        if history[username] and history[username][-1]['date'][:10] == now[:10]:
            history[username][-1]['count'] = follower_count
        else:
            history[username].append({'date': now, 'count': follower_count})
        # Son 365 gun sakla
        history[username] = history[username][-365:]
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        return history[username]

    def get_user_info(self, username):
        data = self._graphql_get(
            'https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName',
            {"screen_name": username, "withSafetyModeUserFields": True},
            {
                "hidden_profile_subscriptions_enabled": True, "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": False,
                "subscriptions_verification_info_is_identity_verified_enabled": True,
                "subscriptions_verification_info_verified_since_enabled": True,
                "highlights_tweets_tab_ui_enabled": True, "responsive_web_twitter_article_notes_tab_enabled": True,
                "subscriptions_feature_can_gift_premium": True, "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "responsive_web_graphql_timeline_navigation_enabled": True
            }
        )
        if 'data' not in data:
            raise Exception(data.get('errors', [{'message': 'Unknown error'}])[0].get('message', 'Unknown error'))

        user = data['data']['user']['result']
        legacy = user['legacy']
        follower_count = legacy.get('followers_count', 0)

        # Takipci gecmisini kaydet ve getir
        history = self._save_history(username, follower_count)

        # Onceki gunun takipci sayisini bul
        prev_count = follower_count
        if len(history) >= 2:
            prev_count = history[-2]['count']

        return {
            "id": user['rest_id'],
            "name": legacy.get('name', ''),
            "username": legacy.get('screen_name', ''),
            "description": legacy.get('description', ''),
            "followers_count": follower_count,
            "following_count": legacy.get('friends_count', 0),
            "tweets_count": legacy.get('statuses_count', 0),
            "profile_image_url": legacy.get('profile_image_url_https', '').replace('_normal', '_400x400'),
            "verified": user.get('is_blue_verified', False),
            "location": legacy.get('location', ''),
            "created_at": legacy.get('created_at', ''),
            "follower_growth": follower_count - prev_count,
            "follower_history": history[-30:],  # Son 30 gun
        }

    def get_user_tweets(self, username, count=20):
        user_info = self.get_user_info(username)
        user_id = user_info['id']

        data = self._graphql_get(
            'https://x.com/i/api/graphql/H8OOoI-5ZE4NxgRr8lfyWg/UserTweets',
            {"userId": str(user_id), "count": count, "includePromotedContent": False,
             "withQuickPromoteEligibilityTweetFields": True, "withVoice": True, "withV2Timeline": True},
            {
                "rweb_tipjar_consumption_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False, "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "communities_web_enable_tweet_community_results_fetch": True,
                "c9s_tweet_anatomy_moderator_badge_enabled": True, "articles_preview_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True, "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True, "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "rweb_video_timestamps_enabled": True, "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True, "responsive_web_enhance_cards_enabled": False
            }
        )

        if 'data' not in data:
            raise Exception('Could not fetch tweets')

        tweets = []
        timeline = data['data']['user']['result']['timeline_v2']['timeline']
        for instruction in timeline.get('instructions', []):
            if instruction.get('type') == 'TimelineAddEntries':
                for entry in instruction.get('entries', []):
                    if entry.get('entryId', '').startswith('tweet-'):
                        try:
                            tweet_result = entry['content']['itemContent']['tweet_results']['result']
                            if tweet_result.get('__typename') == 'Tweet':
                                legacy = tweet_result['legacy']
                                user_legacy = tweet_result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
                                # created_at'i ISO formatina cevir
                                created_at = legacy.get('created_at', '')
                                # "Thu May 28 12:00:01 +0000 2026" -> "2026-05-28T12:00:01Z"
                                try:
                                    dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                                    created_at_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                                    created_at_ts = int(dt.timestamp())
                                except:
                                    created_at_iso = created_at
                                    created_at_ts = 0

                                tweets.append({
                                    "id": legacy.get('id_str', ''),
                                    "text": legacy.get('full_text', ''),
                                    "created_at": created_at_iso,
                                    "created_at_ts": created_at_ts,
                                    "retweet_count": legacy.get('retweet_count', 0),
                                    "favorite_count": legacy.get('favorite_count', 0),
                                    "reply_count": legacy.get('reply_count', 0),
                                    "quote_count": legacy.get('quote_count', 0),
                                    "bookmark_count": legacy.get('bookmark_count', 0),
                                    "view_count": tweet_result.get('views', {}).get('count', 0),
                                    "lang": legacy.get('lang', ''),
                                    "is_retweet": 'retweeted_status_result' in legacy,
                                    "is_quote": 'quoted_tweet' in tweet_result,
                                    "media": [
                                        {"type": m.get('type', ''), "url": m.get('media_url_https', '')}
                                        for m in legacy.get('extended_entities', {}).get('media', [])
                                    ],
                                    "user": {
                                        "name": user_legacy.get('name', ''),
                                        "username": user_legacy.get('screen_name', ''),
                                        "profile_image": user_legacy.get('profile_image_url_https', '').replace('_normal', '_400x400'),
                                    } if user_legacy else None,
                                })
                        except (KeyError, TypeError):
                            continue

        return tweets

    def search_tweets(self, query, count=20):
        # GraphQL search endpoint dene
        try:
            data = self._graphql_get(
                'https://x.com/i/api/graphql/lZ0GCEojmtQfiUQa5oJSEw/SearchTimeline',
                {"query": query, "count": count, "querySource": "typed_query", "product": "Latest"},
                {
                    "rweb_tipjar_consumption_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True,
                    "verified_phone_label_enabled": False, "creator_subscriptions_tweet_preview_api_enabled": True,
                    "responsive_web_graphql_timeline_navigation_enabled": True,
                    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                    "communities_web_enable_tweet_community_results_fetch": True,
                    "c9s_tweet_anatomy_moderator_badge_enabled": True, "articles_preview_enabled": True,
                    "responsive_web_edit_tweet_api_enabled": True,
                    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                    "view_counts_everywhere_api_enabled": True, "longform_notetweets_consumption_enabled": True,
                    "responsive_web_twitter_article_tweet_consumption_enabled": True,
                    "tweet_awards_web_tipping_enabled": False,
                    "creator_subscriptions_quote_tweet_preview_enabled": False,
                    "freedom_of_speech_not_reach_fetch_enabled": True, "standardized_nudges_misinfo": True,
                    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                    "rweb_video_timestamps_enabled": True, "longform_notetweets_rich_text_read_enabled": True,
                    "longform_notetweets_inline_media_enabled": True, "responsive_web_enhance_cards_enabled": False
                }
            )

            if 'data' not in data:
                raise Exception('Could not search tweets')

            tweets = []
            timeline = data['data']['search_by_raw_query']['search_timeline']['timeline']
            for instruction in timeline.get('instructions', []):
                if instruction.get('type') == 'TimelineAddEntries':
                    for entry in instruction.get('entries', []):
                        if entry.get('entryId', '').startswith('tweet-'):
                            try:
                                tweet_result = entry['content']['itemContent']['tweet_results']['result']
                                if tweet_result.get('__typename') == 'Tweet':
                                    legacy = tweet_result['legacy']
                                    user_legacy = tweet_result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
                                    created_at = legacy.get('created_at', '')
                                    try:
                                        dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                                        created_at_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                                        created_at_ts = int(dt.timestamp())
                                    except:
                                        created_at_iso = created_at
                                        created_at_ts = 0

                                    tweets.append({
                                        "id": legacy.get('id_str', ''),
                                        "text": legacy.get('full_text', ''),
                                        "created_at": created_at_iso,
                                        "created_at_ts": created_at_ts,
                                        "retweet_count": legacy.get('retweet_count', 0),
                                        "favorite_count": legacy.get('favorite_count', 0),
                                        "reply_count": legacy.get('reply_count', 0),
                                        "quote_count": legacy.get('quote_count', 0),
                                        "bookmark_count": legacy.get('bookmark_count', 0),
                                        "view_count": tweet_result.get('views', {}).get('count', 0),
                                        "lang": legacy.get('lang', ''),
                                        "is_retweet": 'retweeted_status_result' in legacy,
                                        "is_quote": 'quoted_tweet' in tweet_result,
                                        "media": [
                                            {"type": m.get('type', ''), "url": m.get('media_url_https', '')}
                                            for m in legacy.get('extended_entities', {}).get('media', [])
                                        ],
                                        "user": {
                                            "name": user_legacy.get('name', ''),
                                            "username": user_legacy.get('screen_name', ''),
                                            "profile_image": user_legacy.get('profile_image_url_https', '').replace('_normal', '_400x400'),
                                        } if user_legacy else None,
                                    })
                            except (KeyError, TypeError):
                                continue
            return tweets
        except Exception as e:
            # Fallback: Twitter web search API
            try:
                resp = self.client.get(
                    'https://x.com/i/api/2/search/adaptive.json',
                    params={
                        'q': query,
                        'count': count,
                        'query_source': 'typed_query',
                        'pc': '1',
                        'spelling_corrections': '1',
                        'include_ext_edit_control': 'true',
                        'tweet_search_mode': 'live',
                    }
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                tweets = []
                for tweet_id, tweet_data in data.get('globalObjects', {}).get('tweets', {}).items():
                    user_id = tweet_data.get('user_id_str', '')
                    user_data = data.get('globalObjects', {}).get('users', {}).get(user_id, {})
                    tweets.append({
                        "id": tweet_id,
                        "text": tweet_data.get('full_text', ''),
                        "created_at": tweet_data.get('created_at', ''),
                        "retweet_count": tweet_data.get('retweet_count', 0),
                        "favorite_count": tweet_data.get('favorite_count', 0),
                        "reply_count": tweet_data.get('reply_count', 0),
                        "view_count": 0,
                        "is_retweet": tweet_data.get('retweeted_status_result_id_str') is not None,
                        "user": {
                            "name": user_data.get('name', ''),
                            "username": user_data.get('screen_name', ''),
                            "profile_image": user_data.get('profile_image_url_https', '').replace('_normal', '_400x400'),
                        } if user_data else None,
                    })
                return tweets
            except Exception:
                return []

    def get_trends(self):
        try:
            resp = self.client.get('https://x.com/i/api/2/guide.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&count=20&candidate_source=trends&include_page_configuration=false&entity_tokens=false')
            data = resp.json()
            trends = []
            for section in data.get('timeline', {}).get('instructions', []):
                if section.get('type') == 'TimelineAddEntries':
                    for entry in section.get('entries', []):
                        if entry.get('entryId', '').startswith('trend-'):
                            try:
                                content = entry['content']
                                if content.get('entryType') == 'TimelineTimelineItem':
                                    items = content.get('itemContent', {}).get('content', {}).get('timelineModule', {}).get('items', [])
                                    if items:
                                        trend_meta = items[0].get('item', {}).get('clientEventInfo', {}).get('details', {}).get('guideDetails', {}).get('trendMetadata', {})
                                        name = trend_meta.get('domainContext', {}).get('name', '')
                                        if name:
                                            trends.append({"name": name, "tweet_count": trend_meta.get('metaDescription', '')})
                            except (KeyError, TypeError, IndexError):
                                continue
            return trends
        except Exception:
            return []

    def _get_user_id(self, username):
        user_info = self.get_user_info(username)
        return user_info['id']

    def _graphql_timeline_users(self, endpoint, user_id, count=20):
        users = []
        cursor = None
        fetched = 0
        while fetched < count:
            variables = {
                "userId": str(user_id),
                "count": min(count - fetched, 20),
                "includePromotedContent": False,
            }
            if cursor:
                variables["cursor"] = cursor

            features = {
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "communities_web_enable_tweet_community_results_fetch": True,
                "c9s_tweet_anatomy_moderator_badge_enabled": True,
                "articles_preview_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "rweb_video_timestamps_enabled": True,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "responsive_web_enhance_cards_enabled": False,
            }

            data = self._graphql_get(endpoint, variables, features)

            if 'data' not in data:
                break

            timeline = data['data']['user']['result']['timeline']['timeline']
            new_users = []
            next_cursor = None

            for instruction in timeline.get('instructions', []):
                if instruction.get('type') == 'TimelineAddEntries':
                    for entry in instruction.get('entries', []):
                        entry_id = entry.get('entryId', '')
                        if entry_id.startswith('user-'):
                            try:
                                user_result = entry['content']['itemContent']['user_results']['result']
                                legacy = user_result['legacy']
                                new_users.append({
                                    "id": user_result['rest_id'],
                                    "name": legacy.get('name', ''),
                                    "username": legacy.get('screen_name', ''),
                                    "description": legacy.get('description', ''),
                                    "followers_count": legacy.get('followers_count', 0),
                                    "following_count": legacy.get('friends_count', 0),
                                    "tweets_count": legacy.get('statuses_count', 0),
                                    "profile_image_url": legacy.get('profile_image_url_https', '').replace('_normal', '_400x400'),
                                    "verified": user_result.get('is_blue_verified', False),
                                })
                            except (KeyError, TypeError):
                                continue
                        elif entry_id.startswith('cursor-bottom-'):
                            next_cursor = entry.get('content', {}).get('value')

            users.extend(new_users)
            fetched += len(new_users)

            if not next_cursor or not new_users:
                break
            cursor = next_cursor

        return users[:count]

    def get_followers(self, username, count=20):
        user_id = self._get_user_id(username)
        return self._graphql_timeline_users(
            'https://x.com/i/api/graphql/tmdbyNsaRrTWEzTzwLJN3g/Followers',
            user_id, count
        )

    def get_following(self, username, count=20):
        user_id = self._get_user_id(username)
        return self._graphql_timeline_users(
            'https://x.com/i/api/graphql/iSicc7LrzWGBgDPL0tM_TQ/Following',
            user_id, count
        )

    def get_similar_accounts(self, username, count=20):
        return self.get_followers(username, count)
