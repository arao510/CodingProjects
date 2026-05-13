class Point {
    constructor(){
      this.type='point';
      this.position = [0.0, 0.0, 0.0];  // (x, y, z) position of the point
      this.color = [0.0, 0.0, 0.0, 0.0]; // RGBA color values (0–1 range)
      this.size = 20.0;                   // size of the point in pixels (maps to gl_PointSize)
      this.segement = 10;                 // unused for points, kept for consistency with other shapes
    }

    render(){
      var xy = this.position;   // shorthand for position
      var rgba = this.color;    // shorthand for color
      var size = this.size;     // shorthand for size

      gl.disableVertexAttribArray(a_Position);

      // Directly set the position of this single vertex to (x, y, 0).
      // The z component is hardcoded to 0 since points are 2D in this context.
      gl.vertexAttrib3f(a_Position, xy[0], xy[1], 0.0);

      // Set the fragment color uniform so the point draws in this color
      gl.uniform4f(u_FragColor, rgba[0],rgba[1],rgba[2],rgba[3]);

      gl.uniform1f(u_Size, size);
      // gl.POINTS renders each vertex as a square dot sized by gl_PointSize.
      gl.drawArrays(gl.POINTS, 0, 1);
    }
  }