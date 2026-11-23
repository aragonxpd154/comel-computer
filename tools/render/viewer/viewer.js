// Visualizador 3D do COMEL (three.js)
//
// Placa COMEL (placa única): STEP exportado pelo KiCad com os modelos
// 3D dos componentes, tesselado em GLB pelo OpenCascade; as faces recebem texturas
// geradas dos Gerbers (cobre, máscara, serigrafia, furos).
// TSDA 4011R1: modelo reconstruído das fotos (docs/3d/tsda-4011r1.glb).
// Montagem: a carcaça é desenhada a partir de case/saida/carcaca.json — o mesmo
// arquivo que gera os cortes a laser.
//
// Coordenadas glTF das placas: x = x_KiCad, z = y_KiCad, y = altura (topo em 1,6 mm).
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

const T = 1.6;

function b64buf(s) {
  const bin = atob(s.slice(s.indexOf(",") + 1));
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}

async function loadGLB(loader, src) {
  const gltf = src.startsWith("data:") ? await loader.parseAsync(b64buf(src), "") : await loader.loadAsync(src);
  gltf.scene.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true; o.receiveShadow = true;
      const m = o.material;
      if (m && m.isMeshStandardMaterial) { m.roughness = Math.min(0.75, Math.max(0.35, m.roughness)); m.envMapIntensity = 0.55; }
    }
  });
  return gltf.scene;
}

