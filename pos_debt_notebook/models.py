# Copyright 2014-2019 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2015 Alexis de Lattre <https://github.com/alexis-via>
# Copyright 2016-2017 Stanislav Krotov <https://it-projects.info/team/ufaks>
# Copyright 2016 Florent Thomas <https://it-projects.info/team/flotho>
# Copyright 2017 iceship <https://github.com/iceship>
# Copyright 2017 gnidorah <https://github.com/gnidorah>
# Copyright 2018 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
# License MIT (https://opensource.org/licenses/MIT).

import copy
import logging

import pytz
from pytz import timezone

from odoo import api, fields, models
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("report_pos_debt_ids")
    def _compute_debt(self):
        domain = [("partner_id", "in", self.ids)]
        fields = ["partner_id", "balance"]
        res = self.env["report.pos.debt"].read_group(domain, fields, "partner_id")
        res_index = {id: {"balance": 0} for id in self.ids}
        for data in res:
            res_index[data["partner_id"][0]] = data
        for r in self:
            #print("rrrrr",r,res_index[r.id])
            r.debt = -res_index[r.id]["balance"]
            r.credit_balance = -r.debt

    @api.depends("report_pos_debt_ids")
    def _compute_debt_company(self):
        for p in self:
            p.debt_company += 0
            p.credit_balance_company += 0
        #print("_compute_debt_company22")
        partners = self.filtered(lambda r: len(r.child_ids))
        #print("partners",partners)
        if not partners:
            return
        domain = [("partner_id", "in", partners.ids + partners.mapped("child_ids").ids)]
        fields = ["partner_id", "balance"]
        res = self.env["report.pos.debt"].read_group(domain, fields, "partner_id")
        #print("resssssss",res)
        res_index = {id: 0 for id in partners.ids}
        for data in res:
            pid = data["partner_id"][0]
            balance = data["balance"]
            for r in partners:
                #print("wwww",r,pid)
                if pid == r.id or pid in r.child_ids.ids:
                    res_index[r.id] += balance

        for r in partners:
            r.debt_company = -res_index[r.id]
            r.credit_balance_company = -r.debt_company

    def debt_history(self, limit=0):
        print("debt_historyyyyyy13",self, limit)
        """
        Get debt details

        :param int limit: max number of records to return
        :return: dictionary with keys:
             * partner_id: partner identification                   
             * debt: current debt
             * debts: dictionary with keys:

                 * balance
                 * journal_id: list

                    * id
                    * name
                    * code

             * records_count: total count of records
             * history: list of dictionaries

                 * date
                 * config_id
                 * balance
                 * journal_code

        """
        fields = [
            "date",
            "config_id",
            "order_id",
            "invoice_id",
            "balance",
            "product_list",
            "payment_method_id",
            "partner_id",
        ]
        debt_payment_method = self.env["pos.payment.method"].search([("debt", "=", True)])
        data = {
            id: {
                "history": [],
                "partner_id": id,
                "debt": 0,
                "records_count": 0,
                "debts": {
                    dj.id: {
                        "balance": 0,
                        "payment_method_id": [dj.id, dj.name],
                        "payment_method": dj.name,

                    }
                    for dj in debt_payment_method
                },
            }
            for id in self.ids
        }
        #print("debt_payment_method",debt_payment_method)
        records = self.env["report.pos.debt"].read_group(
            domain=[
                ("partner_id", "in", self.ids),
                ("payment_method_id", "in", debt_payment_method.ids),
            ],
            fields=fields,
            groupby=["partner_id", "payment_method_id"],
            lazy=False,
        )
        #print("records",records)
        for rec in records:
            partner_id = rec["partner_id"][0]
            data[partner_id]["debts"][rec["payment_method_id"][0]]["balance"] = rec["balance"]
            data[partner_id]["records_count"] += rec["__count"]
            # -= due to it's debt, and balances per journals are credits
            data[partner_id]["debt"] -= rec["balance"]
        #print("limt",limit)
        if limit:
            for partner_id in self.ids:
                data[partner_id]["history"] = self.env["report.pos.debt"].search_read(
                    domain=[("partner_id", "=", partner_id),('company_id', '=', self.env.company.id)], fields=fields, limit=limit
                )
                #print("data[partner_id]",data[partner_id])
                for rec in data[partner_id]["history"]:
                    rec["date"] = self._get_date_formats(rec["date"])
                    print("data[partner_id]",data[partner_id])
                    rec["payment_method_code"] = data[partner_id]["debts"][rec["payment_method_id"][0]]["payment_method"]
                    #    rec["payment_method_id"][0]
                    #]["payment_method_code"]

        #print("data13",data)
        return data

    debt = fields.Float(
        compute="_compute_debt",
        string="Debt",
        readonly=True,
        digits="Account",
        help="Debt of this partner only.",
    )
    credit_balance = fields.Float(
        compute="_compute_debt",
        string="Credit",
        readonly=True,
        digits="Account",
        help="Credit balance of this partner only.",
    )
    debt_company = fields.Float(
        compute="_compute_debt_company",
        string="Total Debt",
        readonly=True,
        digits="Account",
        help="Debt value of this company (including its contacts)",
    )
    credit_balance_company = fields.Float(
        compute="_compute_debt_company",
        string="Total Credit",
        readonly=True,
        digits="Account",
        help="Credit balance of this company (including its contacts)",
    )
    debt_type = fields.Selection(
        compute="_compute_debt_type",
        selection=[("debt", "Display Debt"), ("credit", "Display Credit")],
    )
    report_pos_debt_ids = fields.One2many(
        "pos.credit.update",
        "partner_id",
        help="Technical field for proper recomputations of computed fields",
    )

    def _get_date_formats(self, date):

        lang_code = self.env.user.lang or "en_US"
        lang = self.env["res.lang"]._lang_get(lang_code)
        date_format = lang.date_format
        time_format = lang.time_format
        fmt = date_format + " " + time_format
        utc_tz = pytz.utc.localize(date, is_dst=False)
        user_tz = self.env.user.tz
        user_tz = user_tz and timezone(self.env.user.tz) or timezone("GMT")
        final = utc_tz.astimezone(user_tz)

        return final.strftime(fmt)

    def _compute_debt_type(self):
        debt_type = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("pos_debt_notebook.debt_type", default="debt")
        )
        for partner in self:
            partner.debt_type = debt_type

    @api.model
    def create_from_ui(self, partner):
        if partner.get("debt_limit") is False:
            del partner["debt_limit"]
        return super(ResPartner, self).create_from_ui(partner)

    #before _compute_partner_journal_debt
    def _compute_partner_payment_method_debt(self, payment_method_id):
        domain = [("partner_id", "in", self.ids), ("payment_method_id", "=", payment_method_id)]
        fields = ["partner_id", "balance", "payment_method_id"]
        res = self.env["report.pos.debt"].read_group(domain, fields, "partner_id")

        res_index = {id: {"balance": 0} for id in self.ids}

        for data in res:
            res_index[data["partner_id"][0]] = data
        return res_index


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    debt_type = fields.Selection(
        [("debt", "Display Debt"), ("credit", "Display Credit")],
        default="debt",
        string="Debt Type",
        help="Way to display debt value (label and sign of the amount). "
        "In both cases debt will be red, credit - green",
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        config_parameters = self.env["ir.config_parameter"].sudo()
        for record in self:
            config_parameters.sudo().set_param(
                "pos_debt_notebook.debt_type", record.debt_type
            )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_parameters = self.env["ir.config_parameter"].sudo()
        res.update(
            debt_type=config_parameters.sudo().get_param(
                "pos_debt_notebook.debt_type", default="debt"
            )
        )
        return res


class PosConfig(models.Model):
    _inherit = "pos.config"

    debt_dummy_product_id = fields.Many2one(
        "product.product",
        string="Dummy Product for Debt",
        domain=[("available_in_pos", "=", True)],
        help="Dummy product used when a customer pays his debt "
        "without ordering new products. This is a workaround to the fact "
        "that Odoo needs to have at least one product on the order to "
        "validate the transaction.",
    )
    debt_type = fields.Selection(
        compute="_compute_debt_type",
        selection=[("debt", "Display Debt"), ("credit", "Display Credit")],
    )

    def _compute_debt_type(self):
        debt_type = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("pos_debt_notebook.debt_type", default="debt")
        )
        for pos in self:
            pos.debt_type = debt_type

    def init_debt_payment_method(self):
        print("init_debt_payment_method")
        payment_method_obj = self.env["pos.payment.method"]
        user = self.env.user
        company = self.env.company
        #debt_payment_method_active = payment_method_obj.search(
        #    [("company_id", "=", user.company_id.id), ("debt", "=", True)]
        #)
        debt_payment_method_active = payment_method_obj.search(
            [("company_id", "=", company.id), ("debt", "=", True)]
        )
        if debt_payment_method_active:
            #  Check if the debt journal is created already for the company.
            return

        account_obj = self.env["account.account"].sudo()
        #debt_account_old_version = account_obj.search(
        #    [("code", "=", "XDEBT"), ("company_id", "=", user.company_id.id)]
        #)
        debt_account_old_version = account_obj.search(
            [("code", "=", "XDEBT"), ("company_id", "=", company.id)]
        )
        if debt_account_old_version:
            debt_account = debt_account_old_version[0]
        else:
            debt_account = account_obj.create(
                {
                    "name": "Debt",
                    "code": "XDEBT",
                    "user_type_id": self.env.ref(
                        "account.data_account_type_receivable"
                    ).id,
                    "company_id": company.id,
                    "reconcile": True,
                }
            )
            self.env["ir.model.data"].create(
                {
                    "name": "debt_account_for_company" + str(company.id),
                    "model": "account.account",
                    "module": "pos_debt_notebook",
                    "res_id": debt_account.id,
                    "noupdate": True,  # If it's False, target record (res_id) will be removed while module update
                }
            )

        default_debt_limit = 0
        demo_is_on = (
            self.env["ir.module.module"].sudo()
            .search([("name", "=", "pos_debt_notebook")])
            .demo
        )
        """if demo_is_on:
            self.create_demo_debt_journals(user, debt_account)
            default_debt_limit = 1000"""

        debt_payment_method_inactive = payment_method_obj.search(
            [
                ("code", "=", "TCRED"),
                ("company_id", "=", company.id),
                ("debt", "=", False),
            ]
        )
        #print("print_debt_payment_method_inactive13", debt_payment_method_inactive)
        if debt_payment_method_inactive:
            debt_payment_method_inactive.sudo().write(
                {
                    "debt": True,
                    "receivable_account_id":debt_account.id,
                    "credits_via_discount": False,
                    "category_ids": False,
                    "debt_limit": default_debt_limit,
                    "pos_cash_out": False,
                }
                #"default_debit_account_id": debt_account.id,
                #"default_credit_account_id": debt_account.id,
                #"debt_dummy_product_id": self.env.ref(
                #        "pos_debt_notebook.product_pay_debt"
                #    ).id,
                #"write_statement": False,
            )
            debt_payment_method = debt_payment_method_inactive
        else:
            debt_payment_method = self.create_payment_method(
                {
                    "sequence_name": "Account Default Credit Journal ",
                    "prefix": "CRED ",
                    "user": user,
                    "noupdate": True,
                    "payment_method_name": "Credits",
                    "code": "TCRED",
                    "type": "cash",
                    "debt": True,
                    "debt_account": debt_account,
                    "credits_via_discount": False,
                    "category_ids": False,
                    "write_statement": False,
                    "debt_dummy_product_id": self.env.ref(
                        "pos_debt_notebook.product_pay_debt"
                    ).id,
                    "debt_limit": default_debt_limit,
                    "pos_cash_out": False,
                    "credits_autopay": True,

                }
                #"journal_user": True,
            )
        self.sudo().write(
            {
                "payment_method_ids": [(4, debt_payment_method.id)],
                "debt_dummy_product_id": self.env.ref(
                    "pos_debt_notebook.product_pay_debt"
                ).id,
            }

        )
        current_session = self.current_session_id
        """statement = [
            (
                0,
                0,
                {
                    "name": current_session.name,
                    "journal_id": debt_journal.id,
                    "user_id": user.id,
                    "company_id": user.company_id.id,
                },
            )
        ]
        current_session.write({"statement_ids": statement})"""
        if demo_is_on:
            self.env.ref("pos_debt_notebook.product_credit_product").write(
                {"credit_product": debt_payment_method.id}
            )

        return

    def create_payment_method(self, vals):
        print("create_payment_method13",vals)
        if self.env["pos.payment.method"].search([("code", "=", vals["code"])]):
            return
        _logger.info("Creating '" + vals["payment_method_name"] + "' payment_method")
        user = vals["user"]
        ##
        company = self.env.company
        debt_account = vals["debt_account"]
        """new_sequence = self.env["ir.sequence"].create(
            {
                "name": vals["sequence_name"] + str(user.company_id.id),
                "padding": 3,
                "prefix": vals["prefix"] + str(user.company_id.id),
            }
        )
        self.env["ir.model.data"].create(
            {
                "name": "payment_method_sequence" + str(new_sequence.id),
                "model": "ir.sequence",
                "module": "pos_debt_notebook",
                "res_id": new_sequence.id,
                "noupdate": vals[
                    "noupdate"
                ],  # If it's False, target record (res_id) will be removed while module update
            }
        )"""
        debt_payment_method = self.env["pos.payment.method"].sudo().create(
            {
                "name": "Credits",
                "code": vals["code"],
                "debt": vals["debt"],
                "company_id": company.id,
                "receivable_account_id": debt_account.id,
                "debt_limit": vals["debt_limit"],
                "category_ids": vals["category_ids"],
                "pos_cash_out": vals["pos_cash_out"],
                "credits_via_discount": vals["credits_via_discount"],
                "credits_autopay": vals["credits_autopay"],
            }
            #"journal_user": vals["journal_user"],
            #"code": vals["code"],
            #"type": vals["type"],
            #"sequence_id": new_sequence.id,
            # "default_debit_account_id": debt_account.id,
            # "default_credit_account_id": debt_account.id,

        )
        self.env["ir.model.data"].create(
            {
                "name": "debt_payment_method" + str(debt_payment_method.id),
                "model": "pos.payment.method",
                "module": "pos_debt_notebook",
                "res_id": int(debt_payment_method.id),
                "noupdate": True,  # If it's False, target record (res_id) will be removed while module update
            }
        )
        if vals["write_statement"]:
            self.sudo().write(
                {
                    "payment_method_ids": [(4, debt_payment_method.id)],
                    "debt_dummy_product_id": vals["debt_dummy_product_id"],
                }

            )
            current_session = self.current_session_id
            """statement = [
                (
                    0,
                    0,
                    {
                        "name": current_session.name,
                        "journal_id": debt_journal.id,
                        "user_id": user.id,
                        "company_id": user.company_id.id,
                    },
                )
            ]
            current_session.write({"statement_ids": statement})"""
        #print("debt_payment_method",debt_payment_method)
        return debt_payment_method

    def open_session_cb(self):
        print("open_session_cb")
        self.init_debt_payment_method()
        res = super(PosConfig, self).open_session_cb()

        return res

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    debt = fields.Boolean(string="Credit Payment Method")
    pos_cash_out = fields.Boolean(
        string="Allow to cash out credits",
        default=False,
        help="Partner can exchange credits to cash in POS",
    )
    category_ids = fields.Many2many(
        "pos.category",
        string="POS product categories",
        help="POS product categories that can be paid with this credits."
        "If the field is empty then all categories may be purchased with this payment method",
    )
    debt_limit = fields.Float(
        string="Max Debt",
        digits="Account",
        default=0,
        help="Partners is not allowed to have a debt more than this value",
    )
    credits_via_discount = fields.Boolean(
        default=False,
        string="Zero transactions on credit payments",
        help="Discount the order (mostly 100%) when user pay via this type of credits",
    )
    credits_autopay = fields.Boolean(
        "Autopay",
        default=False,
        help="On payment screen it will be automatically used if balance is positive. "
        "In case of several autopay payment method they will be applied in Payment Method order until full amount is paid",
    )
    code = fields.Char(string='Short Code', size=5)

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the payment method must be unique per company !')
    ]

    @api.onchange("credits_via_discount")
    def _onchange_partner(self):
        if self.credits_via_discount is True:
            self.pos_cash_out = False


