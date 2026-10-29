# Modelo entidad-relación

```mermaid
erDiagram
    ROLES ||--o{ USUARIOS : asigna
    CATEGORIAS ||--o{ PRODUCTOS : agrupa
    USUARIOS ||--o{ PEDIDOS : compra_como_revendedor
    USUARIOS o|--o{ PEDIDOS : atiende_como_vendedor
    PEDIDOS ||--|{ DETALLE_PEDIDO : contiene
    PRODUCTOS ||--o{ DETALLE_PEDIDO : vendido_en
    PEDIDOS ||--o{ PAGOS : recibe
    USUARIOS ||--o{ PAGOS : registra
```

Un usuario tiene un rol. Cada producto pertenece a una categoría. Un pedido pertenece a un revendedor y puede ser atendido por un vendedor. El detalle relaciona productos con pedidos. Los pagos pertenecen a un pedido y guardan quién los registró.
