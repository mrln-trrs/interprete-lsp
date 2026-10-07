// ── Config ────────────────────────────────────────────────────────────────
const TARGET_FPS = 12;
const JPEG_Q    = 0.65;
const MAX_W     = 640;

// ── Refs ───────────────────────────────────────────────────────────────────
const video    = document.getElementById('local-video');
const procImg  = document.getElementById('processed-img');
const capCanvas= document.getElementById('cap-canvas');
const capCtx   = capCanvas.getContext('2d');
const kpCanvas = document.getElementById('kp-canvas');
const kpCtx    = kpCanvas.getContext('2d');
const overlay  = document.getElementById('overlay');
const btnStart = document.getElementById('btn-start');
const btnFlip  = document.getElementById('btn-flip');
const livePill = document.getElementById('live-pill');
const latBadge = document.getElementById('lat-badge');
const latVal   = document.getElementById('lat-val');
const sFps     = document.getElementById('s-fps');
const sLat     = document.getElementById('s-lat');
const sHands   = document.getElementById('s-hands');
const sKp      = document.getElementById('s-kp');
const handsRow = document.getElementById('hands-row');

// ── Estado ─────────────────────────────────────────────────────────────────
let stream      = null;
let facing      = 'user';
let sending     = false;
let lastSend    = 0;
let frameCount  = 0;
let fpsTs       = Date.now();
let displayFps  = 0;
let sessionId = null;
let sessionStart = 0;
let frameId = 0;
let generation = 0;
let starting = false;
let inFlight = null;
const statusText = document.getElementById('status');

async function stopCamera() {
  generation++;
  inFlight?.abort();
  stream?.getTracks().forEach(t => t.stop());
  stream = null;
  video.srcObject = null;
  const closingSession = sessionId;
  sessionId = null;
  overlay.style.display = 'flex';
  livePill.style.display = 'none';
  btnFlip.style.display = 'none';
  statusText.textContent = 'Cámara detenida';
  if (closingSession) {
    try { await fetch('/api/v1/sessions/' + closingSession, {
      method:'DELETE', headers:{Authorization:'Bearer ' + closingSession},
      signal:AbortSignal.timeout(3000), keepalive:true
    }); } catch(e) { statusText.textContent = 'Cámara detenida; la sesión expira automáticamente'; }
  }
}
document.getElementById('btn-stop').addEventListener('click', stopCamera);
window.addEventListener('pagehide', stopCamera);

// ── Activar cámara ──────────────────────────────────────────────────────────
async function startCamera() {
  if (starting || stream) return;
  starting = true;
  const openingGeneration = ++generation;
  try {
    if (!sessionId) {
      const keyInput = document.getElementById('access-key');
      const accessKey = keyInput.value;
      keyInput.value = '';
      const response = await fetch('/api/v1/sessions', {
        method:'POST', headers:{'Content-Type':'application/json', Authorization:'Bearer ' + accessKey},
        body:'{}', signal:AbortSignal.timeout(3000)
      });
      if (!response.ok) throw new Error('No se pudo autorizar la sesión. Revisa la clave o disponibilidad.');
      sessionId = (await response.json()).data.session_id;
      sessionStart = performance.now(); frameId = 0;
      if (openingGeneration !== generation) { await stopCamera(); return; }
    }
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: facing, width:{ideal:1280}, height:{ideal:720} },
      audio: false
    });
    if (openingGeneration !== generation) { stream.getTracks().forEach(t => t.stop()); stream = null; return; }
    video.srcObject = stream;
    await video.play();
    overlay.style.display  = 'none';
    btnFlip.style.display  = 'flex';
    livePill.style.display = 'flex';
    latBadge.style.display = 'block';
    statusText.textContent = 'Detectando manos';
    requestAnimationFrame(() => loop(openingGeneration));
  } catch(e) {
    await stopCamera();
    statusText.textContent = e.message;
  } finally {
    starting = false;
  }
}
btnStart.addEventListener('click', startCamera);

btnFlip.addEventListener('click', async () => {
  stream?.getTracks().forEach(t => t.stop());
  stream = null; generation++; inFlight?.abort();
  facing = facing === 'user' ? 'environment' : 'user';
  await startCamera();
});

// ── Loop de captura ─────────────────────────────────────────────────────────
function loop(loopGeneration) {
  if (!stream || loopGeneration !== generation) return;
  requestAnimationFrame(() => loop(loopGeneration));
  const now = Date.now();
  if ((now - lastSend) < 1000 / TARGET_FPS) return;
  if (sending || video.readyState < 2) return;
  lastSend = now;
  send();
  frameCount++;
  if (now - fpsTs >= 1000) { displayFps = frameCount; frameCount = 0; fpsTs = now; }
}

