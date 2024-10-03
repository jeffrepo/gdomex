import xmlrpc.client
import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)

class SyncPurchaseOrder(models.Model):
    _name = 'sync.purchase.order'
    _description = 'Sincronizar Órdenes de Compra de Odoo 10 a Odoo 15'

    def sync_purchase_orders(self):
        # Establecer el contexto de la compañía
        self = self.with_company(6)

        # Conexión a Odoo 10
        url_odoo10 = 'http://45.79.219.125'
        db_odoo10 = 'domex'
        username_odoo10 = 'admin'
        password_odoo10 = '@!DMS1'

        orders_faltantes = []     # Para rastrear órdenes que no se crean
        orders_ya_existentes = [] # Para rastrear órdenes que ya existen
        orders_creados = []       # Para rastrear órdenes que se crean con éxito

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

            # Obtener al usuario administrador que pertenece a la compañía 6
            admin_user = self.env['res.users'].search([
                ('login', '=', 'admin'),
                ('company_ids', 'in', [6])
            ], limit=1)

            if not admin_user:
                _logger.error("No se encontró un usuario administrador que pertenezca a la compañía 6.")
                return

            # Obtener el país de la compañía
            company = self.env['res.company'].browse(6)
            country = company.country_id
            if not country:
                _logger.error(f"La compañía con ID 6 no tiene país definido. No se puede crear el impuesto.")
                return  # Detener el proceso si el país no está definido

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
                        'name', 'vat', 'ref', 'company_type', 'street', 'city', 'state_id', 'country_id', 'phone', 'email'
                    ]}
                )[0]

                partner = self.env['res.partner'].search([
                    ('x_almex_id', '=', partner_odoo10['id']),
                    ('company_id', '=', 6)
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
                        country_partner = self.env['res.country'].search([('name', '=', partner_odoo10['country_id'][1])], limit=1)
                        if country_partner:
                            partner_vals['country_id'] = country_partner.id
                    if partner_odoo10.get('state_id'):
                        state = self.env['res.country.state'].search([('name', '=', partner_odoo10['state_id'][1])], limit=1)
                        if state:
                            partner_vals['state_id'] = state.id
                    partner = self.env['res.partner'].create(partner_vals)
                    _logger.info(f"Proveedor '{partner.name}' creado exitosamente.")
                else:
                    _logger.info(f"Proveedor '{partner.name}' ya existe en Odoo 15.")

                # Preparar líneas de pedido
                order_lines = []
                for line_id in order['order_line']:
                    line_odoo10 = models10.execute_kw(
                        db_odoo10, uid_odoo10, password_odoo10,
                        'purchase.order.line', 'read', [line_id], {'fields': [
                            'product_id', 'name', 'product_qty', 'price_unit', 'taxes_id', 'date_planned'
                        ]}
                    )[0]

                    # Obtener o crear el producto
                    product = self.env['product.product'].search([
                        ('x_almex_id', '=', line_odoo10['product_id'][0]),
                        ('company_id', '=', 6)
                    ], limit=1)

                    if not product:
                        # Obtener datos del producto desde Odoo 10
                        product_odoo10 = models10.execute_kw(
                            db_odoo10, uid_odoo10, password_odoo10,
                            'product.product', 'read', [line_odoo10['product_id'][0]], {'fields': [
                                'name', 'default_code', 'list_price', 'standard_price', 'type', 'categ_id', 'uom_id', 'uom_po_id', 'description_sale', 'description_purchase'
                            ]}
                        )[0]

                        # Crear categoría si no existe (sin 'company_id')
                        category = self.env['product.category'].search([
                            ('name', '=', product_odoo10['categ_id'][1]),
                        ], limit=1)
                        if not category:
                            category = self.env['product.category'].create({
                                'name': product_odoo10['categ_id'][1],
                            })

                        # Crear unidad de medida si no existe
                        uom = self.env['uom.uom'].search([('name', '=', product_odoo10['uom_id'][1])], limit=1)
                        if not uom:
                            uom = self.env['uom.uom'].create({
                                'name': product_odoo10['uom_id'][1],
                                'category_id': self.env.ref('uom.product_uom_categ_unit').id,
                                'uom_type': 'reference',
                                'factor_inv': 1,
                            })

                        # Crear producto
                        product_vals = {
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
                            'responsible_id': admin_user.id,  # Asignar el usuario responsable
                        }

                        product = self.env['product.product'].create(product_vals)
                        _logger.info(f"Producto '{product.name}' creado exitosamente.")
                    else:
                        _logger.info(f"Producto '{product.name}' ya existe en Odoo 15.")

                    # Obtener impuestos
                    taxes = []
                    for tax_id in line_odoo10['taxes_id']:
                        tax_odoo10 = models10.execute_kw(
                            db_odoo10, uid_odoo10, password_odoo10,
                            'account.tax', 'read', [tax_id], {'fields': ['name', 'amount', 'type_tax_use', 'amount_type', 'price_include', 'tax_group_id', 'sequence']}
                        )[0]

                        tax = self.env['account.tax'].search([
                            ('name', '=', tax_odoo10['name']),
                            ('company_id', '=', 6)
                        ], limit=1)
                        if not tax:
                            # Obtener o crear el grupo de impuestos
                            tax_group_name = tax_odoo10.get('tax_group_id', False) and tax_odoo10['tax_group_id'][1] or 'Tax Group'
                            tax_group = self.env['account.tax.group'].search([('name', '=', tax_group_name)], limit=1)
                            if not tax_group:
                                tax_group = self.env['account.tax.group'].create({
                                    'name': tax_group_name,
                                    'sequence': tax_odoo10.get('sequence', 1),
                                })
                            # Mapear amount_type de Odoo 10 a valores válidos en Odoo 15
                            amount_type_odoo10 = tax_odoo10.get('amount_type', 'percent')
                            amount_type_map = {
                                'percent': 'percent',
                                'fixed': 'fixed',
                                'code': 'percent',  # Mapear 'code' a 'percent'
                            }
                            amount_type_odoo15 = amount_type_map.get(amount_type_odoo10, 'percent')

                            # Si amount_type es 'code', establecer amount en 0.0 y registrar una advertencia
                            if amount_type_odoo10 == 'code':
                                _logger.warning(f"El impuesto '{tax_odoo10['name']}' tiene amount_type 'code' en Odoo 10. Se asignará 'percent' en Odoo 15 y amount=0.0.")
                                tax_amount = 0.0
                            else:
                                tax_amount = tax_odoo10['amount']

                            # Crear impuesto incluyendo 'country_id' y amount_type mapeado
                            tax = self.env['account.tax'].create({
                                'name': tax_odoo10['name'],
                                'amount': tax_amount,
                                'amount_type': amount_type_odoo15,
                                'type_tax_use': tax_odoo10['type_tax_use'],
                                'company_id': 6,
                                'country_id': country.id,
                                'price_include': tax_odoo10.get('price_include', False),
                                'tax_group_id': tax_group.id,
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
                        'company_id': 6,
                    }
                    order_lines.append((0, 0, order_line_vals))

                # Preparar valores de la orden de compra
                order_vals = {
                    'name': order['name'],
                    'partner_id': partner.id,
                    'date_order': order['date_order'],
                    'order_line': order_lines,
                    'company_id': 6,
                    'x_almex_id': order_id_odoo10,
                    'user_id': admin_user.id,
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
                    invoice_ids_odoo10 = models10.execute_kw(
                        db_odoo10, uid_odoo10, password_odoo10,
                        'account.invoice', 'search', [[['origin', '=', order['name']]]]
                    )

                    if invoice_ids_odoo10:
                        invoices_odoo10 = models10.execute_kw(
                            db_odoo10, uid_odoo10, password_odoo10,
                            'account.invoice', 'read', [invoice_ids_odoo10], {'fields': [
                                'id', 'number', 'partner_id', 'date_invoice', 'invoice_line_ids', 'state', 'type', 'origin', 'account_id', 'currency_id', 'company_id', 'amount_total', 'journal_id'
                            ]}
                        )

                        for invoice in invoices_odoo10:
                            invoice_id_odoo10 = invoice['id']
                            _logger.info(f"Verificando si la factura '{invoice.get('number', '')}' (ID Odoo 10: {invoice_id_odoo10}) ya existe en Odoo 15...")

                            # Verificar si la factura ya existe en Odoo 15 basado en 'x_almex_id'
                            existing_invoice = self.env['account.move'].search([
                                ('x_almex_id', '=', invoice_id_odoo10),
                                ('company_id', '=', 6)
                            ])

                            if existing_invoice:
                                _logger.info(f"La factura '{invoice.get('number', '')}' ya existe en Odoo 15 con x_almex_id={invoice_id_odoo10}. Saltando creación.")
                                continue

                            # Obtener el diario adecuado
                            journal = self.env['account.journal'].search([
                                ('type', '=', 'purchase'),
                                ('company_id', '=', 6)
                            ], limit=1)
                            if not journal:
                                _logger.error("No se encontró un diario para facturas de proveedor en la compañía 6.")
                                continue  # Saltar esta factura

                            # Obtener el partner de la factura utilizando x_almex_id
                            partner_id_odoo10 = invoice['partner_id'][0]
                            partner = self.env['res.partner'].search([
                                ('x_almex_id', '=', partner_id_odoo10),
                                ('company_id', '=', 6)
                            ], limit=1)
                            if not partner:
                                _logger.error(f"El partner con x_almex_id {partner_id_odoo10} no existe en Odoo 15.")
                                continue  # Saltar esta factura

                            # Preparar líneas de factura
                            invoice_lines = []
                            for line_id in invoice['invoice_line_ids']:
                                line_odoo10 = models10.execute_kw(
                                    db_odoo10, uid_odoo10, password_odoo10,
                                    'account.invoice.line', 'read', [line_id], {'fields': [
                                        'product_id', 'name', 'quantity', 'price_unit', 'invoice_line_tax_ids', 'account_id'
                                    ]}
                                )[0]

                                # Obtener o crear producto
                                product_odoo10_id = line_odoo10['product_id'][0]
                                product = self.env['product.product'].search([
                                    ('x_almex_id', '=', product_odoo10_id),
                                    ('company_id', '=', 6)
                                ], limit=1)
                                if not product:
                                    _logger.error(f"El producto con x_almex_id '{product_odoo10_id}' no existe en Odoo 15. Saltando línea.")
                                    continue

                                # Obtener cuenta de gasto
                                cuenta_id = product.product_tmpl_id.property_account_expense_id
                                if not cuenta_id:
                                    cuenta_id = product.categ_id.property_account_expense_categ_id
                                if not cuenta_id:
                                    _logger.error(f"No se encontró cuenta de gasto para el producto '{product.name}'. Saltando línea.")
                                    continue

                                # Preparar valores de la línea de factura
                                invoice_line_vals = {
                                    'product_id': product.id,
                                    'name': line_odoo10['name'],
                                    'quantity': line_odoo10['quantity'],
                                    'price_unit': line_odoo10['price_unit'],
                                    'account_id': cuenta_id.id,
                                }

                                # Obtener impuestos
                                if line_odoo10.get('invoice_line_tax_ids'):
                                    taxes = []
                                    for tax_id in line_odoo10['invoice_line_tax_ids']:
                                        tax_odoo10 = models10.execute_kw(
                                            db_odoo10, uid_odoo10, password_odoo10,
                                            'account.tax', 'read', [tax_id], {'fields': ['name', 'amount', 'type_tax_use', 'amount_type', 'price_include', 'tax_group_id', 'sequence']}
                                        )[0]

                                        tax = self.env['account.tax'].search([
                                            ('name', '=', tax_odoo10['name']),
                                            ('company_id', '=', 6)
                                        ], limit=1)
                                        if not tax:
                                            # Obtener o crear el grupo de impuestos
                                            tax_group_name = tax_odoo10.get('tax_group_id', False) and tax_odoo10['tax_group_id'][1] or 'Tax Group'
                                            tax_group = self.env['account.tax.group'].search([('name', '=', tax_group_name)], limit=1)
                                            if not tax_group:
                                                tax_group = self.env['account.tax.group'].create({
                                                    'name': tax_group_name,
                                                    'sequence': tax_odoo10.get('sequence', 1),
                                                })
                                            # Mapear amount_type de Odoo 10 a valores válidos en Odoo 15
                                            amount_type_odoo10 = tax_odoo10.get('amount_type', 'percent')
                                            amount_type_map = {
                                                'percent': 'percent',
                                                'fixed': 'fixed',
                                                'code': 'percent',  # Mapear 'code' a 'percent'
                                            }
                                            amount_type_odoo15 = amount_type_map.get(amount_type_odoo10, 'percent')

                                            # Si amount_type es 'code', establecer amount en 0.0 y registrar una advertencia
                                            if amount_type_odoo10 == 'code':
                                                _logger.warning(f"El impuesto '{tax_odoo10['name']}' tiene amount_type 'code' en Odoo 10. Se asignará 'percent' en Odoo 15 y amount=0.0.")
                                                tax_amount = 0.0
                                            else:
                                                tax_amount = tax_odoo10['amount']

                                            # Crear impuesto incluyendo 'country_id' y amount_type mapeado
                                            tax = self.env['account.tax'].create({
                                                'name': tax_odoo10['name'],
                                                'amount': tax_amount,
                                                'amount_type': amount_type_odoo15,
                                                'type_tax_use': tax_odoo10['type_tax_use'],
                                                'company_id': 6,
                                                'country_id': country.id,
                                                'price_include': tax_odoo10.get('price_include', False),
                                                'tax_group_id': tax_group.id,
                                            })
                                        taxes.append(tax.id)
                                    if taxes:
                                        invoice_line_vals['tax_ids'] = [(6, 0, taxes)]

                                invoice_lines.append((0, 0, invoice_line_vals))

                            # Preparar valores de la factura (account.move)
                            invoice_vals = {
                                'move_type': 'in_invoice',  # Factura de proveedor
                                'partner_id': partner.id,
                                'invoice_date': invoice['date_invoice'],
                                'company_id': 6,
                                'journal_id': journal.id,
                                'invoice_line_ids': invoice_lines,
                                'ref': invoice.get('number', ''),
                                'x_almex_id': invoice_id_odoo10,
                                'currency_id': self.env.user.company_id.currency_id.id,
                            }

                            # Crear la factura
                            try:
                                move = self.env['account.move'].create(invoice_vals)
                                _logger.info(f"Factura '{move.name}' creada exitosamente en Odoo 15.")
                            except Exception as e:
                                _logger.error(f"Error al crear la factura '{invoice.get('number', '')}' en Odoo 15: {e}")
                                self.env.cr.rollback()
                                continue  # Saltar esta factura

                            # Validar la factura si es necesario
                            try:
                                move.action_post()
                            except Exception as e:
                                _logger.error(f"Error al validar la factura '{move.name}' en Odoo 15: {e}")
                                self.env.cr.rollback()
                                continue  # Saltar si ocurre un error al validar

                except Exception as e:
                    _logger.error(f"Error al crear la orden de compra '{order['name']}' en Odoo 15: {e}")
                    self.env.cr.rollback()
                    orders_faltantes.append(order_id_odoo10)
                    continue

            # Finalizar el proceso y mostrar el resumen
            _logger.info(f"Se crearon {len(orders_creados)} órdenes de compra en Odoo 15.")
            _logger.info(f"{len(orders_ya_existentes)} órdenes de compra ya existían en Odoo 15.")
            if orders_faltantes:
                _logger.error(f"Las siguientes órdenes de compra fallaron al ser creadas: {orders_faltantes}")

        except Exception as e:
            _logger.error(f"Error durante el proceso de sincronización: {e}")
            self.env.cr.rollback()
