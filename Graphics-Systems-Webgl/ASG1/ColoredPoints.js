// ColoredPoints.js (Features 5-7 + Point class)


// Brush state
const BRUSH_POINT = 0;
const BRUSH_TRIANGLE = 1;
const BRUSH_CIRCLE = 2;
let g_selectedBrush = BRUSH_POINT;

// Circle segments (Feature 11)
let g_selectedSegments = 12;

// Buffer for triangle drawing
let g_vertexBuffer = null;


// Vertex shader program
var VSHADER_SOURCE =
  'attribute vec4 a_Position;\n' +
  'uniform float u_Size;\n' +
  'void main() {\n' +
  '  gl_Position = a_Position;\n' +
  '  gl_PointSize = u_Size;\n' +
  '}\n';

// Fragment shader program
var FSHADER_SOURCE =
  'precision mediump float;\n' +
  'uniform vec4 u_FragColor;\n' +
  'void main() {\n' +
  '  gl_FragColor = u_FragColor;\n' +
  '}\n';

let canvas;
let gl;
let a_Position;
let u_FragColor;
let u_Size;

// Single list of shapes (Feature 6)
let shapesList = [];

let pictureList = [];   // Feature 12: picture triangles live here (persistent)

// Current selected UI state
let g_selectedColor = [1.0, 0.0, 0.0, 1.0];
let g_selectedSize = 10.0;

// -------------------- Shape Class --------------------
class Point {
  constructor(position, color, size) {
    this.position = position; // [x, y]
    this.color = color;       // [r, g, b, a]
    this.size = size;         // float
  }

  render() {
    gl.vertexAttrib3f(a_Position, this.position[0], this.position[1], 0.0);
    gl.uniform4f(u_FragColor, this.color[0], this.color[1], this.color[2], this.color[3]);
    gl.uniform1f(u_Size, this.size);
    gl.drawArrays(gl.POINTS, 0, 1);
  }
}

// -------------------- Main --------------------
function main() {
  setupWebGL();
  connectVariablesToGLSL();
  addUIHandlers();
  addMouseHandlers();

  gl.clearColor(0, 0, 0, 1);
  renderAllShapes();
}

function setupWebGL() {
  canvas = document.getElementById('webgl');
  gl = getWebGLContext(canvas);
  if (!gl) {
    console.log('Failed to get WebGL context');
    return;
  }
}

function connectVariablesToGLSL() {
  if (!initShaders(gl, VSHADER_SOURCE, FSHADER_SOURCE)) {
    console.log('Failed to initialize shaders.');
    return;
  }

  a_Position = gl.getAttribLocation(gl.program, 'a_Position');
  if (a_Position < 0) {
    console.log('Failed to get a_Position');
    return;
  }

  u_FragColor = gl.getUniformLocation(gl.program, 'u_FragColor');
  if (!u_FragColor) {
    console.log('Failed to get u_FragColor');
    return;
  }

  // Feature 5: connect size uniform
  u_Size = gl.getUniformLocation(gl.program, 'u_Size');
  if (!u_Size) {
    console.log('Failed to get u_Size');
    return;
  }
    // Create a buffer for triangles/circles
    g_vertexBuffer = gl.createBuffer();
    if (!g_vertexBuffer) {
      console.log('Failed to create the buffer object');
      return;
    }  


}

function drawTriangle(vertices) {
  // vertices: [x1,y1, x2,y2, x3,y3]
  const n = 3;

  gl.bindBuffer(gl.ARRAY_BUFFER, g_vertexBuffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.DYNAMIC_DRAW);

  gl.vertexAttribPointer(a_Position, 2, gl.FLOAT, false, 0, 0);
  gl.enableVertexAttribArray(a_Position);

  gl.drawArrays(gl.TRIANGLES, 0, n);
}



function addMouseHandlers() {
  canvas.onmousedown = function (ev) {
    // LEFT click only
    if (ev.button === 0) {
      click(ev);
    }
  };

  canvas.onmousemove = function (ev) {
    // Drag with LEFT button only
    if (ev.buttons === 1) {
      click(ev);
    }
  };

  // Awesomeness: Right-click clears canvas
  canvas.oncontextmenu = function (ev) {
    ev.preventDefault();   // stop browser menu
    shapesList = [];
    renderAllShapes();
    return false;
  };
}



// Required by your rubric wording
function click(ev) {
  handleClick(ev);
}

function addUIHandlers() {
  // ================= RGB sliders (Feature 4) =================
  const r = document.getElementById('redSlide');
  const g = document.getElementById('greenSlide');
  const b = document.getElementById('blueSlide');

  function updateColor() {
    g_selectedColor = [
      Number(r.value) / 100.0,
      Number(g.value) / 100.0,
      Number(b.value) / 100.0,
      1.0
    ];
  }

  r.oninput = updateColor;
  g.oninput = updateColor;
  b.oninput = updateColor;
  updateColor();


  // ================= Size slider (Feature 5) =================
  const sizeSlide = document.getElementById('sizeSlide');
  const sizeText = document.getElementById('sizeText');

  function updateSize() {
    g_selectedSize = Number(sizeSlide.value);
    if (sizeText) sizeText.textContent = String(g_selectedSize);
  }

  sizeSlide.oninput = updateSize;
  updateSize();


  // ================= Clear button (Feature 7) =================
  const clearButton = document.getElementById('clearButton');
  clearButton.onclick = function () {
    shapesList = [];
    renderAllShapes();
  };


  // ================= Brush buttons (Features 9 & 10) =================
  document.getElementById('pointButton').onclick = function () {
    g_selectedBrush = BRUSH_POINT;
  };

  document.getElementById('triButton').onclick = function () {
    g_selectedBrush = BRUSH_TRIANGLE;
  };

  document.getElementById('circleButton').onclick = function () {
    g_selectedBrush = BRUSH_CIRCLE;
  };
    // Feature 12: draw picture button
    document.getElementById('drawPictureButton').onclick = function () {
      drawMyPicture();
  };
  



  // ================= Circle segments slider (Feature 11) =================
  const segSlide = document.getElementById('segmentsSlide');
  const segText = document.getElementById('segmentsText');

  function updateSegments() {
    g_selectedSegments = Number(segSlide.value);
    if (segText) segText.textContent = String(g_selectedSegments);
  }

  segSlide.oninput = updateSegments;
  updateSegments();
}









