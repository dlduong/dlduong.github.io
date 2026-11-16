"use strict";

const byId = (id) => document.getElementById(id);

function bindControls(ids, update) {
  for (const id of ids) {
    const control = byId(id);
    control.addEventListener(control.tagName === "SELECT" ? "change" : "input", update);
  }
  update();
}

function renderMatrixTest() {
  const wx = Number(byId("weight-x").value);
  const wy = Number(byId("weight-y").value);
  const weighted = byId("matrix-mode").value === "weighted";
  const first = weighted ? wy / wx : 1;
  const second = weighted ? 2 * wy - 1 : 1;
  const left = 3 * wy - 1;
  const right = wx * first + second;
  byId("matrix-result").textContent =
    "wX = " + wx.toFixed(1) + " · wY = " + wy.toFixed(1) +
    " · A*r = (" + first.toFixed(3) + ", " + second.toFixed(3) + ")" +
    " · pairings " + left.toFixed(3) + " and " + right.toFixed(3) +
    " · |difference| = " + Math.abs(left - right).toExponential(1);
}

function diskChordLength(offset, radius) {
  return 2 * Math.sqrt(Math.max(0, radius * radius - offset * offset));
}

function renderBackprojection() {
  const count = Number(byId("view-count").value);
  const cx = Number(byId("disk-x").value);
  const cy = Number(byId("disk-y").value);
  const radius = 0.28;
  const object = byId("object-image");
  const back = byId("back-image");
  const objectCtx = object.getContext("2d");
  const backCtx = back.getContext("2d");
  if (!objectCtx || !backCtx) return;

  const width = back.width;
  const height = back.height;
  const image = backCtx.createImageData(width, height);
  const normals = Array.from({ length: count }, (_, i) => {
    const angle = Math.PI * i / count;
    return [Math.cos(angle), Math.sin(angle)];
  });
  const displayMax = 2 * radius * Math.PI;

  for (let j = 0; j < height; j += 1) {
    const y = 1 - (2 * j + 1) / height - cy;
    for (let i = 0; i < width; i += 1) {
      const x = (2 * i + 1) / width - 1 - cx;
      let integral = 0;
      for (const [nx, ny] of normals) {
        integral += diskChordLength(x * nx + y * ny, radius);
      }
      const value = integral * Math.PI / count;
      const level = Math.min(1, value / displayMax);
      const pixel = 4 * (j * width + i);
      image.data[pixel] = 15 + 230 * level;
      image.data[pixel + 1] = 39 + 161 * level;
      image.data[pixel + 2] = 49 + 68 * level;
      image.data[pixel + 3] = 255;
    }
  }
  backCtx.putImageData(image, 0, 0);

  const px = object.width * (1 + cx) / 2;
  const py = object.height * (1 - cy) / 2;
  objectCtx.fillStyle = "#0f2731";
  objectCtx.fillRect(0, 0, object.width, object.height);
  objectCtx.beginPath();
  objectCtx.arc(px, py, radius * object.width / 2, 0, 2 * Math.PI);
  objectCtx.fillStyle = "#77c3dc";
  objectCtx.fill();
  objectCtx.beginPath();
  objectCtx.moveTo(px, 0);
  objectCtx.lineTo(px, object.height);
  objectCtx.strokeStyle = "#f5c875";
  objectCtx.setLineDash([6, 5]);
  objectCtx.stroke();
  objectCtx.setLineDash([]);

  byId("back-result").textContent =
    count + (count === 1 ? " view" : " views") +
    " · centre (" + cx.toFixed(2) + ", " + cy.toFixed(2) + ")" +
    " · fixed colour scale 0 to " + displayMax.toFixed(2) +
    " · yellow dashed line marks the central ray for view 1";
}

// Solve the linear finite-element system with homogeneous Dirichlet endpoints.
// Each element contributes exp(m[e]) / dx times the 2-by-2 local stiffness matrix.
function solveDirichlet(m, rhs) {
  const elements = m.length;
  const interior = elements - 1;
  const conductivity = m.map((value) => Math.exp(value) * elements);
  const upper = new Array(interior).fill(0);
  const modifiedRhs = new Array(interior).fill(0);
  for (let i = 0; i < interior; i += 1) {
    const lower = i === 0 ? 0 : -conductivity[i];
    const diagonal = conductivity[i] + conductivity[i + 1];
    const pivot = i === 0 ? diagonal : diagonal - lower * upper[i - 1];
    const adjusted = i === 0 ? rhs[i] : rhs[i] - lower * modifiedRhs[i - 1];
    upper[i] = i === interior - 1 ? 0 : -conductivity[i + 1] / pivot;
    modifiedRhs[i] = adjusted / pivot;
  }

  const solution = new Array(elements + 1).fill(0);
  for (let i = interior - 1; i >= 0; i -= 1) {
    solution[i + 1] = modifiedRhs[i] - upper[i] * solution[i + 2];
  }
  return solution;
}

function evaluateMisfit(m) {
  const dx = 1 / m.length;
  const load = new Array(m.length - 1).fill(dx);
  const u = solveDirichlet(m, load);
  const predicted = dx * u.reduce((total, value) => total + value, 0);
  const residual = predicted - 0.11;
  return { u, predicted, residual, value: 0.5 * residual * residual };
}

function renderTaylorTest() {
  const elements = 48;
  const dx = 1 / elements;
  const m = Array.from({ length: elements }, (_, e) =>
    0.36 * Math.sin(2 * Math.PI * (e + 0.5) * dx)
  );
  const constant = byId("direction").value === "constant";
  const h = m.map((_, e) => constant ? 1 : 0.65 + 0.4 * Math.cos(2 * Math.PI * (e + 0.5) * dx));
  const base = evaluateMisfit(m);
  const adjointLoad = new Array(elements - 1).fill(dx * base.residual);
  const p = solveDirichlet(m, adjointLoad);
  const derivative = m.reduce((sum, value, e) =>
    sum - Math.exp(value) * (base.u[e + 1] - base.u[e]) * (p[e + 1] - p[e]) * h[e] / dx, 0
  );
  const signed = byId("gradient-mode").value === "correct" ? derivative : -derivative;
  byId("pde-result").textContent =
    "Cu = " + base.predicted.toFixed(6) + " · residual = " + base.residual.toFixed(6) +
    " · candidate derivative = " + signed.toExponential(4);

  const tableBody = byId("taylor-rows");
  tableBody.replaceChildren();
  const initialStep = Number(byId("step").value);
  let previous = null;
  for (let k = 0; k < 6; k += 1) {
    const step = initialStep * 2 ** (-k);
    const perturbed = evaluateMisfit(m.map((value, e) => value + step * h[e]));
    const change = perturbed.value - base.value;
    const corrected = Math.abs(change - step * signed);
    const order = previous && corrected > 0 ? Math.log2(previous / corrected).toFixed(3) : "–";
    const row = tableBody.insertRow();
    for (const cell of [step.toExponential(2), Math.abs(change).toExponential(3), corrected.toExponential(3), order]) {
      row.insertCell().textContent = cell;
    }
    previous = corrected;
  }
}

bindControls(["weight-x", "weight-y", "matrix-mode"], renderMatrixTest);
bindControls(["view-count", "disk-x", "disk-y"], renderBackprojection);
bindControls(["step", "direction", "gradient-mode"], renderTaylorTest);
