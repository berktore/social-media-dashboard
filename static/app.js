let allTweets = [];
let filteredTweets = [];
let twitterProfile = null;

function showDashboard() {
    switchTab('overview');
    loadOverview();
    loadTwitterData();
}

showDashboard();

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
    document.getElementById('tab-' + tabName).classList.remove('hidden');
    document.querySelectorAll('.nav-item').forEach(n => {
        n.classList.remove('nav-active', 'text-[#1DA1F2]');
        n.classList.add('text-on-surface-variant', 'hover:text-on-surface', 'hover:bg-surface-container-highest/50');
    });
    const activeNav = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeNav) {
        activeNav.classList.add('nav-active', 'text-[#1DA1F2]');
        activeNav.classList.remove('text-on-surface-variant');
    }
    if (tabName === 'overview') {
        loadOverview();
    }
    if (tabName === 'twitter') {
        if (allTweets.length > 0) setTimeout(() => renderAnalytics(), 100);
        else loadTwitterData();
    }
    if (tabName === 'tiktok') {
        if (tiktokAnalytics) setTimeout(() => renderTikTokAll(), 100);
        else loadTikTokData();
    }
    if (tabName === 'youtube') {
        if (youtubeData) setTimeout(() => renderYouTubeAll(), 100);
        else loadYouTubeData('UC-Il4FpbUEatDuaefVzqh8Q');
    }
}

function handleGlobalSearch() {
    const q = document.getElementById('global-search').value.trim();
    if (q && q.startsWith('@')) { switchTab('twitter'); loadTwitterProfile(q.substring(1)); }
}

// ==================== OVERVIEW ====================
function loadOverview() {
    const statusEl = document.getElementById('overview-status');
    statusEl.textContent = 'Yukleniyor...';
    statusEl.className = 'text-label-sm font-label-sm text-on-surface-variant bg-surface-container px-md py-xs rounded-full border border-outline-variant/30';

    fetch('data/overview.json')
    .then(r => r.json()).then(data => {
        statusEl.textContent = 'Guncel';
        statusEl.className = 'text-label-sm font-label-sm text-primary bg-primary/10 px-md py-xs rounded-full border border-primary/20';
        renderOverview(data);
    }).catch(() => {
        statusEl.textContent = 'Hata';
        statusEl.className = 'text-label-sm font-label-sm text-error bg-error/10 px-md py-xs rounded-full border border-error/20';
    });
}

function renderOverview(data) {
    const { twitter, tiktok, youtube } = data;

    // Toplam degerleri hesapla
    const totalFollowers = (twitter?.followers || 0) + (tiktok?.followers || 0) + (youtube?.subscribers || 0);
    const totalImpressions = (twitter?.total_impressions || 0) + (tiktok?.total_views || 0) + (youtube?.total_views || 0);

    // Agirlikli etkilesim orani
    const twEng = twitter?.engagement_rate || 0;
    const ttEng = tiktok?.engagement_rate || 0;
    const ytEng = youtube?.engagement_rate || 0;
    const totalEngWeight = (twitter?.total_impressions || 0) + (tiktok?.total_views || 0) + (youtube?.total_views || 0);
    const avgEngRate = totalEngWeight > 0
        ? ((twEng * (twitter?.total_impressions || 0) + ttEng * (tiktok?.total_views || 0) + ytEng * (youtube?.total_views || 0)) / totalEngWeight).toFixed(2)
        : 0;

    // Toplam follower artisi
    const totalGrowth = (twitter?.follower_growth || 0) + (tiktok?.follower_growth || 0) + (youtube?.subscriber_growth || 0);

    // Core Metrics
    document.getElementById('overview-core-metrics').innerHTML = `
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <div class="flex justify-between items-start mb-4">
                <span class="material-symbols-outlined text-primary p-2 bg-primary/10 rounded-lg">public</span>
                <span class="text-primary font-label-md text-label-md">${totalImpressions > 0 ? '+' + fmt(totalImpressions) : '0'}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Toplam Erisim</h3>
            <div class="flex items-baseline gap-2">
                <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(totalImpressions)}</span>
                <span class="font-body-sm text-body-sm text-on-surface-variant">gorunme</span>
            </div>
            <div class="mt-6 h-12 w-full flex items-end gap-1">
                <div class="flex-1 bg-primary/20 rounded-t-sm h-[${twitter ? '60' : '20'}%]"></div>
                <div class="flex-1 bg-primary/40 rounded-t-sm h-[${tiktok ? '100' : '20'}%]"></div>
                <div class="flex-1 bg-primary rounded-t-sm h-[${youtube ? '40' : '20'}%] group-hover:animate-pulse"></div>
            </div>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <div class="flex justify-between items-start mb-4">
                <span class="material-symbols-outlined text-tertiary p-2 bg-tertiary/10 rounded-lg">bolt</span>
                <span class="text-tertiary font-label-md text-label-md">%${avgEngRate}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Ort. Etkilesim Orani</h3>
            <div class="flex items-baseline gap-2">
                <span class="font-headline-lg text-headline-lg text-on-surface">%${avgEngRate}</span>
                <span class="font-body-sm text-body-sm text-on-surface-variant">tum platformlar</span>
            </div>
            <div class="mt-6 h-12 w-full flex items-center justify-between">
                <div class="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
                    <div class="bg-tertiary h-full w-[${Math.min(100, avgEngRate * 10)}%] shadow-[0_0_10px_rgba(123,208,255,0.5)]"></div>
                </div>
            </div>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary-fixed"></div>
            <div class="flex justify-between items-start mb-4">
                <span class="material-symbols-outlined text-primary-fixed p-2 bg-primary-fixed/10 rounded-lg">person_add</span>
                <span class="${totalGrowth >= 0 ? 'text-primary' : 'text-error'} font-label-md text-label-md">${totalGrowth >= 0 ? '+' : ''}${fmt(totalGrowth)}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Takipci Artisi</h3>
            <div class="flex items-baseline gap-2">
                <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(totalFollowers)}</span>
                <span class="font-body-sm text-body-sm text-on-surface-variant">toplam ag</span>
            </div>
            <div class="mt-6 flex items-center gap-2">
                <div class="flex -space-x-2">
                    ${twitter ? '<div class="w-8 h-8 rounded-full border-2 border-surface bg-surface-bright overflow-hidden"><img src="https://ui-avatars.com/api/?name=TW&background=1DA1F2&color=fff&size=32" alt=""></div>' : ''}
                    ${tiktok ? '<div class="w-8 h-8 rounded-full border-2 border-surface bg-surface-bright overflow-hidden"><img src="https://ui-avatars.com/api/?name=TT&background=00F2EA&color=000&size=32" alt=""></div>' : ''}
                    ${youtube ? '<div class="w-8 h-8 rounded-full border-2 border-surface bg-surface-bright overflow-hidden"><img src="https://ui-avatars.com/api/?name=YT&background=FF0000&color=fff&size=32" alt=""></div>' : ''}
                </div>
                <span class="font-label-sm text-label-sm text-on-surface-variant">${[twitter, tiktok, youtube].filter(Boolean).length} platform aktif</span>
            </div>
        </div>`;

    // Platform Cards
    const platforms = [];
    if (twitter) {
        const twGrowth = twitter.follower_growth || 0;
        platforms.push(`
            <div class="glass-card p-4 rounded-xl platform-twitter hover:bg-surface-bright/20 transition-all cursor-pointer" onclick="switchTab('twitter')">
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-[18px] text-[#1DA1F2]">chat_bubble</span>
                    <span class="font-label-sm text-label-sm">TWITTER</span>
                </div>
                <div class="text-headline-sm font-headline-sm">${fmt(twitter.followers)}</div>
                <div class="text-label-sm text-on-surface-variant flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px] ${twGrowth >= 0 ? 'text-primary' : 'text-error'}">${twGrowth >= 0 ? 'trending_up' : 'trending_down'}</span>
                    ${twGrowth >= 0 ? '+' : ''}${fmt(twGrowth)}
                </div>
            </div>`);
    }
    if (tiktok) {
        const ttGrowth = tiktok.follower_growth || 0;
        platforms.push(`
            <div class="glass-card p-4 rounded-xl platform-tiktok hover:bg-surface-bright/20 transition-all cursor-pointer" onclick="switchTab('tiktok')">
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-[18px] text-[#00F2EA]">video_library</span>
                    <span class="font-label-sm text-label-sm">TIKTOK</span>
                </div>
                <div class="text-headline-sm font-headline-sm">${fmt(tiktok.followers)}</div>
                <div class="text-label-sm text-on-surface-variant flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px] ${ttGrowth >= 0 ? 'text-primary' : 'text-error'}">${ttGrowth >= 0 ? 'trending_up' : 'trending_down'}</span>
                    ${ttGrowth >= 0 ? '+' : ''}${fmt(ttGrowth)}
                </div>
            </div>`);
    }
    if (youtube) {
        const ytGrowth = youtube.subscriber_growth || 0;
        platforms.push(`
            <div class="glass-card p-4 rounded-xl platform-youtube hover:bg-surface-bright/20 transition-all cursor-pointer" onclick="switchTab('youtube')">
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-[18px] text-[#FF0000]">play_circle</span>
                    <span class="font-label-sm text-label-sm">YOUTUBE</span>
                </div>
                <div class="text-headline-sm font-headline-sm">${fmt(youtube.subscribers)}</div>
                <div class="text-label-sm text-on-surface-variant flex items-center gap-1">
                    <span class="material-symbols-outlined text-[14px] ${ytGrowth >= 0 ? 'text-primary' : 'text-error'}">${ytGrowth >= 0 ? 'trending_up' : 'trending_down'}</span>
                    ${ytGrowth >= 0 ? '+' : ''}${fmt(ytGrowth)}
                </div>
            </div>`);
    }
    if (platforms.length === 0) {
        platforms.push('<div class="col-span-4 glass-card rounded-xl p-8 text-center text-on-surface-variant">Henuz platform baglanmadi</div>');
    }
    document.getElementById('overview-platform-cards').innerHTML = platforms.join('');

    // Account Health Table
    const healthRows = [];
    if (twitter) {
        const engPct = Math.min(100, Math.round(twitter.engagement_rate * 10));
        healthRows.push(`
            <tr class="hover:bg-surface-container-highest transition-colors cursor-pointer" onclick="switchTab('twitter')">
                <td class="px-6 py-3">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-[#1DA1F2]">chat_bubble</span>
                        <span class="text-body-sm font-body-sm">Twitter</span>
                    </div>
                </td>
                <td class="px-6 py-3">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-[#1DA1F2] flex items-center justify-center text-label-sm text-white">${twitter.name.substring(0, 2).toUpperCase()}</div>
                        <span class="text-body-sm font-body-sm font-medium">@${twitter.username}</span>
                    </div>
                </td>
                <td class="px-6 py-3 text-right text-body-sm font-body-sm">${fmt(twitter.followers)}</td>
                <td class="px-6 py-3 text-right">
                    <div class="flex items-center justify-end gap-2">
                        <div class="w-16 bg-surface-container h-1 rounded-full overflow-hidden">
                            <div class="bg-primary h-full w-[${engPct}%]"></div>
                        </div>
                        <span class="text-label-sm text-on-surface-variant">%${twitter.engagement_rate}</span>
                    </div>
                </td>
                <td class="px-6 py-3 text-right">
                    <span class="bg-primary/10 text-primary px-3 py-1 rounded-full text-label-sm border border-primary/20">Aktif</span>
                </td>
            </tr>`);
    }
    if (tiktok) {
        const engPct = Math.min(100, Math.round(tiktok.engagement_rate * 10));
        healthRows.push(`
            <tr class="hover:bg-surface-container-highest transition-colors cursor-pointer" onclick="switchTab('tiktok')">
                <td class="px-6 py-3">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-[#00F2EA]">video_library</span>
                        <span class="text-body-sm font-body-sm">TikTok</span>
                    </div>
                </td>
                <td class="px-6 py-3">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-[#00F2EA] flex items-center justify-center text-label-sm text-black">${(tiktok.nickname || tiktok.username).substring(0, 2).toUpperCase()}</div>
                        <span class="text-body-sm font-body-sm font-medium">@${tiktok.username}</span>
                    </div>
                </td>
                <td class="px-6 py-3 text-right text-body-sm font-body-sm">${fmt(tiktok.followers)}</td>
                <td class="px-6 py-3 text-right">
                    <div class="flex items-center justify-end gap-2">
                        <div class="w-16 bg-surface-container h-1 rounded-full overflow-hidden">
                            <div class="bg-[#00F2EA] h-full w-[${engPct}%]"></div>
                        </div>
                        <span class="text-label-sm text-on-surface-variant">%${tiktok.engagement_rate}</span>
                    </div>
                </td>
                <td class="px-6 py-3 text-right">
                    <span class="bg-[#00F2EA]/10 text-[#00F2EA] px-3 py-1 rounded-full text-label-sm border border-[#00F2EA]/20">Aktif</span>
                </td>
            </tr>`);
    }
    if (youtube) {
        const engPct = Math.min(100, Math.round(youtube.engagement_rate * 10));
        healthRows.push(`
            <tr class="hover:bg-surface-container-highest transition-colors cursor-pointer" onclick="switchTab('youtube')">
                <td class="px-6 py-3">
                    <div class="flex items-center gap-2">
                        <span class="material-symbols-outlined text-[#FF0000]">play_circle</span>
                        <span class="text-body-sm font-body-sm">YouTube</span>
                    </div>
                </td>
                <td class="px-6 py-3">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-[#FF0000] flex items-center justify-center text-label-sm text-white">${youtube.title.substring(0, 2).toUpperCase()}</div>
                        <span class="text-body-sm font-body-sm font-medium">${youtube.title}</span>
                    </div>
                </td>
                <td class="px-6 py-3 text-right text-body-sm font-body-sm">${fmt(youtube.subscribers)}</td>
                <td class="px-6 py-3 text-right">
                    <div class="flex items-center justify-end gap-2">
                        <div class="w-16 bg-surface-container h-1 rounded-full overflow-hidden">
                            <div class="bg-[#FF0000] h-full w-[${engPct}%]"></div>
                        </div>
                        <span class="text-label-sm text-on-surface-variant">%${youtube.engagement_rate}</span>
                    </div>
                </td>
                <td class="px-6 py-3 text-right">
                    <span class="bg-[#FF0000]/10 text-[#FF0000] px-3 py-1 rounded-full text-label-sm border border-[#FF0000]/20">Aktif</span>
                </td>
            </tr>`);
    }
    if (healthRows.length === 0) {
        healthRows.push('<tr><td colspan="5" class="px-6 py-8 text-center text-on-surface-variant">Henuz platform baglanmadi</td></tr>');
    }
    document.getElementById('overview-health-table').innerHTML = healthRows.join('');
}

