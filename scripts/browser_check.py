"""Generate a browser harness using synthetic camera/network, never real permissions."""
import ast
from pathlib import Path
import shutil

HARNESS = r"""
<script>
window.requestAnimationFrame = () => 0;
let fixtureStopped = 0;
Object.defineProperty(navigator, 'mediaDevices', {configurable:true, value:{
  getUserMedia: async () => ({getTracks: () => [{stop: () => fixtureStopped++}]})
}});
let fixtureFetches = [];
window.fetch = async (url, options={}) => {
  fixtureFetches.push({url, method:options.method, body:options.body});
  if (url === '/api/v1/sessions') return {ok:true,status:201,json:async()=>({data:{session_id:'test-only-session-id-000000000000'}})};
  if (options.method === 'DELETE' || url.endsWith('/clear')) return {ok:true,status:204};
  return {ok:true,status:200,json:async()=>({data:{frame:'',hands:[],keypoints:Array(126).fill(0),
    model_available:false,pending_glosses:[],confirmed_text:'',prediction:null,translation:null}})};
};
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
    document.getElementById('access-key').value = 'TEST-ONLY-ACCESS-KEY';
    await startCamera();
    check('start authorized session before camera', fixtureFetches[0].url === '/api/v1/sessions' && stream !== null);
    await send();
    check('empty frame is not translation', document.body.dataset.state === 'Empty' && document.getElementById('confirmed-text').textContent === '—');
    const frameRequest = fixtureFetches.find(call=>call.url.includes('process-frame'));
    check('v1 frame contract', JSON.parse(frameRequest.body).frame_id === 0);
    document.getElementById('confirmed-text').textContent = 'Fixture confirmed text';
    await stopCamera();
    check('stop releases tracks and preserves confirmed', fixtureStopped === 1 && document.getElementById('confirmed-text').textContent === 'Fixture confirmed text');
    await clearText();
    check('clear explicit', document.getElementById('confirmed-text').textContent === '—');
    const shift = {cls:0};
    new PerformanceObserver(list=>{ for (const entry of list.getEntries()) if (!entry.hadRecentInput) shift.cls += entry.value; }).observe({type:'layout-shift',buffered:true});
    setTimeout(()=>{
      const output = document.createElement('pre'); output.id='browser-results';
      output.textContent=JSON.stringify({results,cls:shift.cls,fixture:true}); document.body.appendChild(output);
    }, 250);
  } catch(error) {
    const output = document.createElement('pre'); output.id='browser-results';
    output.textContent=JSON.stringify({results,error:String(error),fixture:true}); document.body.appendChild(output);
  }
});
</script>
"""


def main():
    source = ast.parse(Path("web_server.py").read_text(encoding="utf-8"))
    assignment = next(node for node in source.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "_HTML" for target in node.targets))
    html = ast.literal_eval(assignment.value).replace("{{ 'true' if model_ready else 'false' }}", "false")
    html = html.replace('<script src="/static/app.js" defer></script>', HARNESS + '<script src="/static/app.js" defer></script>')
    folder = Path(".tools/browser-preview")
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copytree("static", folder / "static", dirs_exist_ok=True)
    (folder / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