async function loadBoard(b, loader, texLoader) {
  const g = new THREE.Group();
  g.add(await loadGLB(loader, b.glb));
  const face = (url, top) => {
    const tex = texLoader.load(url);
    tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
    if (!top) { tex.center.set(0.5, 0.5); tex.rotation = Math.PI; }
    const mat = new THREE.MeshStandardMaterial({
      map: tex, transparent: true, alphaTest: 0.5, roughness: 0.5, metalness: 0.0, envMapIntensity: 0.5,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(b.w, b.h), mat);
    mesh.rotation.x = top ? -Math.PI / 2 : Math.PI / 2;
    mesh.position.set(b.w / 2, top ? T + 0.015 : -0.015, b.h / 2);
    mesh.receiveShadow = true;
    return mesh;
  };
  g.add(face(b.top, true));
  g.add(face(b.bottom, false));
  return g;
}

// Tela "Commodore" para a tela de 7" da montagem
function c64Screen() {
  const c = document.createElement("canvas"); c.width = 800; c.height = 480;
  const g = c.getContext("2d");
  g.fillStyle = "#000"; g.fillRect(0, 0, 800, 480);
  g.fillStyle = "#6c5eb5"; g.fillRect(80, 0, 640, 480);
  g.fillStyle = "#352879"; g.fillRect(120, 40, 560, 400);
  g.fillStyle = "#8b7fd6"; g.font = "bold 17px 'Courier New', monospace"; g.textBaseline = "top";
  ["", "    **** COMEL 64  BASIC V2 ****", "", " 64K RAM SYSTEM  38911 BASIC BYTES FREE", "", "READY.",
   '10 PRINT "COMEL ";', "20 GOTO 10", "RUN"].forEach((l, i) => g.fillText(l, 130, 50 + i * 21));
  for (let i = 0; i < 8; i++) g.fillText("COMEL COMEL COMEL COMEL COMEL COMEL COMEL", 130, 50 + (9 + i) * 21);
  g.fillRect(130, 50 + 17 * 21, 12, 18);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function buildCase(CASE, groups) {
  const { W, D, T: CT } = CASE;
  const cwp = (X, Y, Z) => new THREE.Vector3(X - W / 2, Y, -(Z - D / 2));
  const mp = (v) => new THREE.Vector3(v[0], v[1], -v[2]);
  const g = new THREE.Group();
  const mdf = new THREE.MeshStandardMaterial({ color: 0xb07f4f, roughness: 0.85, side: THREE.DoubleSide });
  const acr = new THREE.MeshStandardMaterial({ color: 0xa9cfe0, roughness: 0.08, transparent: true, opacity: 0.14,
    side: THREE.DoubleSide, depthWrite: false });
  for (const p of CASE.pecas) {
    const sh = new THREE.Shape(p.contorno.map(([u, v]) => new THREE.Vector2(u, v)));
    for (const f of p.furos) sh.holes.push(new THREE.Path(f.map(([u, v]) => new THREE.Vector2(u, v))));
    const geo = new THREE.ExtrudeGeometry(sh, { depth: CT, bevelEnabled: false, curveSegments: 6 });
    const m4 = new THREE.Matrix4().makeBasis(mp(p.U), mp(p.V), mp(p.N)); m4.setPosition(cwp(...p.O));
    geo.applyMatrix4(m4); geo.computeVertexNormals();
    const mesh = new THREE.Mesh(geo, p.nome === "tampa" ? acr : mdf);
    mesh.castShadow = p.nome !== "tampa"; mesh.receiveShadow = true; mesh.renderOrder = p.nome === "tampa" ? 5 : 0;
    g.add(mesh);
  }
  const yP = CASE.yPlaca;
  // COMEL: borda y = 0 (conectores) para trás, sem rotação
  const cb = groups.comel.clone(); cb.position.set(CASE.comelX0 - W / 2, yP, -(CASE.zBorda - D / 2)); g.add(cb);
  // TSDA 4011R1 (modelo centrado; girada 180° com o RJ-45 e o DB9 para trás)
  if (groups.tsda) {
    const t = groups.tsda.clone(); t.rotation.y = Math.PI;
    t.position.set(CASE.tsdaX0 - W / 2 - 41.5, yP, -(CASE.zBorda - 47 - D / 2) - 23.5); g.add(t);
  }
  // fonte Mean Well RD-35A — a única coisa fora da placa
  const F = CASE.fonte;
  const psu = new THREE.Mesh(new THREE.BoxGeometry(F.L, 35, F.P),
    new THREE.MeshStandardMaterial({ color: 0xb6babd, metalness: 0.7, roughness: 0.4 }));
  psu.position.copy(cwp(F.x0 + F.L / 2, CT + 17.5, F.z0 + F.P / 2)); psu.castShadow = true; g.add(psu);
  // tela de 7" atrás da moldura, no painel inclinado
  const A = CASE.ang * Math.PI / 180, ca = Math.cos(A), sa = Math.sin(A);
  const tv = CASE.tela.v, tt = CT + 2.9;               // centro da tela: ao longo da inclinação e para dentro
  const scr = new THREE.Group();
  scr.position.copy(cwp(CASE.tela.cx, CASE.lip + tv * ca - tt * sa, tv * sa + tt * ca));
  scr.rotation.x = -A; g.add(scr);
  const frame = new THREE.Mesh(new THREE.BoxGeometry(165, 100, 5.7), new THREE.MeshStandardMaterial({ color: 0x1b1d20, roughness: 0.5 }));
  scr.add(frame);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(154.2, 85.9), new THREE.MeshBasicMaterial({ map: c64Screen() }));
  glass.position.z = 2.9; scr.add(glass);
  const drv = new THREE.Mesh(new THREE.BoxGeometry(100, 60, 8), new THREE.MeshStandardMaterial({ color: 0x18652f, roughness: 0.6 }));
  drv.position.set(8, 8, -12.5); scr.add(drv);
  // módulo IEC no painel traseiro
  const iec = new THREE.Mesh(new THREE.BoxGeometry(47.5, 27.5, 26), new THREE.MeshStandardMaterial({ color: 0x151515, roughness: 0.5 }));
  iec.position.copy(cwp(CASE.iec.X, CASE.iec.Y, D - CT - 13)); g.add(iec);
  return g;
}

export async function createViewer(container, boards, opts = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(opts.pixelRatio || Math.min(2, window.devicePixelRatio || 1));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(30, container.clientWidth / container.clientHeight, 1, 4000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.08;

  const sun = new THREE.DirectionalLight(0xffffff, 1.25);
  sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 6; sun.shadow.bias = -0.0004;
  scene.add(sun);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x445566, 0.25));
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200), new THREE.ShadowMaterial({ opacity: 0.22 }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);

  const loader = new GLTFLoader();
  const texLoader = new THREE.TextureLoader();
  const groups = {};
  for (const b of boards.pcbs) groups[b.id] = await loadBoard(b, loader, texLoader);
  if (boards.tsda) groups.tsda = await loadGLB(loader, boards.tsda);
  groups.assembly = boards.case ? buildCase(boards.case, groups) : new THREE.Group();

  const VIEWS = {
    comel: { group: "comel", target: [66, 1, 32], pos: [-10, 105, 175], ground: -9, s: 150 },
    "comel-top": { group: "comel", target: [66, 0, 32], pos: [66, 205, 32.01], ground: -9, up: [0, 0, -1], s: 150 },
    "comel-bottom": { group: "comel", target: [66, 0, 32], pos: [66, -205, 32.01], ground: -300, up: [0, 0, -1], s: 150 },
    assembly: { group: "assembly", target: [0, 40, 0], pos: [300, 330, 420], ground: 0, s: 260 },
    "assembly-back": { group: "assembly", target: [0, 40, 0], pos: [-260, 260, -430], ground: 0, s: 260 },
  };

  let current = null;
  function show(name) {
    const v = VIEWS[name];
    if (current) scene.remove(current);
    current = groups[v.group];
    scene.add(current);
    controls.target.set(...v.target);
    camera.position.set(...v.pos);
    camera.up.set(...(v.up || [0, 1, 0]));
    ground.position.y = v.ground;
    sun.position.set(v.target[0] - v.s * 0.6, v.s * 1.4, v.target[2] + v.s * 0.8);
    sun.target.position.set(...v.target); scene.add(sun.target);
    const sc = sun.shadow.camera;
    sc.left = -v.s; sc.right = v.s; sc.top = v.s; sc.bottom = -v.s; sc.near = 1; sc.far = v.s * 5;
    sc.updateProjectionMatrix();
    controls.update();
  }

  function resize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", resize);
  renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });

  return {
    show, resize, renderer,
    stop: () => renderer.setAnimationLoop(null),
    renderOnce: () => { controls.update(); renderer.render(scene, camera); },
  };
}

window.COMEL3D = { createViewer };
