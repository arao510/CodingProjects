/**
 */
class Triangle{
  constructor(coord){
    this.type = 'triangle';
    this.position = coord;                // [x, y] position of the triangle's right-angle corner
    this.color = [0.0, 0.0, 0.0, 0.0];   // RGBA color (0–1 range)
    this.size = 5.0;                      // side length of the triangle in pixels
    this.segement = 10;                   // unused in this class, kept for consistency with other shapes
  }

  render(){
    var xy = this.position;   // shorthand for position
    var rgba = this.color;    // shorthand for color
    var size = this.size;     // shorthand for size

    // Set the fragment color uniform so the triangle draws in this color
    gl.uniform4f(u_FragColor, rgba[0],rgba[1],rgba[2],rgba[3]);

    // Pass the size to the shader (unused for triangle drawing but kept for consistency)
    gl.uniform1f(u_Size, size);

    // Convert pixel size to normalized device coordinates (-1 to 1 range)
    var d = this.size/200.0

    // Draw a right triangle with vertices at:
    //   (xy[0], xy[1])      — the right-angle corner (origin)
    //   (xy[0]+d, xy[1])    — extends right along X by d
    //   (xy[0], xy[1]+d)    — extends up along Y by d
    drawTriangle([xy[0], xy[1], xy[0]+d, xy[1], xy[0], xy[1]+d]);
  }
}

/**
 * @param {number[]} vertices - Flat array of 2D vertex positions [x1,y1, x2,y2, x3,y3]
 */
function drawTriangle(vertices) {
  var n = 3; // Number of vertices in a triangle

  // Allocate a new buffer object on the GPU
  var vertexBuffer = gl.createBuffer();
  if (!vertexBuffer) {
    console.log('Failed to create the buffer object');
    return -1;
  }

  // Bind the buffer so subsequent GPU calls target it
  gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);

  // Upload the vertex data to the GPU as a Float32Array
  // gl.DYNAMIC_DRAW hints that this data may change frequently
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.DYNAMIC_DRAW);

  // Tell WebGL how to read the buffer: 2 floats per vertex, no padding, starting at offset 0
  gl.vertexAttribPointer(a_Position, 2, gl.FLOAT, false, 0, 0);

  // Enable the a_Position attribute so the vertex shader receives it
  gl.enableVertexAttribArray(a_Position);

  // Draw 3 vertices as a single triangle primitive
  gl.drawArrays(gl.TRIANGLES, 0, n);
}

/**
 *
 * @param {number[]} vertices - Flat array of 3D vertex positions [x1,y1,z1, x2,y2,z2, x3,y3,z3]
 */
function drawTriangle3D(vertices) {
  var n = 3; // Number of vertices in a triangle

  // Allocate a new buffer object on the GPU
  var vertexBuffer = gl.createBuffer();
  if (!vertexBuffer) {
    console.log('Failed to create the buffer object');
    return -1;
  }

  // Bind the buffer so subsequent GPU calls target it
  gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);

  // Upload the vertex data to the GPU as a Float32Array
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.DYNAMIC_DRAW);

  // Tell WebGL how to read the buffer: 3 floats per vertex (x, y, z), no padding, offset 0
  gl.vertexAttribPointer(a_Position, 3, gl.FLOAT, false, 0, 0);

  // Enable the a_Position attribute so the vertex shader receives it
  gl.enableVertexAttribArray(a_Position);

  // Draw 3 vertices as a single triangle primitive
  gl.drawArrays(gl.TRIANGLES, 0, n);
}