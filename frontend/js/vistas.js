// Tablas, filtros y vistas de la aplicación.
function message(text, error = false) {
  $('#message').textContent = text;
  $('#message').className = 'alert ' + (error ? 'alert-danger' : 'alert-success');
  $('#message').hidden = false;
}

function heading(title, action = '') {
  return `<div class="page-heading"><h1>${esc(title)}</h1>${action}</div>`;
}

function format(key, value) {
  if (monetary.includes(key)) return esc(money(value));
  if (key === 'activo') return value ? 'ACTIVO' : 'INACTIVO';
  if (key.startsWith('fecha_')) return esc(new Date(value).toLocaleString('es-CO'));
  return esc(value ?? '—');
}

function table(data, columns, actions) {
  if (!data.length) return '<p class="empty">No hay registros para mostrar.</p>';
  let html = '<div class="table-responsive"><table class="table"><thead><tr>';

  for (const key of columns) {
    html += `<th scope="col">${esc(labels[key] || key)}</th>`;
  }
  if (actions) html += '<th scope="col">Acciones</th>';
  html += '</tr></thead><tbody>';

  for (const row of data) {
    html += '<tr>';
    for (const key of columns) html += `<td>${format(key, row[key])}</td>`;
    if (actions) html += `<td class="actions">${actions(row)}</td>`;
    html += '</tr>';
  }

  return html + '</tbody></table></div>';
}

function canCreate(key) {
  if (key === 'pedidos') return true;
  if (key === 'pagos') return isStaff();
  return isAdmin();
}

function actions(key, row) {
  const id = row[modules[key].pk];
  let html = '';
  let edit = isAdmin();
  let remove = isAdmin();

  if (key === 'pedidos') {
    html = `<a class="btn btn-sm btn-light" href="#pedido/${id}">Ver</a>`;
    edit = row.estado === 'PENDIENTE' && Number(row.total_pagado) === 0;
    remove = edit;
  }
  if (key === 'pagos' && row.estado_pago === 'ANULADO') {
    edit = false;
    remove = false;
  }
  if (key === 'usuarios' && (id === user.id_usuario || !row.activo)) remove = false;
  if (row.estado === 'INACTIVO') remove = false;

  if (edit) {
    html += `<button class="btn btn-sm btn-outline-secondary"
      data-edit="${id}" data-module="${key}">Editar</button>`;
  }
  let label = 'Desactivar';
  if (key === 'pedidos') label = 'Cancelar';
  if (key === 'pagos') label = 'Anular';
  if (remove) {
    html += `<button class="btn btn-sm btn-outline-danger"
      data-delete="${id}" data-module="${key}">${label}</button>`;
  }
  return html;
}

function filters(key) {
  let html = '';
  if (['categorias', 'productos', 'usuarios'].includes(key)) {
    html += `<div class="search">
      <label class="form-label" for="search">Buscar</label>
      <input id="search" name="q" class="form-control" maxlength="100"
        placeholder="Nombre, código o correo">
    </div>`;
  }

  if (key === 'productos' || key === 'pedidos') {
    const states = key === 'productos'
      ? ['ACTIVO', 'INACTIVO']
      : ['PENDIENTE', 'CONFIRMADO', 'CANCELADO'];
    html += `<div>
      <label class="form-label" for="filter-state">Estado</label>
      <select id="filter-state" name="estado" class="form-select">
        <option value="">Todos</option>`;
    for (const state of states) html += `<option>${state}</option>`;
    html += '</select></div>';
  }

  if (key === 'pagos') {
    html += `<div>
      <label class="form-label" for="filter-order">Número de pedido</label>
      <input id="filter-order" name="id_pedido" class="form-control"
        type="number" min="1" step="1">
    </div>`;
  }
  return html + `<button class="btn btn-outline-secondary">Buscar</button>
    <button class="btn btn-light" type="reset">Limpiar</button>`;
}

