lucide.createIcons();
let isLessonActive = false;
let chartInstance = null;

// Weekly Graph Carousel Logic
let weeklyCharts = [];
let currentGraphIndex = 0;
const graphTitles = ["Engagement", "Subjects", "Skills Analysis"];

// --- Navigation Logic ---
let originalNavTo = function(viewId) {
    document.querySelectorAll('.view-section').forEach(el => {
        el.classList.remove('active');
        if(el.id !== viewId) el.style.display = 'none'; // Ensure hidden
    });

    const target = document.getElementById(viewId);
    if (target) {
        target.style.display = (viewId === 'view-weekly') ? 'flex' : 'block';
        // Small delay to allow display change to register before opacity anim
        setTimeout(() => target.classList.add('active'), 10);
    }

    const homeHeader = document.getElementById('homeHeader');
    const dashHeader = document.getElementById('dashHeader');
    const chatHeader = document.getElementById('chatHeader');

    if (homeHeader) homeHeader.style.display = 'none';
    if (dashHeader) dashHeader.style.display = 'none';
    if (chatHeader) chatHeader.style.display = 'none';

    if (viewId === 'view-home' && homeHeader) homeHeader.style.display = 'flex';
    if (viewId === 'view-dashboard' && dashHeader) dashHeader.style.display = 'flex';
    if (viewId === 'view-chat' && chatHeader) chatHeader.style.display = 'flex';

    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    if(viewId === 'view-home') document.querySelector('.nav-item:first-child')?.classList.add('active');
    if(viewId === 'view-chat') document.querySelector('.nav-item:last-child')?.classList.add('active');
};

function navTo(viewId) {
    originalNavTo(viewId);
    if(viewId === 'view-weekly') {
        setTimeout(initWeeklyGauge, 100);
    }
}

// --- Main Action & Status ---
function handleMainAction() {
    if (isLessonActive) { navTo('view-dashboard'); } else { openStartSheet(); }
}

function updateUIState() {
    const mainBtn = document.getElementById('mainActionBtn');
    const statusCard = document.getElementById('statusCard');
    const recentList = document.getElementById('recentSessionList');
    if (!mainBtn || !statusCard) return;

    if (isLessonActive) {
        mainBtn.classList.add('active-session');
        mainBtn.innerHTML = '<i data-lucide="activity"></i>';
        if(recentList) recentList.classList.add('disabled-area');
        statusCard.style.background = 'linear-gradient(135deg, #FCA5A5 0%, #E11D48 100%)';
        statusCard.innerHTML = `<div><h2>Lesson in Progress</h2><p>Tracking engagement live...</p></div><button class="hero-btn" onclick="navTo('view-dashboard')"><i data-lucide="bar-chart-2" size="16"></i> <span>View Dashboard</span></button>`;
    } else {
        mainBtn.classList.remove('active-session');
        mainBtn.innerHTML = '<i data-lucide="plus" size="28"></i>';
        if(recentList) recentList.classList.remove('disabled-area');
        statusCard.style.background = 'linear-gradient(135deg, #C4B5FD 0%, #8B5CF6 100%)';
        statusCard.innerHTML = `<div><h2>Ready to Teach?</h2><p>Start a new session now.</p></div><button class="hero-btn" onclick="openStartSheet()"><i data-lucide="play" size="16"></i> <span>Start Lesson</span></button>`;
    }
    lucide.createIcons();
}

