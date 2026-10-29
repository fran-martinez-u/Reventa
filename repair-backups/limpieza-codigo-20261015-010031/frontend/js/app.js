// Navegación, tablas y formularios de los cinco módulos.
const $ = selector => document.querySelector(selector);
let user, rows = [], editing, routeVersion = 0;

const modules = {
  categorias: {
    title:'Categorías', singular:'categoría', pk:'id_categoria',
    columns:['nombre','descripcion','estado'],
    fields:[['nombre','Nombre','text',80],['descripcion','Descripción','text',200],['estado','Estado','estado']]
  },
  productos: {
    title:'Productos', singular:'producto', pk:'id_producto',
    columns:['codigo','nombre','categoria','precio_base','precio_reventa_sugerido','stock_actual','estado'],
    fields:[['codigo','Código','text',30],['nombre','Nombre','text',120],['id_categoria','Categoría','categorias'],
      ['descripcion','Descripción','text',250],['precio_base','Precio base','money'],
      ['precio_reventa_sugerido','Precio sugerido','money'],['stock_actual','Existencias','number'],
      ['stock_minimo','Stock mínimo','number'],['estado','Estado','estado']]
  },
  pedidos: {
    title:'Pedidos', singular:'pedido', pk:'id_pedido',
    columns:['id_pedido','revendedor','fecha_pedido','estado','total','total_pagado','saldo']
  },
  pagos: {
    title:'Pagos', singular:'pago', pk:'id_pago',
    columns:['id_pago','id_pedido','fecha_pago','monto','metodo_pago','estado_pago'],
    fields:[['id_pedido','Pedido','pedidos'],['monto','Monto','money'],['metodo_pago','Método','metodos'],
      ['referencia_transaccion','Referencia','text',60]]
  },
  usuarios: {
    title:'Usuarios', singular:'usuario', pk:'id_usuario', endpoint:'auth/usuarios',
    columns:['nombre','correo','rol','activo'],
    fields:[['nombre','Nombre completo','text',100],['correo','Correo','email',120],
      ['telefono','Teléfono','tel',20],['id_rol','Rol','roles'],['activo','Estado','activo']]
  }
};
const labels = {
  nombre:'Nombre', descripcion:'Descripción', estado:'Estado', codigo:'Código', categoria:'Categoría',
  precio_base:'Precio base', precio_reventa_sugerido:'Precio sugerido', stock_actual:'Stock',
  id_pedido:'Pedido', revendedor:'Revendedor', fecha_pedido:'Fecha', total:'Total', total_pagado:'Pagado',
  saldo:'Saldo', id_pago:'Pago', fecha_pago:'Fecha', monto:'Monto', metodo_pago:'Método', estado_pago:'Estado',
  correo:'Correo', rol:'Rol', activo:'Estado', producto:'Producto', cantidad:'Cantidad',
  precio_unitario:'Precio unitario', subtotal:'Subtotal', pedidos:'Pedidos', ventas:'Ventas', stock:'Stock',
  minimo:'Mínimo', valor_inventario:'Valor del inventario', nivel:'Nivel'
};
const monetary = ['precio_base','precio_reventa_sugerido','total','total_pagado','saldo','monto',
  'precio_unitario','subtotal','ventas','valor_inventario'];
const isAdmin = () => user.rol === 'ADMIN';
const isStaff = () => ['ADMIN','VENDEDOR'].includes(user.rol);
const endpoint = key => '/' + (modules[key].endpoint || key);

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
  return `<div class="table-responsive"><table class="table"><thead><tr>
    ${columns.map(key => `<th scope="col">${esc(labels[key] || key)}</th>`).join('')}
    ${actions ? '<th scope="col">Acciones</th>' : ''}</tr></thead><tbody>
    ${data.map(row => `<tr>${columns.map(key => `<td>${format(key,row[key])}</td>`).join('')}
      ${actions ? `<td class="actions">${actions(row)}</td>` : ''}</tr>`).join('')}
    </tbody></table></div>`;
}

function canCreate(key) {
  return key === 'pedidos' || (key === 'pagos' ? isStaff() : isAdmin());
}

function actions(key, row) {
  const id = row[modules[key].pk];
  let html = key === 'pedidos' ? `<a class="btn btn-sm btn-light" href="#pedido/${id}">Ver</a>` : '';
  let edit = isAdmin(), remove = isAdmin();
  if (key === 'pedidos') edit = remove = row.estado === 'PENDIENTE' && Number(row.total_pagado) === 0;
  if (key === 'pagos' && row.estado_pago === 'ANULADO') edit = remove = false;
  if (key === 'usuarios' && id === user.id_usuario) remove = false;
  if ((key === 'usuarios' && !row.activo) || row.estado === 'INACTIVO') remove = false;
  if (edit) html += `<button class="btn btn-sm btn-outline-secondary" data-edit="${id}" data-module="${key}">Editar</button>`;
  const label = key === 'pedidos' ? 'Cancelar' : key === 'pagos' ? 'Anular' : 'Desactivar';
  if (remove) html += `<button class="btn btn-sm btn-outline-danger" data-delete="${id}" data-module="${key}">${label}</button>`;
  return html;
}

