# gdomex

## Liquidaciones sin acceso a Contabilidad

Actualizar `gdomex` a `19.0.1.0.11` y asignar al usuario el grupo
**Liquidaciones / Gestionar liquidaciones y facturas de proveedor**
(`gdomex.group_liquidacion_user`). Para un usuario dedicado a este flujo,
dejar sin asignar los permisos de Contabilidad/Facturación. El grupo nuevo
sólo implica Usuario interno; no implica ningún grupo contable.

El menú principal **Liquidaciones** aparece únicamente para ese grupo.
Desde una liquidación en borrador se pueden agregar facturas en la pestaña
**Facturas** o pulsar **Crear factura de proveedor**. El formulario usa un
proveedor existente, permite introducir líneas, impuestos y distribución
analítica, y ofrece **Validar** para publicar la factura.

El perfil permite:

- Consultar y crear liquidaciones de las compañías permitidas; editar las
  que estén en borrador.
- Crear, editar y validar facturas de proveedor vinculadas a esas
  liquidaciones mientras ambos documentos estén en borrador.
- Consultar los pagos ya vinculados y los catálogos necesarios para registrar
  las facturas. No concede edición de diarios, cuentas ni impuestos.

Las facturas publicadas quedan sin edición para este perfil. No concede
permisos para facturas de cliente, notas de crédito, facturas sin liquidación,
asientos independientes, registro de pagos ni conciliación/cancelación de
liquidaciones. Los usuarios que ya tienen Facturación o Contabilidad
conservan sus permisos actuales y el acceso original a liquidaciones.
Agregar otros grupos puede conceder permisos adicionales; este perfil no
retira los grupos que un usuario ya tenga.

Las reglas y comprobaciones del servidor también limitan las llamadas RPC.
Odoo 19 exige `account.group_account_invoice` dentro de `_post`; para este
perfil se comprueban primero los permisos, el tipo de factura, la compañía,
la liquidación y sus estados. Sólo la publicación comprobada ejecuta el
flujo nativo con `sudo`, sin propagar indicadores de omisión enviados por el
cliente y conservando el usuario en la auditoría. Facturas con vínculos
especiales de conciliación o reversión deben ser publicadas por Contabilidad.

Pruebas de integración incluidas en `tests/test_liquidacion_access.py`:

```sh
odoo-bin -d BASE_DE_PRUEBAS -u gdomex --test-enable --test-tags /gdomex:TestLiquidacionAccess --stop-after-init
```

Requieren Odoo 19, las dependencias de `gdomex` y una base de pruebas.
La revisión local verifica sintaxis Python, esquema XML, XPath contra
`account_gt` 19.0 y carga de archivos/ACL; no sustituye esa ejecución de
integración.

## Traslado interno

Después de actualizar el módulo `gdomex` en Odoo 19, abrir una transferencia
en Inventario y elegir **Imprimir → Traslado interno**. También se pueden
seleccionar varias transferencias desde la lista para imprimirlas juntas.

El reporte hereda `stock.report_picking` (Operaciones de picking) como una
plantilla independiente. Conserva el detalle nativo de productos, cantidades,
ubicaciones, lotes, paquetes y observaciones, con el membrete de Grupo Domex
en tamaño carta. Usa un layout propio: el membrete forma parte del contenido
al inicio de cada transferencia y el pie se repite en cada página.
El nombre de la transferencia aparece debajo del membrete, sin códigos de barras
en el encabezado ni en las tablas. Los lotes y paquetes se identifican en texto.
La opción original **Operaciones de picking** sigue disponible.
