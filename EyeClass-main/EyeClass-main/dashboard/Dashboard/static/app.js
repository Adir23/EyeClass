lucide.createIcons();
let isLessonActive = false;
let isSimulatingHistory = false;
let chartInstance = null;
let dashboardPollTimer = null;

let currentTrendData = [];
let zenStartTime = null;
let zenEngagementSum = 0;
let zenUpdatesCount = 0;

let weeklyCharts = [];
let currentGraphIndex = 0;
const graphTitles = ["Monthly Engagement", "Subject Comparison", "Skill Progress"];

let originalNavTo = function (viewId)
{
    document.querySelectorAll('.view-section').forEach(el =>
    {
        el.classList.remove('active');
        if (el.id !== viewId)
        {
            el.style.display = 'none';
        }
    });

    const target = document.getElementById(viewId);
    if (target)
    {
        target.style.display = 'flex';
        setTimeout(() =>
        {
            target.classList.add('active');
        }, 10);
    }

    const homeHeader = document.getElementById('homeHeader');
    const dashHeader = document.getElementById('dashHeader');
    const chatHeader = document.getElementById('chatHeader');

    if (homeHeader) { homeHeader.style.display = 'none'; }
    if (dashHeader) { dashHeader.style.display = 'none'; }
    if (chatHeader) { chatHeader.style.display = 'none'; }

    if (viewId === 'view-home' && homeHeader) { homeHeader.style.display = 'flex'; }
    if (viewId === 'view-dashboard' && dashHeader) { dashHeader.style.display = 'flex'; }
    if (viewId === 'view-chat' && chatHeader) { chatHeader.style.display = 'flex'; }

    document.querySelectorAll('.nav-item').forEach(btn =>
    {
        btn.classList.remove('active');
    });

    if (viewId === 'view-home') { document.querySelector('.nav-item:first-child')?.classList.add('active'); }
    if (viewId === 'view-chat') { document.querySelector('.nav-item:last-child')?.classList.add('active'); }
};

function navTo(viewId)
{
    if (viewId === 'view-home' || viewId === 'view-chat')
    {
        isSimulatingHistory = false;
        document.body.classList.remove('history-mode');
        if (dashboardPollTimer && !isLessonActive)
        {
            clearTimeout(dashboardPollTimer);
        }
        updateUIState();
    }

    originalNavTo(viewId);
    if (viewId === 'view-monthly')
    {
        setTimeout(() =>
        {
            initWeeklyGauge(92);
        }, 100);
    }
}

function handleMainAction()
{
    if (isLessonActive)
    {
        navTo('view-dashboard');
    }
    else
    {
        openStartSheet();
    }
}

function updateUIState()
{
    const mainBtn = document.getElementById('mainActionBtn');
    const statusCard = document.getElementById('statusCard');
    const recentList = document.getElementById('recentSessionList');
    const seeAllBtn = document.getElementById('seeAllBtn');
    const liveTools = document.getElementById('dashboardLiveTools');

    if (!mainBtn || !statusCard)
    {
        return;
    }

    if (isLessonActive)
    {
        mainBtn.classList.add('active-session');
        mainBtn.innerHTML = '<i data-lucide="activity"></i>';
        statusCard.style.background = 'linear-gradient(135deg, #FCA5A5 0%, #E11D48 100%)';
        statusCard.innerHTML = `<div><h2>Lesson in Progress</h2><p>Tracking engagement live...</p></div><button class="hero-btn" onclick="navTo('view-dashboard')"><i data-lucide="bar-chart-2" size="16"></i> <span>View Dashboard</span></button>`;

        if (recentList && seeAllBtn)
        {
            recentList.classList.add('disabled-history');
            seeAllBtn.style.opacity = '0.4';
            seeAllBtn.style.pointerEvents = 'none';
        }
        if (liveTools) liveTools.style.display = 'flex';
    }
    else
    {
        mainBtn.classList.remove('active-session');
        mainBtn.innerHTML = '<i data-lucide="plus" size="28"></i>';
        statusCard.style.background = 'linear-gradient(135deg, #C4B5FD 0%, #8B5CF6 100%)';
        statusCard.innerHTML = `<div><h2>Ready to Teach?</h2><p>Start a new session now.</p></div><button class="hero-btn" onclick="openStartSheet()"><i data-lucide="play" size="16"></i> <span>Start Lesson</span></button>`;

        if (recentList && seeAllBtn)
        {
            recentList.classList.remove('disabled-history');
            seeAllBtn.style.opacity = '1';
            seeAllBtn.style.pointerEvents = 'auto';
        }
        if (liveTools) liveTools.style.display = 'none';
    }
    lucide.createIcons();
}

