// Vertex Shader
const VSHADER_SOURCE = `
  attribute vec4 a_Position;
  attribute vec3 a_Normal;
  attribute vec2 a_UV;
  
  uniform mat4 u_ModelMatrix;
  uniform mat4 u_ViewMatrix;
  uniform mat4 u_ProjectionMatrix;
  
  varying vec2 v_UV;
  varying vec3 v_Normal;
  
  void main() {
  gl_FragColor = vec4(v_UV.x, v_UV.y, 0.0, 1.0);
}
`;

const FSHADER_SOURCE = `
  precision mediump float;
  
  uniform vec4 u_FragColor;
  uniform sampler2D u_Sampler0;
  uniform sampler2D u_Sampler1;
  uniform sampler2D u_Sampler2;
  uniform sampler2D u_Sampler3;
  uniform int u_WhichTexture;
  
  varying vec2 v_UV;
  varying vec3 v_Normal;
  
  void main() {
    if (u_WhichTexture == -1) {
      gl_FragColor = u_FragColor;
    } else if (u_WhichTexture == 0) {
      gl_FragColor = texture2D(u_Sampler0, v_UV);
    } else if (u_WhichTexture == 1) {
      gl_FragColor = texture2D(u_Sampler1, v_UV);
    } else if (u_WhichTexture == 2) {
      gl_FragColor = texture2D(u_Sampler2, v_UV);
    } else if (u_WhichTexture == 3) {
      gl_FragColor = texture2D(u_Sampler3, v_UV);
    } else {
      gl_FragColor = u_FragColor;
    }
  }
`;

// Global variables
let gl;
let canvas;
let camera;

let a_Position;
let a_Normal;
let a_UV;

let u_ModelMatrix;
let u_ViewMatrix;
let u_ProjectionMatrix;
let u_FragColor;
let u_Sampler0, u_Sampler1, u_Sampler2, u_Sampler3;
let u_WhichTexture;

let worldMap;
let walls = [];

function main() {
  canvas = document.getElementById('webgl');
  gl = getWebGLContext(canvas);
  
  if (!gl) {
    console.log('Failed to get WebGL context');
    return;
  }
  
  if (!initShaders(gl, VSHADER_SOURCE, FSHADER_SOURCE)) {
    console.log('Failed to initialize shaders');
    return;
  }
  
  // Get attribute locations
  a_Position = gl.getAttribLocation(gl.program, 'a_Position');
  a_Normal = gl.getAttribLocation(gl.program, 'a_Normal');
  a_UV = gl.getAttribLocation(gl.program, 'a_UV');
  
  // ⭐ CRITICAL DEBUG: Check attribute locations
  console.log("=== ATTRIBUTE LOCATIONS ===");
  console.log("a_Position:", a_Position);
  console.log("a_Normal:", a_Normal);
  console.log("a_UV:", a_UV, "← Should NOT be -1!");
  console.log("===========================");
  
  if (a_UV === -1) {
    console.error("❌ CRITICAL ERROR: a_UV attribute not found!");
    console.error("This means UV coordinates won't work. Check shader compilation.");
  }
  
  // Get uniform locations
  u_ModelMatrix = gl.getUniformLocation(gl.program, 'u_ModelMatrix');
  u_ViewMatrix = gl.getUniformLocation(gl.program, 'u_ViewMatrix');
  u_ProjectionMatrix = gl.getUniformLocation(gl.program, 'u_ProjectionMatrix');
  u_FragColor = gl.getUniformLocation(gl.program, 'u_FragColor');
  u_Sampler0 = gl.getUniformLocation(gl.program, 'u_Sampler0');
  u_Sampler1 = gl.getUniformLocation(gl.program, 'u_Sampler1');
  u_Sampler2 = gl.getUniformLocation(gl.program, 'u_Sampler2');
  u_Sampler3 = gl.getUniformLocation(gl.program, 'u_Sampler3');
  u_WhichTexture = gl.getUniformLocation(gl.program, 'u_WhichTexture');
  
  console.log("=== UNIFORM LOCATIONS ===");
  console.log("u_WhichTexture:", u_WhichTexture, "← Should NOT be null!");
  console.log("u_Sampler0:", u_Sampler0);
  console.log("u_Sampler1:", u_Sampler1);
  console.log("u_Sampler2:", u_Sampler2);
  console.log("u_Sampler3:", u_Sampler3);
  console.log("========================");
  
  initCubeBuffer();
  initTextures();
  
  camera = new Camera();
  initWorld();
  setupEventListeners();
  
  gl.clearColor(0.53, 0.81, 0.92, 1.0);
  gl.enable(gl.DEPTH_TEST);
  
  tick();
}

