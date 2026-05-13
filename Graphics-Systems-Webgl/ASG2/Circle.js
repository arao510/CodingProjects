class Circle {
  constructor(){
    this.type='circle';
    this.position = [0.0, 0.0, 0.0];  // (x, y, z) position on the canvas
    this.color = [0.0, 0.0, 0.0, 0.0]; // RGBA color values (0–1 range)
    this.size = 20.0;                   // diameter of the circle in pixels
    this.segement = 10;                 // number of triangle segments making up the circle
  }

  render(){
    var xy = this.position;  // shorthand for position
    var rgba = this.color;   // shorthand for color
    var size = this.size;    // shorthand for size

    // Set the fragment color uniform so all triangles draw in this circle's color
    gl.uniform4f(u_FragColor, rgba[0],rgba[1],rgba[2],rgba[3]);

    // Convert pixel size to normalized device coordinates (-1 to 1 range)
    // Dividing by 200 maps the size so that size=200 fills half the canvas
    var d = size/200.0;

    // Calculate the angle (in degrees) each triangle segment spans
    var angleStep = 360/this.segement;

    // Loop around 360 degrees, drawing one triangle per segment
    for (var angle = 0; angle < 360; angle += angleStep){
      var centerP = [xy[0], xy[1]];  // the center point of the circle

      var angle1 = angle;              // start angle of this segment
      var angle2 = angle + angleStep;  // end angle of this segment

      // Compute the (x, y) offset from center for the start edge vertex
      // using polar-to-cartesian conversion, scaled by radius d
      var vec1 = [Math.cos(angle1*Math.PI/180)*d, Math.sin(angle1*Math.PI/180)*d];

      // Compute the (x, y) offset for the end edge vertex
      var vec2 = [Math.cos(angle2*Math.PI/180)*d, Math.sin(angle2*Math.PI/180)*d];

      // Translate offsets into world positions by adding the circle's center
      var pt1 = [centerP[0]+vec1[0], centerP[1]+vec1[1]];
      var pt2 = [centerP[0]+vec2[0], centerP[1]+vec2[1]];

      // Draw one triangle: center → pt1 → pt2 (one "slice" of the circle)
      drawTriangle([xy[0], xy[1], pt1[0], pt1[1], pt2[0], pt2[1]]);
    }
  }
}