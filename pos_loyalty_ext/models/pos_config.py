# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _default_payment_methods(self):
        return self.env['pos.payment.method'].search(
            [('split_transactions', '=', False), ('company_id', '=', self.env.company.id)])

    payment_method_loyal_ext = fields.Many2many('pos.payment.method', 'pos_payment_loyalty_execl', string='Payment Methods')
    pricelist_loyal_ext = fields.Many2many('product.pricelist', 'pos_pricelist_loyalty_execl', string='Pricelist')