async function fetchHistory()
{
    try
    {
        const res = await fetch('/api/get_history_list');
        const list = await res.json();
        renderHistoryList('recentSessionList', list.slice(0, 3));
        renderHistoryList('fullHistoryList', list);

        if (list.length > 0)
        {
            let sum = 0;
            list.forEach(item =>
            {
                sum += item.score;
            });
            let avg = Math.round(sum / list.length);

            const engVal = document.getElementById('overallEngagementVal');
            if (engVal)
            {
                engVal.innerText = avg + '%';
            }

            const hoursVal = document.getElementById('totalHoursVal');
            if (hoursVal)
            {
                hoursVal.innerText = Math.round(list.length * 0.75) + 'h';
            }
        }

        if (list.length >= 3)
        {
            if (list[0].score >= 80 && list[1].score >= 80 && list[2].score >= 80)
            {
                const streakEl = document.getElementById('streakBadge');
                if (streakEl)
                {
                    streakEl.style.display = 'flex';
                }
            }
            else
            {
                const streakEl = document.getElementById('streakBadge');
                if (streakEl)
                {
                    streakEl.style.display = 'none';
                }
            }
        }
    }
    catch (e)
    {
        console.error("History error", e);
    }
}

function renderHistoryList(containerId, items)
{
    const container = document.getElementById(containerId);
    if (!container)
    {
        return;
    }
    container.innerHTML = '';

    if (items.length === 0)
    {
        container.innerHTML = '<p style="text-align:center;color:#ccc;">No history yet</p>';
        return;
    }

    items.forEach(item =>
    {
        const div = document.createElement('div');
        div.className = 'session-item';
        div.onclick = () =>
        {
            loadSimulation(item.id, item.subject);
        };

        const iconHtml = item.mode === 'single'
            ? '<i data-lucide="user" size="20"></i>'
            : '<i data-lucide="users" size="20"></i>';

        div.innerHTML = `
            <div style="display:flex; align-items:center;">
                <div class="session-icon">${iconHtml}</div>
                <div>
                    <h4 style="margin:0; font-size:15px; color:var(--text-main);">${item.subject}</h4>
                    <p style="margin:2px 0 0; font-size:12px; color:var(--text-secondary);">${item.date}</p>
                </div>
            </div>
            <div style="text-align:right;">
                <span style="color:${item.score >= 80 ? 'var(--status-green)' : 'var(--status-yellow)'}; font-weight:800; font-size:15px;">${item.score}%</span>
                <p style="margin:0; font-size:11px; color:#999;">${item.mode === 'single' ? 'Single' : 'Group'}</p>
            </div>
        `;
        container.appendChild(div);
    });
    lucide.createIcons();
}

function openHistoryModal()
{
    document.getElementById('historyModal').classList.add('active');
}

function closeHistoryModal()
{
    document.getElementById('historyModal').classList.remove('active');
}

async function loadDashboardData(isStatic = false, specificFileId = null)
{
    const aiBox = document.getElementById('aiSuggestionsList');

    if (dashboardPollTimer)
    {
        clearTimeout(dashboardPollTimer);
    }

    try
    {
        let url = isStatic ? '/api/get_dashboard_data?history=true' : '/api/get_dashboard_data';
        if (specificFileId)
        {
            url += `&file_id=${specificFileId}`;
        }

        const res = await fetch(url);
        const json = await res.json();
        const data = json.data;

        window.latestBlocksData = data.blocks;
        window.currentTrendData = data.attention_time;

        if (isStatic)
        {
            window.replayFrames = [];
            let finalBlocks = data.blocks;
            let trend = data.attention_time;

            for(let i = 0; i < 6; i++)
            {
                let frameAvg = trend[i];
                let frameBlocks = finalBlocks.map(b =>
                {
                    let diff = frameAvg - data.avg_attention;
                    let val = b.attention + diff + (Math.random() * 8 - 4);
                    val = Math.max(10, Math.min(100, val));
                    return { id: b.id, attention: Math.round(val) };
                });

                if (i === 5)
                {
                    frameBlocks = finalBlocks;
                }
                window.replayFrames.push(frameBlocks);
            }

            document.getElementById('replayContainer').style.display = 'block';
            document.getElementById('replaySlider').value = 5;
            document.getElementById('replayTime').innerText = 'End';
        }
        else
        {
            document.getElementById('replayContainer').style.display = 'none';
        }

        renderHeatmap(data.blocks);
        renderChart(data.attention_time);

        renderAISuggestions(data.suggestions.slice(0, 3));

        if (document.body.classList.contains('zen-mode-active'))
        {
            updateZenVibe();
        }

        if (isLessonActive && !isStatic)
        {
            dashboardPollTimer = setTimeout(loadDashboardData, 3000);
        }
    }
    catch (e)
    {
        console.error("Dashboard load error:", e);
    }
}

