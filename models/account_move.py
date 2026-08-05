# -*- coding: utf-8 -*-

from datetime import datetime, time
import logging

import pytz

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    # IDs conservados del desarrollo original. Es recomendable sustituirlos
    # posteriormente por campos de configuración en res.company.
    _DELIVERY_COMPANY_ID = 40
    _DELIVERY_PICKING_TYPE_ID = 401
    _DELIVERY_SOURCE_LOCATION_ID = 536
    _DELIVERY_DEST_LOCATION_ID = 5

    otro_comentario = fields.Char("Otro comentario")
    picking_id = fields.Many2one(
        "stock.picking",
        string="Albarán",
        copy=False,
        readonly=True,
        check_company=True,
    )
    x_almex_id = fields.Integer(
        "Almex ID",
        help="ID de la orden de compra en Odoo 10",
    )

    def _get_invoice_delivery_datetime(self):
        """Convert the invoice date into a timezone-safe UTC datetime."""
        self.ensure_one()
        invoice_date = self.invoice_date or self.date
        if not invoice_date:
            raise ValidationError(
                _("La factura %s no tiene fecha.", self.display_name)
            )

        tz_name = (
            self.company_id.partner_id.tz
            or self.env.user.tz
            or "UTC"
        )
        try:
            local_tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            local_tz = pytz.UTC

        # Mediodía evita que la fecha cambie al convertirla a UTC.
        local_datetime = local_tz.localize(
            datetime.combine(invoice_date, time(hour=12))
        )
        return local_datetime.astimezone(pytz.UTC).replace(tzinfo=None)

    def _get_invoice_delivery_setup(self):
        """Return and validate the picking type and locations."""
        self.ensure_one()
        picking_type = self.env["stock.picking.type"].browse(
            self._DELIVERY_PICKING_TYPE_ID
        ).exists()
        source_location = self.env["stock.location"].browse(
            self._DELIVERY_SOURCE_LOCATION_ID
        ).exists()
        destination_location = self.env["stock.location"].browse(
            self._DELIVERY_DEST_LOCATION_ID
        ).exists()

        if not picking_type or picking_type.code != "outgoing":
            raise ValidationError(
                _(
                    "El tipo de operación con ID %(id)s no existe o no es una salida.",
                    id=self._DELIVERY_PICKING_TYPE_ID,
                )
            )
        if picking_type.company_id != self.company_id:
            raise ValidationError(
                _(
                    "El tipo de operación %(picking_type)s no pertenece a "
                    "la compañía de la factura %(invoice)s.",
                    picking_type=picking_type.display_name,
                    invoice=self.display_name,
                )
            )
        if not source_location or not destination_location:
            raise ValidationError(
                _(
                    "No se encontraron las ubicaciones configuradas para generar "
                    "la salida de la factura %(invoice)s.",
                    invoice=self.display_name,
                )
            )

        return picking_type, source_location, destination_location

    def _get_invoice_stock_lines(self):
        """Return invoice lines that must produce a stock move in Odoo 19."""
        self.ensure_one()
        return self.invoice_line_ids.filtered(
            lambda line:
                line.display_type == "product"
                and line.product_id
                and line.quantity > 0
                and (
                    line.product_id.is_storable
                    or line.product_id.is_kits
                )
        )

    def _create_invoice_picking(self):
        """Create, confirm and reserve one delivery per posted invoice."""
        invoices = self.sorted(
            key=lambda move: (
                move.invoice_date or move.date,
                move.name or "",
                move.id,
            )
        )
        for invoice in invoices:
            if invoice.state != "posted":
                raise UserError(
                    _(
                        "La factura %(invoice)s debe estar publicada antes de "
                        "generar su salida.",
                        invoice=invoice.display_name,
                    )
                )
            if invoice.move_type != "out_invoice":
                continue
            if invoice.company_id.id != invoice._DELIVERY_COMPANY_ID:
                continue
            existing_picking = (
                invoice.picking_id
                or self.env["stock.picking"].search([
                    ("company_id", "=", invoice.company_id.id),
                    ("invoice_id", "=", invoice.id),
                ], limit=1)
                or self.env["stock.picking"].search([
                    ("company_id", "=", invoice.company_id.id),
                    (
                        "picking_type_id",
                        "=",
                        invoice._DELIVERY_PICKING_TYPE_ID,
                    ),
                    ("origin", "=", invoice.name),
                ], limit=1)
            )
            if existing_picking:
                if not invoice.picking_id:
                    invoice.picking_id = existing_picking
                _logger.info(
                    "No se volvió a crear la salida de %s porque ya está "
                    "relacionada con %s.",
                    invoice.display_name,
                    existing_picking.display_name,
                )
                continue

            invoice_lines = invoice._get_invoice_stock_lines()
            if not invoice_lines:
                _logger.info(
                    "No se creó salida para %s porque no contiene productos "
                    "almacenables ni kits.",
                    invoice.display_name,
                )
                continue

            (
                picking_type,
                source_location,
                destination_location,
            ) = invoice._get_invoice_delivery_setup()
            effective_datetime = invoice._get_invoice_delivery_datetime()

            picking = self.env["stock.picking"].create({
                "partner_id": (
                    invoice.partner_shipping_id
                    or invoice.partner_id
                ).id,
                "location_id": source_location.id,
                "location_dest_id": destination_location.id,
                "picking_type_id": picking_type.id,
                "origin": invoice.name,
                "move_type": "direct",
                "scheduled_date": effective_datetime,
                "invoice_id": invoice.id,
                "invoice_effective_date": effective_datetime,
                "invoice_picking_created_at": fields.Datetime.now(),
            })

            move_values = []
            for line in invoice_lines:
                move_values.append({
                    "product_id": line.product_id.id,
                    "product_uom_qty": line.quantity,
                    "product_uom": (
                        line.product_uom_id
                        or line.product_id.uom_id
                    ).id,
                    "description_picking": (
                        line.name
                        or line.product_id.display_name
                    ),
                    "picking_id": picking.id,
                    "location_id": source_location.id,
                    "location_dest_id": destination_location.id,
                    "date": effective_datetime,
                    "origin": invoice.name,
                })

            self.env["stock.move"].create(move_values)

            # Odoo 19 explota automáticamente las BoM de tipo phantom (kit)
            # durante la confirmación. No se deben crear también los
            # componentes manualmente porque duplicaría la salida.
            picking.action_confirm()
            picking.action_assign()

            unavailable_moves = picking.move_ids.filtered(
                lambda stock_move:
                    stock_move.product_id.is_storable
                    and stock_move.state not in ("done", "cancel")
                    and stock_move.product_uom.compare(
                        stock_move.quantity,
                        stock_move.product_uom_qty,
                    ) < 0
            )
            if unavailable_moves:
                unavailable_products = ", ".join(
                    unavailable_moves.product_id.mapped("display_name")
                )
                raise UserError(
                    _(
                        "No se puede validar automáticamente la salida "
                        "%(picking)s porque no existe disponibilidad completa "
                        "para: %(products)s. No se generó una salida parcial.",
                        picking=picking.display_name,
                        products=unavailable_products,
                    )
                )

            # button_validate ejecuta las validaciones normales de Odoo para
            # cantidades, lotes y números de serie. StockPicking._action_done,
            # definido abajo, aplica la fecha efectiva de la factura.
            picking.button_validate()
            if picking.state != "done":
                raise UserError(
                    _(
                        "Odoo no pudo validar automáticamente la salida "
                        "%(picking)s. Revise si requiere lotes, números de "
                        "serie o la confirmación de un backorder.",
                        picking=picking.display_name,
                    )
                )

            invoice.picking_id = picking
            invoice.message_post(
                body=_(
                    "Se creó y validó la salida %(picking)s con fecha "
                    "efectiva %(date)s.",
                    picking=picking.display_name,
                    date=invoice.invoice_date or invoice.date,
                )
            )
            _logger.info(
                "Salida %s creada para la factura %s.",
                picking.display_name,
                invoice.display_name,
            )

        return True

    def action_create_picking(self):
        """Create missing pickings for invoices that are already posted."""
        self._create_invoice_picking()
        if len(self) == 1 and self.picking_id:
            return self.action_view_picking()
        return True

    def action_post(self):
        result = super().action_post()

        # En Odoo 19 action_post puede devolver un asistente sin publicar aún.
        # Sólo se procesan las facturas que realmente quedaron en estado posted.
        self.filtered(lambda move: move.state == "posted")._create_invoice_picking()
        return result

    def action_view_picking(self):
        self.ensure_one()
        if not self.picking_id:
            raise UserError(
                _("No hay un albarán asociado a esta factura.")
            )

        return {
            "type": "ir.actions.act_window",
            "name": _("Albarán"),
            "res_model": "stock.picking",
            "view_mode": "form",
            "views": [(False, "form")],
            "res_id": self.picking_id.id,
            "target": "current",
        }


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_id = fields.Many2one(
        "account.move",
        string="Factura origen",
        copy=False,
        readonly=True,
        index=True,
        check_company=True,
    )
    invoice_effective_date = fields.Datetime(
        string="Fecha efectiva de la factura",
        copy=False,
        readonly=True,
        index=True,
    )
    invoice_picking_created_at = fields.Datetime(
        string="Fecha de creación de la regularización",
        copy=False,
        readonly=True,
    )

    def _action_done(self):
        """Validate invoice deliveries using the invoice's effective date."""
        result = True

        # A validation can contain several transfers with different invoice
        # dates. Each date must receive its own force_period_date context.
        grouped_pickings = {}
        for picking in self:
            accounting_date = (
                picking.invoice_id.invoice_date
                or picking.invoice_id.date
                or False
            )
            key = (
                accounting_date,
                picking.invoice_effective_date or False,
            )
            grouped_pickings.setdefault(key, self.env["stock.picking"])
            grouped_pickings[key] |= picking

        ordered_keys = sorted(
            grouped_pickings,
            key=lambda key: (
                key[0] is False,
                key[0] or fields.Date.today(),
                key[1] or fields.Datetime.now(),
            ),
        )
        for (
            accounting_date,
            effective_datetime,
        ) in ordered_keys:
            pickings = grouped_pickings[
                (accounting_date, effective_datetime)
            ]
            dated_pickings = pickings
            if accounting_date:
                dated_pickings = dated_pickings.with_context(
                    force_period_date=accounting_date
                )

            result = (
                super(StockPicking, dated_pickings)._action_done()
                and result
            )

            if effective_datetime:
                done_moves = pickings.move_ids.filtered(
                    lambda move: move.state == "done"
                )
                # En Odoo 19, escribir la fecha en un movimiento terminado
                # también actualiza la fecha de sus stock.move.line.
                done_moves.write({"date": effective_datetime})
                pickings.write({"date_done": effective_datetime})

        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_account_id(self):
        """Port of the former _get_computed_account customization."""
        super()._compute_account_id()
        for line in self:
            journal = line.move_id.journal_id
            if (
                line.display_type == "product"
                and journal.cuenta_default
                and journal.default_account_id
                and line.move_id.is_sale_document(include_receipts=True)
            ):
                line.account_id = journal.default_account_id