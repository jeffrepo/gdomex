from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestJournalAnalyticDistribution(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.analytic_plan = cls.env["account.analytic.plan"].create({
            "name": "Journal analytic plan",
            "company_id": cls.env.company.id,
        })
        cls.sale_analytic_account = cls.env[
            "account.analytic.account"
        ].create({
            "name": "Sale journal analytic account",
            "plan_id": cls.analytic_plan.id,
            "company_id": cls.env.company.id,
        })
        cls.alternate_analytic_account = cls.env[
            "account.analytic.account"
        ].create({
            "name": "Alternate journal analytic account",
            "plan_id": cls.analytic_plan.id,
            "company_id": cls.env.company.id,
        })
        cls.purchase_analytic_account = cls.env[
            "account.analytic.account"
        ].create({
            "name": "Purchase journal analytic account",
            "plan_id": cls.analytic_plan.id,
            "company_id": cls.env.company.id,
        })

        cls.sale_journal = cls.company_data["default_journal_sale"]
        cls.sale_journal.analytic_account_id = cls.sale_analytic_account
        cls.alternate_sale_journal = cls.sale_journal.copy({
            "name": "Alternate sale journal",
            "code": "ASJ",
            "analytic_account_id": cls.alternate_analytic_account.id,
        })
        cls.purchase_journal = cls.company_data["default_journal_purchase"]
        cls.purchase_journal.analytic_account_id = (
            cls.purchase_analytic_account
        )

    @classmethod
    def _create_invoice(cls, move_type, journal):
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type=move_type,
            )
        )
        move_form.invoice_date = fields.Date.today()
        move_form.partner_id = cls.partner_a
        if not move_form._get_modifier("journal_id", "invisible"):
            move_form.journal_id = journal
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product_a
        return move_form.save()

    def test_sale_and_purchase_lines_use_journal_analytic_account(self):
        sale_invoice = self._create_invoice("out_invoice", self.sale_journal)
        purchase_invoice = self._create_invoice(
            "in_invoice",
            self.purchase_journal,
        )

        self.assertEqual(
            sale_invoice.invoice_line_ids.analytic_distribution,
            {str(self.sale_analytic_account.id): 100.0},
        )
        self.assertEqual(
            purchase_invoice.invoice_line_ids.analytic_distribution,
            {str(self.purchase_analytic_account.id): 100.0},
        )

    def test_changing_journal_replaces_analytic_account(self):
        invoice = self._create_invoice("out_invoice", self.sale_journal)

        with Form(invoice) as move_form:
            move_form.journal_id = self.alternate_sale_journal

        self.assertEqual(
            invoice.invoice_line_ids.analytic_distribution,
            {str(self.alternate_analytic_account.id): 100.0},
        )

    def test_generated_line_with_distribution_uses_journal_account(self):
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "journal_id": self.sale_journal.id,
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                Command.create({
                    "product_id": self.product_a.id,
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "analytic_distribution": {
                        str(self.alternate_analytic_account.id): 100.0,
                    },
                }),
            ],
        })

        self.assertEqual(
            invoice.invoice_line_ids.analytic_distribution,
            {str(self.sale_analytic_account.id): 100.0},
        )
