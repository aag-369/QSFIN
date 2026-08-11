"""
Builds a self-contained HTML digital-twin viewer by embedding the scene's
render JSON directly into the page (avoids fetch/CORS issues when opened
as a local file). Run after twin.py has produced scene_render.json.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>QSFIN Digital Twin Viewer — __CASE_ID__</title>
<style>
  html, body { margin:0; padding:0; height:100%; background:#0b0e14; font-family: -apple-system, Segoe UI, Roboto, sans-serif; color:#e8ecf1; overflow:hidden; }
  #canvas-wrap { position:absolute; inset:0; }
  #hud { position:absolute; top:0; left:0; padding:16px 20px; pointer-events:none; }
  #hud h1 { font-size:15px; margin:0 0 4px 0; font-weight:600; letter-spacing:.02em; color:#fff;}
  #hud p { font-size:12px; margin:0; color:#8fa0b8; }
  #legend { position:absolute; top:16px; right:16px; background:rgba(15,19,28,.85); border:1px solid #202836; border-radius:10px; padding:12px 14px; font-size:12px; backdrop-filter: blur(6px);}
  #legend .row { display:flex; align-items:center; gap:8px; margin:4px 0;}
  #legend .sw { width:10px; height:10px; border-radius:3px; flex:none;}
  #panel { position:absolute; bottom:16px; left:16px; right:16px; max-width:420px; background:rgba(15,19,28,.92); border:1px solid #202836; border-radius:12px; padding:14px 16px; font-size:12.5px; display:none; line-height:1.5;}
  #panel h2 { font-size:13px; margin:0 0 6px 0; color:#fff; }
  #panel .k { color:#8fa0b8; }
  #panel .coc { margin-top:8px; padding-top:8px; border-top:1px solid #202836; }
  #hint { position:absolute; bottom:16px; right:16px; font-size:11px; color:#5c6b82; }
</style>
</head>
<body>
<div id="canvas-wrap"></div>
<div id="hud">
  <h1>QSFIN Digital Twin — __TITLE__</h1>
  <p>Case __CASE_ID__ · drag to orbit, scroll to zoom, click a marker for evidence detail</p>
</div>
<div id="legend"></div>
<div id="panel"></div>
<div id="hint">Simulated scan (LiDAR + photogrammetry placeholder) — synthetic demo data</div>

<script>__THREE_JS__</script>
<script>
const SCENE_DATA = __SCENE_JSON__;

const wrap = document.getElementById('canvas-wrap');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0e14);
scene.fog = new THREE.Fog(0x0b0e14, 15, 40);

const camera = new THREE.PerspectiveCamera(50, window.innerWidth/window.innerHeight, 0.1, 100);
camera.position.set(8, 7, 10);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
wrap.appendChild(renderer.domElement);

// Lighting
scene.add(new THREE.AmbientLight(0x8899aa, 0.9));
const dl = new THREE.DirectionalLight(0xffffff, 0.6);
dl.position.set(6,10,4);
scene.add(dl);

// Floor grid
const grid = new THREE.GridHelper(20, 40, 0x2a3446, 0x1a2130);
scene.add(grid);

// Simple orbit control (no external dep): drag to rotate, wheel to zoom
let isDown=false, lastX=0, lastY=0, theta=0.6, phi=1.0, radius=13;
function updateCamera(){
  camera.position.x = radius * Math.sin(phi) * Math.cos(theta);
  camera.position.z = radius * Math.sin(phi) * Math.sin(theta);
  camera.position.y = radius * Math.cos(phi);
  camera.lookAt(4,1.5,2);
}
renderer.domElement.addEventListener('mousedown', e=>{isDown=true; lastX=e.clientX; lastY=e.clientY;});
window.addEventListener('mouseup', ()=>isDown=false);
window.addEventListener('mousemove', e=>{
  if(!isDown) return;
  theta -= (e.clientX-lastX)*0.008;
  phi = Math.min(Math.max(phi - (e.clientY-lastY)*0.008, 0.2), 1.5);
  lastX=e.clientX; lastY=e.clientY;
  updateCamera();
});
renderer.domElement.addEventListener('wheel', e=>{
  radius = Math.min(Math.max(radius + e.deltaY*0.01, 4), 30);
  updateCamera();
});
updateCamera();

// Build rooms as translucent boxes
SCENE_DATA.rooms.forEach(r=>{
  const [w,d,h] = r.dimensions_m;
  const geo = new THREE.BoxGeometry(w, h, d);
  const mat = new THREE.MeshBasicMaterial({color:0x1b2536, transparent:true, opacity:0.18, wireframe:false});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(r.origin[0]+w/2, h/2, r.origin[1]+d/2);
  scene.add(mesh);
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({color:0x3a4a63}));
  edges.position.copy(mesh.position);
  scene.add(edges);

  // room label sprite (simple text via canvas)
  const label = makeLabel(r.room_id.replace('_',' '));
  label.position.set(r.origin[0]+0.3, 0.05, r.origin[1]+0.3);
  scene.add(label);
});

function makeLabel(text){
  const c = document.createElement('canvas'); c.width=256; c.height=64;
  const ctx = c.getContext('2d');
  ctx.fillStyle='rgba(0,0,0,0)'; ctx.fillRect(0,0,256,64);
  ctx.font='28px sans-serif'; ctx.fillStyle='#5c6b82';
  ctx.fillText(text, 4, 40);
  const tex = new THREE.CanvasTexture(c);
  const mat = new THREE.SpriteMaterial({map:tex, transparent:true});
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(2,0.5,1);
  sprite.rotation.x = -Math.PI/2;
  return sprite;
}

// Evidence markers
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const markerMeshes = [];

SCENE_DATA.evidence.forEach(ev=>{
  const geo = new THREE.SphereGeometry(0.12, 16, 16);
  const mat = new THREE.MeshStandardMaterial({color: new THREE.Color(ev.color), emissive: new THREE.Color(ev.color), emissiveIntensity:0.5});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(ev.position[0], ev.position[2]+0.12, ev.position[1]);
  mesh.userData = ev;
  scene.add(mesh);
  markerMeshes.push(mesh);

  // pulsing ring
  const ringGeo = new THREE.RingGeometry(0.18, 0.22, 24);
  const ringMat = new THREE.MeshBasicMaterial({color: new THREE.Color(ev.color), side: THREE.DoubleSide, transparent:true, opacity:0.6});
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.position.set(ev.position[0], 0.02, ev.position[1]);
  ring.rotation.x = -Math.PI/2;
  scene.add(ring);
});

// Trajectories
SCENE_DATA.trajectories.forEach(t=>{
  const pts = [
    new THREE.Vector3(t.from[0], t.from[2]+0.12, t.from[1]),
    new THREE.Vector3(t.to[0], t.to[2]+0.12, t.to[1]),
  ];
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  const mat = new THREE.LineDashedMaterial({color:0xffffff, dashSize:0.15, gapSize:0.08, transparent:true, opacity:0.7});
  const line = new THREE.Line(geo, mat);
  line.computeLineDistances();
  scene.add(line);
});

// Legend
const legendEl = document.getElementById('legend');
const seen = {};
SCENE_DATA.evidence.forEach(ev=>{ seen[ev.type]=ev.color; });
Object.entries(seen).forEach(([type,color])=>{
  const row = document.createElement('div'); row.className='row';
  row.innerHTML = `<div class="sw" style="background:${color}"></div><div>${type.replace('_',' ')}</div>`;
  legendEl.appendChild(row);
});

// Click detection
const panel = document.getElementById('panel');
renderer.domElement.addEventListener('click', (e)=>{
  mouse.x = (e.clientX/window.innerWidth)*2-1;
  mouse.y = -(e.clientY/window.innerHeight)*2+1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(markerMeshes);
  if(hits.length){
    const ev = hits[0].object.userData;
    panel.style.display='block';
    panel.innerHTML = `<h2>${ev.evidence_id} — ${ev.type.replace('_',' ')}</h2>
      <div><span class="k">Room:</span> ${ev.room.replace('_',' ')}</div>
      <div><span class="k">Description:</span> ${ev.description}</div>
      <div class="coc"><span class="k">Chain of custody:</span><br>${ev.chain_of_custody.join(' → ')}</div>`;
  } else {
    panel.style.display='none';
  }
});

window.addEventListener('resize', ()=>{
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

function animate(){
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();
</script>
</body>
</html>
"""

