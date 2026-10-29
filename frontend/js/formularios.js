// Construcción de los formularios de creación y edición.
function selectControl(name, options, value, disabled = false) {
  let html = `<select class="form-select" id="field-${name}" name="${name}" required`;
  if (disabled) html += ' disabled';
  html += '><option value="">Seleccionar…</option>';

  for (const [id, label] of options) {
    const selected = String(value) === String(id) ? 'selected' : '';
    html += `<option value="${esc(id)}" ${selected}>${esc(label)}</option>`;
  }

  return html + '</select>';
}

async function loadOptions(type, row) {
  if (type === 'estado') return [['ACTIVO', 'Activo'], ['INACTIVO', 'Inactivo']];
  if (type === 'activo') return [[1, 'Activo'], [0, 'Inactivo']];
  if (type === 'metodos') {
    return [['EFECTIVO', 'EFECTIVO'], ['TRANSFERENCIA', 'TRANSFERENCIA'], ['TARJETA', 'TARJETA']];
  }

  const path = type === 'roles' ? '/auth/roles' : '/' + type;
  const data = await api(path);
  const options = [];

  for (const record of data) {
    if (type === 'categorias') {
      options.push([record.id_categoria, record.nombre]);
    } else if (type === 'roles') {
      options.push([record.id_rol, record.nombre]);
    } else {
      const available = record.estado !== 'CANCELADO' && Number(record.saldo) > 0;
      const currentOrder = record.id_pedido === row.id_pedido;
      if (available || currentOrder) {
        const label = `#${record.id_pedido} · ${record.revendedor} · Saldo ${money(record.saldo)}`;
        options.push([record.id_pedido, label]);
      }
    }
  }

  return options;
}

function inputControl(name, type, max, value) {
  const numeric = type === 'number' || type === 'money';
  const optional = ['descripcion', 'telefono', 'referencia_transaccion'].includes(name);
  const inputType = numeric ? 'number' : type;
  let attributes = '';

  if (!optional) attributes += ' required';
  if (max) attributes += ` maxlength="${max}"`;
  if (numeric) {
    const minimum = type === 'money' ? '0.01' : '0';
    const step = type === 'money' ? '0.01' : '1';
    const maximum = type === 'money' ? '9999999999.99' : '1000000';
    attributes += ` min="${minimum}" step="${step}" max="${maximum}"`;
  }
  if (type === 'password') attributes += ' minlength="8" autocomplete="new-password"';

  return `<input class="form-control" id="field-${name}" name="${name}"
    type="${inputType}" value="${esc(value)}" ${attributes}>`;
}

async function fieldControl(field, row) {
  const [name, label, type, max] = field;
  const defaults = {estado: 'ACTIVO', activo: 1, stock_actual: 0, stock_minimo: 5};
  const value = row[name] ?? defaults[name] ?? '';
  const selectTypes = ['estado', 'activo', 'metodos', 'categorias', 'roles', 'pedidos'];
  let control;

  if (selectTypes.includes(type)) {
    const options = await loadOptions(type, row);
    const disabled = type === 'pedidos' && Boolean(editing.id);
    control = selectControl(name, options, value, disabled);
  } else {
    control = inputControl(name, type, max, value);
  }

  return `<div class="col-12 col-sm-6">
    <label class="form-label" for="field-${name}">${esc(label)}</label>
    ${control}
  </div>`;
}

async function orderFields(row) {
  const products = await api('/productos');
  let html = '';

  if (isStaff()) {
    const users = await api('/auth/revendedores');
    const options = users.map(user => [user.id_usuario, user.nombre]);
    html += `<div class="col-12">
      <label class="form-label" for="field-id_revendedor">Revendedor</label>
      ${selectControl('id_revendedor', options, row.id_revendedor)}
    </div>`;
  }

  html += `<div class="col-12">
    <p class="text-secondary small">Indica las cantidades. Deja en cero los productos que no necesitas.</p>`;

  for (const product of products) {
    if (product.estado !== 'ACTIVO') continue;
    const item = row.items?.find(item => item.id_producto === product.id_producto);
    const previous = item ? item.cantidad : 0;
    const available = product.stock_actual + previous;

    html += `<div class="order-line">
      <label for="qty-${product.id_producto}">
        ${esc(product.nombre)}<br>
        <small class="text-secondary">${esc(money(product.precio_base))} · Disponible: ${available}</small>
      </label>
      <input class="form-control order-quantity" id="qty-${product.id_producto}"
        data-product="${product.id_producto}" data-price="${product.precio_base}"
        type="number" min="0" max="${available}" step="1" value="${previous}" required>
    </div>`;
  }

  html += `</div>
    <div class="col-12"><strong id="order-total"></strong></div>
    <div class="col-12">
      <label class="form-label" for="field-observaciones">Observaciones</label>
      <input class="form-control" id="field-observaciones" name="observaciones"
        maxlength="250" value="${esc(row.observaciones || '')}">
    </div>`;
  return html;
}

function updateTotal() {
  let total = 0;
  for (const input of document.querySelectorAll('.order-quantity')) {
    total += Number(input.value) * Number(input.dataset.price);
  }
  $('#order-total').textContent = 'Total: ' + money(total);
}

async function openEditor(key, id, orderId) {
  let row = {};
  if (id) row = await api(endpoint(key) + '/' + id);
  else if (orderId) row.id_pedido = orderId;

  editing = {key, id, row};
  $('#form-error').hidden = true;
  $('#editor-title').textContent = (id ? 'Editar ' : 'Crear ') + modules[key].singular;

  if (key === 'pedidos') {
    $('#fields').innerHTML = await orderFields(row);
  } else {
    const fields = [...modules[key].fields];
    if (key === 'usuarios' && !id) {
      fields.push(['contrasena', 'Contraseña inicial', 'password', 128]);
    }

    let html = '';
    for (const field of fields) html += await fieldControl(field, row);
    $('#fields').innerHTML = html;
  }

  $('#editor').showModal();
  if (key === 'pedidos') updateTotal();
}