async function showModule(key, version) {
  const config = modules[key];
  if (key === 'usuarios' && !isAdmin()) {
    throw new Error('Se requiere una cuenta de administrador.');
  }

  let addButton = '';
  if (canCreate(key)) {
    addButton = `<button class="btn btn-primary" data-new="${key}">
      + Crear ${esc(config.singular)}</button>`;
  }
  $('#view').innerHTML = heading(config.title, addButton) + `
    <section class="panel">
      <form id="filters" class="filters">${filters(key)}</form>
      <div id="results"></div>
    </section>`;

  let requestVersion = 0;
  async function load() {
    const request = ++requestVersion;
    const params = new URLSearchParams();
    for (const [name, value] of new FormData($('#filters'))) {
      if (value.trim()) params.set(name, value.trim());
    }

    try {
      const data = await api(endpoint(key) + '?' + params);
      if (version !== routeVersion || request !== requestVersion) return;
      $('#results').innerHTML = table(data, config.columns, row => actions(key, row));
    } catch (error) {
      if (version === routeVersion) message(error.message, true);
    }
  }

  $('#filters').onsubmit = event => {
    event.preventDefault();
    load();
  };
  $('#filters').onreset = () => setTimeout(load, 0);
  await load();
}

async function showDashboard(version) {
  const data = await api('/reportes/dashboard');
  if (version !== routeVersion) return;
  const names = {
    productos_activos: 'Productos activos',
    stock_bajo: 'Productos con stock bajo',
    pedidos_pendientes: 'Pedidos pendientes',
    ventas: 'Ventas',
    recaudado: 'Recaudado',
    saldo: 'Saldo pendiente'
  };

  let html = heading('Resumen') + '<div class="stats">';
  for (const [key, value] of Object.entries(data)) {
    const isMoney = ['ventas', 'recaudado', 'saldo'].includes(key);
    const formattedValue = isMoney ? money(value) : value;
    html += `<article class="stat">
      <span>${esc(names[key])}</span>
      <strong>${esc(formattedValue)}</strong>
    </article>`;
  }
  $('#view').innerHTML = html + '</div>';
}

async function showReports(version) {
  $('#view').innerHTML = heading('Reportes') + `
    <section class="panel">
      <form id="report-form" class="filters">
        <div>
          <label class="form-label" for="report-kind">Consulta</label>
          <select id="report-kind" class="form-select">
            <option value="ventas-revendedor">Ventas por revendedor</option>
            <option value="inventario">Inventario y stock bajo</option>
          </select>
        </div>
        <button class="btn btn-primary">Consultar</button>
      </form>
      <div id="report-results"></div>
    </section>`;

  let requestVersion = 0;
  async function load() {
    const request = ++requestVersion;
    try {
      const kind = $('#report-kind').value;
      const data = await api('/reportes/' + kind);
      if (version !== routeVersion || request !== requestVersion) return;
      const columns = kind === 'inventario'
        ? ['codigo', 'producto', 'stock', 'minimo', 'valor_inventario', 'nivel']
        : ['revendedor', 'pedidos', 'ventas'];
      $('#report-results').innerHTML = table(data, columns);
    } catch (error) {
      if (version === routeVersion) message(error.message, true);
    }
  }

  $('#report-form').onsubmit = event => {
    event.preventDefault();
    load();
  };
  await load();
}

async function showOrder(id, version) {
  const [order, payments] = await Promise.all([
    api('/pedidos/' + id),
    api('/pagos?id_pedido=' + id)
  ]);
  if (version !== routeVersion) return;

  let paymentButton = '';
  if (isStaff() && order.estado !== 'CANCELADO' && Number(order.saldo) > 0) {
    paymentButton = `<button class="btn btn-primary" data-new="pagos"
      data-order="${id}">Registrar pago</button>`;
  }
  const productColumns = ['producto', 'cantidad', 'precio_unitario', 'subtotal'];
  const productsTable = table(order.items, productColumns);
  const paymentsTable = table(payments, modules.pagos.columns, row => actions('pagos', row));
  const back = '<a class="btn btn-light" href="#pedidos">Volver</a>';

  $('#view').innerHTML = heading('Pedido #' + id, back) + `
    <p>${esc(order.revendedor)} · ${esc(order.estado)} ·
      Total: ${esc(money(order.total))} · Pagado: ${esc(money(order.total_pagado))} ·
      Saldo: ${esc(money(order.saldo))}</p>
    <p>${esc(order.observaciones)}</p>
    <h2 class="h5 mt-4">Productos</h2>
    <section class="panel">${productsTable}</section>
    <div class="page-heading mt-4">
      <h2 class="h5 mb-0">Pagos</h2>${paymentButton}
    </div>
    <section class="panel">${paymentsTable}</section>`;
}
