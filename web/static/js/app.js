/* CA Lab — Shared JavaScript utilities */

const API_BASE = '';

const api = {
    async get(path) {
        const res = await fetch(API_BASE + path);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },

    async post(path, data) {
        const res = await fetch(API_BASE + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            const detail = err.detail;
            const message = typeof detail === 'string' ? detail
                : Array.isArray(detail) ? (detail[0]?.msg || JSON.stringify(detail))
                : detail || `HTTP ${res.status}`;
            throw new Error(message);
        }
        return res.json();
    },

    async put(path, data) {
        const res = await fetch(API_BASE + path, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            const detail = err.detail;
            const message = typeof detail === 'string' ? detail
                : Array.isArray(detail) ? (detail[0]?.msg || JSON.stringify(detail))
                : detail || `HTTP ${res.status}`;
            throw new Error(message);
        }
        return res.json();
    },

    async delete(path) {
        const res = await fetch(API_BASE + path, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            const detail = err.detail;
            const message = typeof detail === 'string' ? detail : `HTTP ${res.status}`;
            throw new Error(message);
        }
        return res.json();
    },

    async postForm(path, formData) {
        const res = await fetch(API_BASE + path, {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            const detail = err.detail;
            const message = typeof detail === 'string' ? detail
                : Array.isArray(detail) ? (detail[0]?.msg || JSON.stringify(detail))
                : detail || `HTTP ${res.status}`;
            throw new Error(message);
        }
        return res.json();
    }
};

// Format numbers
function fmt(n, decimals = 4) {
    return Number(n).toFixed(decimals);
}

// Create element with classes
function el(tag, classes = '', text = '') {
    const e = document.createElement(tag);
    if (classes) e.className = classes;
    if (text) e.textContent = text;
    return e;
}

// Show toast notification
function toast(message, type = 'info') {
    const t = el('div', `toast toast-${type}`, message);
    t.style.cssText = `
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#2563eb'};
        color: white;
        font-weight: 600;
        z-index: 1000;
        animation: fadeIn 0.3s;
    `;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}

// Render grid to canvas
function renderGrid(canvas, grid, palette, cellSize) {
    const ctx = canvas.getContext('2d');
    const h = grid.length;
    const w = grid[0].length;
    canvas.width = w * cellSize;
    canvas.height = h * cellSize;

    // Fill background
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw cells
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const state = grid[y][x];
            if (state > 0 && palette[state]) {
                const [r, g, b] = palette[state];
                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
            }
        }
    }

    // Draw grid lines
    if (cellSize >= 4) {
        ctx.strokeStyle = '#333333';
        ctx.lineWidth = 0.5;
        for (let x = 0; x <= w; x++) {
            ctx.beginPath();
            ctx.moveTo(x * cellSize, 0);
            ctx.lineTo(x * cellSize, h * cellSize);
            ctx.stroke();
        }
        for (let y = 0; y <= h; y++) {
            ctx.beginPath();
            ctx.moveTo(0, y * cellSize);
            ctx.lineTo(w * cellSize, y * cellSize);
            ctx.stroke();
        }
    }
}

// WebSocket simulation client
class SimulationClient {
    constructor(sessionId, onFrame, onStatus) {
        this.sessionId = sessionId;
        this.onFrame = onFrame;
        this.onStatus = onStatus;
        this.ws = null;
        this.reconnect = true;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/sim/ws/${this.sessionId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.onStatus({ type: 'status', status: 'connected' });
        };

        this.ws.onmessage = async (event) => {
            if (typeof event.data === 'string') {
                const msg = JSON.parse(event.data);
                this.onStatus(msg);
            } else {
                // Binary data - grid bytes
                const arrayBuffer = await event.data.arrayBuffer();
                const uint8Array = new Uint8Array(arrayBuffer);
                this.onFrame(uint8Array);
            }
        };

        this.ws.onclose = () => {
            if (this.reconnect) {
                setTimeout(() => this.connect(), 1000);
            }
        };

        this.ws.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    }

    send(action, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ action, ...data }));
        }
    }

    start(grid = null) { this.send('start', grid ? { grid } : {}); }
    pause() { this.send('pause'); }
    stop() { this.send('stop'); }
    step(count = 1) { this.send('step', { count }); }
    reset() { this.send('reset'); }
    paint(x, y, state) { this.send('paint', { x, y, state }); }
    speed(fps) { this.send('speed', { fps }); }
    snapshot() { this.send('snapshot'); }

    disconnect() {
        this.reconnect = false;
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(style);