function filters(key) {
  let html = '';
  if (['categorias','productos','usuarios'].includes(key)) {
    html += '<div class="search"><label class="form-label" for="search">Buscar</label><input id="search" name="q" class="form-control" maxlength="100" placeholder="Nombre, código o correo"></div>';
  }
  if (['productos','pedidos'].includes(key)) {
    const states = key === 'productos' ? ['ACTIVO','INACTIVO'] : ['PENDIENTE','CONFIRMADO','CANCELADO'];
    html += `<div><label class="form-label" for="filter-state">Estado</label><select id="filter-state" name="estado" class="form-select"><option value="">Todos</option>${states.map(s=>`<option>${s}</option>`).join('')}</select></div>`;
  }
  if (key === 'pagos') html += '<div><label class="form-label" for="filter-order">Número de pedido</label><input id="filter-order" name="id_pedido" class="form-control" type="number" min="1" step="1"></div>';
  return html + '<button class="btn btn-outline-secondary">Buscar</button><button class="btn btn-light" type="reset">Limpiar</button>';
}

async function showModule(key, version) {
  const config = modules[key];
  if (key === 'usuarios' && !isAdmin()) throw new Error('Se requiere una cuenta de administrador.');
  const add = canCreate(key) ? `<button class="btn btn-primary" data-new="${key}">+ Crear ${esc(config.singular)}</button>` : '';
  $('#view').innerHTML = heading(config.title, add) + `<section class="panel"><form id="filters" class="filters">${filters(key)}</form><div id="results"></div></section>`;
  let requestVersion = 0;
  const load = async () => {
    const request = ++requestVersion;
    const params = new URLSearchParams();
    for (const [key,value] of new FormData($('#filters'))) if (value.trim()) params.set(key,value.trim());
    try {
      const data = await api(endpoint(key) + '?' + params);
      if (version !== routeVersion || request !== requestVersion) return;
      rows = data;
      $('#results').innerHTML = table(data, config.columns, row => actions(key,row));
    } catch (error) { if (version === routeVersion) message(error.message,true); }
  };
  $('#filters').onsubmit = event => { event.preventDefault(); load(); };
  $('#filters').onreset = () => { setTimeout(load,0); };
  await load();
}

async function showDashboard(version) {
  const data = await api('/reportes/dashboard');
  if (version !== routeVersion) return;
  const names = {productos_activos:'Productos activos',stock_bajo:'Productos con stock bajo',
    pedidos_pendientes:'Pedidos pendientes',ventas:'Ventas',recaudado:'Recaudado',saldo:'Saldo pendiente'};
  $('#view').innerHTML = heading('Resumen') + '<div class="stats">' + Object.entries(data).map(([key,value]) =>
    `<article class="stat"><span>${esc(names[key])}</span><strong>${esc(['ventas','recaudado','saldo'].includes(key)?money(value):value)}</strong></article>`).join('') + '</div>';
}

async function showReports(version) {
  $('#view').innerHTML = heading('Reportes') + `<section class="panel"><form id="report-form" class="filters"><div><label class="form-label" for="report-kind">Consulta</label><select id="report-kind" class="form-select"><option value="ventas-revendedor">Ventas por revendedor</option><option value="inventario">Inventario y stock bajo</option></select></div><button class="btn btn-primary">Consultar</button></form><div id="report-results"></div></section>`;
  let requestVersion = 0;
  const load = async () => {
    const request = ++requestVersion;
    try {
      const kind = $('#report-kind').value;
      const data = await api('/reportes/' + kind);
      if (version !== routeVersion || request !== requestVersion) return;
      const columns = kind === 'inventario' ? ['codigo','producto','stock','minimo','valor_inventario','nivel'] : ['revendedor','pedidos','ventas'];
      $('#report-results').innerHTML = table(data,columns);
    } catch (error) { if (version === routeVersion) message(error.message,true); }
  };
  $('#report-form').onsubmit = event => { event.preventDefault(); load(); };
  await load();
}

