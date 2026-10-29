// Estado de la página, navegación y acciones del usuario.
const $ = selector => document.querySelector(selector);
let user;
let editing;
let routeVersion = 0;

async function route() {
  const version = ++routeVersion;
  const key = location.hash.slice(1) || 'dashboard';
  const activeModule = key.startsWith('pedido/') ? 'pedidos' : key;

  $('#message').hidden = true;
  $('#view').innerHTML = '<p class="empty">Cargando…</p>';
  for (const link of document.querySelectorAll('[data-nav]')) {
    link.classList.toggle('active', link.dataset.nav === activeModule);
  }

  try {
    if (key === 'dashboard') {
      await showDashboard(version);
    } else if (key === 'reportes') {
      await showReports(version);
    } else if (/^pedido\/\d+$/.test(key)) {
      const id = Number(key.split('/')[1]);
      await showOrder(id, version);
    } else if (modules[key]) {
      await showModule(key, version);
    } else {
      location.hash = 'dashboard';
    }
  } catch (error) {
    if (version !== routeVersion) return;
    $('#view').innerHTML = '<p class="empty">No se pudo cargar esta sección.</p>';
    message(error.message, true);
  }
}

async function saveForm(event) {
  event.preventDefault();
  const {key, id, row} = editing;
  const data = Object.fromEntries(new FormData(event.target));
  const numbers = [
    'id_categoria', 'id_rol', 'id_pedido', 'id_revendedor',
    'stock_actual', 'stock_minimo', 'activo'
  ];

  $('#save-button').disabled = true;
  $('#form-error').hidden = true;

  try {
    for (const name of numbers) {
      if (name in data) data[name] = Number(data[name]);
    }
    if (key === 'pagos' && id) data.id_pedido = row.id_pedido;

    if (key === 'pedidos') {
      data.items = [];
      for (const input of document.querySelectorAll('.order-quantity')) {
        if (Number(input.value) > 0) {
          data.items.push({
            id_producto: Number(input.dataset.product),
            cantidad: Number(input.value)
          });
        }
      }
      if (!data.items.length) throw new Error('Selecciona al menos un producto.');
    }

    const path = endpoint(key) + (id ? '/' + id : '');
    const method = id ? 'PUT' : 'POST';
    await api(path, method, data);
    $('#editor').close();
    await route();
    message('Registro guardado correctamente.');
  } catch (error) {
    $('#form-error').textContent = error.message;
    $('#form-error').hidden = false;
  } finally {
    $('#save-button').disabled = false;
  }
}

async function handleAction(event) {
  const button = event.target.closest('[data-new],[data-edit],[data-delete]');
  if (!button) return;

  try {
    if (button.dataset.new) {
      const orderId = Number(button.dataset.order) || null;
      await openEditor(button.dataset.new, null, orderId);
      return;
    }

    const key = button.dataset.module;
    if (button.dataset.edit) {
      await openEditor(key, Number(button.dataset.edit));
      return;
    }

    let question = '¿Desactivar este registro?';
    if (key === 'pedidos') question = '¿Cancelar el pedido y devolver las existencias?';
    if (key === 'pagos') question = '¿Anular este pago?';
    if (!confirm(question)) return;

    const result = await api(endpoint(key) + '/' + button.dataset.delete, 'DELETE');
    await route();
    message(result.mensaje);
  } catch (error) {
    message(error.message, true);
  }
}

async function logout() {
  try {
    await api('/auth/logout', 'POST');
  } catch (error) {
    // También cerrar la sesión local si el servidor se reinició.
  }
  session.clear();
  location.href = 'login.html';
}

async function start() {
  if (!session.token()) {
    location.href = 'login.html';
    return;
  }

  try {
    user = await api('/auth/me');
    $('#user-label').textContent = user.nombre + ' · ' + user.rol;
    const keys = ['dashboard', 'categorias', 'productos', 'pedidos', 'pagos', 'reportes'];
    const titles = {dashboard: 'Resumen', reportes: 'Reportes'};
    if (isAdmin()) keys.push('usuarios');

    let navigation = '';
    for (const key of keys) {
      const title = modules[key] ? modules[key].title : titles[key];
      navigation += `<a href="#${key}" data-nav="${key}">${esc(title)}</a>`;
    }
    $('#navigation').innerHTML = navigation;
    await route();
  } catch (error) {
    message(error.message, true);
  }
}

$('#edit-form').onsubmit = saveForm;
$('#view').onclick = handleAction;
$('#fields').oninput = event => {
  if (event.target.classList.contains('order-quantity')) updateTotal();
};
$('#close-editor').onclick = () => $('#editor').close();
$('#cancel-editor').onclick = () => $('#editor').close();
$('#logout').onclick = logout;
window.addEventListener('hashchange', route);
start();
