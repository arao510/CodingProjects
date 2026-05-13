let canvas;
let ctx;

function main() {
  canvas = document.getElementById('example');
  if (!canvas) {
    console.log('Failed to retrieve the <canvas> element');
    return;
  }

  ctx = canvas.getContext('2d');

  // Hook up buttons
  document.getElementById('drawButton').onclick = handleDrawEvent;
  document.getElementById('opDrawButton').onclick = handleDrawOperationEvent;

  // Initial draw
  handleDrawEvent();
}

// Draw just v1 (red) and v2 (blue)
function handleDrawEvent() {
  clearCanvas();

  const v1 = readVectorFromInputs('v1x', 'v1y');
  const v2 = readVectorFromInputs('v2x', 'v2y');

  drawVector(v1, "red");
  drawVector(v2, "blue");
}

function handleDrawOperationEvent() {
  // Clear canvas
  ctx.fillStyle = "black";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Read vectors
  const v1 = readVectorFromInputs('v1x', 'v1y');
  const v2 = readVectorFromInputs('v2x', 'v2y');

  // Always draw original vectors
  drawVector(v1, "red");
  drawVector(v2, "blue");

  const op = document.getElementById('opSelect').value;
  const s = parseFloat(document.getElementById('scalarInput').value);

  if (op === "add") {
    const v3 = copyVec(v1);
    v3.add(v2);
    drawVector(v3, "green");

  } else if (op === "sub") {
    const v3 = copyVec(v1);
    v3.sub(v2);
    drawVector(v3, "green");

  } else if (op === "mul") {
    const v3 = copyVec(v1);
    const v4 = copyVec(v2);
    v3.mul(s);
    v4.mul(s);
    drawVector(v3, "green");
    drawVector(v4, "green");

  } else if (op === "div") {
    const v3 = copyVec(v1);
    const v4 = copyVec(v2);
    v3.div(s);
    v4.div(s);
    drawVector(v3, "green");
    drawVector(v4, "green");

  } else if (op === "mag") {
    console.log("v1 magnitude:", v1.magnitude());
    console.log("v2 magnitude:", v2.magnitude());

  } else if (op === "norm") {
    const v3 = copyVec(v1).normalize();
    const v4 = copyVec(v2).normalize();
    drawVector(v3, "green");
    drawVector(v4, "green");

  } else if (op === "angle") {
    const angle = angleBetween(v1, v2);
    console.log("Angle between v1 and v2 (degrees):", angle);

  } else if (op === "area") {
    const area = areaTriangle(v1, v2);
    console.log("Area of triangle formed by v1 and v2:", area);
  }
}




function clearCanvas() {
  ctx.fillStyle = "black";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function readVectorFromInputs(xId, yId) {
  const x = parseFloat(document.getElementById(xId).value);
  const y = parseFloat(document.getElementById(yId).value);
  return new Vector3([x, y, 0]);
}

function copyVec(v) {
  return new Vector3([v.elements[0], v.elements[1], v.elements[2]]);
}

// Draw a vector from canvas center using scale=20
function drawVector(v, color) {
  const ox = 200;
  const oy = 200;

  const endX = ox + v.elements[0] * 20;
  const endY = oy - v.elements[1] * 20; // flip y-axis

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;

  ctx.beginPath();
  ctx.moveTo(ox, oy);
  ctx.lineTo(endX, endY);
  ctx.stroke();
}

function angleBetween(v1, v2) {
  const dot = Vector3.dot(v1, v2);
  const m1 = v1.magnitude();
  const m2 = v2.magnitude();

  // Avoid divide-by-zero
  if (m1 === 0 || m2 === 0) return NaN;

  // cos(alpha) = dot / (|v1||v2|)
  let cosAlpha = dot / (m1 * m2);

  // Clamp to [-1, 1] to avoid NaN from floating point drift
  cosAlpha = Math.max(-1, Math.min(1, cosAlpha));

  const radians = Math.acos(cosAlpha);
  const degrees = radians * 180 / Math.PI;
  return degrees;
}

function areaTriangle(v1, v2) {
  // ||v1 x v2|| is area of parallelogram -> triangle area is half
  const c = Vector3.cross(v1, v2);
  return c.magnitude() / 2;
}
