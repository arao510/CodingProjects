// ============================================================
// BlockyAnimal.js — Koala + REAL 3D + diffuse lighting + rubric
// ============================================================

// ================= GLOBALS =================
let canvas;
let gl;

let a_Position;
let a_Normal;
let u_FragColor;
let u_ModelMatrix;
let u_GlobalRotateMatrix;
let u_ViewProjMatrix;

// UI-controlled globals
let gAnimalGlobalRotation = 0;
let g_leftHipAngle = 0;
let g_leftKneeAngle = 0;
let g_leftAnkleAngle = 0;

// Time / animation
let g_seconds = 0;
let g_animationOn = false;

// Extra animation state
let g_headBob = 0;
let g_armSwing = 0;
let g_bodySway = 0;

// FPS indicator (multi-frame)
let g_lastFPSTime = performance.now();
let g_frameCount = 0;
let g_fps = 0;

// -------- Mouse rotate --------
let g_mouseDown = false;
let g_lastMouseX = 0;
let g_lastMouseY = 0;
let g_mouseRotX = 0;
let g_mouseRotY = 0;

// -------- Poke animation --------
let g_pokeActive = false;
let g_pokeStartTime = 0;

// -------- Non-cube primitive: pyramid VBO --------
let g_pyrVBO = null;
let g_pyrVertCount = 0;

// -------- Sphere VBO --------
let g_sphereVBO = null;
let g_sphereVertCount = 0;

// ================= SHADERS =================
const VSHADER_SOURCE = `
attribute vec4 a_Position;
attribute vec3 a_Normal;
uniform mat4 u_ModelMatrix;
uniform mat4 u_GlobalRotateMatrix;
uniform mat4 u_ViewProjMatrix;

varying vec3 v_Normal;

void main() {
  gl_Position = u_ViewProjMatrix * u_GlobalRotateMatrix * u_ModelMatrix * a_Position;
  v_Normal = normalize((u_GlobalRotateMatrix * u_ModelMatrix * vec4(a_Normal, 0.0)).xyz);
}
`;

const FSHADER_SOURCE = `
precision mediump float;
uniform vec4 u_FragColor;
varying vec3 v_Normal;

void main() {
  vec3 lightDir = normalize(vec3(0.4, 1.0, 1.2));
  float diff = max(dot(v_Normal, lightDir), 0.0);
  float ambient = 0.28;
  float light = ambient + (1.0 - ambient) * diff;
  gl_FragColor = vec4(u_FragColor.rgb * light, u_FragColor.a);
}
`;

// ================= WEBGL SETUP =================
function setupWebGL() {
  canvas = document.getElementById('webgl');
  gl = canvas.getContext('webgl');
  if (!gl) { console.log('WebGL failed'); return; }
  gl.clearColor(0.0, 0.0, 0.0, 1.0);
  gl.enable(gl.DEPTH_TEST);
}

function connectVariablesToGLSL() {
  if (!initShaders(gl, VSHADER_SOURCE, FSHADER_SOURCE)) {
    console.log('Failed to init shaders.');
    return;
  }

  a_Position = gl.getAttribLocation(gl.program, 'a_Position');
  a_Normal   = gl.getAttribLocation(gl.program, 'a_Normal');
  u_FragColor = gl.getUniformLocation(gl.program, 'u_FragColor');
  u_ModelMatrix = gl.getUniformLocation(gl.program, 'u_ModelMatrix');
  u_GlobalRotateMatrix = gl.getUniformLocation(gl.program, 'u_GlobalRotateMatrix');
  u_ViewProjMatrix = gl.getUniformLocation(gl.program, 'u_ViewProjMatrix');

  const identity = new Matrix4();
  gl.uniformMatrix4fv(u_ModelMatrix, false, identity.elements);
}

// ================= RUBRIC: drawCube(Matrix M) =================
function drawCube(M, color = [1, 1, 1, 1]) {
  const c = new Cube();
  c.color = color;
  c.matrix = new Matrix4(M);
  c.render();
}