async function send() {
  sending = true;
  const t0 = Date.now();
  const vw = video.videoWidth  || 640;
  const vh = video.videoHeight || 480;
  const sc = Math.min(1, MAX_W / vw);
  capCanvas.width  = Math.round(vw * sc);
  capCanvas.height = Math.round(vh * sc);
  capCtx.drawImage(video, 0, 0, capCanvas.width, capCanvas.height);
  const dataUrl = capCanvas.toDataURL('image/jpeg', JPEG_Q);
  const sendingGeneration = generation;
  inFlight = new AbortController();
  const timeout = setTimeout(() => inFlight?.abort(), 3000);
  try {
    const r = await fetch('/api/v1/process-frame', {
      method:'POST',
      headers:{'Content-Type':'application/json', Authorization:'Bearer ' + sessionId},
      body: JSON.stringify({ frame: dataUrl, session_id:sessionId,
        frame_id:frameId++, captured_at_ms:performance.now() - sessionStart }),
      signal:inFlight.signal
    });
    if (!r.ok) {
      statusText.textContent = 'Procesamiento no disponible; detén y vuelve a iniciar';
      if ([401,403,503].includes(r.status)) await stopCamera();
      return;
    }
    const d = (await r.json()).data;
    if (sendingGeneration !== generation) return;
    document.getElementById('pending-glosses').textContent = (d.pending_glosses || []).join(' · ') || '—';
    document.getElementById('confirmed-text').textContent = d.confirmed_text || '—';
    document.getElementById('model-state').textContent = d.model_available ? 'Modelo exploratorio; revisión lingüística pendiente' : 'Demo de manos: modelo no disponible';
    d.manos = d.hands.map(h => ({label:h.side,
      label_es:h.side === 'Left' ? 'Izquierda' : 'Derecha', confidence:Math.round(h.confidence * 100)}));
    const lat = Date.now() - t0;
    if (d.frame) procImg.src = d.frame;
    sFps.textContent   = displayFps;
    sLat.textContent   = lat;
    sHands.textContent = (d.manos||[]).length;
    const kp = d.keypoints||[];
    sKp.textContent    = kp.filter(v=>v!==0).length;
    latVal.textContent = lat;
    renderHands(d.manos||[]);
    renderKP(kp);
  } catch(e){ if (sendingGeneration === generation) statusText.textContent = 'Conexión interrumpida'; }
  finally{ clearTimeout(timeout); inFlight = null; sending=false; }
}

// ── Render manos ──────────────────────────────────────────────────────────
function renderHands(manos) {
  handsRow.innerHTML = '';
  if (!manos.length) {
    handsRow.innerHTML = '<div class="no-hands">✋ No se detectan manos</div>';
    return;
  }
  manos.forEach(m => {
    const icon = m.label === 'Left' ? '🤚' : '✋';
    const d = document.createElement('div');
    d.className = 'hand-chip';
    d.innerHTML = `
      <span class="icon">${icon}</span>
      <div>
        <div style="font-weight:600;font-size:.82rem">Mano ${m.label_es}</div>
        <div style="font-size:.7rem;color:var(--muted)">${m.confidence}%</div>
        <div class="conf-mini"><div class="conf-mini-fill" style="width:${m.confidence}%"></div></div>
      </div>`;
    handsRow.appendChild(d);
  });
}

// ── Render keypoints ─────────────────────────────────────────────────────────
function renderKP(kp) {
  const w = kpCanvas.offsetWidth || 300;
  kpCanvas.width  = w;
  kpCanvas.height = 46;
  kpCtx.clearRect(0, 0, w, 46);
  if (!kp.length) return;
  const bw  = Math.max(1, (w - kp.length) / kp.length);
  const mid = 23;
  const g   = kpCtx.createLinearGradient(0,0,w,0);
  g.addColorStop(0,   'rgba(59,130,246,.85)');
  g.addColorStop(.5,  'rgba(0,229,160,.85)');
  g.addColorStop(1,   'rgba(59,130,246,.85)');
  kpCtx.fillStyle = g;
  kp.forEach((v,i) => {
    const x = i*(bw+1);
    const h = Math.abs(v)*20+1;
    kpCtx.fillRect(x, mid-h/2, bw, h);
  });
}
