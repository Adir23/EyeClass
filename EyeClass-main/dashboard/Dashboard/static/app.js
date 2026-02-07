lucide.createIcons();
let isLessonActive = false;
let chartInstance = null;

// --- Navigation Logic ---
function navTo(viewId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');

    // Header Logic
    document.getElementById('homeHeader').style.display = 'none';
    document.getElementById('dashHeader').style.display = 'none';
    document.getElementById('chatHeader').style.display = 'none';

    if (viewId === 'view-home') document.getElementById('homeHeader').style.display = 'flex';
    if (viewId === 'view-dashboard') document.getElementById('dashHeader').style.display = 'flex';
    if (viewId === 'view-chat') document.getElementById('chatHeader').style.display = 'flex';

    // Nav Icons
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    if(viewId === 'view-home') document.querySelector('.nav-item:first-child').classList.add('active');
    if(viewId === 'view-chat') document.querySelector('.nav-item:last-child').classList.add('active');
}

// --- Main Action & Status ---
function handleMainAction() {
    if (isLessonActive) {
        navTo('view-dashboard');
    } else {
        openStartSheet();
    }
}

function updateUIState() {
    const mainBtn = document.getElementById('mainActionBtn');
    const statusCard = document.getElementById('statusCard');
    const recentList = document.getElementById('recentSessionList');

    if (isLessonActive) {
        mainBtn.classList.add('active-session');
        mainBtn.innerHTML = '<i data-lucide="activity"></i>';
        if(recentList) recentList.classList.add('disabled-area');

        statusCard.style.background = 'linear-gradient(135deg, #FCA5A5 0%, #E11D48 100%)';
        statusCard.innerHTML = `
            <div>
                <h2>Lesson in Progress</h2>
                <p>Tracking engagement live...</p>
            </div>
            <button class="hero-btn" onclick="navTo('view-dashboard')">
                <i data-lucide="bar-chart-2" size="16"></i> <span>View Dashboard</span>
            </button>
        `;
    } else {
        mainBtn.classList.remove('active-session');
        mainBtn.innerHTML = '<i data-lucide="plus" size="28"></i>';
        if(recentList) recentList.classList.remove('disabled-area');

        statusCard.style.background = 'linear-gradient(135deg, #C4B5FD 0%, #8B5CF6 100%)';
        statusCard.innerHTML = `
            <div>
                <h2>Ready to Teach?</h2>
                <p>Start a new session now.</p>
            </div>
            <button class="hero-btn" onclick="openStartSheet()">
                <i data-lucide="play" size="16"></i> <span>Start Lesson</span>
            </button>
        `;
    }
    lucide.createIcons();
}

// --- Chat Logic (UPDATED) ---

function autoResize(textarea) {
    textarea.style.height = 'auto'; // Reset height
    textarea.style.height = textarea.scrollHeight + 'px'; // Set to content height
}

function handleEnter(e) {
    // Send on Enter, but allow new line with Shift+Enter
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;

    // 1. Add User Message
    addMessageToUI(text, 'user');

    // Reset Input & Height
    input.value = '';
    input.style.height = 'auto';

    // 2. Show Typing Indicator
    const typingId = addTypingIndicator();

    try {
        // 3. Send to Server
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        // 4. Remove Typing & Add AI Response
        removeMessage(typingId);
        addMessageToUI(data.reply, 'ai');

    } catch (e) {
        removeMessage(typingId);
        addMessageToUI("Sorry, I'm having trouble connecting right now.", 'ai');
    }
}

