import xmlrpc.client
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SyncProduct(models.Model):
    _name = 'sync.product'
    _description = 'sincronizar Productos de Odoo 10 a Odoo 15'

    def sync_products(self):
        # Conexión a Odoo 10
        url_odoo10 = 'http://45.79.219.125'
        db_odoo10 = 'domex'
        username_odoo10 = 'admin'
        password_odoo10 = '@!DMS1'

        productos_faltantes = []  # Para rastrear productos que no se crean
        productos_ya_existentes = []  # Para rastrear productos que ya existen
        productos_creados = []  # Para rastrear productos que se crean con éxito

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

            # Buscar productos de la compañía 1 en Odoo 10
            _logger.info("Buscando productos en Odoo 10 para la compañía 1...")
            product_ids_odoo10 = models10.execute_kw(db_odoo10, uid_odoo10, password_odoo10,
                'product.product', 'search', [[['company_id', '=', 1]]])

            _logger.info(f"Se encontraron {len(product_ids_odoo10)} productos en Odoo 10.")

            if not product_ids_odoo10:
                _logger.warning("No se encontraron productos en Odoo 10 para la compañía 1.")
                return

            # Leer los productos encontrados en Odoo 10
            _logger.info("Leyendo los datos de los productos en Odoo 10...")
            products_odoo10 = models10.execute_kw(db_odoo10, uid_odoo10, password_odoo10,
                'product.product', 'read', [product_ids_odoo10], {'fields': [
                    'id', 'name', 'default_code', 'list_price', 'standard_price', 'type', 'categ_id', 'uom_id', 'uom_po_id', 'description_sale', 'description_purchase'
                ]})

            _logger.info(f"Datos de productos leídos correctamente. Iniciando sincronización con Odoo 15.")

            # Obtener el ID del Administrador en Odoo 15
            admin_user = self.env.ref('base.user_admin')

            for product in products_odoo10:
                product_id_odoo10 = product['id']  # ID del producto en Odoo 10

                _logger.info(f"Verificando si el producto '{product['name']}' (ID Odoo 10: {product_id_odoo10}) ya existe en Odoo 15...")

                # Verificar si el producto ya existe en Odoo 15 basado en 'x_almex_id'
                existing_product = self.env['product.product'].search([
                    ('x_almex_id', '=', product_id_odoo10),
                    ('company_id', '=', 6)  # Asegurarse de que pertenece a la compañía correcta
                ])

                if existing_product:
                    _logger.info(f"El producto '{product['name']}' ya existe en Odoo 15 con almex_id={product_id_odoo10}. Saltando creación.")
                    productos_ya_existentes.append(product_id_odoo10)
                    continue

                # Crear la categoría si no existe en Odoo 15
                category_id = self.env['product.category'].search([('id', '=', product['categ_id'][0])], limit=1)
                if not category_id:
                    _logger.warning(f"Categoría no encontrada en Odoo 15 para '{product['name']}'. Creando la categoría...")
                    category_id = self.env['product.category'].create({
                        'name': f'Categoría Odoo 10 - {product["categ_id"][1]}',
                    })
                    _logger.info(f"Categoría '{category_id.name}' creada exitosamente.")

                # Crear la unidad de medida (uom_id) si no existe en Odoo 15
                uom_id = self.env['uom.uom'].search([('id', '=', product['uom_id'][0])], limit=1) if product.get('uom_id') else False
                if not uom_id and product.get('uom_id'):
                    _logger.warning(f"Unidad de medida no encontrada en Odoo 15 para '{product['name']}'. Creando unidad de medida...")
                    uom_id = self.env['uom.uom'].create({
                        'name': f'Unidad Odoo 10 - {product["uom_id"][1]}',
                        'category_id': 1,  # Ajusta la categoría si es necesario
                        'uom_type': 'reference',
                        'factor': 1.0,
                    })
                    _logger.info(f"Unidad de medida '{uom_id.name}' creada exitosamente.")

                # Crear la unidad de compra (uom_po_id) si no existe en Odoo 15
                uom_po_id = self.env['uom.uom'].search([('id', '=', product['uom_po_id'][0])], limit=1) if product.get('uom_po_id') else False
                if not uom_po_id and product.get('uom_po_id'):
                    _logger.warning(f"Unidad de compra no encontrada en Odoo 15 para '{product['name']}'. Creando unidad de compra...")
                    uom_po_id = self.env['uom.uom'].create({
                        'name': f'Unidad Compra Odoo 10 - {product["uom_po_id"][1]}',
                        'category_id': 1,  # Ajusta la categoría si es necesario
                        'uom_type': 'reference',
                        'factor': 1.0,
                    })
                    _logger.info(f"Unidad de compra '{uom_po_id.name}' creada exitosamente.")

                # Intentar crear el producto
                try:
                    self.env['product.product'].create({
                        'name': product['name'],
                        'default_code': product.get('default_code', ''),
                        'list_price': product.get('list_price', 0),
                        'standard_price': product.get('standard_price', 0),
                        'categ_id': category_id.id,
                        'uom_id': uom_id.id if uom_id else False,
                        'uom_po_id': uom_po_id.id if uom_po_id else False,
                        'description_sale': product.get('description_sale', ''),
                        'description_purchase': product.get('description_purchase', ''),
                        'company_id': 6,
                        'x_almex_id': product_id_odoo10,
                        'type': product.get('type', 'product'),
                        'responsible_id': admin_user.id
                    })
                    _logger.info(f"Producto '{product['name']}' (ID Odoo 10: {product_id_odoo10}) creado exitosamente en Odoo 15.")
                    productos_creados.append(product_id_odoo10)
                except Exception as e:
                    _logger.error(f"Error al crear el producto '{product['name']}' en Odoo 15: {e}")
                    productos_faltantes.append(product_id_odoo10)

            # Finalizar el proceso y mostrar el resumen
            _logger.info(f"Se crearon {len(productos_creados)} productos en Odoo 15.")
            _logger.info(f"{len(productos_ya_existentes)} productos ya existían en Odoo 15.")
            if productos_faltantes:
                _logger.error(f"Los siguientes productos fallaron al ser creados: {productos_faltantes}")

        except Exception as e:
            _logger.error(f"Error durante el proceso de sincronización: {e}")

    