function handleReplaySlide(val)
{
    let index = parseInt(val);
    if (!window.replayFrames || !window.replayFrames[index])
    {
        return;
    }

    let blocks = window.replayFrames[index];
    renderHeatmap(blocks);

    let partialTrend = window.currentTrendData.map((v, i) => i <= index ? v : null);
    renderChart(partialTrend);

    let timeLabels = ['Start', '5m', '10m', '15m', '20m', 'End'];
    document.getElementById('replayTime').innerText = timeLabels[index];
}

function renderHeatmap(blocks)
{
    const grid = document.getElementById('classroomGrid');
    if (!grid)
    {
        return;
    }
    grid.innerHTML = '';

    if (blocks.length === 1)
    {
        grid.className = 'heatmap-grid single-mode';

        const block = blocks[0];
        const div = document.createElement('div');

        let type = '';
        if (block.attention > 75)
        {
            type = 'high';
        }
        else if (block.attention > 45)
        {
            type = 'med';
        }
        else if (block.attention >= 40)
        {
            type = 'low';
        }
        else
        {
            type = 'critical';
        }

        div.className = `heat-circle single ${type}`;
        div.setAttribute('data-val', block.attention);
        grid.appendChild(div);
    }
    else
    {
        grid.className = 'heatmap-grid';
        blocks.forEach(block =>
        {
            const div = document.createElement('div');
            let type = '';
            if (block.attention > 75)
            {
                type = 'high';
            }
            else if (block.attention > 45)
            {
                type = 'med';
            }
            else if (block.attention >= 40)
            {
                type = 'low';
            }
            else
            {
                type = 'critical';
            }
            div.className = `heat-circle ${type}`;
            div.setAttribute('data-val', block.attention);
            grid.appendChild(div);
        });
    }
}

function renderAISuggestions(suggestions)
{
    const list = document.getElementById('aiSuggestionsList');
    if (!list)
    {
        return;
    }
    list.innerHTML = '';

    suggestions.forEach(text =>
    {
        const item = document.createElement('div');
        // הקצאת מחלקה ייעודית שה-CSS יודע לכווץ במצב היסטוריה ולהגדיל בלייב
        item.className = 'ai-insight-item';
        item.innerHTML = `<i data-lucide="sparkles" size="18" style="min-width:18px; color:#7C3AED; display:flex;"></i> <span style="line-height:1.25;">${text}</span>`;
        list.appendChild(item);
    });
    lucide.createIcons();
}