// ================= SPHERE (with normals) =================
function initSphereBuffer(latBands, lonBands) {
  latBands = latBands || 24;
  lonBands = lonBands || 24;
  const verts = [];
  const r = 0.5;

  for (let lat = 0; lat < latBands; lat++) {
    const theta1 = (lat / latBands) * Math.PI;
    const theta2 = ((lat + 1) / latBands) * Math.PI;
    const sinT1 = Math.sin(theta1), cosT1 = Math.cos(theta1);
    const sinT2 = Math.sin(theta2), cosT2 = Math.cos(theta2);

    for (let lon = 0; lon < lonBands; lon++) {
      const phi1 = (lon / lonBands) * Math.PI * 2;
      const phi2 = ((lon + 1) / lonBands) * Math.PI * 2;
      const sinP1 = Math.sin(phi1), cosP1 = Math.cos(phi1);
      const sinP2 = Math.sin(phi2), cosP2 = Math.cos(phi2);

      const p00 = [r*sinT1*cosP1, r*cosT1, r*sinT1*sinP1];
      const p10 = [r*sinT1*cosP2, r*cosT1, r*sinT1*sinP2];
      const p01 = [r*sinT2*cosP1, r*cosT2, r*sinT2*sinP1];
      const p11 = [r*sinT2*cosP2, r*cosT2, r*sinT2*sinP2];

      // normals = pos * 2 (radius=0.5 so *2 normalizes)
      const n00 = [p00[0]*2, p00[1]*2, p00[2]*2];
      const n10 = [p10[0]*2, p10[1]*2, p10[2]*2];
      const n01 = [p01[0]*2, p01[1]*2, p01[2]*2];
      const n11 = [p11[0]*2, p11[1]*2, p11[2]*2];

      verts.push(p00[0],p00[1],p00[2], n00[0],n00[1],n00[2]);
      verts.push(p10[0],p10[1],p10[2], n10[0],n10[1],n10[2]);
      verts.push(p01[0],p01[1],p01[2], n01[0],n01[1],n01[2]);

      verts.push(p10[0],p10[1],p10[2], n10[0],n10[1],n10[2]);
      verts.push(p11[0],p11[1],p11[2], n11[0],n11[1],n11[2]);
      verts.push(p01[0],p01[1],p01[2], n01[0],n01[1],n01[2]);
    }
  }

  const v = new Float32Array(verts);
  g_sphereVertCount = v.length / 6;

  g_sphereVBO = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, g_sphereVBO);
  gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW);
}

function drawSphere(M, color) {
  color = color || [1,1,1,1];
  gl.uniform4f(u_FragColor, color[0], color[1], color[2], color[3]);
  gl.uniformMatrix4fv(u_ModelMatrix, false, M.elements);

  gl.bindBuffer(gl.ARRAY_BUFFER, g_sphereVBO);
  gl.vertexAttribPointer(a_Position, 3, gl.FLOAT, false, 24, 0);
  gl.enableVertexAttribArray(a_Position);
  gl.vertexAttribPointer(a_Normal, 3, gl.FLOAT, false, 24, 12);
  gl.enableVertexAttribArray(a_Normal);

  gl.drawArrays(gl.TRIANGLES, 0, g_sphereVertCount);
}

// ================= NON-CUBE: PYRAMID (with normals) =================
function initPyramidBuffer() {
  // Approximate outward face normals (normalized)
  var nF  = [ 0,  0.447, -0.894];
  var nR  = [ 0.894, 0.447,  0];
  var nB  = [ 0,  0.447,  0.894];
  var nL  = [-0.894, 0.447,  0];
  var nD  = [ 0, -1, 0];

  var v = new Float32Array([
    // Front face
    0,0,0, nF[0],nF[1],nF[2],   1,0,0, nF[0],nF[1],nF[2],   0.5,1,0.5, nF[0],nF[1],nF[2],
    // Right face
    1,0,0, nR[0],nR[1],nR[2],   1,0,1, nR[0],nR[1],nR[2],   0.5,1,0.5, nR[0],nR[1],nR[2],
    // Back face
    1,0,1, nB[0],nB[1],nB[2],   0,0,1, nB[0],nB[1],nB[2],   0.5,1,0.5, nB[0],nB[1],nB[2],
    // Left face
    0,0,1, nL[0],nL[1],nL[2],   0,0,0, nL[0],nL[1],nL[2],   0.5,1,0.5, nL[0],nL[1],nL[2],
    // Base tri 1
    0,0,0, nD[0],nD[1],nD[2],   1,0,1, nD[0],nD[1],nD[2],   1,0,0, nD[0],nD[1],nD[2],
    // Base tri 2
    0,0,0, nD[0],nD[1],nD[2],   0,0,1, nD[0],nD[1],nD[2],   1,0,1, nD[0],nD[1],nD[2]
  ]);

  g_pyrVertCount = 18;
  g_pyrVBO = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, g_pyrVBO);
  gl.bufferData(gl.ARRAY_BUFFER, v, gl.STATIC_DRAW);
}

