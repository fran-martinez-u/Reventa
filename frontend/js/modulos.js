// Campos, columnas y permisos de los cinco módulos.
const modules = {
  categorias: {
    title: 'Categorías',
    singular: 'categoría',
    pk: 'id_categoria',
    columns: ['nombre', 'descripcion', 'estado'],
    fields: [
      ['nombre', 'Nombre', 'text', 80],
      ['descripcion', 'Descripción', 'text', 200],
      ['estado', 'Estado', 'estado']
    ]
  },
  productos: {
    title: 'Productos',
    singular: 'producto',
    pk: 'id_producto',
    columns: ['codigo', 'nombre', 'categoria', 'precio_base', 'precio_reventa_sugerido',
      'stock_actual', 'estado'
    ],
    fields: [
      ['codigo', 'Código', 'text', 30],
      ['nombre', 'Nombre', 'text', 120],
      ['id_categoria', 'Categoría', 'categorias'],
      ['descripcion', 'Descripción', 'text', 250],
      ['precio_base', 'Precio base', 'money'],
      ['precio_reventa_sugerido', 'Precio sugerido', 'money'],
      ['stock_actual', 'Existencias', 'number'],
      ['stock_minimo', 'Stock mínimo', 'number'],
      ['estado', 'Estado', 'estado']
    ]
  },
  pedidos: {
    title: 'Pedidos',
    singular: 'pedido',
    pk: 'id_pedido',
    columns: ['id_pedido', 'revendedor', 'fecha_pedido', 'estado', 'total', 'total_pagado',
      'saldo'
    ]
  },
  pagos: {
    title: 'Pagos',
    singular: 'pago',
    pk: 'id_pago',
    columns: ['id_pago', 'id_pedido', 'fecha_pago', 'monto', 'metodo_pago', 'estado_pago'],
    fields: [
      ['id_pedido', 'Pedido', 'pedidos'],
      ['monto', 'Monto', 'money'],
      ['metodo_pago', 'Método', 'metodos'],
      ['referencia_transaccion', 'Referencia', 'text', 60]
    ]
  },
  usuarios: {
    title: 'Usuarios',
    singular: 'usuario',
    pk: 'id_usuario',
    endpoint: 'auth/usuarios',
    columns: ['nombre', 'correo', 'rol', 'activo'],
    fields: [
      ['nombre', 'Nombre completo', 'text', 100],
      ['correo', 'Correo', 'email', 120],
      ['telefono', 'Teléfono', 'tel', 20],
      ['id_rol', 'Rol', 'roles'],
      ['activo', 'Estado', 'activo']
    ]
  }
};
const labels = {
  nombre: 'Nombre',
  descripcion: 'Descripción',
  estado: 'Estado',
  codigo: 'Código',
  categoria: 'Categoría',
  precio_base: 'Precio base',
  precio_reventa_sugerido: 'Precio sugerido',
  stock_actual: 'Stock',
  id_pedido: 'Pedido',
  revendedor: 'Revendedor',
  fecha_pedido: 'Fecha',
  total: 'Total',
  total_pagado: 'Pagado',
  saldo: 'Saldo',
  id_pago: 'Pago',
  fecha_pago: 'Fecha',
  monto: 'Monto',
  metodo_pago: 'Método',
  estado_pago: 'Estado',
  correo: 'Correo',
  rol: 'Rol',
  activo: 'Estado',
  producto: 'Producto',
  cantidad: 'Cantidad',
  precio_unitario: 'Precio unitario',
  subtotal: 'Subtotal',
  pedidos: 'Pedidos',
  ventas: 'Ventas',
  stock: 'Stock',
  minimo: 'Mínimo',
  valor_inventario: 'Valor del inventario',
  nivel: 'Nivel'
};
const monetary = ['precio_base', 'precio_reventa_sugerido', 'total', 'total_pagado', 'saldo',
  'monto',
  'precio_unitario', 'subtotal', 'ventas', 'valor_inventario'
];
const isAdmin = () => user.rol === 'ADMIN';
const isStaff = () => ['ADMIN', 'VENDEDOR'].includes(user.rol);
const endpoint = key => '/' + (modules[key].endpoint || key);
