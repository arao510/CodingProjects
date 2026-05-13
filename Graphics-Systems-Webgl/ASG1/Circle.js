// Circle.js

class Circle {
  constructor(position, color, size, segments) {
    this.position = position;   // [x,y]
    this.color = color;         // [r,g,b,a]
    this.size = size;           // float
    this.segments = segments;   // int
  }

  render() {
    gl.uniform4f(u_FragColor, this.color[0], this.color[1], this.color[2], this.color[3]);

    const cx = this.position[0];
    const cy = this.position[1];
    const r = this.size / 200.0;

    const step = (2 * Math.PI) / this.segments;

    // draw as triangles: center + edge(i) + edge(i+1)
    for (let i = 0; i < this.segments; i++) {
      const a1 = i * step;
      const a2 = (i + 1) * step;

      const x1 = cx + r * Math.cos(a1);
      const y1 = cy + r * Math.sin(a1);
      const x2 = cx + r * Math.cos(a2);
      const y2 = cy + r * Math.sin(a2);

      drawTriangle([
        cx, cy,
        x1, y1,
        x2, y2
      ]);
    }
  }
}

