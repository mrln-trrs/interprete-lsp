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
const STATES = new Set(['Idle','Loading','Success','Empty','Error','Partial','Offline']);
const voiceEnabled = document.getElementById('voice-enabled');
const voiceState = document.getElementById('voice-state');
const gestureDemo = document.body.dataset.gestureDemo === 'true';
function speakConfirmed(text) {
  if (!voiceEnabled.checked || !text) return;
  const synthesis = window.speechSynthesis;
  const voices = synthesis?.getVoices().filter(candidate => candidate.localService) || [];
  const voice = voices.find(candidate => candidate.lang.toLowerCase().startsWith('es')) || voices[0];
  if (!voice) { voiceState.textContent = 'No hay voz local disponible todavía; pulsa Probar voz de nuevo'; return; }
  synthesis.cancel(); // Bound the audio queue to the most recent confirmed sentence.
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = voice; utterance.lang = voice.lang; utterance.rate = 0.9;
  utterance.onerror = () => { voiceState.textContent = 'La voz falló; el texto se conserva'; };
  synthesis.speak(utterance);
  voiceState.textContent = voice.lang.toLowerCase().startsWith('es') ? 'Voz local en español activada' : 'Voz local disponible; instala una voz española para mejorar la pronunciación';
}
window.speechSynthesis?.getVoices(); // Start asynchronous OS voice discovery.
document.getElementById('btn-test-voice').addEventListener('click', () => {
  voiceEnabled.checked = true;
  speakConfirmed('Hola');
});
voiceEnabled.addEventListener('change', () => {
  if (!voiceEnabled.checked) window.speechSynthesis?.cancel();
  voiceState.textContent = voiceEnabled.checked ? 'Voz activada para nuevas frases confirmadas' : 'Voz desactivada';
});
function setState(state, message) {
  if (!STATES.has(state)) throw new Error('Estado desconocido');
  document.body.dataset.state = state;
  if (statusText.textContent !== message) statusText.textContent = message;
}
setState('Idle', 'Preparado para iniciar');
document.getElementById('preflight').textContent =
  'Cámara: ' + (navigator.mediaDevices?.getUserMedia ? 'requiere permiso' : 'no disponible') +
  ' · Modelo: ' + (gestureDemo ? 'regla experimental de saludo' : document.body.dataset.modelReady === 'true' ? 'exploratorio' : 'no disponible') +
  ' · Arduino: futuro opcional';