function setDateRange(days) {
    document.querySelectorAll('.date-btn').forEach(b => { b.classList.remove('bg-primary-container', 'text-on-primary-container'); b.classList.add('text-on-surface-variant'); });
    const btn = document.querySelector(`[data-days="${days}"]`);
    if (btn) { btn.classList.add('bg-primary-container', 'text-on-primary-container'); btn.classList.remove('text-on-surface-variant'); }

    const now = new Date();
    let from;
    if (days === 'all') {
        from = new Date(0);
        document.getElementById('date-from').value = '';
        document.getElementById('date-to').value = '';
    } else {
        from = new Date(now);
        from.setDate(from.getDate() - parseInt(days));
        document.getElementById('date-from').value = from.toISOString().split('T')[0];
        document.getElementById('date-to').value = now.toISOString().split('T')[0];
    }

    filterAndRender(from, now);
}

function filterTweetsByDate() {
    const fromVal = document.getElementById('date-from').value;
    const toVal = document.getElementById('date-to').value;
    if (!fromVal || !toVal) return;

    const from = new Date(fromVal + 'T00:00:00');
    const to = new Date(toVal + 'T23:59:59');

    document.querySelectorAll('.date-btn').forEach(b => { b.classList.remove('bg-primary-container', 'text-on-primary-container'); b.classList.add('text-on-surface-variant'); });

    filterAndRender(from, to);
}

function filterAndRender(from, to) {
    filteredTweets = allTweets.filter(t => {
        const d = new Date(t.created_at);
        return d >= from && d <= to;
    });
    renderAnalytics();
}

function loadTwitterData() { loadTwitterProfile('infoyatirim'); }

function loadTwitterProfile(username) {
    document.getElementById('twitter-status').textContent = 'Yukleniyor...';
    document.getElementById('twitter-profile-cards').innerHTML = '<div class="col-span-12 flex items-center justify-center py-12"><div class="loading-spinner"></div></div>';
    document.getElementById('twitter-analytics-cards').innerHTML = '<div class="col-span-12 flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';
    document.getElementById('content-type-cards').innerHTML = '<div class="col-span-4 flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';
    document.getElementById('best-tweets-grid').innerHTML = '<div class="col-span-3 flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';
    document.getElementById('tweets-table-body').innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center"><div class="loading-spinner mx-auto"></div></td></tr>';

    fetch('data/twitter-profile.json')
    .then(r => r.json()).then(data => {
        if (data.error) { document.getElementById('twitter-status').textContent = 'Hata'; return; }
        twitterProfile = data;
        document.getElementById('twitter-status').textContent = 'Aktif';
        document.getElementById('twitter-status').className = 'text-label-sm font-label-sm text-primary bg-primary/10 px-md py-xs rounded-full border border-primary/20';

        const growth = data.follower_growth || 0;
        const growthClass = growth >= 0 ? 'text-primary' : 'text-error';
        const growthIcon = growth >= 0 ? 'trending_up' : 'trending_down';
        const growthText = growth >= 0 ? '+' + fmt(growth) : fmt(growth);

        document.getElementById('twitter-profile-cards').innerHTML = `
            <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#1DA1F2]"></div>
                <div class="flex items-center gap-3 mb-4">
                    <img src="${data.profile_image_url}" class="w-14 h-14 rounded-full border-2 border-[#1DA1F2]">
                    <div><h3 class="font-body-sm font-semibold text-on-surface">${data.name}</h3><p class="font-label-sm text-on-surface-variant">@${data.username}</p></div>
                </div>
                <p class="font-body-sm text-on-surface-variant text-xs line-clamp-2 mb-3">${data.description || ''}</p>
                ${data.verified ? '<span class="bg-[#1DA1F2]/10 text-[#1DA1F2] px-2 py-1 rounded-full text-label-sm border border-[#1DA1F2]/20 inline-flex items-center gap-1 text-xs"><span class="material-symbols-outlined text-[12px]" style="font-variation-settings: \'FILL\' 1;">verified</span> Verified</span>' : ''}
            </div>
            <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
                <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
                <div class="flex justify-between items-start mb-2">
                    <span class="material-symbols-outlined text-tertiary p-1.5 bg-tertiary/10 rounded-lg text-sm">group</span>
                    <span class="flex items-center gap-1 ${growthClass} font-label-md text-label-md"><span class="material-symbols-outlined text-[14px]">${growthIcon}</span>${growthText}</span>
                </div>
                <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Takipci</h3>
                <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(data.followers_count)}</span>
                <p class="text-label-sm text-on-surface-variant mt-1">Takip: ${fmt(data.following_count)} | Net: ${growth >= 0 ? '+' : ''}${fmt(growth)}</p>
            </div>
            <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
                <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
                <div class="flex justify-between items-start mb-2">
                    <span class="material-symbols-outlined text-primary p-1.5 bg-primary/10 rounded-lg text-sm">article</span>
                </div>
                <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Toplam Tweet</h3>
                <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(data.tweets_count)}</span>
            </div>`;

        return fetch('data/twitter-tweets.json');
    }).then(r => r.json()).then(data => {
        if (data.error) return;
        allTweets = data;
        filteredTweets = [...allTweets];
        renderAnalytics();
    });
}