function handleClick(ev) {
  // Convert mouse to WebGL coords
  let x = ev.clientX;
  let y = ev.clientY;
  const rect = ev.target.getBoundingClientRect();

  x = ((x - rect.left) - canvas.width / 2) / (canvas.width / 2);
  y = (canvas.height / 2 - (y - rect.top)) / (canvas.height / 2);

  let shape = null;

  if (g_selectedBrush === BRUSH_POINT) {
    shape = new Point([x, y], [...g_selectedColor], g_selectedSize);
  } else if (g_selectedBrush === BRUSH_TRIANGLE) {
    shape = new Triangle([x, y], [...g_selectedColor], g_selectedSize);
  } else if (g_selectedBrush === BRUSH_CIRCLE) {
    shape = new Circle([x, y], [...g_selectedColor], g_selectedSize, g_selectedSegments);
  }

  shapesList.push(shape);
  renderAllShapes();
}


function renderAllShapes() {
  gl.clear(gl.COLOR_BUFFER_BIT);

  // Draw the picture first (stays on screen)
  for (let i = 0; i < pictureList.length; i++) {
    pictureList[i].render();
  }

  // Then draw the user's paint strokes
  for (let i = 0; i < shapesList.length; i++) {
    shapesList[i].render();
  }
}



function drawMyPicture() {
  // Clear ONLY the picture and rebuild it (do not clear shapesList!)
  pictureList = [];

  // Helper: add one triangle to pictureList using custom vertices
  function addPicTri(x1, y1, x2, y2, x3, y3, r, g, b, a) {
    pictureList.push(new Triangle(
      [0, 0],
      [r, g, b, a],
      10,
      [x1, y1, x2, y2, x3, y3]
    ));
  }

  // Helper: rectangle made of 2 triangles
  function addRect(xL, yB, xR, yT, r, g, b, a) {
    addPicTri(xL, yB, xR, yB, xR, yT, r, g, b, a);
    addPicTri(xL, yB, xR, yT, xL, yT, r, g, b, a);
  }

  // Helper: one tree = 3 green triangles + trunk (2 triangles)
  function addTree(cx, baseY, s) {
    // Leaves (3 triangles)
    addPicTri(cx, baseY + 3.0*s, cx - 2.0*s, baseY + 1.0*s, cx + 2.0*s, baseY + 1.0*s, 0.0, 0.6, 0.2, 1.0);
    addPicTri(cx, baseY + 2.2*s, cx - 1.8*s, baseY + 0.2*s, cx + 1.8*s, baseY + 0.2*s, 0.0, 0.55, 0.18, 1.0);
    addPicTri(cx, baseY + 1.4*s, cx - 1.6*s, baseY - 0.8*s, cx + 1.6*s, baseY - 0.8*s, 0.0, 0.5, 0.15, 1.0);

    // Trunk (rectangle = 2 triangles)
    addRect(cx - 0.35*s, baseY - 1.6*s, cx + 0.35*s, baseY - 0.8*s, 0.2, 0.1, 0.02, 1.0);
  }

  // ===== Draw 5 trees like your sketch (25 triangles) =====
  addTree(-0.75,  0.00, 0.14);
  addTree(-0.35,  0.00, 0.12);
  addTree( 0.05,  0.05, 0.09);
  addTree( 0.45,  0.00, 0.13);
  addTree( 0.80,  0.05, 0.08);

  // ===== Draw "A.R" using triangles (simple block letters) =====
  // A (left)
  addRect(-0.955, 0.65, -0.935, 0.90, 0.0, 0.7, 1.0, 1.0);
  // right leg
  addRect(-0.885, 0.65, -0.865, 0.90, 0.0, 0.7, 1.0, 1.0);
  // top bar (gives it an A “cap”)
  addRect(-0.955, 0.88, -0.865, 0.90, 0.0, 0.7, 1.0, 1.0);
  // crossbar (lower than before so it doesn’t look like H)
  addRect(-0.945, 0.75, -0.875, 0.77, 0.0, 0.7, 1.0, 1.0);

  // R (right)
  addRect(-0.80, 0.65, -0.77, 0.90, 0.0, 0.7, 1.0, 1.0); // vertical
  addRect(-0.77, 0.87, -0.70, 0.90, 0.0, 0.7, 1.0, 1.0); // top
  addRect(-0.77, 0.78, -0.70, 0.81, 0.0, 0.7, 1.0, 1.0); // mid
  addRect(-0.70, 0.78, -0.67, 0.90, 0.0, 0.7, 1.0, 1.0); // right bar
  // diagonal leg (2 triangles)
  addPicTri(-0.77, 0.78, -0.70, 0.65, -0.67, 0.65, 0.0, 0.7, 1.0, 1.0);
  addPicTri(-0.77, 0.78, -0.67, 0.65, -0.74, 0.78, 0.0, 0.7, 1.0, 1.0);

  // Finally draw everything (picture + paint)
  renderAllShapes();
}
