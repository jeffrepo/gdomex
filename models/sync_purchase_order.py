import xmlrpc.client
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SyncPurchaseOrder(models.Model):
    _name = 'sync.purchase.order'
    _description = 'Sincronizar Órdenes de Compra de Odoo 10 a Odoo 15'

    def sync_purchase_orders(self):
        # Conexión a Odoo 10
        url_odoo10 = 'http://45.79.219.125'
        db_odoo10 = 'domex'
        username_odoo10 = 'admin'
        password_odoo10 = '@!DMS1'

        orders_faltantes = []  # Para rastrear órdenes que no se crean
        orders_ya_existentes = []  # Para rastrear órdenes que ya existen
        orders_creados = []  # Para rastrear órdenes que se crean con éxito

        try:
            # Conexión a Odoo 10
            _logger.info("Iniciando conexión a Odoo 10...")
            common10 = xmlrpc.client.ServerProxy(f'{url_odoo10}/xmlrpc/2/common')
            uid_odoo10 = common10.authenticate(db_odoo10, username_odoo10, password_odoo10, {})

            if not uid_odoo10:
                _logger.error("Error en la autenticación en Odoo 10.")
                return

            _logger.info(f"Autenticado con éxito en Odoo 10. UID: {uid_odoo10}")
            models10 = xmlrpc.client.ServerProxy(f'{url_odoo10}/xmlrpc/2/object')

            # Buscar órdenes de compra de la compañía 1 en Odoo 10
            _logger.info("Buscando órdenes de compra en Odoo 10 para la compañía 1...")
            purchase_order_ids_odoo10 = models10.execute_kw(
                db_odoo10, uid_odoo10, password_odoo10,
                'purchase.order', 'search', [[['company_id', '=', 1]]]
            )

            _logger.info(f"Se encontraron {len(purchase_order_ids_odoo10)} órdenes de compra en Odoo 10.")

            if not purchase_order_ids_odoo10:
                _logger.warning("No se encontraron órdenes de compra en Odoo 10 para la compañía 1.")
                return

            # Leer las órdenes de compra encontradas en Odoo 10
            _logger.info("Leyendo los datos de las órdenes de compra en Odoo 10...")
            purchase_orders_odoo10 = models10.execute_kw(
                db_odoo10, uid_odoo10, password_odoo10,
                'purchase.order', 'read', [purchase_order_ids_odoo10], {'fields': [
                    'id', 'name', 'partner_id', 'date_order', 'order_line', 'currency_id', 'company_id', 'state'
                ]}
            )

            _logger.info("Datos de órdenes de compra leídos correctamente. Iniciando sincronización con Odoo 15.")

            for order in purchase_orders_odoo10:
                order_id_odoo10 = order['id']  # ID de la orden de compra en Odoo 10

                _logger.info(f"Verificando si la orden de compra '{order['name']}' (ID Odoo 10: {order_id_odoo10}) ya existe en Odoo 15...")

                # Verificar si la orden ya existe en Odoo 15 basado en 'x_almex_id'
                existing_order = self.env['purchase.order'].search([
                    ('x_almex_id', '=', order_id_odoo10),
                    ('company_id', '=', 6)  # Asegurarse de que pertenece a la compañía correcta
                ])

                if existing_order:
                    _logger.info(f"La orden de compra '{order['name']}' ya existe en Odoo 15 con x_almex_id={order_id_odoo10}. Saltando creación.")
                    orders_ya_existentes.append(order_id_odoo10)
                    continue

                # Obtener o crear el proveedor
                partner_odoo10 = models10.execute_kw(
                    db_odoo10, uid_odoo10, password_odoo10,
                    'res.partner', 'read', [order['partner_id'][0]], {'fields': [
                        'id', 'name', 'vat', 'ref', 'company_type', 'street', 'city', 'state_id', 'country_id', 'phone', 'email'
                    ]}
                )[0]

                # Buscar el contacto existente por 'x_almex_id' o 'vat'
                partner = self.env['res.partner'].search([
                    '|',
                    ('x_almex_id', '=', partner_odoo10['id']),
                    ('vat', '=', partner_odoo10.get('vat', ''))
                ], limit=1)

                if not partner:
                    # Crear el proveedor
                    _logger.info(f"Creando proveedor '{partner_odoo10['name']}' en Odoo 15...")
                    partner_vals = {
                        'name': partner_odoo10['name'],
                        'vat': partner_odoo10.get('vat', ''),
                        'ref': partner_odoo10.get('ref', ''),
                        'company_type': partner_odoo10.get('company_type', 'company'),
                        'street': partner_odoo10.get('street', ''),
                        'city': partner_odoo10.get('city', ''),
                        'phone': partner_odoo10.get('phone', ''),
                        'email': partner_odoo10.get('email', ''),
                        'x_almex_id': partner_odoo10['id'],
                        'company_id': 6,
                        'supplier_rank': 1,  # Marcar como proveedor
                    }
                    # Obtener país y estado si existen
                    if partner_odoo10.get('country_id'):
                        country = self.env['res.country'].search([('name', '=', partner_odoo10['country_id'][1])], limit=1)
                        if country:
                            partner_vals['country_id'] = country.id
                    if partner_odoo10.get('state_id'):
                        state = self.env['res.country.state'].search([('name', '=', partner_odoo10['state_id'][1])], limit=1)
                        if state:
                            partner_vals['state_id'] = state.id
                    try:
                        partner = self.env['res.partner'].create(partner_vals)
                        _logger.info(f"Proveedor '{partner.name}' creado exitosamente.")
                    except Exception as e:
                        _logger.error(f"Error al crear el proveedor '{partner_odoo10['name']}' en Odoo 15: {e}")
                        orders_faltantes.append(order_id_odoo10)
                        continue  # Saltar al siguiente pedido
                else:
                    _logger.info(f"Proveedor '{partner.name}' ya existe en Odoo 15.")
                    # Actualizar 'x_almex_id' si no está establecido
                    if not partner.x_almex_id:
                        partner.x_almex_id = partner_odoo10['id']
                        _logger.info(f"Actualizado 'x_almex_id' del proveedor '{partner.name}' a {partner.x_almex_id}.")

                # Preparar líneas de pedido
                order_lines = []
                line_error = False  # Variable para rastrear si hubo un error en las líneas
                for line_id in order['order_line']:
                    line_odoo10 = models10.execute_kw(
                        db_odoo10, uid_odoo10, password_odoo10,
                        'purchase.order.line', 'read', [line_id], {'fields': [
                            'product_id', 'name', 'product_qty', 'price_unit', 'taxes_id', 'date_planned'
                        ]}
                    )[0]

                    try:
                        # Obtener o crear el producto
                        product_template = self.env['product.template'].search([('x_almex_id', '=', line_odoo10['product_id'][0])], limit=1)

                        if not product_template:
                            # Obtener datos del producto desde Odoo 10
                            product_odoo10 = models10.execute_kw(
                                db_odoo10, uid_odoo10, password_odoo10,
                                'product.product', 'read', [line_odoo10['product_id'][0]], {'fields': [
                                    'id', 'name', 'default_code', 'list_price', 'standard_price', 'type', 'categ_id', 'uom_id', 'uom_po_id', 'description_sale', 'description_purchase'
                                ]}
                            )[0]

                            # Crear categoría si no existe
                            category = self.env['product.category'].search([('name', '=', product_odoo10['categ_id'][1])], limit=1)
                            if not category:
                                category = self.env['product.category'].create({
                                    'name': product_odoo10['categ_id'][1],
                                })

                            # Crear unidad de medida si no existe
                            uom_name = product_odoo10['uom_id'][1]
                            uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                            if not uom:
                                # Crear o encontrar la categoría de unidad de medida
                                uom_category = self.env['uom.category'].search([('name', '=', uom_name)], limit=1)
                                if not uom_category:
                                    uom_category = self.env['uom.category'].create({'name': uom_name})

                                uom = self.env['uom.uom'].create({
                                    'name': uom_name,
                                    'category_id': uom_category.id,
                                    'uom_type': 'reference',
                                    'factor_inv': 1,
                                })

                            # Establecer el campo 'purchase_method' con un valor por defecto
                            purchase_method = 'receive'  # O 'purchase', dependiendo de tus necesidades

                            # Crear producto
                            product_template = self.env['product.template'].create({
                                'name': product_odoo10['name'],
                                'default_code': product_odoo10.get('default_code', ''),
                                'list_price': product_odoo10.get('list_price', 0),
                                'standard_price': product_odoo10.get('standard_price', 0),
                                'categ_id': category.id,
                                'uom_id': uom.id,
                                'uom_po_id': uom.id,
                                'description_sale': product_odoo10.get('description_sale', ''),
                                'description_purchase': product_odoo10.get('description_purchase', ''),
                                'company_id': 6,
                                'x_almex_id': product_odoo10['id'],
                                'type': product_odoo10.get('type', 'product'),
                                'purchase_method': purchase_method,  # Agregar este campo
                            })
                            _logger.info(f"Producto '{product_template.name}' creado exitosamente.")
                        else:
                            _logger.info(f"Producto '{product_template.name}' ya existe en Odoo 15.")

                        # Obtener el producto variante
                        product = product_template.product_variant_id

                        # Obtener impuestos
                        taxes = []
                        for tax_id in line_odoo10['taxes_id']:
                            tax_odoo10 = models10.execute_kw(
                                db_odoo10, uid_odoo10, password_odoo10,
                                'account.tax', 'read', [tax_id], {'fields': ['name', 'amount', 'type_tax_use']}
                            )[0]

                            tax = self.env['account.tax'].search([('name', '=', tax_odoo10['name']), ('company_id', '=', 6)], limit=1)
                            if not tax:
                                tax = self.env['account.tax'].create({
                                    'name': tax_odoo10['name'],
                                    'amount': tax_odoo10['amount'],
                                    'type_tax_use': tax_odoo10['type_tax_use'],
                                    'company_id': 6,
                                })
                            taxes.append(tax.id)

                        # Preparar línea
                        order_line_vals = {
                            'product_id': product.id,
                            'name': line_odoo10['name'],
                            'product_qty': line_odoo10['product_qty'],
                            'price_unit': line_odoo10['price_unit'],
                            'date_planned': line_odoo10['date_planned'],
                            'taxes_id': [(6, 0, taxes)],
                        }
                        order_lines.append((0, 0, order_line_vals))

                    except Exception as e:
                        _logger.error(f"Error al procesar la línea de pedido del producto ID {line_odoo10['product_id'][0]}: {e}")
                        line_error = True
                        break  # Saltar al siguiente pedido

                if line_error:
                    orders_faltantes.append(order_id_odoo10)
                    continue  # Saltar al siguiente pedido

                # Preparar valores de la orden de compra
                order_vals = {
                    'name': order['name'],
                    'partner_id': partner.id,
                    'date_order': order['date_order'],
                    'order_line': order_lines,
                    'company_id': 6,
                    'x_almex_id': order_id_odoo10,
                }

                # Crear la orden de compra
                try:
                    purchase_order = self.env['purchase.order'].create(order_vals)
                    _logger.info(f"Orden de compra '{purchase_order.name}' (ID Odoo 10: {order_id_odoo10}) creada exitosamente en Odoo 15.")
                    orders_creados.append(order_id_odoo10)

                    # Confirmar la orden si está confirmada en Odoo 10
                    if order['state'] in ['purchase', 'done']:
                        purchase_order.button_confirm()

                    # Sincronizar facturas asociadas
                    # (Puedes agregar aquí el código para sincronizar facturas si es necesario)

                except Exception as e:
                    _logger.error(f"Error al crear la orden de compra '{order['name']}' en Odoo 15: {e}")
                    orders_faltantes.append(order_id_odoo10)

            # Finalizar el proceso y mostrar el resumen
            _logger.info(f"Se crearon {len(orders_creados)} órdenes de compra en Odoo 15.")
            _logger.info(f"{len(orders_ya_existentes)} órdenes de compra ya existían en Odoo 15.")
            if orders_faltantes:
                _logger.error(f"Las siguientes órdenes de compra fallaron al ser creadas: {orders_faltantes}")

        except Exception as e:
            _logger.error(f"Error durante el proceso de sincronización: {e}")
