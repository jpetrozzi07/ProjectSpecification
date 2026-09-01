// Fetch /api/matrix (POST) and render with Bootstrap grid.
// Expects server JSON: { result: { values, y_labels, x_labels } }
// The first column displays y_labels and the column headers correspond to x_labels.

async function fetchAndRenderMatrix(apiPath = '/api/matrix') {
  try {
    const resp = await fetch(apiPath, { method: 'POST' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const payload = await resp.json();
    const data = payload && payload.result ? payload.result : null;

    if (!data || !data.values || !data.y_labels || !data.x_labels) {
      document.getElementById('matrix-container').textContent = 'Unexpected data shape from server';
      console.error('Unexpected result shape', payload);
      return;
    }

    const values = data.values;
    const yLabels = Array.from(data.y_labels);
    const xLabels = Array.from(data.x_labels);

    renderMatrix(values, yLabels, xLabels, 'matrix-container');
  } catch (err) {
    console.error(err);
    const el = document.getElementById('matrix-container');
    if (el) el.textContent = 'Error loading matrix: ' + err;
  }
}

function renderMatrix(values, yLabels, xLabels, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  const rows = yLabels.length;
  const cols = xLabels.length;

  let grid;
  if (Array.isArray(values) && values.length === rows && Array.isArray(values[0])) {
    grid = values;
  } else {
    const flat = flatten(values);
    if (flat.length !== rows * cols) {
      // Best-effort reshape: fill missing with empty string
      grid = [];
      for (let r = 0; r < rows; r++) {
        const row = [];
        for (let c = 0; c < cols; c++) {
          const idx = r * cols + c;
          row.push(idx < flat.length ? flat[idx] : '');
        }
        grid.push(row);
      }
    } else {
      grid = [];
      for (let r = 0; r < rows; r++) {
        grid.push(flat.slice(r * cols, (r + 1) * cols));
      }
    }
  }

  // Header row: empty top-left + x labels
  const headerRow = document.createElement('div');
  headerRow.className = 'row header mb-0';
  headerRow.appendChild(makeCell('', 'col-2 first-col'));
  xLabels.forEach(x => headerRow.appendChild(makeCell(x, 'col')));
  container.appendChild(headerRow);

  // Data rows
  for (let r = 0; r < rows; r++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'row mb-0';
    rowDiv.appendChild(makeCell(yLabels[r] ?? '', 'col-2 first-col'));
    for (let c = 0; c < cols; c++) {
      const value = (grid[r] && typeof grid[r][c] !== 'undefined') ? grid[r][c] : '';
      rowDiv.appendChild(makeCell(formatValue(value), 'col'));
    }
    container.appendChild(rowDiv);
  }
}

function makeCell(content, colClass = 'col') {
  const div = document.createElement('div');
  div.className = `cell ${colClass}`;
  div.textContent = content;
  return div;
}

function formatValue(v) {
  if (v === null || typeof v === 'undefined') return '';
  if (typeof v === 'number' || typeof v === 'string' || typeof v === 'boolean') return String(v);
  try { return JSON.stringify(v); } catch { return String(v); }
}

function flatten(arr) {
  const out = [];
  (function f(a) {
    if (a == null) return;
    if (!Array.isArray(a)) {
      out.push(a);
      return;
    }
    for (const el of a) {
      if (Array.isArray(el)) f(el);
      else out.push(el);
    }
  })(arr);
  return out;
}

document.addEventListener('DOMContentLoaded', () => fetchAndRenderMatrix());