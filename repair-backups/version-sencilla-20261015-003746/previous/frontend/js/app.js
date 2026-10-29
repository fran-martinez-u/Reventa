const $ = s => document.querySelector(s);
let user, currentRows = [], version = 0, editing;
const cfg = {
  productos: {title:'Productos', pk:'id_producto', columns:['sku','nombre','categoria','precio_base','precio_sugerido','stock_actual','estado'], fields:[['id_categoria','Categoría','categorias'],['sku','Código'],['nombre','Nombre'],['precio_base','Precio base','number'],['precio_sugerido','Precio sugerido','number'],['stock_actual','Existencias','number'],['stock_minimo','Stock mínimo','number']]},
  categorias: {title:'Categorías', pk:'id_categoria', columns:['nombre','descripcion','estado'], fields:[['nombre','Nombre'],['descripcion','Descripción']]},
  pedidos: {title:'Pedidos', pk:'id_pedido', columns:['codigo_pedido','revendedor','fecha_pedido','estado_pedido','total','total_pagado','saldo_pendiente']},
  pagos: {title:'Pagos', pk:'id_pago', columns:['id_pedido','fecha_pago','monto','metodo_pago','referencia','estado_pago'], fields:[['id_pedido','Pedido','pedidos'],['monto','Monto','number'],['metodo_pago','Método de pago'],['referencia','Referencia']]},
  usuarios: {title:'Usuarios', endpoint:'auth/usuarios', pk:'id_usuario', columns:['nombre_completo','correo','rol','estado'], fields:[['nombre_completo','Nombre completo'],['correo','Correo','email'],['password','Contraseña inicial','password'],['id_rol','Rol','auth/roles'],['telefono','Teléfono']]}
};
const labels = {sku:'Código',nombre_completo:'Nombre',precio_base:'Precio base',precio_sugerido:'Precio sugerido',stock_actual:'Stock',codigo_pedido:'Pedido',fecha_pedido:'Fecha',estado_pedido:'Estado',total_pagado:'Pagado',saldo_pendiente:'Saldo',id_pedido:'Pedido',fecha_pago:'Fecha',metodo_pago:'Método',estado_pago:'Estado',subtotal_linea:'Subtotal',precio_unitario:'Precio unitario'};
const amounts = new Set(['precio_base','precio_sugerido','total','total_pagado','saldo_pendiente','monto','precio_unitario','subtotal_linea']);
function notify(s){$('#message').hidden=false;$('#message').className='alert alert-danger';$('#message').textContent=s;}
function table(rows, columns, actions){return rows.length ? `<div class="table-responsive"><table class="table"><thead><tr>${columns.map(k=>`<th>${esc(labels[k]||k)}</th>`).join('')}${actions?'<th>Acciones</th>':''}</tr></thead><tbody>${rows.map(r=>`<tr>${columns.map(k=>`<td>${esc(amounts.has(k)?money(r[k]):r[k]??'—')}</td>`).join('')}${actions?`<td>${actions(r)}</td>`:''}</tr>`).join('')}</tbody></table></div>`:'<p class="empty">No hay registros para mostrar.</p>';}
function intro(title){return `<div class="intro"><h1>${esc(title)}</h1></div>`;}
async function route(){
  const v=++version, key=location.hash.slice(1)||'dashboard'; $('#message').hidden=true;
  $('#breadcrumb').textContent=cfg[key]?.title||'Resumen';
  document.querySelectorAll('[data-nav]').forEach(a=>a.classList.toggle('active',a.dataset.nav===key));
  $('#view').innerHTML='<p class="empty">Cargando información…</p>';
  try{
    if(key==='dashboard'||key==='reportes'){
      const r=await api('/reportes/dashboard'); if(v!==version)return;
      const names={productos_activos:'Productos activos',productos_bajo_stock:'Productos con stock bajo',total_pedidos:'Pedidos',ventas_totales:'Ventas',total_recaudado:'Recaudado',cartera_pendiente:'Cartera pendiente'};
      $('#view').innerHTML=intro(key==='reportes'?'Reportes':'Resumen de tu negocio')+'<div class="stats">'+Object.entries(r.kpis).map(([k,n])=>`<article class="stat"><div class="stat-label">${esc(names[k]||k)}</div><div class="stat-value">${esc(['ventas_totales','total_recaudado','cartera_pendiente'].includes(k)?money(n):n)}</div></article>`).join('')+'</div>';return;
    }
    if(key.startsWith('pedido/')){
      const r=await api('/pedidos/'+Number(key.split('/')[1]));if(v!==version)return;
      $('#view').innerHTML=intro(r.codigo_pedido)+`<p>${esc(r.revendedor)} · ${esc(r.estado_pedido)} · Total ${esc(money(r.total))} · Saldo ${esc(money(r.saldo_pendiente))}</p><section class="panel">${table(r.items,['nombre','cantidad','precio_unitario','subtotal_linea'])}</section><p><a href="#pedidos">Volver a pedidos</a></p>`;return;
    }
    if(!cfg[key]){location.hash='dashboard';return;}
    if(key==='usuarios'&&user.rol!=='ADMIN')throw new Error('Se requiere rol administrador.');
    const c=cfg[key], rows=await api('/'+(c.endpoint||key));if(v!==version)return;currentRows=rows;
    $('#view').innerHTML=intro(c.title)+`<button class="btn btn-primary mb-3" data-new="${key}">+ Nuevo registro</button><section class="panel">${table(rows,c.columns,r=>key==='pedidos'?`<a class="btn btn-sm btn-light" href="#pedido/${r.id_pedido}">Ver detalle</a>`:key==='productos'?`<button class="btn btn-sm btn-light" data-edit="${r.id_producto}">Editar</button>`:'')}</section>`;
  }catch(e){if(v===version){$('#view').innerHTML='<p class="empty">No se pudo cargar la información.</p>';notify(e.message);}}
}
async function openEditor(key, row={}){
  editing={key,id:row[cfg[key].pk]};$('#form-error').hidden=true;$('#editor-title').textContent=(editing.id?'Editar ':'Crear ')+cfg[key].title.toLowerCase();
  let html='';
  if(key==='pedidos'){
    const products=await api('/productos');
    html='<p>Selecciona las cantidades de los productos del pedido.</p>'+products.filter(p=>p.estado==='ACTIVO'&&p.stock_actual>0).map(p=>`<div class="col-12"><label class="form-label">${esc(p.nombre)} · ${esc(money(p.precio_base))} · Disponible: ${p.stock_actual}</label><input class="form-control" type="number" data-product="${p.id_producto}" value="0" min="0" max="${p.stock_actual}" step="1"></div>`).join('')+'<div class="col-12"><label class="form-label">Observación</label><input class="form-control" name="observacion" maxlength="250"></div>';
    if(user.rol==='ADMIN'||user.rol==='VENDEDOR'){
      const users=await api('/auth/usuarios');html+=`<div class="col-12"><label class="form-label">Revendedor</label><select class="form-select" name="id_revendedor" required><option value="">Seleccionar…</option>${users.filter(u=>u.rol==='REVENDEDOR'&&u.estado==='ACTIVO').map(u=>`<option value="${u.id_usuario}">${esc(u.nombre_completo)}</option>`).join('')}</select></div>`;
    }
  }else for(const [name,label,type='text'] of cfg[key].fields){
    let control;
    if(['categorias','pedidos','auth/roles'].includes(type)){
      const rows=await api('/'+type), pk=type==='auth/roles'?'id_rol':cfg[type].pk;
      control=`<select class="form-select" name="${name}" required><option value="">Seleccionar…</option>${rows.map(r=>`<option value="${r[pk]}" ${String(row[name])===String(r[pk])?'selected':''}>${esc(r.nombre||r.codigo_pedido)}</option>`).join('')}</select>`;
    }else control=`<input class="form-control" name="${name}" type="${type}" value="${esc(row[name]??(type==='number'?0:''))}" ${type==='number'?'min="0" step="'+(name.startsWith('precio')||name==='monto'?'0.01':'1')+'"':''} ${type==='password'?'minlength="8" autocomplete="new-password"':''} ${['descripcion','referencia','telefono'].includes(name)?'':'required'}>`;
    html+=`<div class="col-12 col-sm-6"><label class="form-label">${esc(label)}</label>${control}</div>`;
  }
  $('#fields').innerHTML=html;$('#editor').showModal();
}
$('#edit-form').onsubmit=async e=>{
  e.preventDefault();const {key,id}=editing, data=Object.fromEntries(new FormData(e.target));$('#save-button').disabled=true;
  try{
    for(const n of ['id_categoria','id_pedido','id_rol','id_revendedor','precio_base','precio_sugerido','stock_actual','stock_minimo','monto'])if(n in data)data[n]=Number(data[n]);
    if(key==='productos')Object.assign(data,{talla:'',color:'',estado:currentRows.find(r=>r.id_producto===id)?.estado||'ACTIVO'});
    if(key==='usuarios')data.username=data.correo;
    if(key==='pedidos'){data.tipo_pago='CONTADO';data.items=[...document.querySelectorAll('[data-product]')].filter(i=>Number(i.value)>0).map(i=>({id_producto:Number(i.dataset.product),cantidad:Number(i.value)}));if(!data.items.length)throw new Error('Selecciona al menos un producto.');}
    await api('/'+(cfg[key].endpoint||key)+(id?'/'+id:''),id?'PUT':'POST',data);$('#editor').close();await route();
  }catch(e){$('#form-error').hidden=false;$('#form-error').textContent=e.message;}finally{$('#save-button').disabled=false;}
};
$('#view').onclick=async e=>{try{const b=e.target.closest('[data-new],[data-edit]');if(!b)return;if(b.dataset.new)await openEditor(b.dataset.new);else await openEditor('productos',currentRows.find(r=>r.id_producto===Number(b.dataset.edit)));}catch(e){notify(e.message);}};
$('#close-editor').onclick=$('#cancel-editor').onclick=()=>$('#editor').close();
$('#logout').onclick=()=>{session.clear();location.href='login.html';};
window.addEventListener('hashchange',route);
(async()=>{
  if(!session.token()){location.href='login.html';return;}
  try{user=await api('/auth/me');$('#user-label').textContent=`${user.nombre_completo} · ${user.rol}`;const keys=['dashboard','productos','categorias','pedidos','pagos','reportes',...(user.rol==='ADMIN'?['usuarios']:[])];$('#navigation').innerHTML=keys.map(k=>`<a href="#${k}" data-nav="${k}">${esc(cfg[k]?.title||({dashboard:'Resumen',reportes:'Reportes'})[k])}</a>`).join('');await route();}catch(e){notify(e.message);}
})();