function renderAnalytics() {
    const ac = document.getElementById('twitter-analytics-cards');
    const cc = document.getElementById('content-type-cards');
    const bt = document.getElementById('best-tweets-grid');
    const tb = document.getElementById('tweets-table-body');
    if (!ac || !cc || !bt || !tb) return;

    const tweets = filteredTweets;
    const totalImpressions = tweets.reduce((s, t) => s + (parseInt(t.view_count) || 0), 0);
    const totalLikes = tweets.reduce((s, t) => s + (t.favorite_count || 0), 0);
    const totalRetweets = tweets.reduce((s, t) => s + (t.retweet_count || 0), 0);
    const totalReplies = tweets.reduce((s, t) => s + (t.reply_count || 0), 0);
    const totalQuotes = tweets.reduce((s, t) => s + (t.quote_count || 0), 0);
    const avgImpressions = tweets.length ? Math.round(totalImpressions / tweets.length) : 0;
    const engagementRate = totalImpressions > 0 ? ((totalLikes + totalRetweets + totalReplies + totalQuotes) / totalImpressions * 100).toFixed(2) : 0;

    // Takipci bilgisi
    const followers = twitterProfile ? twitterProfile.followers_count : 0;
    const followerGrowth = twitterProfile ? (twitterProfile.follower_growth || 0) : 0;
    const nonFollowerReach = Math.max(0, totalImpressions - (followers * tweets.length));

    ac.innerHTML = `
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <div class="flex justify-between items-start mb-4">
                <span class="material-symbols-outlined text-tertiary p-2 bg-tertiary/10 rounded-lg">visibility</span>
                <span class="text-tertiary font-label-md text-label-md">${tweets.length} tweet</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Toplam Gosterim</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(totalImpressions)}</span>
            <p class="text-label-sm text-on-surface-variant mt-2">Tweet basina: ${fmt(avgImpressions)}</p>
        </div>
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <div class="flex justify-between items-start mb-4">
                <span class="material-symbols-outlined text-primary p-2 bg-primary/10 rounded-lg">bolt</span>
                <span class="text-primary font-label-md text-label-md">%${engagementRate}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Etkilesim Orani</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(totalLikes + totalRetweets + totalReplies + totalQuotes)}</span>
            <p class="text-label-sm text-on-surface-variant mt-2">Begeni + RT + Yanit + Alinti</p>
        </div>
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#1DA1F2]"></div>
            <div class="flex justify-between items-start mb-4">
                <span class="material-symbols-outlined text-[#1DA1F2] p-2 bg-[#1DA1F2]/10 rounded-lg">group</span>
                <span class="${followerGrowth >= 0 ? 'text-primary' : 'text-error'} font-label-md text-label-md">${followerGrowth >= 0 ? '+' : ''}${fmt(followerGrowth)}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Takipci Artisi</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(followers)}</span>
            <p class="text-label-sm text-on-surface-variant mt-2">Guncel takipci sayisi</p>
        </div>
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
            <div class="flex justify-between items-start mb-4">
                <span class="material-symbols-outlined text-[#00F2EA] p-2 bg-[#00F2EA]/10 rounded-lg">public</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Takipci Disi Erisim</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(nonFollowerReach)}</span>
            <p class="text-label-sm text-on-surface-variant mt-2">Takipci olmayan kullanici</p>
        </div>`;

    const originalTweets = tweets.filter(t => !t.is_retweet && !t.is_quote && !t.text.startsWith('RT'));
    const retweets = tweets.filter(t => t.is_retweet || t.text.startsWith('RT'));
    const withMedia = tweets.filter(t => t.media && t.media.length > 0);
    const withVideo = tweets.filter(t => t.media && t.media.some(m => m.type === 'video'));

    cc.innerHTML = `
        <div class="glass-card rounded-xl p-5 relative overflow-hidden"><div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <div class="flex items-center gap-3 mb-3"><span class="material-symbols-outlined text-primary text-lg">edit</span><span class="font-label-md text-label-md text-on-surface-variant">Orijinal</span></div>
            <div class="font-headline-md text-headline-md text-on-surface">${originalTweets.length}</div>
            <div class="text-label-sm text-on-surface-variant">%${tweets.length ? Math.round(originalTweets.length / tweets.length * 100) : 0}</div>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden"><div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
            <div class="flex items-center gap-3 mb-3"><span class="material-symbols-outlined text-[#00F2EA] text-lg">repeat</span><span class="font-label-md text-label-md text-on-surface-variant">Retweet</span></div>
            <div class="font-headline-md text-headline-md text-on-surface">${retweets.length}</div>
            <div class="text-label-sm text-on-surface-variant">%${tweets.length ? Math.round(retweets.length / tweets.length * 100) : 0}</div>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden"><div class="absolute top-0 left-0 w-full h-1 bg-[#E4405F]"></div>
            <div class="flex items-center gap-3 mb-3"><span class="material-symbols-outlined text-[#E4405F] text-lg">image</span><span class="font-label-md text-label-md text-on-surface-variant">Gorsel</span></div>
            <div class="font-headline-md text-headline-md text-on-surface">${withMedia.length}</div>
            <div class="text-label-sm text-on-surface-variant">%${tweets.length ? Math.round(withMedia.length / tweets.length * 100) : 0}</div>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden"><div class="absolute top-0 left-0 w-full h-1 bg-[#FF0000]"></div>
            <div class="flex items-center gap-3 mb-3"><span class="material-symbols-outlined text-[#FF0000] text-lg">play_circle</span><span class="font-label-md text-label-md text-on-surface-variant">Video</span></div>
            <div class="font-headline-md text-headline-md text-on-surface">${withVideo.length}</div>
            <div class="text-label-sm text-on-surface-variant">%${tweets.length ? Math.round(withVideo.length / tweets.length * 100) : 0}</div>
        </div>`;

    const byImp = [...tweets].sort((a, b) => (parseInt(b.view_count) || 0) - (parseInt(a.view_count) || 0));
    const byRT = [...tweets].sort((a, b) => (b.retweet_count || 0) - (a.retweet_count || 0));
    const byLike = [...tweets].sort((a, b) => (b.favorite_count || 0) - (a.favorite_count || 0));

    bt.innerHTML = `
        <div class="glass-card rounded-xl overflow-hidden"><div class="p-4 border-b border-outline-variant/30 bg-[#1DA1F2]/5"><div class="flex items-center gap-2"><span class="material-symbols-outlined text-[#1DA1F2] text-lg">visibility</span><h3 class="font-label-md text-label-md text-[#1DA1F2] uppercase">En Cok Gosterim</h3></div></div>
            <div class="p-4">${byImp.slice(0, 3).map((t, i) => `<div class="flex items-start gap-3 py-3 ${i < 2 ? 'border-b border-outline-variant/20' : ''}"><span class="font-headline-sm text-headline-sm text-on-surface-variant">${i + 1}</span><div class="flex-1 min-w-0"><p class="text-body-sm text-on-surface line-clamp-2">${linkify(t.text.substring(0, 80))}</p><div class="flex items-center gap-3 mt-2 text-label-sm text-on-surface-variant"><span>${fmt(parseInt(t.view_count) || 0)} gorunme</span><span>${fmt(t.favorite_count || 0)} begeni</span></div></div></div>`).join('')}</div>
        </div>
        <div class="glass-card rounded-xl overflow-hidden"><div class="p-4 border-b border-outline-variant/30 bg-[#00F2EA]/5"><div class="flex items-center gap-2"><span class="material-symbols-outlined text-[#00F2EA] text-lg">repeat</span><h3 class="font-label-md text-label-md text-[#00F2EA] uppercase">En Cok Retweet</h3></div></div>
            <div class="p-4">${byRT.slice(0, 3).map((t, i) => `<div class="flex items-start gap-3 py-3 ${i < 2 ? 'border-b border-outline-variant/20' : ''}"><span class="font-headline-sm text-headline-sm text-on-surface-variant">${i + 1}</span><div class="flex-1 min-w-0"><p class="text-body-sm text-on-surface line-clamp-2">${linkify(t.text.substring(0, 80))}</p><div class="flex items-center gap-3 mt-2 text-label-sm text-on-surface-variant"><span>${fmt(t.retweet_count || 0)} RT</span><span>${fmt(t.favorite_count || 0)} begeni</span></div></div></div>`).join('')}</div>
        </div>
        <div class="glass-card rounded-xl overflow-hidden"><div class="p-4 border-b border-outline-variant/30 bg-[#E4405F]/5"><div class="flex items-center gap-2"><span class="material-symbols-outlined text-[#E4405F] text-lg">favorite</span><h3 class="font-label-md text-label-md text-[#E4405F] uppercase">En Cok Begeni</h3></div></div>
            <div class="p-4">${byLike.slice(0, 3).map((t, i) => `<div class="flex items-start gap-3 py-3 ${i < 2 ? 'border-b border-outline-variant/20' : ''}"><span class="font-headline-sm text-headline-sm text-on-surface-variant">${i + 1}</span><div class="flex-1 min-w-0"><p class="text-body-sm text-on-surface line-clamp-2">${linkify(t.text.substring(0, 80))}</p><div class="flex items-center gap-3 mt-2 text-label-sm text-on-surface-variant"><span>${fmt(t.favorite_count || 0)} begeni</span><span>${fmt(t.retweet_count || 0)} RT</span></div></div></div>`).join('')}</div>
        </div>`;

    document.getElementById('tweet-count-label').textContent = `${tweets.length} tweet`;
    tb.innerHTML = tweets.map(t => {
        const eng = (t.favorite_count || 0) + (t.retweet_count || 0) + (t.reply_count || 0);
        const engRate = parseInt(t.view_count) > 0 ? ((eng / parseInt(t.view_count)) * 100).toFixed(1) : 0;
        let ct = 'Tweet';
        if (t.is_retweet || t.text.startsWith('RT')) ct = 'Retweet';
        else if (t.is_quote) ct = 'Alinti';
        else if (t.media && t.media.length > 0) ct = t.media.some(m => m.type === 'video') ? 'Video' : 'Gorsel';

        return `<tr class="hover:bg-surface-container-highest transition-colors">
            <td class="px-4 py-3 max-w-xs"><p class="text-body-sm text-on-surface line-clamp-1">${linkify(t.text.substring(0, 60))}</p><p class="text-label-sm text-on-surface-variant mt-1">${formatDate(t.created_at)}</p></td>
            <td class="px-4 py-3"><span class="text-label-sm px-2 py-1 rounded-full ${ct === 'Video' ? 'bg-[#FF0000]/10 text-[#FF0000]' : ct === 'Gorsel' ? 'bg-[#E4405F]/10 text-[#E4405F]' : ct === 'Retweet' ? 'bg-[#00F2EA]/10 text-[#00F2EA]' : 'bg-primary/10 text-primary'}">${ct}</span></td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(parseInt(t.view_count) || 0)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(t.favorite_count || 0)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(t.retweet_count || 0)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(t.reply_count || 0)}</td>
            <td class="px-4 py-3 text-right"><span class="text-label-sm ${engRate > 5 ? 'text-primary' : engRate > 2 ? 'text-tertiary' : 'text-on-surface-variant'}">%${engRate}</span></td>
        </tr>`;
    }).join('');
}

function fmt(n) { if (!n) return '0'; if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'; if (n >= 1000) return (n / 1000).toFixed(1) + 'K'; return n.toString(); }

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return 'simdi';
    if (diff < 3600000) return Math.floor(diff / 60000) + 'dk once';
    if (diff < 86400000) return Math.floor(diff / 3600000) + 'sa once';
    return d.toLocaleDateString('tr-TR', {day: 'numeric', month: 'short', year: 'numeric'});
}

function linkify(text) {
    if (!text) return '';
    return text.replace(/@(\w+)/g, '<a href="https://x.com/$1" target="_blank" class="text-[#1DA1F2] hover:underline">@$1</a>').replace(/#(\w+)/g, '<a href="https://x.com/hashtag/$1" target="_blank" class="text-[#1DA1F2] hover:underline">#$1</a>').replace(/(https?:\/\/\S+)/g, '<a href="$1" target="_blank" class="text-[#1DA1F2] hover:underline">$1</a>');
}

// ==================== TIKTOK ====================
let tiktokAnalytics = null;

function setTikTokRange(days) {
    document.querySelectorAll('.tiktok-range-btn').forEach(b => {
        b.classList.remove('bg-[#00F2EA]', 'text-black');
        b.classList.add('text-on-surface-variant');
    });
    const btn = document.querySelector(`[data-days="${days}"]`);
    if (btn) {
        btn.classList.add('bg-[#00F2EA]', 'text-black');
        btn.classList.remove('text-on-surface-variant');
    }

    const fromEl = document.getElementById('tiktok-date-from');
    const toEl = document.getElementById('tiktok-date-to');
    if (days === 'all') {
        fromEl.value = '';
        toEl.value = '';
    } else {
        const now = new Date();
        const from = new Date();
        from.setDate(from.getDate() - parseInt(days));
        fromEl.value = from.toISOString().split('T')[0];
        toEl.value = now.toISOString().split('T')[0];
    }
    loadTikTokData();
}

function loadTikTokData() {
    const input = document.getElementById('tiktok-username-input');
    const username = input ? input.value.trim().replace('@', '') : 'infoyatirim';
    if (!username) {
        document.getElementById('tiktok-status').textContent = 'Kullanici adi gerekli';
        return;
    }

    const fromVal = document.getElementById('tiktok-date-from').value || '';
    const toVal = document.getElementById('tiktok-date-to').value || '';
    const params = new URLSearchParams();
    if (fromVal) params.set('from', fromVal);
    if (toVal) params.set('to', toVal);

    const statusEl = document.getElementById('tiktok-status');
    statusEl.textContent = 'Yukleniyor...';

    const loadingIds = ['tiktok-profile-cards', 'tiktok-follower-growth', 'tiktok-view-quality', 'tiktok-engagement', 'tiktok-video-rankings', 'tiktok-formats', 'tiktok-hashtags'];
    loadingIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '<div class="col-span-full flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';
    });
    document.getElementById('tiktok-videos-table').innerHTML = '<tr><td colspan="7" class="px-4 py-8 text-center"><div class="loading-spinner mx-auto"></div></td></tr>';

    fetch('data/tiktok-analytics.json')
    .then(r => r.json()).then(data => {
        if (data.error) {
            statusEl.textContent = 'Hata';
            statusEl.className = 'text-label-sm font-label-sm text-error bg-error/10 px-md py-xs rounded-full border border-error/20';
            return;
        }
        tiktokAnalytics = data;
        statusEl.textContent = 'Aktif';
        statusEl.className = 'text-label-sm font-label-sm text-[#00F2EA] bg-[#00F2EA]/10 px-md py-xs rounded-full border border-[#00F2EA]/20';
        renderTikTokAll();
    }).catch(() => {
        statusEl.textContent = 'Hata';
        statusEl.className = 'text-label-sm font-label-sm text-error bg-error/10 px-md py-xs rounded-full border border-error/20';
    });
}