function addMessageToUI(text, sender) {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = `message ${sender}`;

    let content = '';
    if (sender === 'ai') {
        content = `
            <div class="avatar-small"><i data-lucide="bot" size="16"></i></div>
            <div class="bubble">${text}</div>
        `;
    } else {
        content = `<div class="bubble">${text}</div>`;
    }

    div.innerHTML = content;
    container.appendChild(div);
    lucide.createIcons();

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('chatContainer');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'message ai';
    div.id = id;
    div.innerHTML = `
        <div class="avatar-small"><i data-lucide="bot" size="16"></i></div>
        <div class="bubble">
            <div class="typing-dots">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    lucide.createIcons();
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// --- Modal & API Calls ---
function openStartSheet() { document.getElementById('startModal').classList.add('active'); }
function closeStartSheet() { document.getElementById('startModal').classList.remove('active'); }
function handleOverlayClick(e) { if (e.target.id === 'startModal') closeStartSheet(); }

function loadSimulation(id) {
    if(isLessonActive) { alert("Please end the active lesson first."); return; }
    const subject = id === 1 ? "Algebra II" : "Literature";
    document.getElementById('liveSubjectTitle').innerText = subject;
    navTo('view-dashboard');
    loadDashboardData(true);
}

async function handleStart(e) {
    e.preventDefault();
    const subject = document.getElementById('inpSubject').value;
    const topic = document.getElementById('inpTopic').value;
    await fetch('/api/start_lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject, topic })
    });
    isLessonActive = true;
    document.getElementById('liveSubjectTitle').innerText = subject;
    closeStartSheet();
    updateUIState();
    navTo('view-dashboard');
    loadDashboardData();
}

async function endSession() {
    if(confirm("End current session?")) {
        await fetch('/api/end_lesson', { method: 'POST' });
        isLessonActive = false;
        updateUIState();
        navTo('view-home');
    }
}

async function loadDashboardData(isStatic = false) {
    try {
        const url = isStatic ? '/api/get_dashboard_data?history=true' : '/api/get_dashboard_data';
        const res = await fetch(url);
        const json = await res.json();

        renderHeatmap(json.data.blocks.slice(0, 6));
        renderChart(json.data.attention_time);
        renderAISuggestions(json.data.suggestions);

        if(isLessonActive && !isStatic) setTimeout(loadDashboardData, 3000);
    } catch(e) { console.error(e); }
}

function renderHeatmap(blocks) {
    const grid = document.getElementById('classroomGrid');
    grid.innerHTML = '';
    blocks.forEach(block => {
        const div = document.createElement('div');
        const type = block.attention > 75 ? 'high' : block.attention > 45 ? 'med' : 'low';
        div.className = `heat-circle ${type}`;
        div.setAttribute('data-val', block.attention);
        grid.appendChild(div);
    });
}

function renderAISuggestions(suggestions) {
    const list = document.getElementById('aiSuggestionsList');
    list.innerHTML = '';
    const safeSuggestions = suggestions.length ? suggestions : ["Front row needs attention.", "Great pacing!"];
    safeSuggestions.slice(0, 5).forEach(text => {
        const item = document.createElement('div');
        item.style.cssText = "display:flex; gap:10px; background:#F5F3FF; padding:12px; border-radius:12px; font-size:13px; color:#2E1065;";
        item.innerHTML = `<i data-lucide="sparkles" size="16" style="min-width:16px; color:#7C3AED;"></i> <span>${text}</span>`;
        list.appendChild(item);
    });
    lucide.createIcons();
}

function renderChart(dataPoints) {
    const ctx = document.getElementById('lineChart').getContext('2d');
    if (chartInstance) {
        chartInstance.data.datasets[0].data = dataPoints;
        chartInstance.update();
        return;
    }
    let gradient = ctx.createLinearGradient(0, 0, 0, 150);
    gradient.addColorStop(0, 'rgba(124, 58, 237, 0.4)');
    gradient.addColorStop(1, 'rgba(124, 58, 237, 0.0)');

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['10m', '15m', '20m', '25m', '30m', 'Now'],
            datasets: [{
                data: dataPoints,
                borderColor: '#7C3AED',
                borderWidth: 2,
                backgroundColor: gradient,
                fill: true,
                pointRadius: 5,
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
            scales: { x: { display: false }, y: { display: false, min: 20, max: 100 } },
            animation: { duration: 1000 }
        }
    });
}

// Init
if (window.initialSessionActive) {
    isLessonActive = true;
    updateUIState();
    loadDashboardData();
} else {
    updateUIState();
}