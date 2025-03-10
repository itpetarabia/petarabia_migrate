# Copyright 2017-2018 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2017 Stanislav Krotov <https://it-projects.info/team/ufaks>
# Copyright 2018 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import fields, models, tools


class PosDebtReport(models.Model):

    _name = "report.pos.debt"
    _description = "POS Debt Statistics"
    _auto = False
    _order = "date desc"

    order_id = fields.Many2one("pos.order", string="POS Order", readonly=True)
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    payment_id = fields.Many2one("account.payment", string="Payment", readonly=True)
    update_id = fields.Many2one(
        "pos.credit.update", string="Manual Update", readonly=True
    )

    date = fields.Datetime(string="Date", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    user_id = fields.Many2one("res.users", string="Salesperson", readonly=True)
    session_id = fields.Many2one("pos.session", string="Session", readonly=True)
    config_id = fields.Many2one("pos.config", string="POS", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    payment_method_id = fields.Many2one("pos.payment.method", string="Payment Method", readonly=True)

    state = fields.Selection(
    #    [("open", "Open"), ("confirm", "Validated")], readonly=True
    #)
        [('draft', 'New'), ('cancel', 'Cancelled'), ('open', 'Paid'), ('confirm', 'Posted'), ('invoiced', 'Invoiced')], readonly=True
    )
    credit_product = fields.Boolean(
        string="Journal Credit Product",
        help="Record is registered as Purchasing credit product",
        readonly=True,
    )
    balance = fields.Monetary(
        "Balance",
        help="Negative value for purchases without money (debt). Positive for credit payments (prepament or payments for debts).",
        readonly=True,
    )
    product_list = fields.Text("Product List", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, "report_pos_debt")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW report_pos_debt AS (
                (
                --
                -- Using Debt journal in POS
                --
                SELECT
                    paym.id as id,
                    o.id as order_id,
                    NULL::integer as invoice_id,
                    NULL::integer as payment_id,
                    NULL::integer as update_id,
                    -paym.amount as balance,
                    CASE o.state
                        WHEN 'done' THEN 'confirm'
                        WHEN 'paid' THEN 'open'
                        ELSE o.state
                    END as state,
                    false as credit_product,

                    o.date_order as date,
                    o.partner_id as partner_id,
                    o.user_id as user_id,
                    o.session_id as session_id,
                    session.config_id as config_id,
                    o.company_id as company_id,
                    pricelist.currency_id as currency_id,
                    o.product_list as product_list,

                    paym.payment_method_id as payment_method_id

                FROM pos_payment as paym
                    LEFT JOIN pos_payment_method payment ON (payment.id=paym.payment_method_id)
                    LEFT JOIN pos_order o ON (o.id=paym.pos_order_id)
                    LEFT JOIN pos_session session ON (session.id=o.session_id)
                    LEFT JOIN product_pricelist pricelist ON (pricelist.id=o.pricelist_id)
                WHERE
                    payment.debt=true
                    
                )
                UNION ALL
                (
                --
                -- Sales of credit products in POS
                --
                SELECT
                    -pos_line.id as id,
                    o.id as order_id,
                    NULL::integer as invoice_id,
                    NULL::integer as payment_id,
                    NULL::integer as update_id,
                    -- FIXME: price_subtotal cannot be used, because it's not stored field
                    pos_line.price_unit * qty as balance,
                    CASE o.state
                        WHEN 'done' THEN 'confirm'
                        WHEN 'paid' THEN 'open'
                        ELSE o.state
                    END as state,
                    true as credit_product,

                    o.date_order as date,
                    o.partner_id as partner_id,
                    o.user_id as user_id,
                    o.session_id as session_id,
                    session.config_id as config_id,
                    o.company_id as company_id,
                    pricelist.currency_id as currency_id,
                    o.product_list as product_list,

                    pt.credit_product as payment_method_id

                FROM pos_order_line as pos_line
                    LEFT JOIN product_product pp ON (pp.id=pos_line.product_id)
                    LEFT JOIN product_template pt ON (pt.id=pp.product_tmpl_id)

                    LEFT JOIN pos_order o ON (o.id=pos_line.order_id)

                    LEFT JOIN pos_session session ON (session.id=o.session_id)
                    LEFT JOIN product_pricelist pricelist ON (pricelist.id=o.pricelist_id)
                    LEFT JOIN pos_payment_method payment ON (payment.id=pt.credit_product)
                WHERE
                    payment.debt=true
                    AND o.state IN ('paid','done')
                )
                UNION ALL
                (
                --
                -- Sales of credit products in via Invoices
                --
                SELECT
                    (2147483647 - inv_line.id) as id,
                    NULL::integer as order_id,
                    inv.id as invoice_id,
                    NULL::integer as payment_id,
                    NULL::integer as update_id,
                    inv_line.price_subtotal as balance,
                    'confirm' as state,
                    true as credit_product,

                    inv.invoice_date as date,
                    inv.partner_id as partner_id,
                    inv.invoice_user_id as user_id,
                    NULL::integer as session_id,
                    NULL::integer as config_id,
                    inv.company_id as company_id,
                    inv.currency_id as currency_id,
                    '' as product_list,

                    pt.credit_product as payment_method_id

                FROM account_move_line as inv_line
                    LEFT JOIN product_product pp ON (pp.id=inv_line.product_id)
                    LEFT JOIN product_template pt ON (pt.id=pp.product_tmpl_id)
                    LEFT JOIN account_move inv ON (inv.id=inv_line.move_id)
                    LEFT JOIN pos_payment_method payment ON (payment.id=pt.credit_product)
                WHERE
                    payment.debt=true
                    AND inv.state in ('paid')
                )
                UNION ALL
                (
                --
                -- Manual Credit Updates
                --
                SELECT
                    (-2147483647 + record.id) as id,
                    record.order_id as order_id,
                    NULL::integer as invoice_id,
                    NULL::integer as payment_id,
                    record.id as update_id,
                    record.balance as balance,
                    record.state as state,
                    false as credit_product,

                    record.date as date,
                    record.partner_id as partner_id,
                    record.user_id as user_id,
                    NULL::integer as session_id,
                    record.config_id as config_id,
                    record.company_id as company_id,
                    record.currency_id as currency_id,
                    record.note as product_list,
                    record.payment_method_id as payment_method_id

                FROM pos_credit_update as record
                WHERE
                    record.state in ('confirm')
                )
                UNION ALL
                (
                --
                -- Invoices paid by credit journal
                --
                SELECT
                    (-1073741823 - pay.id) as id,
                    NULL::integer as order_id,
                    NULL::integer as invoice_id,
                    pay.id as payment_id,
                    NULL::integer as update_id,
                    -pay.amount as balance,
                    'confirm' as state,
                    false as credit_product,

                    inv2.date as date,
                    pay.partner_id as partner_id,
                    NULL::integer as user_id,
                    NULL::integer as session_id,
                    NULL::integer as config_id,
                    inv2.company_id as company_id,
                    pay.currency_id as currency_id,
                    '' as product_list,

                    pay.payment_method_id as payment_method_id

                FROM account_payment as pay
                    LEFT JOIN pos_payment_method payment ON (payment.id=pay.payment_method_id)
                    LEFT JOIN account_move inv2 ON (inv2.id=pay.move_id)
                WHERE
                    payment.debt=true
                    AND inv2.state != 'cancelled'
                    AND pay.has_invoices = true
                )
            )
        """
        )