async function clearText() {
  window.speechSynthesis?.cancel();
  if (sessionId) {
    try {
      const response = await fetch('/api/v1/sessions/' + sessionId + '/clear', {
        method:'POST', headers:{'Content-Type':'application/json', Authorization:'Bearer ' + sessionId},
        body:'{}', signal:AbortSignal.timeout(3000)
      });
      if (!response.ok) { setState('Partial', 'No se pudo limpiar; vuelve a intentar'); return; }
    } catch(e) { setState('Offline', 'No se pudo conectar para limpiar'); return; }
  }
  document.getElementById('confirmed-text').textContent = '—';
  document.getElementById('pending-glosses').textContent = '—';
  document.getElementById('candidate').textContent = '—';
  document.getElementById('history').replaceChildren();
  setState(stream ? 'Empty' : 'Idle', 'Salida limpiada');
}
document.getElementById('btn-clear').addEventListener('click', clearText);
window.addEventListener('keydown', event => {
  const editing = ['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName) || event.target.isContentEditable;
  if (editing) return;
  if (event.key === 'Escape') { event.preventDefault(); stopCamera(); }
  if (event.altKey && event.key.toLowerCase() === 'i') { event.preventDefault(); stream ? stopCamera() : startCamera(); }
  if (event.altKey && event.key.toLowerCase() === 'l') { event.preventDefault(); clearText(); }
});

async function stopCamera() {
  window.speechSynthesis?.cancel();
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
  setState('Idle', 'Cámara detenida');
  document.getElementById('candidate').textContent = '—';
  document.getElementById('pending-glosses').textContent = '—';
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
  if (gestureDemo && voiceEnabled.checked) speakConfirmed('Voz activada');
  starting = true;
  btnStart.disabled = true;
  setState('Loading', 'Autorizando sesión y preparando cámara');
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
    setState('Success', 'Detectando manos');
    requestAnimationFrame(() => loop(openingGeneration));
  } catch(e) {
    await stopCamera();
    setState('Error', 'No se pudo iniciar. Revisa la clave y el permiso de cámara.');
  } finally {
    starting = false;
    btnStart.disabled = false;
    if (!stream) btnStart.focus();
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
  const sendingGeneration = generation;
  const controller = new AbortController();
  inFlight = controller;
  const timeout = setTimeout(() => controller.abort(), 3000);
  try {
  const vw = video.videoWidth  || 640;
  const vh = video.videoHeight || 480;
  const sc = Math.min(1, MAX_W / vw, 720 / vh);
  capCanvas.width  = Math.round(vw * sc);
  capCanvas.height = Math.round(vh * sc);
  capCtx.drawImage(video, 0, 0, capCanvas.width, capCanvas.height);
  const dataUrl = capCanvas.toDataURL('image/jpeg', JPEG_Q);
    const r = await fetch('/api/v1/process-frame', {
      method:'POST',
      headers:{'Content-Type':'application/json', Authorization:'Bearer ' + sessionId},
      body: JSON.stringify({ frame: dataUrl, session_id:sessionId,
        frame_id:frameId++, captured_at_ms:performance.now() - sessionStart }),
      signal:controller.signal
    });
    if (!r.ok) {
      if ([401,403].includes(r.status)) { await stopCamera(); setState('Error', 'Sesión no disponible; vuelve a iniciar'); }
      else if ([429,503].includes(r.status)) { setState('Partial', 'Procesador ocupado; pausa breve'); lastSend = Date.now() + 1000; }
      else { setState('Error', 'No se pudo procesar el frame'); }
      return;
    }
    const d = (await r.json()).data;
    if (sendingGeneration !== generation) return;
    document.getElementById('pending-glosses').textContent = (d.pending_glosses || []).join(' · ') || '—';
    document.getElementById('confirmed-text').textContent = d.confirmed_text || '—';
    document.getElementById('model-state').textContent = gestureDemo ? 'Abre la mano y agítala de lado a lado 2–3 veces. Baja la mano un segundo para repetir. Regla experimental.' : d.model_available ? 'Modelo exploratorio; revisión lingüística pendiente' : 'Demo de manos: modelo no disponible';
    document.getElementById('candidate').textContent = d.prediction ?
      d.prediction.gloss + ' · ' + (d.prediction.confidence_kind === 'rule_match' ? 'patrón gestual' : Math.round(d.prediction.confidence * 100) + '%') + ' · ' + d.prediction.stable_frames + '/10' : '—';
    if (d.translation?.text) {
      speakConfirmed(d.translation.text);
      const item = document.createElement('li'); item.textContent = d.translation.text;
      const history = document.getElementById('history'); history.appendChild(item);
      while (history.children.length > 10) history.firstChild.remove();
    }
    if (!d.hands.length) setState('Empty', 'No se detectan manos');
    else if (!d.model_available) setState('Partial', 'Manos detectadas; reconocimiento pendiente de modelo');
    else if (d.translation?.status === 'Partial') setState('Partial', 'Sin plantilla disponible para estas glosas');
    else if (d.prediction?.status === 'accepted') setState('Success', 'Glosa confirmada');
    else setState('Partial', 'Esperando una predicción estable');
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
  } catch(e){ if (sendingGeneration === generation) { await stopCamera(); setState('Offline', 'Conexión interrumpida; vuelve a iniciar cuando esté disponible'); } }
  finally{ clearTimeout(timeout); if (inFlight === controller) inFlight = null; sending=false; }
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
