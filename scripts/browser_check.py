"""Generate a browser harness using synthetic camera/network, never real permissions."""
import ast
from pathlib import Path
import shutil

HARNESS = r"""
<script>
window.requestAnimationFrame = () => 0;
let fixtureStopped = 0;
Object.defineProperty(navigator, 'mediaDevices', {configurable:true, value:{
  getUserMedia: async () => Object.assign(new MediaStream(), {
    getTracks: () => [{stop: () => fixtureStopped++}]
  })
}});
let fixtureFetches = [];
let fixtureFrame = null; // Respuesta de frame configurable por cada check
const emptyFrame = () => ({frame:'',hands:[],keypoints:Array(126).fill(0),
  model_available:false,pending_glosses:[],confirmed_text:'',prediction:null,translation:null});
window.fetch = async (url, options={}) => {
  fixtureFetches.push({url, method:options.method, body:options.body, headers:options.headers});
  if (url === '/api/v1/sessions') return {ok:true,status:201,json:async()=>({data:{session_id:'test-only-session-id-000000000000'}})};
  if (options.method === 'DELETE' || url.endsWith('/clear')) return {ok:true,status:204};
  return {ok:true,status:200,json:async()=>({data:fixtureFrame || emptyFrame()})};
};
// Voz sintética: registra speak/cancel sin reproducir audio.
const fixtureSpeech = {spoken:[], cancels:0, failNext:false};
window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
Object.defineProperty(window, 'speechSynthesis', {configurable:true, value:{
  getVoices: () => [{lang:'es-PE', localService:true, name:'fixture'}],
  speak: utterance => {
    if (fixtureSpeech.failNext) { fixtureSpeech.failNext = false; throw new Error('fixture voice failure'); }
    fixtureSpeech.spoken.push(utterance.text);
  },
  cancel: () => { fixtureSpeech.cancels++; }
}});
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const press = (key, alt=false, target=window) => target.dispatchEvent(new KeyboardEvent('keydown', {key, altKey:alt, bubbles:true, cancelable:true}));
window.addEventListener('DOMContentLoaded', async () => {
  const results = [];
  const check = (name, value) => { results.push({name,pass:Boolean(value)}); if (!value) throw new Error(name); };
  try {
    video.play = async () => {};
    Object.defineProperty(video, 'readyState', {get:()=>2});
    Object.defineProperty(video, 'videoWidth', {get:()=>640});
    Object.defineProperty(video, 'videoHeight', {get:()=>480});
    capCtx.drawImage = () => {};
    check('initial idle', document.body.dataset.state === 'Idle');
    for (const state of ['Idle','Loading','Success','Empty','Error','Partial','Offline']) setState(state, state);
    check('seven states supported', document.body.dataset.state === 'Offline');
    const keyField = document.getElementById('access-key');
    if (keyField) keyField.value = 'TEST-ONLY-ACCESS-KEY';
    await startCamera();
    check('start authorized session before camera', fixtureFetches[0].url === '/api/v1/sessions' && stream !== null);
    const sentAuthorization = Boolean(fixtureFetches[0].headers && fixtureFetches[0].headers.Authorization);
    check(keyField ? 'key sent when required' : 'no key field and no key sent', sentAuthorization === Boolean(keyField));
    await send();
    check('empty frame is not translation', document.body.dataset.state === 'Empty' && document.getElementById('confirmed-text').textContent === '—');
    const frameRequest = fixtureFetches.find(call=>call.url.includes('process-frame'));
    check('v1 frame contract', JSON.parse(frameRequest.body).frame_id === 0);
    document.getElementById('confirmed-text').textContent = 'Fixture confirmed text';
    await stopCamera();
    check('stop releases tracks and preserves confirmed', fixtureStopped === 1 && document.getElementById('confirmed-text').textContent === 'Fixture confirmed text');
    await clearText();
    check('clear explicit', document.getElementById('confirmed-text').textContent === '—');

    // Teclado: Alt+I inicia/detiene, Esc detiene, Alt+L limpia; nada se dispara al escribir en un campo.
    press('i', true); await pause(50);
    check('Alt+I starts camera', stream !== null);
    press('Escape'); await pause(50);
    check('Esc stops camera', stream === null && fixtureStopped === 2);
    document.getElementById('confirmed-text').textContent = 'Texto por limpiar';
    const field = document.createElement('input'); document.body.appendChild(field);
    press('l', true, field); await pause(50);
    check('shortcuts ignored while typing', document.getElementById('confirmed-text').textContent === 'Texto por limpiar');
    field.remove();
    press('l', true); await pause(50);
    check('Alt+L clears', document.getElementById('confirmed-text').textContent === '—');
    const unnamed = [...document.querySelectorAll('button, input, select')].filter(el =>
      !(el.getAttribute('aria-label') || el.textContent.trim() || el.labels?.length || el.title));
    check('controls have accessible names', unnamed.length === 0);

    // Voz: candidatos no hablan; solo texto confirmado, una frase vigente (cancel antes de speak).
    await startCamera();
    const voice = document.getElementById('voice-enabled');
    voice.checked = true; voice.dispatchEvent(new Event('change'));
    const accepted = {gloss:'HOLA', confidence:0.95, stable_frames:10, status:'accepted', accepted_gloss:'HOLA'};
    fixtureFrame = {...emptyFrame(), hands:[{side:'Right',confidence:0.9}], model_available:true,
      prediction:{...accepted, status:'candidate', stable_frames:4}};
    await send();
    check('candidate is not spoken', fixtureSpeech.spoken.length === 0);
    fixtureFrame = {...fixtureFrame, prediction:accepted, confirmed_text:'Hola.', translation:{text:'Hola.', status:'Success'}};
    let cancelsBefore = fixtureSpeech.cancels;
    await send();
    check('confirmed text spoken once', fixtureSpeech.spoken.join('|') === 'Hola.' && fixtureSpeech.cancels > cancelsBefore);
    check('history keeps confirmed text', document.getElementById('history').children.length === 1);
    fixtureSpeech.failNext = true;
    fixtureFrame = {...fixtureFrame, confirmed_text:'Buenos días.', translation:{text:'Buenos días.', status:'Success'}};
    await send();
    check('voice failure keeps camera and text', stream !== null && document.body.dataset.state === 'Success' &&
      document.getElementById('confirmed-text').textContent === 'Buenos días.' &&
      document.getElementById('voice-state').textContent === 'La voz falló; el texto se conserva');
    voice.checked = false; voice.dispatchEvent(new Event('change'));
    fixtureFrame = {...fixtureFrame, confirmed_text:'Gracias.', translation:{text:'Gracias.', status:'Success'}};
    await send();
    check('voice off keeps text silent', fixtureSpeech.spoken.length === 1 && document.getElementById('confirmed-text').textContent === 'Gracias.');
    cancelsBefore = fixtureSpeech.cancels;
    await stopCamera();
    check('stop cancels voice and keeps text', fixtureSpeech.cancels > cancelsBefore && document.getElementById('confirmed-text').textContent === 'Gracias.');
    check('no horizontal overflow', document.documentElement.scrollWidth <= window.innerWidth);
    const shift = {cls:0};
    new PerformanceObserver(list=>{ for (const entry of list.getEntries()) if (!entry.hadRecentInput) shift.cls += entry.value; }).observe({type:'layout-shift',buffered:true});
    setTimeout(()=>{
      const output = document.createElement('pre'); output.id='browser-results';
      output.textContent=JSON.stringify({results,cls:shift.cls,viewport:[window.innerWidth,window.innerHeight],fixture:true}); document.body.appendChild(output);
    }, 250);
  } catch(error) {
    const output = document.createElement('pre'); output.id='browser-results';
    output.textContent=JSON.stringify({results,error:String(error),speech:fixtureSpeech,state:statusText.textContent,
      viewport:[window.innerWidth, document.documentElement.scrollWidth],
      wide:[...document.querySelectorAll('body *')].filter(el => el.getBoundingClientRect().right > window.innerWidth + 0.5)
        .slice(0, 8).map(el => (el.id || el.className || el.tagName) + ':' + Math.round(el.getBoundingClientRect().width)),
      fixture:true}); document.body.appendChild(output);
  }
});
</script>
"""

