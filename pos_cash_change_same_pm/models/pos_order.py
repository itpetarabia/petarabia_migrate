# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def add_payment(self, data):
        """Create a new payment for the order"""
        self.ensure_one()
        if data.get('is_change',False) and data.get('amount',0) < 0:
            cash_trans = self.payment_ids.filtered(lambda l: l.payment_method_id.is_cash_count)
            if cash_trans:
                data['payment_method_id'] = cash_trans[-1].payment_method_id.id
        super(PosOrder,self).add_payment(data)
