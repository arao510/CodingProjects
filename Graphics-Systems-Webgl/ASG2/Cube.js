// ============================================================
// Cube.js  (GLOBAL-SAFE VERSION + NORMALS)
// Interleaved VBO: [px,py,pz, nx,ny,nz] per vertex
// stride = 24 bytes, normal offset = 12 bytes
// ============================================================

var g_cubeVBO = null;
var g_cubeVertexCount = 0;

function initCubeBuffer() {
  // Each vertex: x,y,z, nx,ny,nz
  var vertices = new Float32Array([
    // FRONT (z=0)  normal (0,0,1)
    0,0,0,  0,0,1,   1,1,0,  0,0,1,   1,0,0,  0,0,1,
    0,0,0,  0,0,1,   0,1,0,  0,0,1,   1,1,0,  0,0,1,

    // BACK (z=-1)  normal (0,0,-1)
    0,0,-1, 0,0,-1,  1,0,-1, 0,0,-1,  1,1,-1, 0,0,-1,
    0,0,-1, 0,0,-1,  1,1,-1, 0,0,-1,  0,1,-1, 0,0,-1,

    // TOP (y=1)  normal (0,1,0)
    0,1,0,  0,1,0,   1,1,0,  0,1,0,   1,1,-1, 0,1,0,
    0,1,0,  0,1,0,   1,1,-1, 0,1,0,   0,1,-1, 0,1,0,

    // BOTTOM (y=0)  normal (0,-1,0)
    0,0,0,  0,-1,0,  1,0,0,  0,-1,0,  1,0,-1, 0,-1,0,
    0,0,0,  0,-1,0,  1,0,-1, 0,-1,0,  0,0,-1, 0,-1,0,

    // LEFT (x=0)  normal (-1,0,0)
    0,0,0,  -1,0,0,  0,1,0,  -1,0,0,  0,1,-1, -1,0,0,
    0,0,0,  -1,0,0,  0,1,-1, -1,0,0,  0,0,-1, -1,0,0,

    // RIGHT (x=1)  normal (1,0,0)
    1,0,0,  1,0,0,   1,1,0,  1,0,0,   1,1,-1, 1,0,0,
    1,0,0,  1,0,0,   1,1,-1, 1,0,0,   1,0,-1, 1,0,0
  ]);

  g_cubeVertexCount = 36;

  g_cubeVBO = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, g_cubeVBO);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
}

class Cube {
  constructor() {
    this.color = [1,1,1,1];
    this.matrix = new Matrix4();
  }

  render() {
    gl.uniform4f(u_FragColor,
      this.color[0], this.color[1], this.color[2], this.color[3]);

    gl.uniformMatrix4fv(u_ModelMatrix, false, this.matrix.elements);

    gl.bindBuffer(gl.ARRAY_BUFFER, g_cubeVBO);
    // stride=24 (6 floats * 4 bytes), position at offset 0
    gl.vertexAttribPointer(a_Position, 3, gl.FLOAT, false, 24, 0);
    gl.enableVertexAttribArray(a_Position);
    // normal at offset 12 (3 floats * 4 bytes)
    gl.vertexAttribPointer(a_Normal, 3, gl.FLOAT, false, 24, 12);
    gl.enableVertexAttribArray(a_Normal);

    gl.drawArrays(gl.TRIANGLES, 0, g_cubeVertexCount);
  }
}

window.initCubeBuffer = initCubeBuffer;
window.Cube = Cube;