function initTextures() {
  console.log("🎨 Starting texture loading...");
  
  let image0 = new Image();
  image0.onload = function() { 
    console.log('✅ Loaded dirt.png');
    sendTextureToGLSL(image0, 0); 
  };
  image0.onerror = function() {
    console.error('❌ Failed to load dirt.png - check path!');
  };
  image0.src = 'resources/dirt.png';
  
  let image1 = new Image();
  image1.onload = function() { 
    console.log('✅ Loaded grass.png');
    sendTextureToGLSL(image1, 1); 
  };
  image1.onerror = function() {
    console.error('❌ Failed to load grass.png - check path!');
  };
  image1.src = 'resources/grass.png';
  
  let image2 = new Image();
  image2.onload = function() { 
    console.log('✅ Loaded stone.jpg');
    sendTextureToGLSL(image2, 2); 
  };
  image2.onerror = function() {
    console.error('❌ Failed to load stone.jpg - check path!');
  };
  image2.src = 'resources/stone.jpg';
  
  let image3 = new Image();
  image3.onload = function() { 
    console.log('✅ Loaded grass_side.png');
    sendTextureToGLSL(image3, 3); 
  };
  image3.onerror = function() {
    console.error('❌ Failed to load grass_side.png - check path!');
  };
  image3.src = 'resources/grass_side.png';
}

function sendTextureToGLSL(image, textureUnit) {
  let texture = gl.createTexture();
  if (!texture) {
    console.error('Failed to create texture object for unit ' + textureUnit);
    return;
  }
  
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 1);
  
  gl.activeTexture(gl.TEXTURE0 + textureUnit);
  gl.bindTexture(gl.TEXTURE_2D, texture);
  
  // For non-power-of-2 textures, use CLAMP_TO_EDGE
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
  
  // Set the sampler uniform to point to the correct texture unit
  if (textureUnit === 0) {
    gl.uniform1i(u_Sampler0, 0);
  } else if (textureUnit === 1) {
    gl.uniform1i(u_Sampler1, 1);
  } else if (textureUnit === 2) {
    gl.uniform1i(u_Sampler2, 2);
  } else if (textureUnit === 3) {
    gl.uniform1i(u_Sampler3, 3);
  }
  
  console.log('✅ Texture ' + textureUnit + ' sent to GPU (size: ' + image.width + 'x' + image.height + ')');
}

function initWorld() {
  worldMap = generateWorldMap();
  buildWorld();
}

function generateWorldMap() {
  let map = [];
  for (let x = 0; x < 32; x++) {
    map[x] = [];
    for (let z = 0; z < 32; z++) {
      if (x === 0 || x === 31 || z === 0 || z === 31) {
        map[x][z] = 2;
      } else if ((x % 4 === 0 && z % 2 === 0) || (z % 4 === 0 && x % 2 === 0)) {
        map[x][z] = Math.floor(Math.random() * 3) + 1;
      } else {
        map[x][z] = 0;
      }
    }
  }
  return map;
}

function buildWorld() {
  walls = [];
  for (let x = 0; x < 32; x++) {
    for (let z = 0; z < 32; z++) {
      let height = worldMap[x][z];
      for (let y = 0; y < height; y++) {
        let wall = new Cube();
        wall.matrix.translate(x, y, z);
        // Top blocks use grass (texture 1), others use stone (texture 2)
        wall.textureNum = (y === height - 1) ? 1 : 2;
        walls.push(wall);
      }
    }
  }
  console.log('🌍 World built with ' + walls.length + ' blocks');
  console.log('First block texture:', walls[0].textureNum);
  console.log('Last block texture:', walls[walls.length-1].textureNum);
}

let frameCount = 0;

function renderScene() {
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  
  gl.uniformMatrix4fv(u_ViewMatrix, false, camera.viewMatrix.elements);
  gl.uniformMatrix4fv(u_ProjectionMatrix, false, camera.projectionMatrix.elements);
  
  // Ground plane with grass texture
  let ground = new Cube();
  ground.color = [0.2, 0.7, 0.2, 1.0];
  ground.matrix.translate(16, -0.5, 16);
  ground.matrix.scale(32, 0.1, 32);
  ground.textureNum = 1; // Grass texture
  ground.render();
  
  // Sky box with solid color (no texture)
  let sky = new Cube();
  sky.color = [0.53, 0.81, 0.92, 1.0];
  sky.matrix.translate(16, 16, 16);
  sky.matrix.scale(300, 300, 300);
  sky.textureNum = -1; // No texture, use color
  sky.render();
  
  // Walls with textures
  for (let i = 0; i < walls.length; i++) {
    walls[i].render();
  }
  
  // Debug output every 60 frames (~1 second at 60fps)
  frameCount++;
  if (frameCount === 60) {
    console.log("🎬 Rendering frame 60 - textures should be visible now!");
    frameCount = 0;
  }
}

function tick() {
  renderScene();
  requestAnimationFrame(tick);
}

function setupEventListeners() {
  document.addEventListener('keydown', handleKeyDown);
  
  canvas.addEventListener('click', () => {
    canvas.requestPointerLock();
  });
  
  document.addEventListener('mousemove', (ev) => {
    if (document.pointerLockElement === canvas) {
      camera.rotate(ev.movementX, ev.movementY);
    }
  });
}

function handleKeyDown(ev) {
  switch(ev.key.toLowerCase()) {
    case 'w': camera.moveForward(); break;
    case 's': camera.moveBackward(); break;
    case 'a': camera.moveLeft(); break;
    case 'd': camera.moveRight(); break;
    case 'q': camera.panLeft(); break;
    case 'e': camera.panRight(); break;
  }
}

window.onload = main;