class Product(models.Model):

    _inherit = "product.template"

    credit_product = fields.Many2one(
        "pos.payment.method",
        string="Payment Credit Product",
        domain="[('debt', '=', True)]",
        help="This product is used to buy Credits (pay for debts).",
    )


class PosOrder(models.Model):
    _inherit = "pos.order"

    product_list = fields.Text(
        "Product list", compute="_compute_product_list", store=True, compute_sudo=True
    )
    pos_credit_update_ids = fields.One2many(
        "pos.credit.update", "order_id", string="Non-Accounting Payments"
    )
    amount_via_discount = fields.Float(
        "Amount via Discounts", help="Service field for proper order proceeding"
    )

    @api.depends(
        "lines",
        "lines.product_id",
        "lines.product_id.name",
        "lines.qty",
        "lines.price_unit",
    )
    def _compute_product_list(self):
        for order in self:
            product_list = list()
            for o_line in order.lines:
                product_list.append(
                    "%s(%s * %s)"
                    % (o_line.product_id.name, o_line.qty, o_line.price_unit)
                )
            order.product_list = " + ".join(product_list)

    @api.model
    def _process_order(self, pos_order, draft, existing_order):
        print("_process_order")
        # Don't change original dict, because in case of SERIALIZATION_FAILURE
        # the method will be called again
        pos_order = copy.deepcopy(pos_order)
        credit_updates = []
        amount_via_discount = 0
        print("pos_order",pos_order)
        for payment in pos_order["data"]["statement_ids"]:
            print("payment",payment)
            method = self.env["pos.payment.method"].browse(payment[2]["payment_method_id"])
            if method.credits_via_discount:
                amount = float(payment[2]["amount"])
                product_list = list()
                amount_via_discount += amount
                print("pos_order",pos_order)
                for o_line in pos_order["data"]["lines"]:
                    o_line = o_line[2]
                    name = self.env["product.product"].browse(o_line["product_id"]).name
                    product_list.append(
                        "{}({} * {})".format(name, o_line["qty"], o_line["price_unit"])
                    )
                product_list = " + ".join(product_list)
                credit_updates.append(
                    {
                        "payment_method_id": payment[2]["payment_method_id"],
                        "balance": -amount,
                        "partner_id": pos_order["data"]["partner_id"],
                        "update_type": "balance_update",
                        "note": product_list,
                    }
                )
                payment[2]["amount"] = 0
        pos_order["amount_via_discount"] = amount_via_discount
        order = super(PosOrder, self)._process_order(pos_order, draft, existing_order)
        for update in credit_updates:
            update["order_id"] = order
            entry = self.env["pos.credit.update"].sudo().create(update)
            entry.switch_to_confirm()
        print("order",order)
        self.env['pos.order'].browse(order).set_discounts()
        return order

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res["amount_via_discount"] = ui_order.get("amount_via_discount", 0)
        return res

    def set_discounts(self):
        amount = self.amount_via_discount
        for line in self.lines:
            if float_is_zero(
                amount, self.env["decimal.precision"].precision_get("Account")
            ):
                break
            price = line.price_subtotal_incl
            if not price:
                continue
            disc = line.discount
            line.write(
                {
                    "discount": disc == 100
                    and disc
                    or max(
                        min(
                            line.discount
                            + (
                                amount
                                / (disc and (price / (100 - disc)) * 100 or price)
                            )
                            * 100,
                            100,
                        ),
                        0,
                    )
                }
            )
            # since 12.0v methods used api.depends in 11.0 use api.onchange, so we need to update some fields manually
            line._onchange_amount_line_all()
            amount -= price - line.price_subtotal_incl
        # since 12.0v methods used api.depends in 11.0 use api.onchange, so we need to update some fields manually
        self._onchange_amount_all()
        return amount

    def test_paid(self):
        for order in self:
            if not order.statement_ids and order.amount_via_discount:
                return True
            return super(PosOrder, self).test_paid()