function renderTikTokAll() {
    if (!tiktokAnalytics) return;
    const { profile, follower_growth, summary, view_quality, format_analysis, best_by_views, best_by_engagement, worst_videos, top_hashtags, all_videos } = tiktokAnalytics;

    // === Profile Cards ===
    const growth = profile.follower_growth || 0;
    const growthRate = profile.follower_growth_rate || 0;
    const growthClass = growth >= 0 ? 'text-[#00F2EA]' : 'text-error';
    const growthIcon = growth >= 0 ? 'trending_up' : 'trending_down';
    const growthText = growth >= 0 ? '+' + fmt(growth) : fmt(growth);

    document.getElementById('tiktok-profile-cards').innerHTML = `
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
            <div class="flex items-center gap-3 mb-4">
                ${profile.avatar ? `<img src="${profile.avatar}" class="w-14 h-14 rounded-full border-2 border-[#00F2EA]">` : '<div class="w-14 h-14 rounded-full bg-[#00F2EA]/20 flex items-center justify-center"><span class="material-symbols-outlined text-[#00F2EA]">person</span></div>'}
                <div><h3 class="font-body-sm font-semibold text-on-surface">${profile.nickname || profile.username}</h3><p class="font-label-sm text-on-surface-variant">@${profile.username}</p></div>
            </div>
            <p class="font-body-sm text-on-surface-variant text-xs line-clamp-2 mb-3">${profile.description || ''}</p>
            ${profile.verified ? '<span class="bg-[#00F2EA]/10 text-[#00F2EA] px-2 py-1 rounded-full text-label-sm border border-[#00F2EA]/20 inline-flex items-center gap-1 text-xs"><span class="material-symbols-outlined text-[12px]" style="font-variation-settings: \'FILL\' 1;">verified</span> Verified</span>' : ''}
        </div>
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <div class="flex justify-between items-start mb-2">
                <span class="material-symbols-outlined text-tertiary p-1.5 bg-tertiary/10 rounded-lg text-sm">group</span>
                <span class="flex items-center gap-1 ${growthClass} font-label-md text-label-md"><span class="material-symbols-outlined text-[14px]">${growthIcon}</span>${growthText}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Takipci</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(profile.followers)}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Buyume orani: %${growthRate}</p>
        </div>
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0050]"></div>
            <div class="flex justify-between items-start mb-2">
                <span class="material-symbols-outlined text-[#FF0050] p-1.5 bg-[#FF0050]/10 rounded-lg text-sm">favorite</span>
                <span class="${profile.heart_growth >= 0 ? 'text-[#FF0050]' : 'text-error'} font-label-md text-label-md">${profile.heart_growth >= 0 ? '+' : ''}${fmt(profile.heart_growth)}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Toplam Begeni</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(profile.hearts)}</span>
        </div>
        <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <div class="flex justify-between items-start mb-2">
                <span class="material-symbols-outlined text-primary p-1.5 bg-primary/10 rounded-lg text-sm">videocam</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Toplam Video</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(profile.videos)}</span>
        </div>`;

    // === Follower Growth Chart ===
    const fgEl = document.getElementById('tiktok-follower-growth');
    if (follower_growth && follower_growth.history && follower_growth.history.length >= 2) {
        const hist = follower_growth.history;
        const maxF = Math.max(...hist.map(h => h.followers || 0));
        const minF = Math.min(...hist.map(h => h.followers || 0));
        const range = maxF - minF || 1;
        const netG = follower_growth.net_growth;
        const netClass = netG >= 0 ? 'text-[#00F2EA]' : 'text-error';
        const netIcon = netG >= 0 ? 'trending_up' : 'trending_down';

        fgEl.innerHTML = `
            <div class="col-span-12 glass-card p-xl rounded-xl">
                <div class="flex justify-between items-center mb-6">
                    <div>
                        <h3 class="font-headline-sm text-headline-sm text-on-surface">Takipci Trendi</h3>
                        <p class="text-label-sm text-on-surface-variant">${follower_growth.start_date} - ${follower_growth.end_date}</p>
                    </div>
                    <div class="flex items-center gap-6">
                        <div class="text-right">
                            <p class="text-label-sm text-on-surface-variant">Baslangic</p>
                            <p class="font-headline-sm text-headline-sm text-on-surface">${fmt(follower_growth.start_followers)}</p>
                        </div>
                        <span class="material-symbols-outlined text-on-surface-variant">arrow_forward</span>
                        <div class="text-right">
                            <p class="text-label-sm text-on-surface-variant">Bitis</p>
                            <p class="font-headline-sm text-headline-sm text-on-surface">${fmt(follower_growth.end_followers)}</p>
                        </div>
                        <div class="flex items-center gap-1 ${netClass} bg-surface-container px-3 py-1.5 rounded-full">
                            <span class="material-symbols-outlined text-[16px]">${netIcon}</span>
                            <span class="font-label-md text-label-md">${netG >= 0 ? '+' : ''}${fmt(netG)}</span>
                            <span class="text-label-sm">(%${follower_growth.growth_rate})</span>
                        </div>
                    </div>
                </div>
                <div class="relative h-48 w-full">
                    <svg viewBox="0 0 ${Math.max(hist.length * 40, 400)} 180" class="w-full h-full" preserveAspectRatio="none">
                        <defs>
                            <linearGradient id="tiktokGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stop-color="#00F2EA" stop-opacity="0.3"/>
                                <stop offset="100%" stop-color="#00F2EA" stop-opacity="0.02"/>
                            </linearGradient>
                        </defs>
                        <path d="M${hist.map((h, i) => {
                            const x = (i / (hist.length - 1)) * Math.max(hist.length * 40 - 40, 360) + 20;
                            const y = 170 - ((h.followers - minF) / range) * 150;
                            return `${i === 0 ? 'M' : 'L'}${x},${y}`;
                        }).join(' ')} L${(hist.length - 1) / (hist.length - 1) * Math.max(hist.length * 40 - 40, 360) + 20},170 L20,170 Z" fill="url(#tiktokGrad)"/>
                        <path d="${hist.map((h, i) => {
                            const x = (i / (hist.length - 1)) * Math.max(hist.length * 40 - 40, 360) + 20;
                            const y = 170 - ((h.followers - minF) / range) * 150;
                            return `${i === 0 ? 'M' : 'L'}${x},${y}`;
                        }).join(' ')}" fill="none" stroke="#00F2EA" stroke-width="2.5"/>
                        ${hist.map((h, i) => {
                            const x = (i / (hist.length - 1)) * Math.max(hist.length * 40 - 40, 360) + 20;
                            const y = 170 - ((h.followers - minF) / range) * 150;
                            return `<circle cx="${x}" cy="${y}" r="4" fill="#00F2EA" stroke="#0a1e2e" stroke-width="2"/>`;
                        }).join('')}
                    </svg>
                    <div class="absolute bottom-0 left-0 w-full flex justify-between px-5">
                        <span class="text-label-sm text-on-surface-variant">${hist[0].date ? hist[0].date.substring(0, 10) : ''}</span>
                        <span class="text-label-sm text-on-surface-variant">${hist[hist.length - 1].date ? hist[hist.length - 1].date.substring(0, 10) : ''}</span>
                    </div>
                </div>
            </div>`;
    } else {
        fgEl.innerHTML = `
            <div class="col-span-12 glass-card p-xl rounded-xl">
                <div class="flex items-center gap-4">
                    <span class="material-symbols-outlined text-on-surface-variant">info</span>
                    <div>
                        <h3 class="font-headline-sm text-headline-sm text-on-surface">Takipci Grafigi</h3>
                        <p class="text-label-sm text-on-surface-variant">Takipci gecmisi verisi icin birden fazla gun kontrol edin. Guncel takipci: ${fmt(profile.followers)}</p>
                    </div>
                </div>
            </div>`;
    }

    // === View Quality ===
    document.getElementById('tiktok-view-quality').innerHTML = `
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
            <span class="material-symbols-outlined text-[#00F2EA] text-lg mb-2">visibility</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Ort. Izlenme</h4>
            <div class="font-headline-md text-headline-md text-on-surface">${fmt(summary.avg_views)}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">Video basina</p>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <span class="material-symbols-outlined text-tertiary text-lg mb-2">timer</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Ort. Sure</h4>
            <div class="font-headline-md text-headline-md text-on-surface">${Math.floor(view_quality.avg_duration / 60)}:${String(Math.round(view_quality.avg_duration % 60)).padStart(2, '0')}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">${Math.round(view_quality.avg_duration)} saniye</p>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0050]"></div>
            <span class="material-symbols-outlined text-[#FF0050] text-lg mb-2">speed</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Izlenme/Saniye</h4>
            <div class="font-headline-md text-headline-md text-on-surface">${fmt(view_quality.avg_view_per_second)}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">Saniye basina ortalama</p>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <span class="material-symbols-outlined text-primary text-lg mb-2">replay</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Tekrar Izleme</h4>
            <div class="font-headline-md text-headline-md text-on-surface">%${view_quality.rewatch_rate}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">Takipci basina izlenme</p>
        </div>`;

    // === Engagement ===
    document.getElementById('tiktok-engagement').innerHTML = `
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0050]"></div>
            <span class="material-symbols-outlined text-[#FF0050] text-lg mb-2">favorite</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Begeni</h4>
            <div class="font-headline-md text-headline-md text-on-surface">${fmt(summary.total_likes)}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">Ort: ${fmt(summary.avg_likes)}</p>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <span class="material-symbols-outlined text-primary text-lg mb-2">chat</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Yorum</h4>
            <div class="font-headline-md text-headline-md text-on-surface">${fmt(summary.total_comments)}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">Ort: ${fmt(summary.avg_comments)}</p>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
            <span class="material-symbols-outlined text-[#00F2EA] text-lg mb-2">share</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Paylasim</h4>
            <div class="font-headline-md text-headline-md text-on-surface">${fmt(summary.total_shares)}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">Ort: ${fmt(summary.avg_shares)}</p>
        </div>
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <span class="material-symbols-outlined text-tertiary text-lg mb-2">bookmark</span>
            <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Kaydetme + Etkilesim Orani</h4>
            <div class="font-headline-md text-headline-md text-on-surface">${fmt(summary.total_saves)}</div>
            <p class="text-label-sm text-on-surface-variant mt-1">%${summary.engagement_rate} etkilesim</p>
        </div>`;

    // === Video Rankings ===
    const renderList = (title, icon, color, items) => `
        <div class="glass-card rounded-xl overflow-hidden">
            <div class="p-4 border-b border-outline-variant/30 bg-${color}/5">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-${color} text-lg">${icon}</span>
                    <h3 class="font-label-md text-label-md text-${color} uppercase">${title}</h3>
                </div>
            </div>
            <div class="p-4">${items.map((v, i) => `
                <div class="flex items-start gap-3 py-3 ${i < items.length - 1 ? 'border-b border-outline-variant/20' : ''}">
                    <span class="font-headline-sm text-headline-sm text-on-surface-variant">${i + 1}</span>
                    <div class="flex-1 min-w-0">
                        <p class="text-body-sm text-on-surface line-clamp-2">${v.desc ? v.desc.substring(0, 70) : 'Aciklama yok'}</p>
                        <div class="flex items-center gap-3 mt-2 text-label-sm text-on-surface-variant">
                            <span>${fmt(v.play_count)} izlenme</span>
                            <span>${fmt(v.like_count)} begeni</span>
                            <span>${fmt(v.comment_count)} yorum</span>
                        </div>
                    </div>
                </div>`).join('')}
            </div>
        </div>`;

    document.getElementById('tiktok-video-rankings').innerHTML =
        renderList('En Cok Izlenen', 'visibility', '#00F2EA', best_by_views) +
        renderList('En Cok Etkilesim Alan', 'bolt', '#FF0050', best_by_engagement);

    // === Format Analysis ===
    const formatCards = [
        { key: 'short', label: 'Kisa (≤15s)', icon: 'bolt', color: '#00F2EA' },
        { key: 'medium', label: 'Orta (15-60s)', icon: 'timer', color: '#FF0050' },
        { key: 'long', label: 'Uzun (>60s)', icon: 'schedule', color: 'primary' },
    ];
    document.getElementById('tiktok-formats').innerHTML = formatCards.map(f => {
        const d = format_analysis[f.key];
        return `
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-${f.color}"></div>
            <div class="flex items-center gap-3 mb-3">
                <span class="material-symbols-outlined text-${f.color} text-lg">${f.icon}</span>
                <span class="font-label-md text-label-md text-on-surface-variant">${f.label}</span>
            </div>
            <div class="font-headline-md text-headline-md text-on-surface">${d.count} video</div>
            <div class="text-label-sm text-on-surface-variant mt-1">Ort. izlenme: ${fmt(d.avg_views)}</div>
            <div class="text-label-sm text-on-surface-variant">Ort. begeni: ${fmt(d.avg_likes)}</div>
            <div class="text-label-sm ${d.avg_eng_rate > 5 ? 'text-[#00F2EA]' : 'text-on-surface-variant'} mt-1">Etkilesim: %${d.avg_eng_rate}</div>
        </div>`;
    }).join('');

    // === Hashtags ===
    document.getElementById('tiktok-hashtags').innerHTML = top_hashtags.length ?
        top_hashtags.map(h => `
        <div class="glass-card rounded-xl p-4 text-center">
            <div class="font-headline-sm text-headline-sm text-[#00F2EA]">#${h.tag}</div>
            <div class="text-label-sm text-on-surface-variant mt-1">${h.count} video</div>
            <div class="text-label-sm text-on-surface-variant">${fmt(h.total_views)} izlenme</div>
        </div>`).join('') :
        '<div class="col-span-5 glass-card rounded-xl p-8 text-center"><p class="text-on-surface-variant">Hashtag verisi bulunamadi</p></div>';

    // === All Videos Table ===
    document.getElementById('tiktok-video-count-label').textContent = `${all_videos.length} video`;
    document.getElementById('tiktok-videos-table').innerHTML = all_videos.map(v => {
        const eng = (v.like_count || 0) + (v.comment_count || 0) + (v.share_count || 0) + (v.save_count || 0);
        const engRate = v.play_count > 0 ? ((eng / v.play_count) * 100).toFixed(1) : 0;
        const duration = v.duration ? `${Math.floor(v.duration / 60)}:${(v.duration % 60).toString().padStart(2, '0')}` : '-';
        return `<tr class="hover:bg-surface-container-highest transition-colors">
            <td class="px-4 py-3 max-w-xs">
                <p class="text-body-sm text-on-surface line-clamp-1">${v.desc ? v.desc.substring(0, 60) : 'Aciklama yok'}</p>
                <p class="text-label-sm text-on-surface-variant mt-1">${formatDate(v.created_at * 1000)}</p>
            </td>
            <td class="px-4 py-3 text-body-sm">${duration}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.play_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.like_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.comment_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.save_count)}</td>
            <td class="px-4 py-3 text-right"><span class="text-label-sm ${engRate > 10 ? 'text-[#00F2EA]' : engRate > 5 ? 'text-tertiary' : 'text-on-surface-variant'}">%${engRate}</span></td>
        </tr>`;
    }).join('');
}

