// Triangle.js

class Triangle {
  constructor(position, color, size, vertices = null) {
    this.position = position; // [x,y]
    this.color = color;       // [r,g,b,a]
    this.size = size;         // float
    this.vertices = vertices; // OPTIONAL: [x1,y1,x2,y2,x3,y3]
  }

  render() {
    // Set color
    gl.uniform4f(u_FragColor, this.color[0], this.color[1], this.color[2], this.color[3]);

    // If custom vertices were provided (for Feature 12 pictures), draw those
    if (this.vertices) {
      drawTriangle(this.vertices);
      return;
    }

    // Otherwise draw the normal brush triangle around click position
    const cx = this.position[0];
    const cy = this.position[1];

    const d = this.size / 200.0;

    const verts = [
      cx,     cy + d,
      cx - d, cy - d,
      cx + d, cy - d
    ];

    drawTriangle(verts);
  }
}
