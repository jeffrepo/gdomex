from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    liquidacion_id = fields.Many2one(check_company=True)

    @api.model
    def _is_liquidacion_operator(self):
        return (
            not self.env.su
            and self.env.user.has_group("gdomex.group_liquidacion_user")
            and not self.env.user.has_group("account.group_account_invoice")
        )

    def _check_liquidacion_bill_scope(self, require_draft=False):
        self.check_access("write" if require_draft else "read")
        for move in self:
            liquidation = move.liquidacion_id
            if move.move_type != "in_invoice" or not liquidation:
                raise AccessError(_(
                    "Este perfil sólo permite facturas de proveedor vinculadas "
                    "a una liquidación."
                ))
            liquidation.check_access("write" if require_draft else "read")
            if (
                move.company_id != liquidation.company_id
                or move.company_id not in self.env.companies
            ):
                raise AccessError(_(
                    "La factura y la liquidación deben pertenecer a la misma "
                    "compañía permitida."
                ))
            if require_draft and (
                move.state != "draft" or liquidation.state != "borrador"
            ):
                raise AccessError(_(
                    "Sólo puede modificar o validar facturas en borrador "
                    "de una liquidación en borrador."
                ))

    @api.model
    def _check_liquidacion_bill_values(self, values):
        # These fields can trigger operations on other entries during _post.
        # They are never needed to enter a normal vendor bill.
        if (
            values.get("state", "draft") != "draft"
            or values.get("auto_post", "no") != "no"
            or any(values.get(name) for name in (
                "posted_before", "reversed_entry_id", "origin_payment_id",
                "statement_line_id", "tax_cash_basis_rec_id",
                "tax_cash_basis_origin_move_id", "auto_post_origin_id",
            ))
        ):
            raise AccessError(_(
                "Utilice Validar para publicar una factura de proveedor de "
                "liquidación. Este perfil no permite otras operaciones contables."
            ))

    @api.model_create_multi
    def create(self, vals_list):
        restricted = self._is_liquidacion_operator()
        if restricted:
            for values in vals_list:
                self._check_liquidacion_bill_values(values)
        moves = super().create(vals_list)
        if restricted:
            moves._check_liquidacion_bill_scope(require_draft=True)
            for move in moves:
                move._check_liquidacion_bill_values({
                    name: move[name]
                    for name in (
                        "state", "auto_post", "posted_before", "reversed_entry_id",
                        "origin_payment_id", "statement_line_id",
                        "tax_cash_basis_rec_id", "tax_cash_basis_origin_move_id",
                        "auto_post_origin_id",
                    )
                })
        return moves

    def write(self, vals):
        restricted = self._is_liquidacion_operator()
        if restricted:
            self._check_liquidacion_bill_scope(require_draft=True)
            self._check_liquidacion_bill_values(vals)
        result = super().write(vals)
        if restricted:
            # Record rules check the old record on write; check the destination
            # too, so RPC cannot detach a bill or change it into a journal entry.
            self._check_liquidacion_bill_scope(require_draft=True)
        return result

    def _post(self, soft=True):
        if not self._is_liquidacion_operator():
            return super()._post(soft=soft)

        self._check_liquidacion_bill_scope(require_draft=True)
        for move in self:
            # A draft prepared by Accounting may already have reconciliation
            # links. Publishing it as sudo could otherwise touch other moves.
            inspected = move.sudo()
            if (
                inspected.auto_post != "no"
                or inspected.reversed_entry_id
                or inspected.origin_payment_id
                or inspected.statement_line_id
                or inspected.tax_cash_basis_rec_id
                or inspected.tax_cash_basis_origin_move_id
                or inspected.auto_post_origin_id
                or inspected.line_ids.matched_debit_ids
                or inspected.line_ids.matched_credit_ids
                or inspected.line_ids.reconcile_model_id
                or any(line.matching_number for line in inspected.line_ids)
            ):
                raise UserError(_(
                    "Esta factura contiene vínculos contables especiales. "
                    "Debe validarla un usuario de Contabilidad."
                ))

        # Odoo 19 hard-codes group_account_invoice in _post. Elevation is only
        # for this private, checked operation, preserving all native posting
        # validations and the current uid for the audit trail. No context flag
        # supplied over RPC grants access. Return with the caller's environment.
        # Do not carry client-provided skip/check flags into the elevated call.
        posting = self.sudo().with_context({
            "allowed_company_ids": self.env.companies.ids,
            "lang": self.env.lang,
            "tz": self.env.context.get("tz"),
        })
        posted = super(AccountMove, posting)._post(soft=soft)
        return posted.with_env(self.env)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if self.env["account.move"]._is_liquidacion_operator():
            lines.move_id._check_liquidacion_bill_scope(require_draft=True)
        return lines

    def write(self, vals):
        restricted = self.env["account.move"]._is_liquidacion_operator()
        if restricted:
            self.move_id._check_liquidacion_bill_scope(require_draft=True)
        result = super().write(vals)
        if restricted:
            self.move_id._check_liquidacion_bill_scope(require_draft=True)
        return result

    def unlink(self):
        if self.env["account.move"]._is_liquidacion_operator():
            self.move_id._check_liquidacion_bill_scope(require_draft=True)
        return super().unlink()