def render_html(scene_json: dict, three_js: str) -> str:
    """Reusable renderer: fills the viewer TEMPLATE for a given scene. Used
    both to write the standalone scene_viewer.html AND to embed the same
    viewer inside the dashboard's Digital Twin tab (via iframe.srcdoc), so
    there is exactly one implementation of the 3D viewer to maintain."""
    # Defensive escaping of "</script"/"<!--" in case any embedded string
    # (evidence descriptions etc.) ever contains it — see build_dashboard.py
    # for why this matters when embedding HTML/JSON inside a <script> block.
    scene_json_str = json.dumps(scene_json).replace("</script", "<\\/script").replace("<!--", "<\\!--")
    return (TEMPLATE
            .replace("__CASE_ID__", scene_json["case_id"])
            .replace("__TITLE__", scene_json["title"])
            .replace("__THREE_JS__", three_js)
            .replace("__SCENE_JSON__", scene_json_str))


def load_three_js() -> str:
    with open(HERE.parent / "assets" / "three.min.js") as f:
        return f.read()


def build():
    with open(HERE / "scene_render.json") as f:
        scene_json = json.load(f)
    html = render_html(scene_json, load_three_js())
    out_path = HERE / "scene_viewer.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Built viewer -> {out_path}")

if __name__ == "__main__":
    build()