function drawPyramid(M, color) {
  color = color || [1,1,1,1];
  gl.uniform4f(u_FragColor, color[0], color[1], color[2], color[3]);
  gl.uniformMatrix4fv(u_ModelMatrix, false, M.elements);

  gl.bindBuffer(gl.ARRAY_BUFFER, g_pyrVBO);
  gl.vertexAttribPointer(a_Position, 3, gl.FLOAT, false, 24, 0);
  gl.enableVertexAttribArray(a_Position);
  gl.vertexAttribPointer(a_Normal, 3, gl.FLOAT, false, 24, 12);
  gl.enableVertexAttribArray(a_Normal);

  gl.drawArrays(gl.TRIANGLES, 0, g_pyrVertCount);
}

// ================= UI =================
function addActionsForHtmlUI() {
  function hookSlider(id, setter) {
    var el = document.getElementById(id);
    if (!el) { console.error("Missing element id:", id); return; }
    el.addEventListener('input', function () { setter(+this.value); });
  }
  function hookButton(id, handler) {
    var el = document.getElementById(id);
    if (!el) { console.error("Missing element id:", id); return; }
    el.onclick = handler;
  }

  hookSlider('angleSlide', function(v){ gAnimalGlobalRotation = v; });
  hookSlider('leftHipSlide', function(v){ g_leftHipAngle = v; });
  hookSlider('leftKneeSlide', function(v){ g_leftKneeAngle = v; });
  hookSlider('leftAnkleSlide', function(v){ g_leftAnkleAngle = v; });

  hookButton('animOn', function(){ g_animationOn = true; });
  hookButton('animOff', function(){ g_animationOn = false; });

  canvas = document.getElementById('webgl');

  canvas.addEventListener('mousedown', function(ev) {
    g_mouseDown = true;
    g_lastMouseX = ev.clientX;
    g_lastMouseY = ev.clientY;
  });
  canvas.addEventListener('mousemove', function(ev) {
    if (!g_mouseDown) return;
    var dx = ev.clientX - g_lastMouseX;
    var dy = ev.clientY - g_lastMouseY;
    g_mouseRotY += dx * 0.45;
    g_mouseRotX += dy * 0.45;
    g_mouseRotX = Math.max(-80, Math.min(80, g_mouseRotX));
    g_lastMouseX = ev.clientX;
    g_lastMouseY = ev.clientY;
  });
  window.addEventListener('mouseup', function(){ g_mouseDown = false; });

  canvas.addEventListener('click', function(ev) {
    if (ev.shiftKey) {
      g_pokeActive = true;
      g_pokeStartTime = g_seconds;
    }
  });
}

// ================= MAIN =================
function main() {
  setupWebGL();
  connectVariablesToGLSL();
  addActionsForHtmlUI();

  initCubeBuffer();
  initPyramidBuffer();
  initSphereBuffer();

  requestAnimationFrame(tick);
}

// ================= TICK =================
function tick() {
  g_seconds = performance.now() / 1000.0;

  if (g_pokeActive) {
    updatePokeAnimation();
  } else if (g_animationOn) {
    updateAnimationAngles();
  } else {
    g_headBob = 0;
    g_armSwing = 0;
    g_bodySway = 0;
  }

  renderScene();
  requestAnimationFrame(tick);
}

// ================= ANIMATION =================
function updateAnimationAngles() {
  g_leftHipAngle = 18 * Math.sin(g_seconds * 2.4);
  g_leftKneeAngle = 28 * Math.sin(g_seconds * 2.4 + 1.0);
  g_leftAnkleAngle = 10 * Math.sin(g_seconds * 2.4 + 2.0);
  g_headBob = 4 * Math.sin(g_seconds * 2.4);
  g_armSwing = 10 * Math.sin(g_seconds * 2.4 + 2.0);
  g_bodySway = 2 * Math.sin(g_seconds * 2.4 + 0.5);
}