// --- Chat Logic ---
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}
function handleEnter(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;
    addMessageToUI(text, 'user');
    input.value = ''; input.style.height = 'auto';
    const typingId = addTypingIndicator();
    try {
        const res = await fetch('/api/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: text }) });
        const data = await res.json();
        removeMessage(typingId);
        addMessageToUI(data.reply, 'ai');
    } catch (e) { removeMessage(typingId); addMessageToUI("Connection error.", 'ai'); }
}

function addMessageToUI(text, sender) {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.innerHTML = sender === 'ai' ? `<div class="avatar-small"><i data-lucide="bot" size="16"></i></div><div class="bubble">${text}</div>` : `<div class="bubble">${text}</div>`;
    container.appendChild(div);
    lucide.createIcons();
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('chatContainer');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div'); div.className = 'message ai'; div.id = id;
    div.innerHTML = `<div class="avatar-small"><i data-lucide="bot" size="16"></i></div><div class="bubble"><div class="typing-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>`;
    container.appendChild(div); container.scrollTop = container.scrollHeight; lucide.createIcons(); return id;
}
function removeMessage(id) { const el = document.getElementById(id); if (el) el.remove(); }

// --- Weekly Report Logic ---
function initWeeklyGauge() {
    const scoreEl = document.getElementById('omegaScoreVal');
    const fill = document.getElementById('weeklyProgress');
    if(!scoreEl || !fill) return;
    let score = 0; const target = 92;
    const interval = setInterval(() => { score++; scoreEl.innerText = score + '%'; if(score >= target) clearInterval(interval); }, 12);
    setTimeout(() => { fill.style.strokeDashoffset = '30'; }, 100);
}

function switchWeeklyTab(tabId, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    document.querySelectorAll('.tab-pane').forEach(p => {
        p.style.display = 'none';
    });

    const target = document.getElementById(tabId);
    if(target) {
        // Use flex for graphs to handle height properly
        target.style.display = tabId === 'tab-graphs' ? 'flex' : 'block';

        if(tabId === 'tab-insights') loadWeeklyInsights();
        if(tabId === 'tab-graphs') {
            // Force redraw/resize of charts when becoming visible
            setTimeout(() => {
                initWeeklyGraphs();
                weeklyCharts.forEach(c => c?.resize());
            }, 50);
        }
    }
    lucide.createIcons();
}

// --- Graph Carousel Logic (NEW & FIXED) ---
function initWeeklyGraphs() {
    if (weeklyCharts.length > 0) return;

    const ctx1 = document.getElementById('chart1')?.getContext('2d');
    const ctx2 = document.getElementById('chart2')?.getContext('2d');
    const ctx3 = document.getElementById('chart3')?.getContext('2d');

    if (!ctx1 || !ctx2 || !ctx3) return;

    // Graph 1: Engagement (Comparison Line)
    weeklyCharts[0] = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu'],
            datasets: [
                { label: 'This Week', data: [82, 85, 88, 92, 94], borderColor: '#7C3AED', backgroundColor: 'rgba(124, 58, 237, 0.1)', borderWidth: 3, tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: 'white' },
                { label: 'Last Week', data: [75, 78, 76, 80, 82], borderColor: '#CBD5E1', borderWidth: 2, borderDash: [5, 5], tension: 0.4, fill: false, pointRadius: 0 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 10 } } }, scales: { x: { grid: { display: false } }, y: { display: false, min: 60 } } }
    });

    // Graph 2: Subjects (Comparison Bar - Grouped)
    weeklyCharts[1] = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ['Math', 'Phys', 'Hist', 'Eng'],
            datasets: [
                { label: 'This Week', data: [92, 85, 76, 88], backgroundColor: '#7C3AED', borderRadius: 4, barPercentage: 0.6 },
                { label: 'Last Week', data: [88, 80, 78, 85], backgroundColor: '#E2E8F0', borderRadius: 4, barPercentage: 0.6 }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 10 } } }, scales: { x: { grid: { display: false } }, y: { display: false, min: 0 } } }
    });

    // Graph 3: Skills (Radar Comparison)
    weeklyCharts[2] = new Chart(ctx3, {
        type: 'radar',
        data: {
            labels: ['Pacing', 'Clarity', 'Interact', 'Energy', 'Visuals'],
            datasets: [
                { label: 'This Week', data: [90, 85, 95, 80, 88], borderColor: '#7C3AED', backgroundColor: 'rgba(124, 58, 237, 0.2)', borderWidth: 2, pointRadius: 0 },
                { label: 'Last Week', data: [80, 82, 85, 75, 80], borderColor: '#CBD5E1', backgroundColor: 'transparent', borderWidth: 2, borderDash: [4,4], pointRadius: 0 }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, position: 'top', align: 'end', labels: { boxWidth: 10 } } },
            scales: { r: { ticks: { display: false }, grid: { color: '#F1F5F9' } } }
        }
    });
}

function nextGraph() {
    currentGraphIndex = (currentGraphIndex + 1) % 3;
    updateGraphVisibility();
}

function prevGraph() {
    currentGraphIndex = (currentGraphIndex - 1 + 3) % 3;
    updateGraphVisibility();
}

function updateGraphVisibility() {
    document.querySelectorAll('.chart-slide').forEach((el, idx) => {
        el.style.opacity = idx === currentGraphIndex ? '1' : '0';
        el.style.pointerEvents = idx === currentGraphIndex ? 'auto' : 'none';
        el.style.zIndex = idx === currentGraphIndex ? '5' : '1';
    });
    document.querySelectorAll('.carousel-dots .dot').forEach((d, i) => {
        d.classList.toggle('active', i === currentGraphIndex);
    });
    document.getElementById('carouselTitle').innerText = graphTitles[currentGraphIndex];
}

async function loadWeeklyInsights() {
    const container = document.getElementById('weekly-ai-content');
    if(!container) return;
    container.innerHTML = '<p style="color:#94A3B8; font-size:14px;">Analyzing performance with Gemini...</p>';
    try {
        const res = await fetch('/api/weekly_insights');
        const data = await res.json();
        container.innerHTML = `<p style="font-size:15px; line-height:1.6; color:#334155;">${data.text}</p>`;
    } catch(e) { container.innerHTML = '<p>Unavailable.</p>'; }
}

// --- Standard Boilerplate ---
function openStartSheet() { document.getElementById('startModal').classList.add('active'); }
function closeStartSheet() { document.getElementById('startModal').classList.remove('active'); }
function handleOverlayClick(e) { if (e.target.id === 'startModal') closeStartSheet(); }
function loadSimulation(id) {
    if(isLessonActive) { alert("Please end active lesson."); return; }
    const t = document.getElementById('liveSubjectTitle'); if(t) t.innerText = id === 1 ? "Algebra II" : "Literature";
    navTo('view-dashboard'); loadDashboardData(true);
}
async function handleStart(e) { e.preventDefault(); isLessonActive = true; closeStartSheet(); updateUIState(); navTo('view-dashboard'); loadDashboardData(); }
async function endSession() { if(confirm("End session?")) { await fetch('/api/end_lesson', { method: 'POST' }); isLessonActive = false; updateUIState(); navTo('view-home'); } }
async function loadDashboardData(isStatic=false) { /* ... same ... */ }
if (window.initialSessionActive) { isLessonActive = true; updateUIState(); loadDashboardData(); } else { updateUIState(); }