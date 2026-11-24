from datetime import date

from freezegun import freeze_time

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
@freeze_time("2026-11-24")
class TestVendorCurrencyRate(AccountTestInvoicingCommon):
    invoice_date = date(2026, 8, 4)
    accounting_date = date(2026, 11, 2)
    invoice_rate = 1 / 7.62060
    accounting_rate = 1 / 7.64187

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gtq = cls.env.ref("base.GTQ")
        cls.usd = cls.env.ref("base.USD")
        (cls.gtq | cls.usd).active = True
        cls.vendor_company_data = cls.setup_other_company(
            name="Vendor accounting date tests", currency_id=cls.gtq.id,
        )
        cls.company = cls.vendor_company_data["company"]
        cls.env["res.currency.rate"].create([
            {
                "company_id": cls.company.id,
                "currency_id": currency.id,
                "name": rate_date,
                "rate": rate,
            }
            for currency, rate_date, rate in (
                (cls.gtq, cls.invoice_date, 1),
                (cls.usd, cls.invoice_date, cls.invoice_rate),
                (cls.usd, cls.accounting_date, cls.accounting_rate),
            )
        ])

    def _invoice(self, move_type="in_invoice", company_data=None, **values):
        company_data = company_data or self.vendor_company_data
        is_purchase = move_type in ("in_invoice", "in_refund", "in_receipt")
        return self.env["account.move"].with_company(company_data["company"]).create({
            "move_type": move_type,
            "journal_id": company_data[
                "default_journal_purchase" if is_purchase else "default_journal_sale"
            ].id,
            "partner_id": self.partner_a.id,
            "currency_id": self.usd.id,
            "invoice_date": self.invoice_date,
            "date": self.accounting_date,
            "invoice_line_ids": [Command.create({
                "name": "Currency rate regression",
                "account_id": company_data[
                    "default_account_expense" if is_purchase else "default_account_revenue"
                ].id,
                "quantity": 1760,
                "price_unit": 23.37,
                "tax_ids": [Command.clear()],
            })],
            **values,
        })

    def _assert_amounts(self, invoice, expected_balance):
        self.assertAlmostEqual(abs(invoice.invoice_line_ids.amount_currency), 41131.20, places=2)
        self.assertAlmostEqual(invoice.invoice_line_ids.balance, expected_balance, places=2)
        self.assertAlmostEqual(sum(invoice.line_ids.mapped("balance")), 0, places=2)

    def test_bill_and_credit_note_use_accounting_date(self):
        for move_type, sign in (("in_invoice", 1), ("in_refund", -1)):
            with self.subTest(move_type=move_type):
                invoice = self._invoice(move_type)
                self.assertEqual(invoice._get_invoice_currency_rate_date(), self.accounting_date)
                self.assertAlmostEqual(invoice.invoice_currency_rate, self.accounting_rate)
                self._assert_amounts(invoice, sign * 314319.28)
                invoice.action_post()
                self.assertEqual(invoice.state, "posted")
                self._assert_amounts(invoice, sign * 314319.28)

    def test_date_write_refreshes_cached_rate_and_balances(self):
        for move_type, sign in (("in_invoice", 1), ("in_refund", -1)):
            with self.subTest(move_type=move_type):
                invoice = self._invoice(move_type, date=self.invoice_date)
                self.assertAlmostEqual(invoice.expected_currency_rate, self.invoice_rate)
                self._assert_amounts(invoice, sign * 313444.42)
                invoice.write({"date": self.accounting_date})
                self.assertAlmostEqual(invoice.expected_currency_rate, self.accounting_rate)
                self.assertAlmostEqual(invoice.invoice_currency_rate, self.accounting_rate)
                self._assert_amounts(invoice, sign * 314319.28)

    def test_form_date_onchange(self):
        invoice = self._invoice(date=self.invoice_date)
        with Form(invoice) as form:
            form.date = self.accounting_date
            self.assertAlmostEqual(form.invoice_currency_rate, self.accounting_rate)
        self._assert_amounts(invoice, 314319.28)

    def test_manual_rate_priority_and_unrelated_writes(self):
        invoice = self._invoice(date=self.invoice_date, invoice_currency_rate=0.2)
        invoice.write({"date": self.accounting_date, "invoice_currency_rate": 0.25})
        invoice.write({"date": self.accounting_date})
        invoice.write({"ref": "Keep manual rate"})
        self.assertEqual(invoice.invoice_currency_rate, 0.25)
        self._assert_amounts(invoice, 164524.80)
        invoice.action_post()
        self.assertEqual(invoice.invoice_currency_rate, 0.25)

    def test_customers_and_receipts_keep_standard_rate_and_manual_override(self):
        for move_type in ("out_invoice", "out_refund", "out_receipt", "in_receipt"):
            with self.subTest(move_type=move_type):
                invoice = self._invoice(move_type, date=self.invoice_date)
                self.assertEqual(invoice._get_invoice_currency_rate_date(), self.invoice_date)
                self.assertAlmostEqual(invoice.invoice_currency_rate, self.invoice_rate)
                invoice.invoice_currency_rate = 0.25
                invoice.write({"date": self.accounting_date})
                self.assertEqual(invoice.invoice_currency_rate, 0.25)

    def test_same_currency_and_missing_date_fallback(self):
        invoice = self._invoice(currency_id=self.gtq.id)
        self.assertEqual(invoice.invoice_currency_rate, 1)
        self._assert_amounts(invoice, 41131.20)
        unsaved = self.env["account.move"].new({
            "move_type": "in_invoice", "date": False, "invoice_date": self.invoice_date,
        })
        self.assertEqual(unsaved._get_invoice_currency_rate_date(), self.invoice_date)

    def test_batch_write_only_refreshes_vendor_drafts(self):
        bill = self._invoice(date=self.invoice_date)
        refund = self._invoice("in_refund", date=self.invoice_date)
        customer = self._invoice("out_invoice", date=self.invoice_date, invoice_currency_rate=0.25)
        (bill | refund | customer).write({"date": self.accounting_date})
        self._assert_amounts(bill, 314319.28)
        self._assert_amounts(refund, -314319.28)
        self.assertEqual(customer.invoice_currency_rate, 0.25)

    def test_posted_legacy_rates_survive_forced_recompute(self):
        for move_type in ("in_invoice", "in_refund"):
            with self.subTest(move_type=move_type):
                invoice = self._invoice(move_type, invoice_currency_rate=self.invoice_rate)
                invoice.action_post()
                before = invoice.line_ids.read(["balance", "amount_currency", "debit", "credit"])
                invoice.flush_recordset()
                invoice.invalidate_recordset(["invoice_currency_rate", "expected_currency_rate"])
                self.env.add_to_compute(invoice._fields["invoice_currency_rate"], invoice)
                invoice._recompute_recordset(["invoice_currency_rate"])
                self.assertAlmostEqual(invoice.expected_currency_rate, self.accounting_rate)
                self.assertAlmostEqual(invoice.invoice_currency_rate, self.invoice_rate)
                self.assertEqual(
                    invoice.line_ids.read(["balance", "amount_currency", "debit", "credit"]), before,
                )

    def test_company_specific_rates_in_batch(self):
        other_data = self.setup_other_company(name="Other vendor company", currency_id=self.gtq.id)
        self.env["res.currency.rate"].create([
            {
                "company_id": other_data["company"].id,
                "currency_id": currency.id,
                "name": self.invoice_date,
                "rate": rate,
            }
            for currency, rate in ((self.gtq, 1), (self.usd, 1 / 8))
        ])
        bill = self._invoice(date=self.invoice_date)
        other_bill = self._invoice(company_data=other_data, date=self.invoice_date)
        (bill | other_bill).write({"date": self.accounting_date})
        self._assert_amounts(bill, 314319.28)
        self._assert_amounts(other_bill, 329049.60)

    def test_inherited_compute_dependencies(self):
        model = self.env["account.move"]
        native = {"currency_id", "company_currency_id", "company_id", "invoice_date", "taxable_supply_date"}
        expected_deps, _ = model._fields["expected_currency_rate"].get_depends(model)
        stored_deps, _ = model._fields["invoice_currency_rate"].get_depends(model)
        self.assertTrue((native | {"date", "move_type"}).issubset(expected_deps))
        self.assertTrue(native.issubset(stored_deps))
