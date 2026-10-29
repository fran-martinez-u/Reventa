const session = {
  token: () => sessionStorage.getItem('reventa_token'),
  save: token => sessionStorage.setItem('reventa_token', token),
  clear: () => sessionStorage.removeItem('reventa_token')
};

async function api(path, method = 'GET', data) {
  const headers = {'Content-Type': 'application/json'};
  if (session.token()) headers.Authorization = 'Bearer ' + session.token();
  let response;
  try {
    response = await fetch('/api' + path, {
      method, headers, body: data === undefined ? undefined : JSON.stringify(data)
    });
  } catch (error) {
    throw new Error('No se pudo conectar con el servidor. Intenta de nuevo.');
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      session.clear();
      location.href = 'login.html';
    }
    throw new Error(body.detail || 'No se pudo completar la operación.');
  }
  return body;
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[c]));
}

function money(value) {
  return new Intl.NumberFormat('es-CO', {style:'currency', currency:'COP', maximumFractionDigits:2}).format(Number(value || 0));
}