function renderChart(dataPoints)
{
    const ctx = document.getElementById('lineChart');
    if (!ctx)
    {
        return;
    }

    if (chartInstance)
    {
        chartInstance.data.datasets[0].data = dataPoints;
        chartInstance.update();
        return;
    }
    const context = ctx.getContext('2d');
    let gradient = context.createLinearGradient(0, 0, 0, 150);
    // גרדיאנט חזק ויפה יותר
    gradient.addColorStop(0, 'rgba(124, 58, 237, 0.45)');
    gradient.addColorStop(1, 'rgba(124, 58, 237, 0.0)');

    chartInstance = new Chart(context, {
        type: 'line',
        data: {
            labels: ['Start', '5m', '10m', '15m', '20m', 'Now'],
            datasets: [{
                data: dataPoints,
                borderColor: '#7C3AED',
                borderWidth: 2,
                backgroundColor: gradient,
                fill: true,
                pointRadius: 4,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#7C3AED',
                pointBorderWidth: 2,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { left: -10, bottom: 0, top: 10, right: 10 } },
            plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
            scales: { x: { display: false }, y: { display: false, min: 0, max: 100 } },
            animation: { duration: 1000 }
        }
    });
}

function openStartSheet()
{
    document.getElementById('startModal').classList.add('active');
}

function closeStartSheet()
{
    document.getElementById('startModal').classList.remove('active');
}

function openEndModal()
{
    document.getElementById('endModal').classList.add('active');
}

function closeEndModal()
{
    document.getElementById('endModal').classList.remove('active');
}

function handleOverlayClick(e)
{
    if (e.target.id === 'startModal')
    {
        closeStartSheet();
    }
    if (e.target.id === 'historyModal')
    {
        closeHistoryModal();
    }
    if (e.target.id === 'endModal')
    {
        closeEndModal();
    }
}

function loadSimulation(fileId, subjectName)
{
    if (isLessonActive)
    {
        return;
    }
    isSimulatingHistory = true;
    document.body.classList.add('history-mode');
    document.getElementById('liveSubjectTitle').innerText = subjectName;
    document.getElementById('liveIndicator').style.display = 'none';
    document.getElementById('powerBtn').style.display = 'none';
    const liveTools = document.getElementById('dashboardLiveTools');
    if (liveTools) liveTools.style.display = 'none';
    closeHistoryModal();
    navTo('view-dashboard');
    loadDashboardData(true, fileId);
}

async function handleStart(e)
{
    e.preventDefault();
    const subject = document.getElementById('inpSubject').value;
    const topic = document.getElementById('inpTopic').value;
    const isSingle = document.getElementById('inpSingleMode').checked;

    try
    {
        await fetch('/api/start_lesson', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject, topic, mode: isSingle ? 'single' : 'group' })
        });
        isLessonActive = true;
        isSimulatingHistory = false;
        document.body.classList.remove('history-mode');
        document.getElementById('liveSubjectTitle').innerText = subject;
        document.getElementById('liveIndicator').style.display = 'flex';
        document.getElementById('powerBtn').style.display = 'flex';
        closeStartSheet();
        updateUIState();
        navTo('view-dashboard');
        loadDashboardData();
    }
    catch (err)
    {
        console.error("Start error", err);
    }
}

async function confirmEndSession()
{
    closeEndModal();
    await fetch('/api/end_lesson', { method: 'POST' });
    isLessonActive = false;
    isSimulatingHistory = false;
    document.body.classList.remove('history-mode');

    if (dashboardPollTimer)
    {
        clearTimeout(dashboardPollTimer);
    }

    updateUIState();
    fetchHistory();
    navTo('view-home');
}

function autoResize(textarea)
{
    textarea.style.height = '20px';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function handleEnter(e)
{
    if (e.key === 'Enter' && !e.shiftKey)
    {
        e.preventDefault();
        sendMessage();
    }
}

async function sendMessage()
{
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text)
    {
        return;
    }

    addMessageToUI(text, 'user');
    input.value = '';
    input.style.height = '20px';

    const loadingId = 'msg-loading-' + Date.now();
    addMessageToUI('<span style="letter-spacing: 2px;">...</span>', 'ai', loadingId);

    try
    {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        document.getElementById(loadingId)?.remove();
        addMessageToUI(data.reply, 'ai');
    }
    catch (e)
    {
        document.getElementById(loadingId)?.remove();
        addMessageToUI("שגיאת התחברות. נסה שוב.", 'ai');
    }
}

function addMessageToUI(text, sender, id = null)
{
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    if (id)
    {
        div.id = id;
    }

    div.innerHTML = sender === 'ai'
        ? `<div class="avatar-small"><i data-lucide="bot" size="16"></i></div><div class="bubble" dir="rtl" style="text-align: right;">${text}</div>`
        : `<div class="bubble" dir="rtl" style="text-align: right;">${text}</div>`;

    container.appendChild(div);
    lucide.createIcons();
    container.scrollTop = container.scrollHeight;
}

function activateMagicWand()
{
    if (!window.latestBlocksData || window.latestBlocksData.length === 0)
    {
        return;
    }

    let lowestBlock = window.latestBlocksData[0];

    window.latestBlocksData.forEach(block =>
    {
        if (block.attention < lowestBlock.attention)
        {
            lowestBlock = block;
        }
    });

    let zoneText = "התלמיד";
    if (window.latestBlocksData.length === 6)
    {
        const id = lowestBlock.id;
        const rowText = id < 3 ? "השורה האחורית" : "השורה הקדמית";
        const colText = (id === 0 || id === 3) ? "משמאל" : (id === 1 || id === 4) ? "באמצע" : "מימין";

        zoneText = `${rowText} ${colText}`;
    }

    const toast = document.getElementById('magicToast');
    if (toast)
    {
        toast.innerHTML = `<i data-lucide="wand-2" size="18"></i> כדאי לשאול עכשיו את ${zoneText} (${lowestBlock.attention}%)`;
        lucide.createIcons();
        toast.classList.add('show');
        setTimeout(() =>
        {
            toast.classList.remove('show');
        }, 3500);
    }
}

