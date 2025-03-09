# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from datetime import date

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_total_usd = fields.Monetary(string='Total in usd', store=True, readonly=True, compute='_amount_t_usd', tracking=4)
    currency_usd = fields.Many2one('res.currency', 'Currency', compute='_amount_t_usd')


    @api.depends('amount_total')
    def _amount_t_usd(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            convert_currency = self.env['res.currency'].search([('name', '=', 'USD')])
            amount_total_usd = order.currency_id.with_context(date=date.today()).compute(order.amount_total,
                                                                                       convert_currency)
            print("amount_total_usd",order.amount_total,amount_total_usd)
            order.amount_total_usd = amount_total_usd
            order.currency_usd = convert_currency

            '''
            order.update({
                'amount_total_usd': amount_total_usd,
                'currency_usd':convert_currency,
            })
            '''