async function showOrder(id, version) {
  const [order,payments] = await Promise.all([api('/pedidos/'+id),api('/pagos?id_pedido='+id)]);
  if (version !== routeVersion) return;
  $('#view').innerHTML = heading('Pedido #' + id, '<a class="btn btn-light" href="#pedidos">Volver</a>') +
    `<p>${esc(order.revendedor)} · ${esc(order.estado)} · Total: ${esc(money(order.total))} · Pagado: ${esc(money(order.total_pagado))} · Saldo: ${esc(money(order.saldo))}</p>
    <p>${esc(order.observaciones)}</p><h2 class="h5 mt-4">Productos</h2><section class="panel">${table(order.items,['producto','cantidad','precio_unitario','subtotal'])}</section>
    <div class="page-heading mt-4"><h2 class="h5 mb-0">Pagos</h2>${isStaff() && order.estado !== 'CANCELADO' && Number(order.saldo)>0 ? `<button class="btn btn-primary" data-new="pagos" data-order="${id}">Registrar pago</button>`:''}</div><section class="panel">${table(payments,modules.pagos.columns,row=>actions('pagos',row))}</section>`;
}

async function route() {
  const version = ++routeVersion;
  const key = location.hash.slice(1) || 'dashboard';
  $('#message').hidden = true;
  $('#view').innerHTML = '<p class="empty">Cargando…</p>';
  document.querySelectorAll('[data-nav]').forEach(a => a.classList.toggle('active',a.dataset.nav === (key.startsWith('pedido/')?'pedidos':key)));
  try {
    if (key === 'dashboard') await showDashboard(version);
    else if (key === 'reportes') await showReports(version);
    else if (/^pedido\/\d+$/.test(key)) await showOrder(Number(key.split('/')[1]),version);
    else if (modules[key]) await showModule(key,version);
    else location.hash = 'dashboard';
  } catch (error) {
    if (version === routeVersion) { $('#view').innerHTML = '<p class="empty">No se pudo cargar esta sección.</p>'; message(error.message,true); }
  }
}

function selectControl(name, options, value, disabled = false) {
  return `<select class="form-select" id="field-${name}" name="${name}" required ${disabled?'disabled':''}><option value="">Seleccionar…</option>${options.map(([id,label])=>`<option value="${esc(id)}" ${String(value)===String(id)?'selected':''}>${esc(label)}</option>`).join('')}</select>`;
}

async function fieldControl(field, row) {
  const [name,label,type,max] = field;
  const value = row[name] ?? ({estado:'ACTIVO',activo:1,stock_actual:0,stock_minimo:5})[name] ?? '';
  let control;
  if (['estado','activo','metodos'].includes(type)) {
    const options = type === 'estado' ? [['ACTIVO','Activo'],['INACTIVO','Inactivo']] : type === 'activo' ? [[1,'Activo'],[0,'Inactivo']] : ['EFECTIVO','TRANSFERENCIA','TARJETA'].map(s=>[s,s]);
    control = selectControl(name,options,value);
  } else if (['categorias','roles','pedidos'].includes(type)) {
    const data = await api(type === 'roles'?'/auth/roles':'/'+type);
    const pk = type === 'categorias'?'id_categoria':type === 'roles'?'id_rol':'id_pedido';
    const options = data.filter(r=>type !== 'pedidos'||(r.estado!=='CANCELADO'&&Number(r.saldo)>0)||r[pk]===row.id_pedido).map(r=>[r[pk],r.nombre||`#${r.id_pedido} · ${r.revendedor} · Saldo ${money(r.saldo)}`]);
    control = selectControl(name,options,value,type==='pedidos'&&!!editing.id);
  } else {
    const numeric = ['number','money'].includes(type);
    const optional = ['descripcion','telefono','referencia_transaccion'].includes(name);
    control = `<input class="form-control" id="field-${name}" name="${name}" type="${numeric?'number':type}" value="${esc(value)}" ${optional?'':'required'} ${max?`maxlength="${max}"`:''} ${numeric?`min="${type==='money'?'0.01':'0'}" step="${type==='money'?'0.01':'1'}" max="${type==='money'?'9999999999.99':'1000000'}"`:''} ${type==='password'?'minlength="8" autocomplete="new-password"':''}>`;
  }
  return `<div class="col-12 col-sm-6"><label class="form-label" for="field-${name}">${esc(label)}</label>${control}</div>`;
}

