# Social Media Dashboard — Çalışma Özeti

## Amaç
SocialNexus dashboard'u Flask + Vercel'de calistirmak. Twitter/TikTok/YouTube canli verileri, username/password login, dark theme, Turkce UI.

## Son Durum (18 Haziran 2026)

### Çalışanlar
- **Vercel URL**: https://social-media-dashboard-nu-ten.vercel.app/
- **Giriş**: `info` / `info` (username/password)
- **YouTube**: Canli calisiyor (API key Vercel env'de)
- **TikTok profil**: Takipci, kalp, video sayisi geliyor (curl_cffi ile HTML scraping)
- **Login session**: Static SECRET_KEY sayesinde Vercel'de stabil

### Fix'ler (son 2 seansta)
1. **Read-only filesystem**: Tum history dosyalari `tempfile.gettempdir()` -> `/tmp/` yonlendirildi, yazma hatalari silent catch
2. **`/api/status`**: Twitter login status yerine Flask session donuyor, `@login_required` kaldirildi
3. **TikTok video**: yt-dlp subprocess -> Python API, uzerine:
   - **yt-dlp** (birincil, local'de calisir, 30 video ceker)
   - **TikTok API** `(/api/post/item_list/)` (curl_cffi ile, Vercel'de calisir)
   - **Cache JSON** `(tiktok_videos_cache.json)` — repo'da commitli, son care
4. **Static `SECRET_KEY`**: `secrets.token_hex(16)` yerine sabit key

### Bloke / Bekleyen
- **Twitter**: `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` env Vercel'de ayarlanmadi -> Twitter tabi calismaz
- **TikTok video cache guncellemesi**: Yeni video eklendiginde cache'in yenilenmesi icin local'de `app.py` calistirilip push edilmeli

### Kritik Bilgiler
- Flask creds: `info` / `info`
- YouTube API key: `AIzaSyDPcCe5HTg3v1qzC5Yy0YkL8W4AHZAtcHA` (Vercel env)
- YouTube channel: `UC-Il4FpbUEatDuaefVzqh8Q`
- GitHub: `berktore/social-media-dashboard`
- TikTok video cache: `tiktok_videos_cache.json` (30 video, repo'da)
- Tum history'ler `/tmp/` altinda