MOBILE_VIEWPORTS = ((390, 844), (320, 640))
MOBILE_WRAPPER = """<!DOCTYPE html><html><body style="margin:0">
<iframe id="device" src="index.html" width="{width}" height="{height}" style="border:0"></iframe>
<script>
const copy = setInterval(() => {{
  const inner = document.getElementById('device').contentDocument?.getElementById('browser-results');
  if (!inner) return;
  clearInterval(copy);
  const output = document.createElement('pre'); output.id = 'browser-results';
  output.textContent = inner.textContent; document.body.appendChild(output);
}}, 50);
</script></body></html>"""


def main(key_required=True):
    source = ast.parse(Path("web_server.py").read_text(encoding="utf-8"))
    assignment = next(node for node in source.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "_HTML" for target in node.targets))
    # Se renderiza como Flask para que los bloques {% if %} no queden literales.
    from jinja2 import Template
    html = Template(ast.literal_eval(assignment.value)).render(model_ready=False, gesture_demo=False, key_required=key_required)
    html = html.replace('<script src="/static/app.js" defer></script>', HARNESS + '<script src="/static/app.js" defer></script>')
    folder = Path(".tools/browser-preview" + ("" if key_required else "-sin-clave"))
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copytree("static", folder / "static", dirs_exist_ok=True)
    (folder / "index.html").write_text(html, encoding="utf-8")
    # Edge sin ventana no baja de ~500 px; el iframe da un viewport real de celular.
    for width, height in MOBILE_VIEWPORTS:
        (folder / f"mobile-{width}.html").write_text(MOBILE_WRAPPER.format(width=width, height=height), encoding="utf-8")


if __name__ == "__main__":
    import sys
    main(key_required="--sin-clave" not in sys.argv)
