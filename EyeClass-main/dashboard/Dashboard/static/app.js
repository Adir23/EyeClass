lucide.createIcons();
let isLessonActive = false;
let chartInstance = null;

// --- Navigation Logic ---
function navTo(viewId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');

    const isDash = viewId === 'view-dashboard';
    document.getElementById('homeHeader').style.display = isDash ? 'none' : 'flex';
    document.getElementById('dashHeader').style.display = isDash ? 'flex' : 'none';

    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    if(viewId === 'view-home') document.querySelector('.nav-item:first-child').classList.add('active');
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
        // Active State (Warm Red Gradient)
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
                <i data-lucide="bar-chart-2" size="16"></i> 
                <span>View Dashboard</span>
            </button>
        `;
    } else {
        // Idle State (Gentle Silky Purple)
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
                <i data-lucide="play" size="16"></i> 
                <span>Start Lesson</span>
            </button>
        `;
    }
    lucide.createIcons();
}

// --- Modal Logic ---
function openStartSheet() { document.getElementById('startModal').classList.add('active'); }
function closeStartSheet() { document.getElementById('startModal').classList.remove('active'); }

function handleOverlayClick(e) {
    if (e.target.id === 'startModal') {
        closeStartSheet();
    }
}

// --- Simulation Logic ---
function loadSimulation(id) {
    if(isLessonActive) {
        alert("Please end the active lesson to view history.");
        return;
    }
    const subject = id === 1 ? "Algebra II" : "Literature";
    document.getElementById('liveSubjectTitle').innerText = subject;
    navTo('view-dashboard');
    // Load static data once (isStatic = true)
    loadDashboardData(true);
}

// --- API Calls ---
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

// --- Dashboard Logic ---
async function loadDashboardData(isStatic = false) {
    try {
        // If isStatic is true, append ?history=true query param
        const url = isStatic ? '/api/get_dashboard_data?history=true' : '/api/get_dashboard_data';

        const res = await fetch(url);
        const json = await res.json();

        renderHeatmap(json.data.blocks.slice(0, 6));
        renderChart(json.data.attention_time);
        renderAISuggestions(json.data.suggestions);

        // Only loop if active and NOT static
        if(isLessonActive && !isStatic) {
            setTimeout(loadDashboardData, 3000);
        }
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
    const safeSuggestions = suggestions.length ? suggestions : ["Front row needs attention.", "Great pacing so far!"];

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
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: { display: false },
                y: { display: false, min: 20, max: 100 }
            },
            animation: {
                duration: 1000
            }
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