async function orderFields(row) {
  const products = await api('/productos');
  let html = '';
  if (isStaff()) {
    const users = await api('/auth/revendedores');
    html += `<div class="col-12"><label class="form-label" for="field-id_revendedor">Revendedor</label>${selectControl('id_revendedor',users.map(u=>[u.id_usuario,u.nombre]),row.id_revendedor)}</div>`;
  }
  html += '<div class="col-12"><p class="text-secondary small">Indica las cantidades. Deja en cero los productos que no necesitas.</p>';
  for (const product of products.filter(p=>p.estado==='ACTIVO')) {
    const previous = row.items?.find(i=>i.id_producto===product.id_producto)?.cantidad || 0;
    const available = product.stock_actual + previous;
    html += `<div class="order-line"><label for="qty-${product.id_producto}">${esc(product.nombre)}<br><small class="text-secondary">${esc(money(product.precio_base))} · Disponible: ${available}</small></label><input class="form-control order-quantity" id="qty-${product.id_producto}" data-product="${product.id_producto}" data-price="${product.precio_base}" type="number" min="0" max="${available}" step="1" value="${previous}" required></div>`;
  }
  html += '</div><div class="col-12"><strong id="order-total"></strong></div>';
  html += `<div class="col-12"><label class="form-label" for="field-observaciones">Observaciones</label><input class="form-control" id="field-observaciones" name="observaciones" maxlength="250" value="${esc(row.observaciones||'')}"></div>`;
  return html;
}

function updateTotal() {
  const total = [...document.querySelectorAll('.order-quantity')].reduce((sum,input)=>sum+Number(input.value)*Number(input.dataset.price),0);
  $('#order-total').textContent = 'Total: ' + money(total);
}

async function openEditor(key, id, orderId) {
  const row = id ? await api(endpoint(key)+'/'+id) : (orderId?{id_pedido:orderId}:{});
  editing = {key,id,row};
  $('#form-error').hidden = true;
  $('#editor-title').textContent = (id?'Editar ':'Crear ') + modules[key].singular;
  if (key === 'pedidos') $('#fields').innerHTML = await orderFields(row);
  else {
    const fields = [...modules[key].fields];
    if (key === 'usuarios' && !id) fields.push(['contrasena','Contraseña inicial','password',128]);
    let html = '';
    for (const field of fields) html += await fieldControl(field,row);
    $('#fields').innerHTML = html;
  }
  $('#editor').showModal();
  if (key === 'pedidos') updateTotal();
}

$('#edit-form').onsubmit = async event => {
  event.preventDefault();
  const {key,id,row} = editing;
  const data = Object.fromEntries(new FormData(event.target));
  $('#save-button').disabled = true;
  $('#form-error').hidden = true;
  try {
    for (const name of ['id_categoria','id_rol','id_pedido','id_revendedor','stock_actual','stock_minimo','activo']) if (name in data) data[name] = Number(data[name]);
    if (key === 'pagos' && id) data.id_pedido = row.id_pedido;
    if (key === 'pedidos') {
      data.items = [...document.querySelectorAll('.order-quantity')].filter(input=>Number(input.value)>0).map(input=>({id_producto:Number(input.dataset.product),cantidad:Number(input.value)}));
      if (!data.items.length) throw new Error('Selecciona al menos un producto.');
    }
    await api(endpoint(key)+(id?'/'+id:''),id?'PUT':'POST',data);
    $('#editor').close();
    await route();
    message('Registro guardado correctamente.');
  } catch (error) { $('#form-error').textContent = error.message; $('#form-error').hidden = false; }
  finally { $('#save-button').disabled = false; }
};

$('#view').onclick = async event => {
  const button = event.target.closest('[data-new],[data-edit],[data-delete]');
  if (!button) return;
  try {
    if (button.dataset.new) return await openEditor(button.dataset.new,null,Number(button.dataset.order)||null);
    const key = button.dataset.module;
    if (button.dataset.edit) return await openEditor(key,Number(button.dataset.edit));
    const text = key === 'pedidos'?'¿Cancelar el pedido y devolver las existencias?':key==='pagos'?'¿Anular este pago?':'¿Desactivar este registro?';
    if (!confirm(text)) return;
    const result = await api(endpoint(key)+'/'+button.dataset.delete,'DELETE');
    await route();
    message(result.mensaje);
  } catch (error) { message(error.message,true); }
};
$('#fields').oninput = event => { if (event.target.classList.contains('order-quantity')) updateTotal(); };
$('#close-editor').onclick = $('#cancel-editor').onclick = () => $('#editor').close();
$('#logout').onclick = async () => {
  try { await api('/auth/logout','POST'); } catch (error) { /* La sesión local también se cierra si el servidor se reinició. */ }
  session.clear(); location.href = 'login.html';
};
window.addEventListener('hashchange',route);

(async () => {
  if (!session.token()) { location.href = 'login.html'; return; }
  try {
    user = await api('/auth/me');
    $('#user-label').textContent = user.nombre + ' · ' + user.rol;
    const keys = ['dashboard','categorias','productos','pedidos','pagos','reportes'];
    if (isAdmin()) keys.push('usuarios');
    $('#navigation').innerHTML = keys.map(key=>`<a href="#${key}" data-nav="${key}">${esc(modules[key]?.title||({dashboard:'Resumen',reportes:'Reportes'})[key])}</a>`).join('');
    await route();
  } catch (error) { message(error.message,true); }
})();
