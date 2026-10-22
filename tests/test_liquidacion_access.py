from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestLiquidacionAccess(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operator = new_test_user(
            cls.env,
            login="liquidacion_operator",
            groups="base.group_user,gdomex.group_liquidacion_user",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )
        cls.employee = new_test_user(
            cls.env,
            login="liquidacion_employee",
            groups="base.group_user",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )
        cls.accountant = new_test_user(
            cls.env,
            login="liquidacion_accountant",
            groups="base.group_user,account.group_account_invoice",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )
        cls.liquidation = cls.env["account_gt.liquidacion"].with_user(cls.operator).create({
            "descripcion": "Gastos de prueba",
            "fecha": fields.Date.today(),
            "diario_id": cls.company_data["default_journal_misc"].id,
        })

    def _bill_values(self, **overrides):
        values = {
            "move_type": "in_invoice",
            "liquidacion_id": self.liquidation.id,
            "journal_id": self.company_data["default_journal_purchase"].id,
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [Command.create({
                "name": "Gasto",
                "account_id": self.company_data["default_account_expense"].id,
                "quantity": 1,
                "price_unit": 100,
                "tax_ids": [Command.clear()],
            })],
        }
        values.update(overrides)
        return values

    def _create_bill(self, **overrides):
        return self.env["account.move"].with_user(self.operator).create(
            self._bill_values(**overrides)
        )

    def _assert_inline_bill_type_is_sent(self, form):
        # Readonly fields are omitted from nested commands unless force_save
        # is set. A child's default_move_type context does not reach the
        # parent save RPC, so its CREATE command must carry the type itself.
        commands = form._get_save_values()["factura_relacion_ids"]
        created = [command[2] for command in commands if command[0] == Command.CREATE]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].get("move_type"), "in_invoice")

    def test_menu_and_groups(self):
        root = self.env.ref("gdomex.menu_liquidaciones_root")
        finance = self.env.ref("account.menu_finance")
        operator_menus = self.env["ir.ui.menu"].with_user(self.operator)._visible_menu_ids()
        employee_menus = self.env["ir.ui.menu"].with_user(self.employee)._visible_menu_ids()
        self.assertIn(root.id, operator_menus)
        self.assertNotIn(finance.id, operator_menus)
        self.assertNotIn(root.id, employee_menus)
        self.assertFalse(self.operator.has_group("account.group_account_invoice"))
        self.assertFalse(self.operator.has_group("account.group_account_readonly"))
        with self.assertRaises(AccessError):
            self.liquidation.with_user(self.employee).read(["descripcion"])

    def test_create_and_post_vendor_bill(self):
        bill = self._create_bill()
        bill.action_post()
        self.assertEqual(bill.state, "posted")
        self.assertEqual(bill.liquidacion_id, self.liquidation)
        self.assertEqual(bill.write_uid, self.operator)
        self.assertAlmostEqual(sum(bill.line_ids.mapped("balance")), 0)
        self.assertFalse(bill.env.su)
        self.assertFalse(self.operator.has_group("account.group_account_invoice"))

    def test_vendor_bill_form_and_line_editing(self):
        action = self.liquidation.action_create_vendor_bill()
        move_model = self.env["account.move"].with_user(self.operator).with_context(action["context"])
        with Form(move_model, view="gdomex.view_liquidacion_vendor_bill_form") as form:
            form.partner_id = self.partner_a
            form.invoice_date = fields.Date.today()
            with form.invoice_line_ids.new() as line:
                line.product_id = self.product_a
                line.quantity = 1
                line.price_unit = 100
        bill = form.record
        self.assertEqual(bill.move_type, "in_invoice")
        self.assertEqual(bill.liquidacion_id, self.liquidation)
        with Form(bill, view="gdomex.view_liquidacion_vendor_bill_form") as form:
            with form.invoice_line_ids.edit(0) as line:
                line.price_unit = 125
        bill.action_post()
        self.assertEqual(bill.state, "posted")

    def test_inline_creation_from_liquidation(self):
        with Form(self.liquidation, view="gdomex.view_liquidacion_operator_form") as form:
            with form.factura_relacion_ids.new() as bill:
                bill.partner_id = self.partner_a
                bill.invoice_date = fields.Date.today()
                with bill.invoice_line_ids.new() as line:
                    line.product_id = self.product_a
                    line.quantity = 1
                    line.price_unit = 100
            self._assert_inline_bill_type_is_sent(form)
        invoice = self.liquidation.factura_relacion_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.move_type, "in_invoice")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_forbidden_creation_and_direct_state_change(self):
        for overrides in (
            {"liquidacion_id": False},
            {"move_type": "out_invoice", "journal_id": self.company_data["default_journal_sale"].id},
            {"move_type": "in_refund"},
            {"state": "posted"},
            {"auto_post": "monthly"},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(AccessError), self.cr.savepoint():
                self._create_bill(**overrides)
        bill = self._create_bill()
        for values in ({"state": "posted"}, {"liquidacion_id": False}, {"move_type": "entry"}):
            with self.subTest(values=values), self.assertRaises(AccessError), self.cr.savepoint():
                bill.write(values)

    def test_unrelated_bills_and_journal_entries_are_not_accessible(self):
        unrelated = self.env["account.move"].create(self._bill_values(liquidacion_id=False))
        customer = self.env["account.move"].create(self._bill_values(
            move_type="out_invoice",
            journal_id=self.company_data["default_journal_sale"].id,
        ))
        entry = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.company_data["default_journal_misc"].id,
        })
        allowed = self._create_bill()
        forbidden = unrelated | customer | entry
        operator_moves = self.env["account.move"].with_user(self.operator)
        self.assertFalse(operator_moves.search([("id", "in", forbidden.ids)]))
        for move in forbidden:
            with self.assertRaises(AccessError):
                move.with_user(self.operator).read(["name"])
            with self.assertRaises(AccessError), self.cr.savepoint():
                (allowed | move).with_user(self.operator).action_post()
        self.assertEqual(allowed.state, "draft")
        with self.assertRaises(AccessError):
            unrelated.line_ids.with_user(self.operator).read(["balance"])

    def test_posted_documents_are_immutable_for_operator(self):
        bill = self._create_bill()
        bill.action_post()
        for operation in (
            lambda: bill.write({"ref": "Changed"}),
            lambda: bill.button_draft(),
            lambda: bill.button_cancel(),
            lambda: bill.invoice_line_ids.write({"price_unit": 1}),
            lambda: bill.invoice_line_ids.unlink(),
            lambda: bill.unlink(),
        ):
            with self.assertRaises((AccessError, UserError)), self.cr.savepoint():
                operation()

    def test_other_groups_do_not_widen_the_restricted_bill_scope(self):
        self.operator.group_ids = [Command.link(self.env.ref("sales_team.group_sale_salesman").id)]
        self.assertFalse(self.operator.has_group("account.group_account_invoice"))
        # A global restriction alone does not grant access when Sales adds a
        # group rule limited to customer invoices. Exercise the allowed path
        # too: previously this failed on read while creating the vendor bill.
        bill = self._create_bill()
        bill.read(["name", "company_id", "liquidacion_id"])
        bill.line_ids.read(["name", "balance"])
        bill.invoice_line_ids.write({"price_unit": 125})
        bill.action_post()
        self.assertEqual(bill.state, "posted")
        unrelated = self.env["account.move"].create(self._bill_values(liquidacion_id=False))
        self.assertFalse(self.env["account.move"].with_user(self.operator).search([
            ("id", "=", unrelated.id),
        ]))

    def test_sales_operator_saves_bill_with_existing_liquidation(self):
        self.operator.group_ids = [Command.link(self.env.ref("sales_team.group_sale_salesman").id)]
        with Form(self.liquidation, view="gdomex.view_liquidacion_operator_form") as form:
            with form.factura_relacion_ids.new() as bill:
                bill.partner_id = self.partner_a
                bill.invoice_date = fields.Date.today()
                with bill.invoice_line_ids.new() as line:
                    line.product_id = self.product_a
                    line.quantity = 1
                    line.price_unit = 100
            self._assert_inline_bill_type_is_sent(form)
        invoice = self.liquidation.factura_relacion_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.company_id, self.liquidation.company_id)
        self.assertEqual(invoice.move_type, "in_invoice")
        self.assertEqual(invoice.state, "draft")
        invoice.line_ids.read(["balance"])

    def test_sales_operator_saves_bill_with_new_liquidation(self):
        self.operator.group_ids = [Command.link(self.env.ref("sales_team.group_sale_salesman").id)]
        model = self.env["account_gt.liquidacion"].with_user(self.operator)
        with Form(model, view="gdomex.view_liquidacion_operator_form") as form:
            form.descripcion = "Liquidación nueva con factura y permiso de Ventas"
            form.fecha = fields.Date.today()
            form.diario_id = self.company_data["default_journal_misc"]
            with form.factura_relacion_ids.new() as bill:
                bill.partner_id = self.partner_a
                bill.invoice_date = fields.Date.today()
                with bill.invoice_line_ids.new() as line:
                    line.product_id = self.product_a
                    line.quantity = 1
                    line.price_unit = 100
            self._assert_inline_bill_type_is_sent(form)
        liquidation = form.record
        invoice = liquidation.factura_relacion_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.liquidacion_id, liquidation)
        self.assertEqual(invoice.company_id, liquidation.company_id)
        self.assertEqual(invoice.move_type, "in_invoice")
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_native_bill_date_validation_is_preserved(self):
        bill = self._create_bill(invoice_date=False)
        with self.assertRaises(UserError), self.cr.savepoint():
            bill.action_post()
        self.assertEqual(bill.state, "draft")

    def test_no_payment_or_configuration_write_access(self):
        for model in ("account.payment", "account.journal", "account.account", "account.tax"):
            recordset = self.env[model].with_user(self.operator)
            self.assertFalse(recordset.has_access("create"), model)
            self.assertFalse(recordset.has_access("write"), model)
        self.assertFalse(self.env["account.payment.register"].with_user(self.operator).has_access("create"))
        for method in ("conciliar_liquidacion", "cancelar_liquidacion", "cambiar_borrador"):
            with self.assertRaises(AccessError):
                getattr(self.liquidation, method)()

    def test_closed_liquidation_blocks_modifications(self):
        bill = self._create_bill()
        self.liquidation.sudo().state = "conciliado"
        with self.assertRaises(AccessError):
            bill.action_post()
        with self.assertRaises(AccessError):
            bill.write({"ref": "Changed"})
        with self.assertRaises(AccessError):
            self.liquidation.write({"descripcion": "Changed"})

    def test_other_company_is_not_accessible(self):
        other_company = self.env["res.company"].create({"name": "Otra compañía de liquidaciones"})
        other_journal = self.env["account.journal"].create({
            "name": "Liquidaciones de otra compañía", "code": "LIQX",
            "type": "general", "company_id": other_company.id,
        })
        other_liquidation = self.env["account_gt.liquidacion"].create({
            "company_id": other_company.id,
            "diario_id": other_journal.id,
        })
        with self.assertRaises(AccessError):
            other_liquidation.with_user(self.operator).read(["descripcion"])
        with self.assertRaises((AccessError, UserError)), self.cr.savepoint():
            self._create_bill(liquidacion_id=other_liquidation.id)

    def test_marked_reconciliation_cannot_be_posted_as_sudo(self):
        bill = self._create_bill()
        bill.invoice_line_ids.sudo().matching_number = "I-liquidacion-test"
        with self.assertRaises(UserError):
            bill.action_post()
        self.assertEqual(bill.state, "draft")

    def test_existing_accounting_access_is_preserved(self):
        bill = self.env["account.move"].with_user(self.accountant).create(
            self._bill_values(liquidacion_id=False)
        )
        bill.action_post()
        self.assertEqual(bill.state, "posted")
        self.liquidation.with_user(self.accountant).read(["descripcion"])