class Liquidacion(models.Model):
    _inherit = "account_gt.liquidacion"

    def action_create_vendor_bill(self):
        self.ensure_one()
        self.check_access("write")
        if not self.env.user.has_group("gdomex.group_liquidacion_user"):
            raise AccessError(_("Necesita el grupo de Liquidaciones."))
        if self.state != "borrador":
            raise UserError(_("La liquidación debe estar en borrador."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Factura de proveedor"),
            "res_model": "account.move",
            "view_mode": "form",
            "views": [(self.env.ref("gdomex.view_liquidacion_vendor_bill_form").id, "form")],
            "target": "current",
            "context": {
                "default_move_type": "in_invoice",
                "default_tipo_factura": "compra",
                "default_liquidacion_id": self.id,
                "default_company_id": self.company_id.id,
                "allowed_company_ids": self.env.companies.ids,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        if self.env["account.move"]._is_liquidacion_operator():
            for vals in vals_list:
                if vals.get("state", "borrador") != "borrador" or vals.get("move_id"):
                    raise AccessError(_("Debe crear la liquidación en borrador."))
        records = super().create(vals_list)
        if self.env["account.move"]._is_liquidacion_operator():
            if any(r.state != "borrador" or r.move_id for r in records):
                raise AccessError(_("Debe crear la liquidación en borrador."))
        return records

    def write(self, vals):
        if self.env["account.move"]._is_liquidacion_operator():
            self.check_access("write")
            if (
                any(record.state != "borrador" for record in self)
                or "state" in vals
                or "move_id" in vals
            ):
                raise AccessError(_(
                    "La conciliación y la cancelación de liquidaciones "
                    "requieren permisos de Contabilidad."
                ))
            if "company_id" in vals and any(
                record.company_id.id != vals["company_id"]
                and (record.factura_relacion_ids or record.pago_relacion_ids)
                for record in self
            ):
                raise UserError(_(
                    "No puede cambiar la compañía de una liquidación con documentos."
                ))
        return super().write(vals)

    def _check_liquidacion_accounting_access(self):
        if self.env["account.move"]._is_liquidacion_operator():
            raise AccessError(_(
                "La conciliación y la cancelación de liquidaciones "
                "requieren permisos de Contabilidad."
            ))

    def conciliar_liquidacion(self):
        self._check_liquidacion_accounting_access()
        return super().conciliar_liquidacion()

    def cancelar_liquidacion(self):
        self._check_liquidacion_accounting_access()
        return super().cancelar_liquidacion()

    def cambiar_borrador(self):
        self._check_liquidacion_accounting_access()
        return super().cambiar_borrador()