// ==================== YOUTUBE ====================
let youtubeData = null;
let youtubeChannelId = '';
let youtubeDays = 30;

function setYouTubeDays(days) {
    youtubeDays = days;
    document.querySelectorAll('.yt-days-btn').forEach(b => {
        b.classList.remove('bg-[#FF0000]', 'text-white');
        b.classList.add('text-on-surface-variant');
    });
    const btn = document.querySelector(`.yt-days-btn[data-days="${days}"]`);
    if (btn) {
        btn.classList.add('bg-[#FF0000]', 'text-white');
        btn.classList.remove('text-on-surface-variant');
    }
    if (youtubeChannelId) {
        loadYouTubeData(youtubeChannelId);
    }
}

function searchYouTube() {
    const input = document.getElementById('youtube-search-input');
    const query = input ? input.value.trim() : '';
    if (!query) return;

    // Eger dogrudan kanal ID girilmis ise
    if (query.startsWith('UC') && query.length > 20) {
        youtubeChannelId = query;
        loadYouTubeData(query);
        return;
    }

    document.getElementById('youtube-status').textContent = 'Aranıyor...';
    fetch('data/youtube-search-cache.json')
    .then(r => r.json()).then(cache => {
        const data = [];
        const q = query.toLowerCase();
        for (const [key, results] of Object.entries(cache)) {
            if (key.includes(q)) {
                data.push(...results);
            }
        }
        // Also search by title
        for (const [key, results] of Object.entries(cache)) {
            for (const ch of results) {
                if (ch.title && ch.title.toLowerCase().includes(q) && !data.find(d => d.id === ch.id)) {
                    data.push(ch);
                }
            }
        }
        if (!data.length) {
            document.getElementById('youtube-status').textContent = 'Sonuc yok';
            return;
        }
        document.getElementById('youtube-status').textContent = `${data.length} kanal bulundu`;
        const grid = document.getElementById('youtube-search-grid');
        document.getElementById('youtube-search-results').classList.remove('hidden');
        grid.innerHTML = data.map(ch => `
            <div class="glass-card rounded-xl p-4 cursor-pointer hover:bg-surface-bright/20 transition-all" onclick="loadYouTubeData('${ch.id}')">
                <div class="flex items-center gap-3">
                    <img src="${ch.thumbnail}" class="w-12 h-12 rounded-full">
                    <div>
                        <h4 class="font-body-sm font-semibold text-on-surface">${ch.title}</h4>
                        <p class="text-label-sm text-on-surface-variant line-clamp-1">${ch.description}</p>
                    </div>
                </div>
            </div>
        `).join('');
    });
}

function loadYouTubeData(channelId) {
    youtubeChannelId = channelId;
    const statusEl = document.getElementById('youtube-status');
    statusEl.textContent = 'Yukleniyor...';

    // Input guncelle
    const input = document.getElementById('youtube-search-input');
    if (input && !input.value) input.value = 'İnfo Yatırım';

    // Hide search results
    document.getElementById('youtube-search-results').classList.add('hidden');

    // Show loading in all sections
    ['youtube-profile-cards', 'yt-sub-growth', 'yt-metrics', 'yt-rankings', 'yt-duration', 'yt-tags'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '<div class="col-span-full flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';
    });
    document.getElementById('yt-videos-table').innerHTML = '<tr><td colspan="6" class="px-4 py-8 text-center"><div class="loading-spinner mx-auto"></div></td></tr>';

    fetch('data/youtube-analytics.json')
    .then(r => r.json()).then(data => {
        if (data.error) {
            statusEl.textContent = 'Hata';
            statusEl.className = 'text-label-sm font-label-sm text-error bg-error/10 px-md py-xs rounded-full border border-error/20';
            return;
        }
        youtubeData = data;
        statusEl.textContent = 'Aktif';
        statusEl.className = 'text-label-sm font-label-sm text-[#FF0000] bg-[#FF0000]/10 px-md py-xs rounded-full border border-[#FF0000]/20';
        renderYouTubeAll();
    }).catch(() => {
        statusEl.textContent = 'Hata - API Key gerekli';
        statusEl.className = 'text-label-sm font-label-sm text-error bg-error/10 px-md py-xs rounded-full border border-error/20';
    });
}

