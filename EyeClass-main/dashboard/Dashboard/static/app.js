lucide.createIcons();

// --- Sheet Modal Logic ---
function openStartSheet() {
    const modal = document.getElementById('startSheetModal');
    modal.classList.add('active');
    // Prevent body scrolling when modal is open (mobile best practice)
    document.body.style.overflow = 'hidden';
}

function closeStartSheet(e) {
    // Close if clicking overlay OR the close button
    if (!e || e.target === document.getElementById('startSheetModal') || e.currentTarget.classList.contains('close-sheet-btn')) {
        document.getElementById('startSheetModal').classList.remove('active');
        document.body.style.overflow = '';
    }
}

// --- Navigation Logic ---
function navTo(viewId) {
    // 1. Update Views
    document.querySelectorAll('.view-container').forEach(el => el.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');

    // 2. Update Header state
    document.querySelectorAll('.header-content').forEach(el => el.classList.remove('active'));
    if (viewId === 'view-home') document.querySelector('.home-header').classList.add('active');
    if (viewId === 'view-dashboard') document.querySelector('.dash-header').classList.add('active');

    // 3. Update Bottom Nav active state
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    // Simple check to activate correct nav icon
    if (viewId.includes('home')) document.querySelector('.nav-item:first-child').classList.add('active');
    if (viewId.includes('dash')) document.querySelector('.nav-item:last-child').classList.add('active');
}

// --- App Core Logic ---

async function handleStart(e) {
    e.preventDefault();
    // Use the new button styling for loading state
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Starting...';
    lucide.createIcons();

    const subject = document.getElementById('inpSubject').value;
    const classVal = document.getElementById('inpClass').value;
    const topic = document.getElementById('inpTopic').value;

    await fetch('/api/start_lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject, class_name: classVal, topic })
    });

    closeStartSheet();
    // Reset button
    btn.innerHTML = originalText;
    navTo('view-dashboard');
    // Trigger skeleton and load
    loadDashboardData();
}

let isFetching = false;
async function loadDashboardData() {
    if (isFetching) return;
    isFetching = true;

    // Show skeleton, hide real content
    document.getElementById('dash-skeleton').classList.add('active');
    document.getElementById('dash-real-content').style.display = 'none';

    try {
        const res = await fetch('/api/get_dashboard_data');
        if (!res.ok) throw new Error("No session");

        const json = await res.json();
        renderDashboard(json);
        // Hide skeleton, show content with a slight delay for smoothness
        setTimeout(() => {
            document.getElementById('dash-skeleton').classList.remove('active');
            // Use CSS animation to fade real content in
            const realContent = document.getElementById('dash-real-content');
            realContent.style.display = 'block';
            realContent.style.animation = 'fadeIn 0.5s ease';
        }, 600);

    } catch (e) {
        console.log("No active session or error fetching");
        navTo('view-home');
    } finally {
        isFetching = false;
    }
}

function renderDashboard(json) {
    const { data, meta } = json;
    document.getElementById('live-subject').innerText = meta.subject;
    document.getElementById('live-topic').innerText = meta.topic;

    // Render Heatmap Grid
    const grid = document.getElementById('classroomGrid');
    grid.innerHTML = '';
    data.blocks.forEach(block => {
        const div = document.createElement('div');
        // Determine color based on attention
        const type = block.attention > 75 ? 'high' : block.attention > 45 ? 'med' : 'low';
        div.className = `heat-spot ${type}`;
        // Use restlessness to adjust breathing speed dynamically (advanced)
        const breathSpeed = (3 - (block.restlessness / 50)).toFixed(1) + 's';
        div.style.setProperty('--animate-duration', breathSpeed);
        grid.appendChild(div);
    });

    renderAdvancedChart(data.attention_time);

    // Render AI Stream
    const aiContainer = document.getElementById('aiSuggestions');
    // Don't clear, just prepend new ones for a "stream" feel
    if (data.suggestions.length > 0) {
        const latestSuggestion = data.suggestions[0]; // Just take the first for demo
        const bubble = document.createElement('div');
        bubble.className = 'ai-bubble';
        bubble.innerText = latestSuggestion;
        aiContainer.prepend(bubble);
        // Keep stream short
        if (aiContainer.children.length > 3) aiContainer.lastChild.remove();
    }
}

async function endSession() {
    // Use native confirm dialog for speed
    if (confirm("End live tracking session?")) {
        await fetch('/api/end_lesson', { method: 'POST' });
        navTo('view-home');
    }
}

let chartInstance = null;
function renderAdvancedChart(dataPoints) {
    const ctx = document.getElementById('lineChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    // Create a cool gradient for the chart fill
    let gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(124, 58, 237, 0.5)'); // Purple
    gradient.addColorStop(1, 'rgba(6, 182, 212, 0.05)'); // Cyan

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['10m', '15m', '20m', '25m', '30m', '35m', '40m', 'Now'],
            datasets: [{
                data: dataPoints,
                borderColor: '#7c3aed',
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4, // Smooth curves
                pointRadius: 4,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#7c3aed',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false, drawBorder: false }, ticks: { color: '#94a3b8', font: { size: 11 } } },
                y: { min: 40, max: 100, grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false }, ticks: { color: '#94a3b8', font: { size: 11 }, stepSize: 20 } }
            },
            animation: {
                y: { duration: 1000, easing: 'easeOutQuart' }
            }
        }
    });
}

// Init: Check server-injected state
if (window.initialSessionActive) {
    navTo('view-dashboard');
    loadDashboardData();
} else {
    navTo('view-home');
}