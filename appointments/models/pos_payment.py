# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_is_zero


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    ##modify
    """#@api.multi
    def check(self):
        super(PosMakePayment, self).check()
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        if order.appointment_id:
            appoint = self.env['pos.appointments'].browse(order.appointment_id.id)
            if order.state == 'paid':
                appoint._action_paid()"""
    