function renderYouTubeAll() {
    if (!youtubeData) return;
    const { channel, analytics, summary, duration_analysis, best_by_views, best_by_likes, best_by_comments, worst_videos, top_tags, all_videos } = youtubeData;

    // Show all sections
    ['yt-sub-section', 'yt-metrics-section', 'yt-rankings-section', 'yt-duration-section', 'yt-tags-section', 'yt-table-section'].forEach(id => {
        document.getElementById(id).classList.remove('hidden');
    });

    // === Profile Cards ===
    const sg = summary.subscriber_growth || 0;
    const sgRate = summary.subscriber_growth_rate || 0;
    const sgClass = sg >= 0 ? 'text-[#FF0000]' : 'text-error';
    const sgIcon = sg >= 0 ? 'trending_up' : 'trending_down';

    document.getElementById('youtube-profile-cards').innerHTML = `
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0000]"></div>
            <div class="flex items-center gap-3 mb-4">
                <img src="${channel.thumbnail}" class="w-14 h-14 rounded-full border-2 border-[#FF0000]">
                <div><h3 class="font-body-sm font-semibold text-on-surface">${channel.title}</h3><p class="font-label-sm text-on-surface-variant">${channel.country || 'Global'}</p></div>
            </div>
            <p class="font-body-sm text-on-surface-variant text-xs line-clamp-2 mb-3">${channel.description || ''}</p>
            <p class="text-label-sm text-on-surface-variant">Son ${youtubeDays} gune ait ${summary.fetched_videos} video</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <div class="flex justify-between items-start mb-2">
                <span class="material-symbols-outlined text-tertiary p-1.5 bg-tertiary/10 rounded-lg text-sm">group</span>
                <span class="flex items-center gap-1 ${sgClass} font-label-md text-label-md"><span class="material-symbols-outlined text-[14px]">${sgIcon}</span>${sg >= 0 ? '+' : ''}${fmt(sg)}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Abone</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${channel.subscribers_hidden ? 'Gizli' : fmt(channel.subscribers)}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Buyume: %${sgRate}</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden group">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <div class="flex justify-between items-start mb-2">
                <span class="material-symbols-outlined text-primary p-1.5 bg-primary/10 rounded-lg text-sm">visibility</span>
                <span class="text-primary font-label-md text-label-md">+${fmt(summary.view_growth || 0)}</span>
            </div>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Toplam Izlenme</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(channel.total_views)}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">${fmt(summary.total_videos)} video yuklendi</p>
        </div>`;

    // === Subscriber Growth ===
    const sgEl = document.getElementById('yt-sub-growth');
    if (analytics && analytics.totals) {
        const at = analytics.totals;
        sgEl.innerHTML = `
            <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#00C853]"></div>
                <span class="material-symbols-outlined text-[#00C853] text-lg mb-2">person_add</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Kazanilan Abone</h4>
                <div class="font-headline-md text-headline-md text-on-surface">+${fmt(at.subs_gained)}</div>
            </div>
            <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-error"></div>
                <span class="material-symbols-outlined text-error text-lg mb-2">person_remove</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Kaybedilen Abone</h4>
                <div class="font-headline-md text-headline-md text-on-surface">-${fmt(at.subs_lost)}</div>
            </div>
            <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0000]"></div>
                <span class="material-symbols-outlined text-[#FF0000] text-lg mb-2">group</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Net Buyume</h4>
                <div class="font-headline-md text-headline-md text-on-surface">${at.subs_gained - at.subs_lost >= 0 ? '+' : ''}${fmt(at.subs_gained - at.subs_lost)}</div>
                <div class="text-label-sm text-on-surface-variant">Son 30 gun</div>
            </div>
            <div class="col-span-12 md:col-span-3 glass-card p-xl rounded-xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
                <span class="material-symbols-outlined text-tertiary text-lg mb-2">trending_up</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Net Oran</h4>
                <div class="font-headline-md text-headline-md text-on-surface">%${at.subs_gained > 0 ? Math.round(((at.subs_gained - at.subs_lost) / at.subs_gained) * 100) : 0}</div>
                <div class="text-label-sm text-on-surface-variant">Retention rate</div>
            </div>`;
    } else {
        sgEl.innerHTML = `
            <div class="col-span-12 glass-card p-xl rounded-xl">
                <div class="flex items-center gap-4">
                    <span class="material-symbols-outlined text-on-surface-variant">info</span>
                    <div>
                        <h3 class="font-headline-sm text-headline-sm text-on-surface">Abone Degisimi</h3>
                        <p class="text-label-sm text-on-surface-variant">Detayli veriler icin YouTube Analytics API (OAuth) gerekli. Guncel abone: ${fmt(channel.subscribers)}</p>
                    </div>
                </div>
            </div>`;
    }

    // === Metrics (Watch Time, Duration, CTR) ===
    const mEl = document.getElementById('yt-metrics');
    if (analytics && analytics.totals) {
        const at = analytics.totals;
        mEl.innerHTML = `
            <div class="glass-card rounded-xl p-5 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0000]"></div>
                <span class="material-symbols-outlined text-[#FF0000] text-lg mb-2">visibility</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Toplam Izlenme</h4>
                <div class="font-headline-md text-headline-md text-on-surface">${fmt(at.views)}</div>
                <div class="text-label-sm text-on-surface-variant">Son 30 gun</div>
            </div>
            <div class="glass-card rounded-xl p-5 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
                <span class="material-symbols-outlined text-tertiary text-lg mb-2">schedule</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Toplam Izleme Suresi</h4>
                <div class="font-headline-md text-headline-md text-on-surface">${fmt(Math.round(at.watch_time_min))} dk</div>
                <div class="text-label-sm text-on-surface-variant">${(at.watch_time_min / 60).toFixed(1)} saat</div>
            </div>
            <div class="glass-card rounded-xl p-5 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
                <span class="material-symbols-outlined text-[#00F2EA] text-lg mb-2">timer</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Ort. Izleme Suresi</h4>
                <div class="font-headline-md text-headline-md text-on-surface">${Math.floor(at.avg_duration / 60)}:${String(Math.round(at.avg_duration % 60)).padStart(2, '0')}</div>
                <div class="text-label-sm text-on-surface-variant">${Math.round(at.avg_duration)} saniye</div>
            </div>
            <div class="glass-card rounded-xl p-5 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
                <span class="material-symbols-outlined text-primary text-lg mb-2">speed</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Izleyici Tutma</h4>
                <div class="font-headline-md text-headline-md text-on-surface">%${Math.round(at.avg_view_pct)}</div>
                <div class="text-label-sm text-on-surface-variant">Ort. izlenme yuzdesi</div>
            </div>`;
    } else {
        mEl.innerHTML = `
            <div class="col-span-4 glass-card rounded-xl p-5 text-center">
                <span class="material-symbols-outlined text-on-surface-variant text-2xl mb-2">schedule</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Ort. Video Suresi</h4>
                <div class="font-headline-md text-headline-md text-on-surface">${Math.floor(summary.avg_duration_sec / 60)}:${String(Math.round(summary.avg_duration_sec % 60)).padStart(2, '0')}</div>
            </div>
            <div class="col-span-4 glass-card rounded-xl p-5 text-center">
                <span class="material-symbols-outlined text-on-surface-variant text-2xl mb-2">visibility</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Ort. Izlenme</h4>
                <div class="font-headline-md text-headline-md text-on-surface">${fmt(summary.avg_views)}</div>
            </div>
            <div class="col-span-4 glass-card rounded-xl p-5 text-center">
                <span class="material-symbols-outlined text-on-surface-variant text-2xl mb-2">favorite</span>
                <h4 class="font-label-md text-label-md text-on-surface-variant mb-1">Ort. Begeni</h4>
                <div class="font-headline-md text-headline-md text-on-surface">${fmt(summary.avg_likes)}</div>
            </div>`;
    }

    // === Rankings ===
    const rEl = document.getElementById('yt-rankings');
    const renderRank = (title, icon, color, items, metric, metricLabel) => `
        <div class="glass-card rounded-xl overflow-hidden">
            <div class="p-4 border-b border-outline-variant/30 bg-${color}/5">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-${color} text-lg">${icon}</span>
                    <h3 class="font-label-md text-label-md text-${color} uppercase">${title}</h3>
                </div>
            </div>
            <div class="p-4">${items.map((v, i) => `
                <div class="flex items-start gap-3 py-3 ${i < items.length - 1 ? 'border-b border-outline-variant/20' : ''}">
                    <span class="font-headline-sm text-headline-sm text-on-surface-variant">${i + 1}</span>
                    <img src="${v.thumbnail}" class="w-16 h-12 rounded object-cover flex-shrink-0">
                    <div class="flex-1 min-w-0">
                        <p class="text-body-sm text-on-surface line-clamp-1">${v.title}</p>
                        <div class="flex items-center gap-3 mt-1 text-label-sm text-on-surface-variant">
                            <span>${fmt(v[metric])} ${metricLabel}</span>
                            <span>${fmt(v.view_count)} izlenme</span>
                        </div>
                    </div>
                </div>`).join('')}
            </div>
        </div>`;

    rEl.innerHTML =
        renderRank('En Cok Izlenen', 'visibility', '#FF0000', best_by_views, 'view_count', 'izlenme') +
        renderRank('En Cok Begeni', 'favorite', '#EA4335', best_by_likes, 'like_count', 'begeni');

    // === Duration Analysis ===
    const durEl = document.getElementById('yt-duration');
    const durCards = [
        { key: 'short', label: 'Kisa (≤1 dk)', icon: 'bolt', color: '#FF0000' },
        { key: 'medium', label: 'Orta (1-10 dk)', icon: 'timer', color: '#FBBC04' },
        { key: 'long', label: 'Uzun (>10 dk)', icon: 'schedule', color: '#00C853' },
    ];
    durEl.innerHTML = durCards.map(d => {
        const data = duration_analysis[d.key];
        return `
        <div class="glass-card rounded-xl p-5 relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-${d.color}"></div>
            <div class="flex items-center gap-3 mb-3">
                <span class="material-symbols-outlined text-${d.color} text-lg">${d.icon}</span>
                <span class="font-label-md text-label-md text-on-surface-variant">${d.label}</span>
            </div>
            <div class="font-headline-md text-headline-md text-on-surface">${data.count} video</div>
            <div class="text-label-sm text-on-surface-variant mt-1">Ort. izlenme: ${fmt(data.avg_views)}</div>
            <div class="text-label-sm text-on-surface-variant">Ort. begeni: ${fmt(data.avg_likes)}</div>
        </div>`;
    }).join('');

    // === Tags ===
    const tagEl = document.getElementById('yt-tags');
    tagEl.innerHTML = top_tags.length ?
        top_tags.map(t => `
        <div class="glass-card rounded-xl p-4 text-center">
            <div class="font-headline-sm text-headline-sm text-[#FF0000]">${t.tag}</div>
            <div class="text-label-sm text-on-surface-variant mt-1">${t.count} video</div>
            <div class="text-label-sm text-on-surface-variant">${fmt(t.total_views)} izlenme</div>
        </div>`).join('') :
        '<div class="col-span-5 glass-card rounded-xl p-8 text-center text-on-surface-variant">Etiket verisi bulunamadi</div>';

    // === Videos Table ===
    document.getElementById('yt-video-count-label').textContent = `${all_videos.length} video`;
    document.getElementById('yt-videos-table').innerHTML = all_videos.map(v => {
        const dur = v.duration ? `${Math.floor(v.duration / 3600)}:${String(Math.floor((v.duration % 3600) / 60)).padStart(2, '0')}:${String(v.duration % 60).padStart(2, '0')}` : '-';
        const eng = (v.like_count || 0) + (v.comment_count || 0);
        const engRate = v.view_count > 0 ? ((eng / v.view_count) * 100).toFixed(1) : 0;
        return `<tr class="hover:bg-surface-container-highest transition-colors cursor-pointer" onclick="window.open('https://youtube.com/watch?v=${v.id}','_blank')">
            <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                    <img src="${v.thumbnail}" class="w-16 h-10 rounded object-cover flex-shrink-0">
                    <p class="text-body-sm text-on-surface line-clamp-1">${v.title}</p>
                </div>
            </td>
            <td class="px-4 py-3 text-body-sm">${dur}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.view_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.like_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.comment_count)}</td>
            <td class="px-4 py-3 text-right text-label-sm text-on-surface-variant">${v.published_at ? new Date(v.published_at).toLocaleDateString('tr-TR') : '-'}</td>
        </tr>`;
    }).join('');
}

// ==================== RAKIP ANALIZI ====================
let competitorData = null;
let competitorCurrentPlatform = null;

function searchCompetitor() {
    const input = document.getElementById('competitor-search-input');
    const query = input ? input.value.trim() : '';
    if (!query) return;

    const statusEl = document.getElementById('competitor-status');
    statusEl.textContent = 'Aranıyor...';
    statusEl.className = 'text-label-sm font-label-sm text-on-surface-variant bg-surface-container px-md py-xs rounded-full border border-outline-variant/30';

    document.getElementById('competitor-empty').classList.add('hidden');
    document.getElementById('competitor-detail').classList.add('hidden');
    document.getElementById('competitor-results').classList.remove('hidden');
    document.getElementById('competitor-results-title').textContent = `"${query}" icin sonuclar`;
    document.getElementById('competitor-platform-cards').innerHTML = '<div class="col-span-5 flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';

    fetch('data/competitors.json')
    .then(r => r.json()).then(cache => {
        const q = query.toLowerCase();
        let platforms = {};
        for (const [tag, data] of Object.entries(cache)) {
            if (tag.includes(q)) {
                platforms = {...platforms, ...data.platforms};
            }
        }
        const result = { query, platforms };
        competitorData = result;
        statusEl.textContent = `${Object.keys(platforms).length} platform bulundu`;
        statusEl.className = 'text-label-sm font-label-sm text-primary bg-primary/10 px-md py-xs rounded-full border border-primary/20';
        renderCompetitorResults(result);
    }).catch(() => {
        statusEl.textContent = 'Hata';
        statusEl.className = 'text-label-sm font-label-sm text-error bg-error/10 px-md py-xs rounded-full border border-error/20';
    });
}

function renderCompetitorResults(data) {
    const { platforms } = data;
    const cards = [];

    const platformConfig = {
        twitter: { icon: 'chat_bubble', color: '#1DA1F2', label: 'Twitter', borderClass: 'platform-twitter' },
        tiktok: { icon: 'video_library', color: '#00F2EA', label: 'TikTok', borderClass: 'platform-tiktok' },
        youtube: { icon: 'play_circle', color: '#FF0000', label: 'YouTube', borderClass: 'platform-youtube' },
        instagram: { icon: 'camera_alt', color: '#E4405F', label: 'Instagram', borderClass: 'platform-instagram' },
        linkedin: { icon: 'corporate_fare', color: '#0A66C2', label: 'LinkedIn', borderClass: 'platform-linkedin' },
    };

    for (const [key, cfg] of Object.entries(platformConfig)) {
        const p = platforms[key];
        if (!p) continue;

        // Hata durumu
        if (p.error) {
            cards.push(`
                <div class="glass-card p-5 rounded-xl opacity-50 hover:bg-surface-bright/20 transition-all">
                    <div class="flex items-center gap-2 mb-3">
                        <span class="material-symbols-outlined text-[18px]" style="color:${cfg.color}">${cfg.icon}</span>
                        <span class="font-label-sm text-label-sm">${cfg.label.toUpperCase()}</span>
                    </div>
                    <div class="text-headline-sm font-headline-sm mb-1 text-on-surface-variant">${p.username || 'Hesap bulunamadi'}</div>
                    <div class="text-label-sm text-error">${p.error}</div>
                </div>
            `);
            continue;
        }

        let statText = '';
        let clickable = '';
        if (key === 'twitter' && p.username) {
            statText = `${fmt(p.followers)} takipci`;
            clickable = `onclick="openCompetitorDetail('twitter','${p.username}')" style="cursor:pointer"`;
        } else if (key === 'tiktok' && p.username) {
            statText = `${fmt(p.followers)} takipci`;
            clickable = `onclick="openCompetitorDetail('tiktok','${p.username}')" style="cursor:pointer"`;
        } else if (key === 'youtube' && p.channel_id) {
            statText = `${fmt(p.subscribers)} abone`;
            clickable = `onclick="openCompetitorDetail('youtube','${p.channel_id}')" style="cursor:pointer"`;
        } else if (key === 'instagram' && p.username) {
            statText = `${fmt(p.followers)} takipci`;
            clickable = `onclick="window.open('${p.profile_url}','_blank')" style="cursor:pointer"`;
        } else if (key === 'linkedin') {
            statText = 'Profil icin tiklayin';
            clickable = `onclick="window.open('${p.search_url}','_blank')" style="cursor:pointer"`;
        }

        cards.push(`
            <div class="glass-card p-5 rounded-xl ${cfg.borderClass} hover:bg-surface-bright/20 transition-all" ${clickable}>
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-[18px]" style="color:${cfg.color}">${cfg.icon}</span>
                    <span class="font-label-sm text-label-sm">${cfg.label.toUpperCase()}</span>
                </div>
                <div class="text-headline-sm font-headline-sm mb-1">${p.username || p.title || 'Bulunamadi'}</div>
                <div class="text-label-sm text-on-surface-variant">${statText}</div>
            </div>
        `);
    }

    if (cards.length === 0) {
        cards.push('<div class="col-span-5 glass-card rounded-xl p-8 text-center text-on-surface-variant">Bu isimle eslesen hesap bulunamadi</div>');
    }

    document.getElementById('competitor-platform-cards').innerHTML = cards.join('');
}