function toggleZenMode()
{
    const body = document.body;

    if (body.classList.contains('zen-mode-active'))
    {
        body.classList.remove('zen-mode-active');
        body.classList.remove('critical-edge');
        document.body.style.setProperty('--zen-glow-color', 'transparent');
        showZenSummary();
    }
    else
    {
        body.classList.add('zen-mode-active');
        zenStartTime = new Date();
        zenEngagementSum = 0;
        zenUpdatesCount = 0;
        updateZenVibe();
    }
}

function updateZenVibe()
{
    if (!window.latestBlocksData || window.latestBlocksData.length === 0) return;

    let totalAttention = 0;
    let hasCritical = false;

    window.latestBlocksData.forEach(block => {
        totalAttention += block.attention;
        if (block.attention < 30) hasCritical = true;
    });

    const average = totalAttention / window.latestBlocksData.length;

    zenEngagementSum += average;
    zenUpdatesCount++;

    let glowColor = 'transparent';
    if (average >= 75)
    {
        glowColor = 'rgba(5, 150, 105, 0.5)';
    }
    else if (average >= 45)
    {
        glowColor = 'rgba(217, 119, 6, 0.4)';
    }
    else
    {
        glowColor = 'rgba(185, 28, 28, 0.6)';
    }

    document.body.style.setProperty('--zen-glow-color', glowColor);

    if (hasCritical)
    {
        document.body.classList.add('critical-edge');
    }
    else
    {
        document.body.classList.remove('critical-edge');
    }
}

function showZenSummary()
{
    if (!zenStartTime || zenUpdatesCount === 0) return;

    const now = new Date();
    const durationSeconds = Math.round((now - zenStartTime) / 1000);
    const averageEngagement = Math.round(zenEngagementSum / zenUpdatesCount);

    let timeStr = durationSeconds + " שניות";
    if (durationSeconds >= 60)
    {
        timeStr = Math.floor(durationSeconds / 60) + " דקות";
    }

    const toast = document.getElementById('magicToast');
    if (toast)
    {
        toast.innerHTML = `🧘 סיכום זן: היינו פה ${timeStr} עם ממוצע קשב של ${averageEngagement}%`;
        toast.classList.add('show');
        setTimeout(() =>
        {
            toast.classList.remove('show');
        }, 4000);
    }

    zenStartTime = null;
}

function initWeeklyGauge(targetScore = 0)
{
    const scoreEl = document.getElementById('omegaScoreVal');
    const fill = document.getElementById('weeklyProgress');
    if (!scoreEl || !fill)
    {
        return;
    }

    let score = 0;
    const maxOffset = 502;
    const targetOffset = maxOffset - ((targetScore / 100) * maxOffset);

    if (targetScore === 0)
    {
        scoreEl.innerText = '0%';
        return;
    }

    const interval = setInterval(() =>
    {
        score++;
        scoreEl.innerText = score + '%';
        if (score >= targetScore)
        {
            clearInterval(interval);
        }
    }, 12);

    setTimeout(() =>
    {
        fill.style.strokeDashoffset = targetOffset;
    }, 100);
}

function switchWeeklyTab(tabId, btn)
{
    document.querySelectorAll('.tab-btn').forEach(b =>
    {
        b.classList.remove('active');
    });
    btn.classList.add('active');

    document.querySelectorAll('.tab-pane').forEach(p =>
    {
        p.style.display = 'none';
    });

    const target = document.getElementById(tabId);
    if (target)
    {
        target.style.display = tabId === 'tab-graphs' ? 'flex' : 'block';

        if (tabId === 'tab-insights')
        {
            loadMonthlyInsights();
        }
        if (tabId === 'tab-graphs')
        {
            setTimeout(() =>
            {
                initWeeklyGraphs();
                weeklyCharts.forEach(c =>
                {
                    if (c)
                    {
                        c.update();
                        c.resize();
                    }
                });
            }, 50);
        }
    }
    lucide.createIcons();
}