function updatePokeAnimation() {
  var t = g_seconds - g_pokeStartTime;
  if (t > 1.2) {
    g_pokeActive = false;
    g_headBob = 0; g_armSwing = 0; g_bodySway = 0;
    return;
  }
  var wiggle = Math.sin(t * 18.0);
  var fade = Math.exp(-t * 2.0);
  g_headBob = 22 * wiggle * fade;
  g_armSwing = 55 * Math.sin(t * 22.0) * fade;
  g_bodySway = 10 * Math.sin(t * 16.0) * fade;
  g_leftHipAngle = 10 * Math.sin(t * 20.0) * fade;
  g_leftKneeAngle = 14 * Math.sin(t * 18.0) * fade;
  g_leftAnkleAngle = 8 * Math.sin(t * 24.0) * fade;
}

// ================= RENDER =================
function renderScene() {
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  var proj = new Matrix4();
  proj.setPerspective(60, canvas.width / canvas.height, 0.1, 100);

  var view = new Matrix4();
  view.setLookAt(
    0.0, 0.45, 1.6,
    0.0, 0.20, -1.2,
    0, 1, 0
  );

  var viewProj = new Matrix4(proj);
  viewProj.multiply(view);
  gl.uniformMatrix4fv(u_ViewProjMatrix, false, viewProj.elements);

  var globalRot = new Matrix4();
  globalRot.rotate(gAnimalGlobalRotation + g_mouseRotY, 0, 1, 0);
  globalRot.rotate(g_mouseRotX, 1, 0, 0);
  gl.uniformMatrix4fv(u_GlobalRotateMatrix, false, globalRot.elements);

  // Colors
  var FUR    = [0.68, 0.68, 0.68, 1.0];
  var FUR2   = [0.58, 0.58, 0.58, 1.0];
  var BELLY  = [0.88, 0.88, 0.88, 1.0];
  var DARK   = [0.12, 0.12, 0.12, 1.0];
  var FOOT   = [0.35, 0.35, 0.35, 1.0];
  var SNOUT  = [0.42, 0.42, 0.42, 1.0];
  var PINK   = [0.90, 0.78, 0.82, 1.0];
  var WHITE  = [1.0, 1.0, 1.0, 1.0];

  function drawPart(color, attachMat, sx, sy, sz) {
    var M = new Matrix4(attachMat);
    M.scale(sx, sy, sz);
    drawCube(M, color);
  }

  // ==========================================================
  // BODY
  // ==========================================================
  var bodyAttach = new Matrix4();
  bodyAttach.translate(-0.18, -0.62, -1.25);
  bodyAttach.scale(1.35, 1.35, 1.35);
  if (g_animationOn || g_pokeActive) {
    bodyAttach.rotate(g_bodySway, 0, 0, 1);
  }
  drawPart(FUR, bodyAttach, 0.52, 0.40, 0.36);

  var chestAttach = new Matrix4(bodyAttach);
  chestAttach.translate(0.02, 0.32, -0.02);
  drawPart(FUR2, chestAttach, 0.46, 0.30, 0.34);

  var bellyAttach = new Matrix4(bodyAttach);
  bellyAttach.translate(0.10, 0.06, 0.22);
  drawPart(BELLY, bellyAttach, 0.32, 0.26, 0.08);

  // ==========================================================
  // HEAD — sphere for real volume
  // ==========================================================
  var headAttach = new Matrix4(chestAttach);
  headAttach.translate(0.00, 0.34, -0.06);
  if (g_animationOn || g_pokeActive) {
    headAttach.rotate(g_headBob, 0, 0, 1);
  }

  // Head sphere (centered at origin in local space, radius 0.5)
  var headM = new Matrix4(headAttach);
  headM.translate(0.22, 0.20, 0.10);
  headM.scale(0.58, 0.50, 0.46);
  drawSphere(headM, FUR2);

  // Snout sphere
  var snoutM = new Matrix4(headAttach);
  snoutM.translate(0.24, 0.13, 0.28);
  snoutM.scale(0.24, 0.17, 0.18);
  drawSphere(snoutM, SNOUT);

  // Eyes — in front of head sphere surface
  // Head sphere front face is at z = 0.10 + 0.46*0.5 = 0.33
  // Place eyes at z=0.37 so they sit on the face
  var eyeL = new Matrix4(headAttach);
  eyeL.translate(0.13, 0.24, 0.37);
  drawPart(DARK, eyeL, 0.06, 0.06, 0.04);

  var eyeR = new Matrix4(headAttach);
  eyeR.translate(0.33, 0.24, 0.37);
  drawPart(DARK, eyeR, 0.06, 0.06, 0.04);

  // Eye highlights (tiny white spheres)
  var hiL = new Matrix4(headAttach);
  hiL.translate(0.148, 0.248, 0.40);
  hiL.scale(0.018, 0.018, 0.018);
  drawSphere(hiL, WHITE);

  var hiR = new Matrix4(headAttach);
  hiR.translate(0.348, 0.248, 0.40);
  hiR.scale(0.018, 0.018, 0.018);
  drawSphere(hiR, WHITE);

  // Nose (pyramid)
  var noseM = new Matrix4(headAttach);
  noseM.translate(0.22, 0.10, 0.36);
  noseM.scale(0.08, 0.12, 0.08);
  drawPyramid(noseM, DARK);

  // ==========================================================
  // EARS — spheres
  // ==========================================================
  var earL = new Matrix4(headAttach);
  earL.translate(0.07, 0.43, 0.06);
  earL.scale(0.24, 0.24, 0.20);
  drawSphere(earL, FUR2);

  var earLi = new Matrix4(headAttach);
  earLi.translate(0.07, 0.43, 0.09);
  earLi.scale(0.13, 0.13, 0.10);
  drawSphere(earLi, PINK);

  var earR = new Matrix4(headAttach);
  earR.translate(0.37, 0.43, 0.06);
  earR.scale(0.24, 0.24, 0.20);
  drawSphere(earR, FUR2);

  var earRi = new Matrix4(headAttach);
  earRi.translate(0.37, 0.43, 0.09);
  earRi.scale(0.13, 0.13, 0.10);
  drawSphere(earRi, PINK);

  // ==========================================================
  // ARMS
  // ==========================================================
  var armL = new Matrix4(chestAttach);
  armL.translate(-0.10, 0.06, 0.12);
  armL.rotate(-20, 0, 0, 1);
  if (g_animationOn || g_pokeActive) armL.rotate(-g_armSwing * 0.5, 1, 0, 0);
  drawPart(FUR, armL, 0.10, 0.22, 0.10);

  var armR = new Matrix4(chestAttach);
  armR.translate(0.46, 0.06, 0.12);
  armR.rotate(20, 0, 0, 1);
  if (g_animationOn || g_pokeActive) armR.rotate(g_armSwing * 0.5, 1, 0, 0);
  drawPart(FUR, armR, 0.10, 0.22, 0.10);

  // ==========================================================
  // LEGS (left = 3-level limb)
  // ==========================================================
  var thighAttach = new Matrix4(bodyAttach);
  thighAttach.translate(0.12, -0.06, 0.10);
  thighAttach.rotate(g_leftHipAngle, 1, 0, 0);
  drawPart(FUR, thighAttach, 0.10, 0.14, 0.10);

  var calfAttach = new Matrix4(thighAttach);
  calfAttach.translate(0.00, -0.14, 0.00);
  calfAttach.rotate(g_leftKneeAngle, 1, 0, 0);
  drawPart(FUR2, calfAttach, 0.09, 0.13, 0.09);

  var footAttach = new Matrix4(calfAttach);
  footAttach.translate(-0.02, -0.12, 0.02);
  footAttach.rotate(g_leftAnkleAngle, 1, 0, 0);
  drawPart(FOOT, footAttach, 0.14, 0.05, 0.12);

  var rThigh = new Matrix4(bodyAttach);
  rThigh.translate(0.32, -0.06, 0.08);
  rThigh.rotate(-10, 1, 0, 0);
  drawPart(FUR, rThigh, 0.10, 0.14, 0.10);

  var rCalf = new Matrix4(rThigh);
  rCalf.translate(0.00, -0.14, 0.00);
  rCalf.rotate(18, 1, 0, 0);
  drawPart(FUR2, rCalf, 0.09, 0.13, 0.09);

  var rFoot = new Matrix4(rCalf);
  rFoot.translate(-0.02, -0.12, 0.02);
  drawPart(FOOT, rFoot, 0.14, 0.05, 0.12);

  // ==========================================================
  // FPS indicator
  // ==========================================================
  g_frameCount++;
  var now = performance.now();
  var elapsed = now - g_lastFPSTime;
  if (elapsed >= 250) {
    g_fps = Math.round((g_frameCount * 1000) / elapsed);
    g_frameCount = 0;
    g_lastFPSTime = now;
  }
  sendTextToHTML("fps: " + g_fps, "numdot");
}

// ================= UTILITY =================
function sendTextToHTML(text, id) {
  var elm = document.getElementById(id);
  if (elm) elm.innerHTML = text;
}