function openCompetitorDetail(platform, id) {
    competitorCurrentPlatform = platform;
    document.getElementById('competitor-results').classList.add('hidden');
    document.getElementById('competitor-empty').classList.add('hidden');
    document.getElementById('competitor-detail').classList.remove('hidden');
    document.getElementById('competitor-detail-title').textContent = `${platform.toUpperCase()} Detay Analiz`;
    document.getElementById('competitor-detail-badge').textContent = platform;
    const color = getPlatformColor(platform);
    document.getElementById('competitor-detail-badge').className = `text-label-sm font-label-sm px-md py-xs rounded-full border`;
    document.getElementById('competitor-detail-badge').style.borderColor = color + '50';
    document.getElementById('competitor-detail-badge').style.backgroundColor = color + '15';
    document.getElementById('competitor-detail-badge').style.color = color;

    document.getElementById('competitor-profile-cards').innerHTML = '<div class="col-span-12 flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';
    document.getElementById('competitor-analytics-cards').innerHTML = '';
    document.getElementById('competitor-table-header').innerHTML = '';
    document.getElementById('competitor-table-body').innerHTML = '<tr><td colspan="6" class="px-4 py-8 text-center"><div class="loading-spinner mx-auto"></div></td></tr>';

    // Statik surumde sadece onceden toplanmis veriler kullanilabilir
    const detailPromise = platform === 'twitter' ? fetch('data/twitter-profile.json').then(r => r.json()).then(p => ({profile: p, tweets: [], analytics: {}}))
        : platform === 'tiktok' ? fetch('data/tiktok-analytics.json').then(r => r.json())
        : platform === 'youtube' ? fetch('data/youtube-analytics.json').then(r => r.json()).then(d => ({channel: d.channel, videos: d.all_videos || [], analytics: d.summary || {}}))
        : Promise.reject('Desteklenmiyor');
    detailPromise.then(data => {
        }
        if (platform === 'twitter') renderCompetitorTwitter(data);
        else if (platform === 'tiktok') renderCompetitorTikTok(data);
        else if (platform === 'youtube') renderCompetitorYouTube(data);
    });
}

function closeCompetitorDetail() {
    document.getElementById('competitor-detail').classList.add('hidden');
    document.getElementById('competitor-results').classList.remove('hidden');
}

function getPlatformColor(p) {
    const m = { twitter: '#1DA1F2', tiktok: '#00F2EA', youtube: '#FF0000', instagram: '#E4405F', linkedin: '#0A66C2' };
    return m[p] || 'primary';
}

function renderCompetitorTwitter(data) {
    const { profile: p, analytics: a, best_tweets, tweets } = data;

    document.getElementById('competitor-profile-cards').innerHTML = `
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#1DA1F2]"></div>
            <div class="flex items-center gap-3 mb-4">
                <img src="${p.profile_image_url}" class="w-14 h-14 rounded-full border-2 border-[#1DA1F2]">
                <div><h3 class="font-body-sm font-semibold text-on-surface">${p.name}</h3><p class="font-label-sm text-on-surface-variant">@${p.username}</p></div>
            </div>
            <p class="font-body-sm text-on-surface-variant text-xs line-clamp-2">${p.description || ''}</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <span class="material-symbols-outlined text-tertiary text-lg mb-2">group</span>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Takipci</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(p.followers_count)}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Takip: ${fmt(p.following_count)} | Tweet: ${fmt(p.tweets_count)}</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <span class="material-symbols-outlined text-primary text-lg mb-2">bolt</span>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Etkilesim Orani</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">%${a.engagement_rate}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Gosterim: ${fmt(a.total_impressions)}</p>
        </div>`;

    document.getElementById('competitor-analytics-cards').innerHTML = `
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-[#1DA1F2] text-lg mb-2">visibility</span><h4 class="font-label-md text-on-surface-variant mb-1">Gosterim</h4><div class="font-headline-md text-on-surface">${fmt(a.total_impressions)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-[#FF0050] text-lg mb-2">favorite</span><h4 class="font-label-md text-on-surface-variant mb-1">Begeni</h4><div class="font-headline-md text-on-surface">${fmt(a.total_likes)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-[#00F2EA] text-lg mb-2">repeat</span><h4 class="font-label-md text-on-surface-variant mb-1">Retweet</h4><div class="font-headline-md text-on-surface">${fmt(a.total_retweets)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-tertiary text-lg mb-2">chat</span><h4 class="font-label-md text-on-surface-variant mb-1">Yanit</h4><div class="font-headline-md text-on-surface">${fmt(a.total_replies)}</div></div>`;

    document.getElementById('competitor-content-title').textContent = 'Son Tweetler';
    document.getElementById('competitor-content-count').textContent = `${tweets.length} tweet`;
    document.getElementById('competitor-table-header').innerHTML = `
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest">Icerik</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Gosterim</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Begeni</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">RT</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Etkilesim</th>`;
    document.getElementById('competitor-table-body').innerHTML = tweets.map(t => {
        const eng = (t.favorite_count || 0) + (t.retweet_count || 0) + (t.reply_count || 0);
        const engRate = parseInt(t.view_count) > 0 ? ((eng / parseInt(t.view_count)) * 100).toFixed(1) : 0;
        return `<tr class="hover:bg-surface-container-highest transition-colors">
            <td class="px-4 py-3 max-w-xs"><p class="text-body-sm text-on-surface line-clamp-1">${linkify(t.text.substring(0, 80))}</p><p class="text-label-sm text-on-surface-variant mt-1">${formatDate(t.created_at)}</p></td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(parseInt(t.view_count) || 0)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(t.favorite_count || 0)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(t.retweet_count || 0)}</td>
            <td class="px-4 py-3 text-right"><span class="text-label-sm ${engRate > 5 ? 'text-primary' : 'text-on-surface-variant'}">%${engRate}</span></td>
        </tr>`;
    }).join('');
}

function renderCompetitorTikTok(data) {
    const { profile: p, analytics: a, format_analysis, best_videos, videos } = data;

    document.getElementById('competitor-profile-cards').innerHTML = `
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
            <div class="flex items-center gap-3 mb-4">
                ${p.avatar ? `<img src="${p.avatar}" class="w-14 h-14 rounded-full border-2 border-[#00F2EA]">` : '<div class="w-14 h-14 rounded-full bg-[#00F2EA]/20 flex items-center justify-center"><span class="material-symbols-outlined text-[#00F2EA]">person</span></div>'}
                <div><h3 class="font-body-sm font-semibold text-on-surface">${p.nickname || p.username}</h3><p class="font-label-sm text-on-surface-variant">@${p.username}</p></div>
            </div>
            <p class="font-body-sm text-on-surface-variant text-xs line-clamp-2">${p.description || ''}</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <span class="material-symbols-outlined text-tertiary text-lg mb-2">group</span>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Takipci</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${fmt(p.followers)}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Begeni: ${fmt(p.hearts)} | Video: ${fmt(p.videos)}</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0050]"></div>
            <span class="material-symbols-outlined text-[#FF0050] text-lg mb-2">bolt</span>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Etkilesim Orani</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">%${a.engagement_rate}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Izlenme: ${fmt(a.total_views)}</p>
        </div>`;

    document.getElementById('competitor-analytics-cards').innerHTML = `
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-[#00F2EA] text-lg mb-2">visibility</span><h4 class="font-label-md text-on-surface-variant mb-1">Izlenme</h4><div class="font-headline-md text-on-surface">${fmt(a.total_views)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-[#FF0050] text-lg mb-2">favorite</span><h4 class="font-label-md text-on-surface-variant mb-1">Begeni</h4><div class="font-headline-md text-on-surface">${fmt(a.total_likes)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-primary text-lg mb-2">chat</span><h4 class="font-label-md text-on-surface-variant mb-1">Yorum</h4><div class="font-headline-md text-on-surface">${fmt(a.total_comments)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-tertiary text-lg mb-2">share</span><h4 class="font-label-md text-on-surface-variant mb-1">Paylasim</h4><div class="font-headline-md text-on-surface">${fmt(a.total_shares)}</div></div>`;

    document.getElementById('competitor-content-title').textContent = 'Son Videolar';
    document.getElementById('competitor-content-count').textContent = `${videos.length} video`;
    document.getElementById('competitor-table-header').innerHTML = `
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest">Video</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Izlenme</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Begeni</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Yorum</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Etkilesim</th>`;
    document.getElementById('competitor-table-body').innerHTML = videos.map(v => {
        const eng = (v.like_count || 0) + (v.comment_count || 0) + (v.share_count || 0);
        const engRate = v.play_count > 0 ? ((eng / v.play_count) * 100).toFixed(1) : 0;
        const dur = v.duration ? `${Math.floor(v.duration / 60)}:${(v.duration % 60).toString().padStart(2, '0')}` : '-';
        return `<tr class="hover:bg-surface-container-highest transition-colors">
            <td class="px-4 py-3 max-w-xs"><p class="text-body-sm text-on-surface line-clamp-1">${v.desc ? v.desc.substring(0, 60) : 'Aciklama yok'}</p><p class="text-label-sm text-on-surface-variant mt-1">${dur} | ${formatDate(v.created_at * 1000)}</p></td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.play_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.like_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.comment_count)}</td>
            <td class="px-4 py-3 text-right"><span class="text-label-sm ${engRate > 10 ? 'text-[#00F2EA]' : 'text-on-surface-variant'}">%${engRate}</span></td>
        </tr>`;
    }).join('');
}

