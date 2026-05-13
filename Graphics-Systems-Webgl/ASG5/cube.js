// ============================================================
// Cube.js - Complete working version with UV coordinates
// Interleaved VBO: [px,py,pz, nx,ny,nz, u,v] per vertex
// stride = 32 bytes, UV offset = 24 bytes
// ============================================================

var g_cubeVBO = null;
var g_cubeVertexCount = 0;

function initCubeBuffer() {
  // Each vertex: x,y,z (3 floats), nx,ny,nz (3 floats), u,v (2 floats) = 8 floats = 32 bytes
  var vertices = new Float32Array([
    // FRONT FACE (z=0) - normal (0,0,1)
    0,0,0,  0,0,1,  0,0,
    1,1,0,  0,0,1,  1,1,
    1,0,0,  0,0,1,  1,0,
    
    0,0,0,  0,0,1,  0,0,
    0,1,0,  0,0,1,  0,1,
    1,1,0,  0,0,1,  1,1,

    // BACK FACE (z=-1) - normal (0,0,-1)
    0,0,-1, 0,0,-1, 0,0,
    1,0,-1, 0,0,-1, 1,0,
    1,1,-1, 0,0,-1, 1,1,
    
    0,0,-1, 0,0,-1, 0,0,
    1,1,-1, 0,0,-1, 1,1,
    0,1,-1, 0,0,-1, 0,1,

    // TOP FACE (y=1) - normal (0,1,0)
    0,1,0,  0,1,0,  0,0,
    1,1,0,  0,1,0,  1,0,
    1,1,-1, 0,1,0,  1,1,
    
    0,1,0,  0,1,0,  0,0,
    1,1,-1, 0,1,0,  1,1,
    0,1,-1, 0,1,0,  0,1,

    // BOTTOM FACE (y=0) - normal (0,-1,0)
    0,0,0,  0,-1,0, 0,0,
    1,0,0,  0,-1,0, 1,0,
    1,0,-1, 0,-1,0, 1,1,
    
    0,0,0,  0,-1,0, 0,0,
    1,0,-1, 0,-1,0, 1,1,
    0,0,-1, 0,-1,0, 0,1,

    // LEFT FACE (x=0) - normal (-1,0,0)
    0,0,0,  -1,0,0, 0,0,
    0,1,0,  -1,0,0, 0,1,
    0,1,-1, -1,0,0, 1,1,
    
    0,0,0,  -1,0,0, 0,0,
    0,1,-1, -1,0,0, 1,1,
    0,0,-1, -1,0,0, 1,0,

    // RIGHT FACE (x=1) - normal (1,0,0)
    1,0,0,  1,0,0,  0,0,
    1,1,0,  1,0,0,  0,1,
    1,1,-1, 1,0,0,  1,1,
    
    1,0,0,  1,0,0,  0,0,
    1,1,-1, 1,0,0,  1,1,
    1,0,-1, 1,0,0,  1,0
  ]);

  g_cubeVertexCount = 36;

  g_cubeVBO = gl.createBuffer();
  if (!g_cubeVBO) {
    console.error('❌ Failed to create cube VBO');
    return;
  }
  
  gl.bindBuffer(gl.ARRAY_BUFFER, g_cubeVBO);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
  
  console.log("✅ Cube buffer initialized");
  console.log("   Total vertices: " + g_cubeVertexCount);
  console.log("   Stride: 32 bytes (8 floats × 4)");
  console.log("   Position offset: 0");
  console.log("   Normal offset: 12");
  console.log("   UV offset: 24");
}

class Cube {
  constructor() {
    this.color = [1, 1, 1, 1];
    this.matrix = new Matrix4();
    this.textureNum = -1;  // -1 = use color only, 0-3 = use texture
  }

  render() {
    // Set fragment color (for solid color rendering)
    gl.uniform4f(u_FragColor,
      this.color[0], this.color[1], this.color[2], this.color[3]);

    // Set model matrix
    gl.uniformMatrix4fv(u_ModelMatrix, false, this.matrix.elements);
    
    // CRITICAL: Tell shader which texture to use (-1 for none, 0-3 for textures)
    gl.uniform1i(u_WhichTexture, this.textureNum);

    // Bind the cube VBO
    gl.bindBuffer(gl.ARRAY_BUFFER, g_cubeVBO);
    
    // Position attribute (3 floats at offset 0)
    gl.vertexAttribPointer(a_Position, 3, gl.FLOAT, false, 32, 0);
    gl.enableVertexAttribArray(a_Position);
    
    // Normal attribute (3 floats at offset 12)
    gl.vertexAttribPointer(a_Normal, 3, gl.FLOAT, false, 32, 12);
    gl.enableVertexAttribArray(a_Normal);
    
    // UV attribute (2 floats at offset 24)
    if (a_UV !== -1) {
      gl.vertexAttribPointer(a_UV, 2, gl.FLOAT, false, 32, 24);
      gl.enableVertexAttribArray(a_UV);
    }

    // Draw the cube
    gl.drawArrays(gl.TRIANGLES, 0, g_cubeVertexCount);
  }
}

// Export to global scope
window.initCubeBuffer = initCubeBuffer;
window.Cube = Cube;