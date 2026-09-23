# gdomex

## Traslado interno

Después de actualizar el módulo `gdomex` en Odoo 19, abrir una transferencia
en Inventario y elegir **Imprimir → Traslado interno**. También se pueden
seleccionar varias transferencias desde la lista para imprimirlas juntas.

El reporte hereda `stock.report_picking` (Operaciones de picking) como una
plantilla independiente. Conserva el detalle nativo de productos, cantidades,
ubicaciones, lotes, paquetes y observaciones, con el membrete de Grupo Domex
en tamaño carta. El encabezado y el pie se repiten en cada página.
La opción original **Operaciones de picking** sigue disponible.