function renderCompetitorYouTube(data) {
    const { channel: c, analytics: a, best_videos, videos } = data;

    document.getElementById('competitor-profile-cards').innerHTML = `
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0000]"></div>
            <div class="flex items-center gap-3 mb-4">
                <img src="${c.thumbnail}" class="w-14 h-14 rounded-full border-2 border-[#FF0000]">
                <div><h3 class="font-body-sm font-semibold text-on-surface">${c.title}</h3><p class="font-label-sm text-on-surface-variant">${c.country || 'Global'}</p></div>
            </div>
            <p class="font-body-sm text-on-surface-variant text-xs line-clamp-2">${c.description || ''}</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-tertiary"></div>
            <span class="material-symbols-outlined text-tertiary text-lg mb-2">group</span>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Abone</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">${c.subscribers_hidden ? 'Gizli' : fmt(c.subscribers)}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Video: ${fmt(c.total_videos)} | Izlenme: ${fmt(c.total_views)}</p>
        </div>
        <div class="col-span-12 md:col-span-4 glass-card p-xl rounded-xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
            <span class="material-symbols-outlined text-primary text-lg mb-2">bolt</span>
            <h3 class="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-1">Etkilesim Orani</h3>
            <span class="font-headline-lg text-headline-lg text-on-surface">%${a.engagement_rate}</span>
            <p class="text-label-sm text-on-surface-variant mt-1">Ort. izlenme: ${fmt(a.avg_views)}</p>
        </div>`;

    document.getElementById('competitor-analytics-cards').innerHTML = `
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-[#FF0000] text-lg mb-2">visibility</span><h4 class="font-label-md text-on-surface-variant mb-1">Izlenme</h4><div class="font-headline-md text-on-surface">${fmt(a.total_views)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-[#FF0050] text-lg mb-2">favorite</span><h4 class="font-label-md text-on-surface-variant mb-1">Begeni</h4><div class="font-headline-md text-on-surface">${fmt(a.total_likes)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-primary text-lg mb-2">chat</span><h4 class="font-label-md text-on-surface-variant mb-1">Yorum</h4><div class="font-headline-md text-on-surface">${fmt(a.total_comments)}</div></div>
        <div class="col-span-12 md:col-span-3 glass-card p-5 rounded-xl"><span class="material-symbols-outlined text-tertiary text-lg mb-2">bar_chart</span><h4 class="font-label-md text-on-surface-variant mb-1">Ort. Begeni</h4><div class="font-headline-md text-on-surface">${fmt(a.avg_likes)}</div></div>`;

    document.getElementById('competitor-content-title').textContent = 'Son Videolar';
    document.getElementById('competitor-content-count').textContent = `${videos.length} video`;
    document.getElementById('competitor-table-header').innerHTML = `
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest">Video</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest">Sure</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Izlenme</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Begeni</th>
        <th class="px-4 py-3 font-label-sm text-on-surface-variant uppercase tracking-widest text-right">Yorum</th>`;
    document.getElementById('competitor-table-body').innerHTML = videos.map(v => {
        const dur = v.duration ? `${Math.floor(v.duration / 3600)}:${String(Math.floor((v.duration % 3600) / 60)).padStart(2, '0')}:${String(v.duration % 60).padStart(2, '0')}` : '-';
        return `<tr class="hover:bg-surface-container-highest transition-colors cursor-pointer" onclick="window.open('https://youtube.com/watch?v=${v.id}','_blank')">
            <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                    <img src="${v.thumbnail}" class="w-16 h-10 rounded object-cover flex-shrink-0">
                    <p class="text-body-sm text-on-surface line-clamp-1">${v.title}</p>
                </div>
            </td>
            <td class="px-4 py-3 text-body-sm">${dur}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.view_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.like_count)}</td>
            <td class="px-4 py-3 text-right text-body-sm">${fmt(v.comment_count)}</td>
        </tr>`;
    }).join('');
}

// ==================== INFLUENCER BULUCU ====================
let influencerData = null;

function searchInfluencer() {
    const input = document.getElementById('influencer-search-input');
    const query = input ? input.value.trim() : '';
    if (!query) return;

    const statusEl = document.getElementById('influencer-status');
    statusEl.textContent = 'Aranıyor...';
    statusEl.className = 'text-label-sm font-label-sm text-on-surface-variant bg-surface-container px-md py-xs rounded-full border border-outline-variant/30';

    document.getElementById('influencer-empty').classList.add('hidden');
    document.getElementById('influencer-detail').classList.add('hidden');
    document.getElementById('influencer-results').classList.remove('hidden');
    document.getElementById('influencer-results-title').textContent = `"${query}" icin sonuclar`;
    document.getElementById('influencer-cards').innerHTML = '<div class="col-span-3 flex items-center justify-center py-8"><div class="loading-spinner"></div></div>';

    fetch('data/influencers.json')
    .then(r => r.json()).then(cache => {
        const q = query.toLowerCase();
        let influencers = [];
        for (const [tag, data] of Object.entries(cache)) {
            if (tag.includes(q) || q.includes(tag)) {
                influencers = influencers.concat(data.influencers || []);
            }
        }
        // deduplicate
        const seen = new Set();
        influencers = influencers.filter(x => { const k = x.username.toLowerCase(); if (seen.has(k)) return false; seen.add(k); return true; });
        const result = { query, influencers };
        influencerData = result;
        statusEl.textContent = `${influencers.length} influencer bulundu`;
        statusEl.className = 'text-label-sm font-label-sm text-primary bg-primary/10 px-md py-xs rounded-full border border-primary/20';
        renderInfluencerResults(result);
    }).catch(() => {
        statusEl.textContent = 'Hata';
        statusEl.className = 'text-label-sm font-label-sm text-error bg-error/10 px-md py-xs rounded-full border border-error/20';
    });
}

function searchInfluencerTag(tag) {
    const input = document.getElementById('influencer-search-input');
    if (input) input.value = tag;
    searchInfluencer();
}

function renderInfluencerResults(data) {
    const { influencers } = data;
    const container = document.getElementById('influencer-cards');

    if (!influencers || influencers.length === 0) {
        container.innerHTML = '<div class="col-span-3 glass-card rounded-xl p-8 text-center text-on-surface-variant">Bu konuda influencer bulunamadi</div>';
        return;
    }

    container.innerHTML = influencers.map((inf, idx) => {
        const platforms = inf.platforms || {};
        const platformBadges = [];

        if (platforms.twitter) {
            platformBadges.push(`<span class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-[#1DA1F2]/15 text-[#1DA1F2] border border-[#1DA1F2]/20"><span class="material-symbols-outlined text-[12px]">chat_bubble</span>Twitter</span>`);
        }
        if (platforms.youtube) {
            platformBadges.push(`<span class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-[#FF0000]/15 text-[#FF0000] border border-[#FF0000]/20"><span class="material-symbols-outlined text-[12px]">play_circle</span>YouTube</span>`);
        }
        if (platforms.tiktok) {
            platformBadges.push(`<span class="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-[#00F2EA]/15 text-[#00F2EA] border border-[#00F2EA]/20"><span class="material-symbols-outlined text-[12px]">video_library</span>TikTok</span>`);
        }

        // En buyuk takipci sayisini goster
        let mainStat = '';
        if (platforms.twitter && platforms.twitter.followers) {
            mainStat = `Twitter: ${fmt(platforms.twitter.followers)} takipci`;
        } else if (platforms.youtube && platforms.youtube.subscribers) {
            mainStat = `YouTube: ${fmt(platforms.youtube.subscribers)} abone`;
        } else if (platforms.tiktok) {
            mainStat = `TikTok: ${fmt(platforms.tiktok.followers || platforms.tiktok.total_views)} takipci`;
        }

        return `
            <div class="glass-card p-5 rounded-xl hover:bg-surface-bright/20 transition-all cursor-pointer" onclick="openInfluencerDetail(${idx})">
                <div class="flex items-center gap-3 mb-3">
                    <div class="w-12 h-12 rounded-full bg-primary-container flex items-center justify-center flex-shrink-0">
                        <span class="material-symbols-outlined text-on-primary-container">person</span>
                    </div>
                    <div class="min-w-0 flex-1">
                        <h3 class="font-body-sm font-semibold text-on-surface truncate">${inf.name || inf.username}</h3>
                        <p class="font-label-sm text-on-surface-variant truncate">@${inf.username}</p>
                    </div>
                </div>
                <p class="text-label-sm text-on-surface-variant mb-3">${mainStat}</p>
                <div class="flex flex-wrap gap-1">${platformBadges.join('')}</div>
            </div>
        `;
    }).join('');
}

function openInfluencerDetail(idx) {
    const inf = influencerData.influencers[idx];
    if (!inf) return;

    document.getElementById('influencer-results').classList.add('hidden');
    document.getElementById('influencer-empty').classList.add('hidden');
    document.getElementById('influencer-detail').classList.remove('hidden');
    document.getElementById('influencer-detail-title').textContent = inf.name || inf.username;

    const content = document.getElementById('influencer-detail-content');
    const platforms = inf.platforms || {};
    let html = '<div class="space-y-6">';

    // Platform bazli kartlar
    html += '<div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">';

    if (platforms.twitter) {
        const tw = platforms.twitter;
        html += `
            <div class="glass-card p-5 rounded-xl platform-twitter relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#1DA1F2]"></div>
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-[18px] text-[#1DA1F2]">chat_bubble</span>
                    <span class="font-label-sm text-label-sm">TWITTER</span>
                </div>
                <h3 class="font-body-sm font-semibold text-on-surface mb-1">@${tw.username}</h3>
                <p class="text-label-sm text-on-surface-variant mb-3">${fmt(tw.followers)} takipci</p>
                ${tw.best_tweet ? `<p class="text-xs text-on-surface-variant line-clamp-2 mb-3">"${tw.best_tweet}"</p>` : ''}
                <div class="flex gap-4 text-xs text-on-surface-variant">
                    <span>Gosterim: ${fmt(tw.total_views)}</span>
                    <span>Begeni: ${fmt(tw.total_likes)}</span>
                </div>
                <button onclick="window.open('https://x.com/${tw.username}','_blank')" class="mt-3 w-full py-2 bg-[#1DA1F2]/10 text-[#1DA1F2] rounded-lg text-label-sm hover:bg-[#1DA1F2]/20 transition-colors">Profili Ac</button>
            </div>`;
    }

    if (platforms.youtube) {
        const yt = platforms.youtube;
        html += `
            <div class="glass-card p-5 rounded-xl platform-youtube relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#FF0000]"></div>
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-[18px] text-[#FF0000]">play_circle</span>
                    <span class="font-label-sm text-label-sm">YOUTUBE</span>
                </div>
                <div class="flex items-center gap-3 mb-2">
                    ${yt.thumbnail ? `<img src="${yt.thumbnail}" class="w-10 h-10 rounded-full">` : ''}
                    <div>
                        <h3 class="font-body-sm font-semibold text-on-surface">${yt.title}</h3>
                        <p class="text-label-sm text-on-surface-variant">${fmt(yt.subscribers)} abone</p>
                    </div>
                </div>
                <button onclick="window.open('https://youtube.com/channel/${yt.channel_id}','_blank')" class="w-full py-2 bg-[#FF0000]/10 text-[#FF0000] rounded-lg text-label-sm hover:bg-[#FF0000]/20 transition-colors">Kanali Ac</button>
            </div>`;
    }

    if (platforms.tiktok) {
        const tt = platforms.tiktok;
        html += `
            <div class="glass-card p-5 rounded-xl platform-tiktok relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-[#00F2EA]"></div>
                <div class="flex items-center gap-2 mb-3">
                    <span class="material-symbols-outlined text-[18px] text-[#00F2EA]">video_library</span>
                    <span class="font-label-sm text-label-sm">TIKTOK</span>
                </div>
                <h3 class="font-body-sm font-semibold text-on-surface mb-1">@${tt.username}</h3>
                <p class="text-label-sm text-on-surface-variant mb-3">${fmt(tt.followers || tt.total_views)} takipci</p>
                ${tt.best_video ? `<p class="text-xs text-on-surface-variant line-clamp-2 mb-3">"${tt.best_video}"</p>` : ''}
                <div class="flex gap-4 text-xs text-on-surface-variant">
                    <span>Begeni: ${fmt(tt.total_likes)}</span>
                </div>
                <button onclick="window.open('https://tiktok.com/@${tt.username}','_blank')" class="mt-3 w-full py-2 bg-[#00F2EA]/10 text-[#00F2EA] rounded-lg text-label-sm hover:bg-[#00F2EA]/20 transition-colors">Profili Ac</button>
            </div>`;
    }

    if (!platforms.twitter && !platforms.youtube && !platforms.tiktok) {
        html += '<div class="col-span-3 text-center text-on-surface-variant py-8">Bu influencer icin platform bilgisi bulunamadi</div>';
    }

    html += '</div></div>';
    content.innerHTML = html;
}

function closeInfluencerDetail() {
    document.getElementById('influencer-detail').classList.add('hidden');
    document.getElementById('influencer-results').classList.remove('hidden');
}
