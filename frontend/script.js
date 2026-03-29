/**
 * MargMitra - Frontend Script
 * Connects to Main API at localhost:8000
 */

const API_BASE = "http://localhost:8000";

document.addEventListener('DOMContentLoaded', () => {

    // ── Theme ──────────────────────────────────────────────────────────────
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon   = document.getElementById('theme-icon');

    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
        themeIcon.classList.replace('ph-moon', 'ph-sun');
    }

    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        themeIcon.classList.toggle('ph-moon', !isDark);
        themeIcon.classList.toggle('ph-sun', isDark);
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // ── Camera ────────────────────────────────────────────────────────────
    const openScanBtn   = document.getElementById('open-scan-btn');
    const fabScan       = document.getElementById('fab-scan');
    const closeCameraBtn = document.getElementById('close-camera');
    const cameraOverlay = document.getElementById('camera-overlay');
    const video         = document.getElementById('webcam');
    const shutterBtn    = document.getElementById('shutter-btn');
    let stream = null;

    async function startCamera() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            video.srcObject = stream;
            cameraOverlay.classList.remove('hidden');
        } catch {
            showToast("Camera permission denied. Please allow camera access.", "error");
        }
    }

    function stopCamera() {
        if (stream) stream.getTracks().forEach(t => t.stop());
        stream = null;
        cameraOverlay.classList.add('hidden');
    }

    openScanBtn.addEventListener('click', startCamera);
    fabScan.addEventListener('click', startCamera);
    closeCameraBtn.addEventListener('click', stopCamera);

    // ── Capture & Send to Backend ─────────────────────────────────────────
    shutterBtn.addEventListener('click', async () => {
        // Flash effect
        cameraOverlay.style.opacity = '0.3';
        setTimeout(() => cameraOverlay.style.opacity = '1', 150);

        // Draw frame to canvas → get image blob
        const canvas = document.createElement('canvas');
        canvas.width  = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);

        canvas.toBlob(async (blob) => {
            stopCamera();
            await processImage(blob, 'captured_sign.jpg');
        }, 'image/jpeg', 0.9);
    });

    // ── Upload from Gallery ───────────────────────────────────────────────
    const uploadCard = document.querySelector('.action-card:first-child');
    const fileInput  = document.createElement('input');
    fileInput.type   = 'file';
    fileInput.accept = 'image/*';

    uploadCard.style.cursor = 'pointer';
    uploadCard.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) await processImage(file, file.name);
        fileInput.value = '';
    });

    // ── Core: Send image to backend ───────────────────────────────────────
    async function processImage(blob, filename) {
        const targetLang = document.getElementById('lang-select')?.value || 'hi';

        showLoader(true);

        const formData = new FormData();
        formData.append('image', blob, filename);
        formData.append('target_lang', targetLang);

        try {
            const response = await fetch(`${API_BASE}/scan`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Server error');
            }

            const result = await response.json();
            showResult(result);
            loadHistory();
            loadStats();

        } catch (err) {
            if (err.message.includes('fetch') || err.message.includes('Failed')) {
                showToast("Cannot reach server. Make sure all 3 Python services are running.", "error");
            } else {
                showToast("Error: " + err.message, "error");
            }
        } finally {
            showLoader(false);
        }
    }

    // ── Result Modal ──────────────────────────────────────────────────────
    function showResult(result) {
        // Remove old modal if any
        document.getElementById('result-modal')?.remove();

        const modal = document.createElement('div');
        modal.id = 'result-modal';
        modal.style.cssText = `
            position:fixed; inset:0; background:rgba(0,0,0,0.6);
            display:flex; align-items:flex-end; justify-content:center;
            z-index:2000; backdrop-filter:blur(4px);
        `;

        modal.innerHTML = `
            <div style="
                background:var(--card-bg); border-radius:24px 24px 0 0;
                padding:28px 24px 40px; width:100%; max-width:480px;
                box-shadow:0 -10px 40px rgba(0,0,0,0.3);
                animation: slideUp 0.35s cubic-bezier(0.34,1.56,0.64,1);
            ">
                <div style="width:40px;height:4px;background:#ccc;border-radius:2px;margin:0 auto 20px;"></div>
                <h3 style="margin:0 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;color:var(--text-muted);">Detected Text</h3>
                <p style="font-size:22px;font-weight:700;margin:0 0 20px;color:var(--text-main);">${result.original}</p>

                <h3 style="margin:0 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;color:#a855f7;">Transliterated — ${result.language_name}</h3>
                <p style="font-size:28px;font-weight:700;margin:0 0 24px;color:#a855f7;">${result.transliterated}</p>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
                    <button onclick="speakText('${result.transliterated}')" style="
                        padding:14px; border-radius:14px; border:none;
                        background:rgba(168,85,247,0.1); color:#a855f7;
                        font-weight:600; font-size:15px; cursor:pointer;
                        display:flex;align-items:center;justify-content:center;gap:8px;
                    "><i class='ph ph-speaker-high'></i> Pronounce</button>
                    <button onclick="copyText('${result.transliterated}')" style="
                        padding:14px; border-radius:14px; border:none;
                        background:rgba(59,130,246,0.1); color:#3b82f6;
                        font-weight:600; font-size:15px; cursor:pointer;
                        display:flex;align-items:center;justify-content:center;gap:8px;
                    "><i class='ph ph-copy'></i> Copy</button>
                </div>

                <button onclick="document.getElementById('result-modal').remove()" style="
                    width:100%; padding:16px; border-radius:14px; border:none;
                    background:linear-gradient(135deg,#a855f7,#3b82f6);
                    color:white; font-size:16px; font-weight:600; cursor:pointer;
                ">Done</button>
            </div>
        `;

        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
    }

    // ── History ───────────────────────────────────────────────────────────
    async function loadHistory() {
        try {
            const res = await fetch(`${API_BASE}/history`);
            if (!res.ok) return;
            const data = await res.json();
            const container = document.querySelector('.recent-section');
            if (!container || !data.scans.length) return;

            // Keep the header, replace items
            const header = container.querySelector('.section-header');
            container.innerHTML = '';
            container.appendChild(header);

            data.scans.slice(0, 5).forEach(scan => {
                const item = document.createElement('div');
                item.className = 'history-item';
                const ago = timeAgo(scan.scanned_at);
                item.innerHTML = `
                    <div class="item-info">
                        <strong>${scan.transliterated}</strong>
                        <span>${scan.original}</span>
                    </div>
                    <span class="time-tag">${ago}</span>
                `;
                container.appendChild(item);
            });
        } catch { /* server not running yet */ }
    }

    // ── Stats ─────────────────────────────────────────────────────────────
    async function loadStats() {
        try {
            const res = await fetch(`${API_BASE}/stats`);
            if (!res.ok) return;
            const data = await res.json();
            const boxes = document.querySelectorAll('.stat-box h3');
            if (boxes[0]) boxes[0].textContent = data.total_scans || '0';
            if (boxes[1]) boxes[1].textContent = data.languages_used || '0';
        } catch { /* server not running yet */ }
    }

    // ── Language selector (inject into header) ────────────────────────────
    const header = document.querySelector('header');
    const select = document.createElement('select');
    select.id = 'lang-select';
    select.style.cssText = `
        background:var(--card-bg); border:1px solid rgba(168,85,247,0.3);
        border-radius:10px; padding:8px 12px; color:var(--text-main);
        font-family:inherit; font-size:13px; cursor:pointer; margin-top:8px;
    `;
    select.innerHTML = `
        <option value="hi">हिन्दी</option>
        <option value="ta">தமிழ்</option>
        <option value="te">తెలుగు</option>
        <option value="bn">বাংলা</option>
        <option value="gu">ગુજરાતી</option>
        <option value="ml">മലയാളം</option>
        <option value="kn">ಕನ್ನಡ</option>
        <option value="pa">ਪੰਜਾਬੀ</option>
        <option value="mr">मराठी</option>
        <option value="or">ଓଡ଼ିଆ</option>
        <option value="ur">اردو</option>
    `;
    header.appendChild(select);

    // ── Loader overlay ────────────────────────────────────────────────────
    function showLoader(show) {
        let loader = document.getElementById('mm-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'mm-loader';
            loader.style.cssText = `
                position:fixed;inset:0;background:rgba(0,0,0,0.55);
                display:flex;flex-direction:column;align-items:center;
                justify-content:center;z-index:3000;backdrop-filter:blur(4px);
                gap:16px;color:white;font-size:15px;font-weight:500;
            `;
            loader.innerHTML = `
                <div style="
                    width:52px;height:52px;border-radius:50%;
                    border:3px solid rgba(255,255,255,0.2);
                    border-top-color:#a855f7;
                    animation:spin 0.8s linear infinite;
                "></div>
                <span>Analysing sign...</span>
                <style>@keyframes spin{to{transform:rotate(360deg)}}</style>
                <style>@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}</style>
            `;
            document.body.appendChild(loader);
        }
        loader.style.display = show ? 'flex' : 'none';
    }

    // ── Toast notification ────────────────────────────────────────────────
    function showToast(msg, type = 'info') {
        document.getElementById('mm-toast')?.remove();
        const t = document.createElement('div');
        t.id = 'mm-toast';
        const bg = type === 'error' ? '#7f1d1d' : '#1e1b4b';
        const border = type === 'error' ? 'rgba(255,80,80,0.4)' : 'rgba(168,85,247,0.4)';
        t.style.cssText = `
            position:fixed;bottom:100px;left:50%;transform:translateX(-50%);
            background:${bg};border:1px solid ${border};
            border-radius:12px;padding:12px 20px;color:white;font-size:14px;
            z-index:4000;max-width:340px;text-align:center;
            animation:slideUp 0.3s ease;
        `;
        t.textContent = msg;
        document.body.appendChild(t);
        setTimeout(() => t.remove(), 4000);
    }

    // ── Helpers ───────────────────────────────────────────────────────────
    function timeAgo(isoString) {
        const diff = (Date.now() - new Date(isoString)) / 1000;
        if (diff < 60) return `${Math.floor(diff)}s`;
        if (diff < 3600) return `${Math.floor(diff/60)}m`;
        if (diff < 86400) return `${Math.floor(diff/3600)}h`;
        return `${Math.floor(diff/86400)}d`;
    }

    // Make these global so inline onclick handlers work
    window.speakText = (text) => {
        const utt = new SpeechSynthesisUtterance(text);
        utt.rate = 0.8;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utt);
    };

    window.copyText = (text) => {
        navigator.clipboard.writeText(text)
            .then(() => showToast('Copied to clipboard ✓'))
            .catch(() => showToast('Copy failed', 'error'));
    };

    // ── Init ──────────────────────────────────────────────────────────────
    loadHistory();
    loadStats();
});