"""class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    pos_credit_update_ids = fields.One2many(
        "pos.credit.update",
        "account_bank_statement_id",
        string="Non-Accounting Transactions",
    )
    pos_credit_update_balance = fields.Monetary(
        compute="_compute_credit_balance",
        string="Non-Accounting Transactions (Balance)",
        store=True,
    )

    @api.depends("pos_credit_update_ids", "pos_credit_update_ids.balance")
    def _compute_credit_balance(self):
        for st in self:
            st.pos_credit_update_balance = -sum(
                [credit_update.balance for credit_update in st.pos_credit_update_ids]
            )"""
class PoSPayment(models.Model):
    _inherit = "pos.payment"

    pos_credit_update_ids = fields.One2many(
        "pos.credit.update",
        "pos_payment_id",
        string="Non-Accounting Transactions",
    )
    pos_credit_update_balance = fields.Monetary(
        compute="_compute_credit_balance",
        string="Non-Accounting Transactions (Balance)",
        store=True,
    )

    @api.depends("pos_credit_update_ids", "pos_credit_update_ids.balance")
    def _compute_credit_balance(self):
        for st in self:
            st.pos_credit_update_balance = -sum(
                [credit_update.balance for credit_update in st.pos_credit_update_ids]
            )

class PosCreditUpdate(models.Model):
    _name = "pos.credit.update"
    _description = "Manual Credit Updates"
    _inherit = ["mail.thread"]
    _order = "id desc"

    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, tracking=True
    )
    user_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda s: s.env.user, readonly=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda s: s.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda s: s.env.company.currency_id,
    )
    balance = fields.Monetary(
        "Balance Update",
        tracking=True,
        help="Change of balance. Negative value for purchases without money (debt). Positive for credit payments (prepament or payments for debts).",
    )
    new_balance = fields.Monetary(
        "New Balance", help="Value to set balance to. Used only in Draft state."
    )
    note = fields.Text("Note")
    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True)

    state = fields.Selection(
        [("draft", "Draft"), ("confirm", "Confirmed"), ("cancel", "Canceled")],
        default="draft",
        required=True,
        tracking=True,
    )
    update_type = fields.Selection(
        [("balance_update", "Balance Update"), ("new_balance", "New Balance")],
        default="balance_update",
        required=True,
    )
    payment_method_id = fields.Many2one(
        "pos.payment.method",
        string="Payment Method",
        required=True,
        domain="[('debt', '=', True)]",
    )
    order_id = fields.Many2one("pos.order", string="POS Order")
    config_id = fields.Many2one(related="order_id.config_id", string="POS", store=True)
    pos_payment_id = fields.Many2one(
        "pos.payment",
        compute="_compute_bank_statement",
        string="Account Bank Statement",
        store=True,
    )
    reversed_balance = fields.Monetary(
        compute="_compute_reversed_balance",
        string="Payments",
        help="Change of balance. Positive value for purchases without money (debt). Negative for credit payments (prepament or payments for debts).",
    )

    @api.depends("order_id", "payment_method_id")
    def _compute_bank_statement(self):
        for record in self:
            if record.order_id:
                order = record.env["pos.order"].browse(record.order_id.id)
                record.payment_ids = (
                    record.env["pos.payment"]
                    .search(
                        [
                            ("payment_method_id", "=", record.payment_method_id.id),
                            ("session_id", "=", order.session_id.id),
                        ]
                    )
                    .id
                )

    @api.depends("balance")
    def _compute_reversed_balance(self):
        for record in self:
            record.reversed_balance = -record.balance

    def get_balance(self, balance, new_balance):
        return -balance + new_balance

    def update_balance(self, vals):
        partner = (
            vals.get("partner_id")
            and self.env["res.partner"].browse(vals.get("partner_id"))
            or self.partner_id
        )
        new_balance = vals.get("new_balance", self.new_balance)
        state = vals.get("state", self.state) or "draft"
        update_type = vals.get("update_type", self.update_type)
        if state == "draft" and update_type == "new_balance":
            data = partner._compute_partner_payment_method_debt(self.payment_method_id.id)
            credit_balance = data[partner.id].get("balance", 0)
            vals["balance"] = self.get_balance(credit_balance, new_balance)

    @api.model
    def create(self, vals):
        self.update_balance(vals)
        return super(PosCreditUpdate, self).create(vals)

    def write(self, vals):
        self.update_balance(vals)
        return super(PosCreditUpdate, self).write(vals)

    def switch_to_confirm(self):
        self.write({"state": "confirm"})

    def switch_to_cancel(self):
        self.write({"state": "cancel"})

    def switch_to_draft(self):
        self.write({"state": "draft"})

    def do_confirm(self):
        active_ids = self._context.get("active_ids")
        for r in self.env["pos.credit.update"].browse(active_ids):
            r.switch_to_confirm()


class AccountPayment(models.Model):
    _inherit = "account.payment"

    has_invoices = fields.Boolean(store=True)
    #company_id = fields.Many2one(store=True)