function initWeeklyGraphs()
{
    if (weeklyCharts.length > 0)
    {
        return;
    }

    const ctx1 = document.getElementById('chart1')?.getContext('2d');
    const ctx2 = document.getElementById('chart2')?.getContext('2d');
    const ctx3 = document.getElementById('chart3')?.getContext('2d');

    if (!ctx1 || !ctx2 || !ctx3)
    {
        return;
    }

    weeklyCharts[0] = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [
                { label: 'This Month', data: [82, 85, 88, 92], borderColor: '#7C3AED', backgroundColor: 'rgba(124, 58, 237, 0.1)', borderWidth: 3, tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: 'white' },
                { label: 'Last Month', data: [75, 78, 76, 80], borderColor: '#CBD5E1', borderWidth: 2, borderDash: [5, 5], tension: 0.4, fill: false, pointRadius: 0 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { bottom: 30 } },
            plugins: { legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 10 } } },
            scales: {
                x: { grid: { display: false }, ticks: { padding: 5 } },
                y: { display: false, min: 60 }
            }
        }
    });

    weeklyCharts[1] = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ['Math', 'Phys', 'Hist', 'Eng'],
            datasets: [
                { label: 'Avg', data: [92, 85, 76, 88], backgroundColor: '#7C3AED', borderRadius: 4, barPercentage: 0.6 },
                { label: 'Prev', data: [88, 80, 78, 85], backgroundColor: '#E2E8F0', borderRadius: 4, barPercentage: 0.6 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { bottom: 30 } },
            plugins: { legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 10 } } },
            scales: {
                x: { grid: { display: false }, ticks: { padding: 5 } },
                y: { display: false, min: 0 }
            }
        }
    });

    weeklyCharts[2] = new Chart(ctx3, {
        type: 'radar',
        data: {
            labels: ['Pacing', 'Clarity', 'Interact', 'Energy', 'Visuals'],
            datasets: [
                { label: 'This Month', data: [90, 85, 95, 80, 88], borderColor: '#7C3AED', backgroundColor: 'rgba(124, 58, 237, 0.2)', borderWidth: 2, pointRadius: 3, pointBackgroundColor: 'white' },
                { label: 'Last Month', data: [82, 78, 88, 75, 80], borderColor: '#CBD5E1', backgroundColor: 'rgba(203, 213, 225, 0.2)', borderWidth: 2, borderDash: [5, 5], pointRadius: 0 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { bottom: 15, top: 10 } },
            plugins: { legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 10 } } },
            scales: { r: { ticks: { display: false, backdropColor: 'transparent' }, grid: { color: '#F1F5F9' }, pointLabels: { font: { size: 11 } } } }
        }
    });
}

function nextGraph()
{
    currentGraphIndex = (currentGraphIndex + 1) % 3;
    updateGraphVisibility();
}

function prevGraph()
{
    currentGraphIndex = (currentGraphIndex - 1 + 3) % 3;
    updateGraphVisibility();
}

function updateGraphVisibility()
{
    document.querySelectorAll('.chart-slide').forEach((el, idx) =>
    {
        if (idx === currentGraphIndex)
        {
            el.style.opacity = '1';
            el.style.pointerEvents = 'auto';
            el.style.zIndex = '5';
        }
        else
        {
            el.style.opacity = '0';
            el.style.pointerEvents = 'none';
            el.style.zIndex = '1';
        }
    });

    document.querySelectorAll('.carousel-dots .dot').forEach((d, i) =>
    {
        if (i === currentGraphIndex)
        {
            d.classList.add('active');
        }
        else
        {
            d.classList.remove('active');
        }
    });

    document.getElementById('carouselTitle').innerText = graphTitles[currentGraphIndex];
}

async function loadMonthlyInsights()
{
    const container = document.getElementById('monthly-ai-content');
    if (!container)
    {
        return;
    }
    try
    {
        const res = await fetch('/api/monthly_insights');
        const data = await res.json();
        container.innerHTML = `<p style="font-size:14px; line-height:1.6; color:#2E1065;">${data.text}</p>`;
    }
    catch (e)
    {
        container.innerHTML = '<p>Unavailable.</p>';
    }
}

fetchHistory();

if (window.initialSessionActive)
{
    isLessonActive = true;
    document.getElementById('liveIndicator').style.display = 'flex';
    document.getElementById('powerBtn').style.display = 'flex';
    updateUIState();
    loadDashboardData();
}
else
{
    updateUIState();
}