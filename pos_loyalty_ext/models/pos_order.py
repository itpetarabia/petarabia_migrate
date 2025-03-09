# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

class PosOrder(models.Model):
    _inherit = 'pos.order'

    spent_point = fields.Float(help='The amount of Loyalty points the customer spent with this order')
    won_point = fields.Float(help='The amount of Loyalty points the customer won with this order')

    @api.model
    def _order_fields(self, ui_order):
        fields = super(PosOrder, self)._order_fields(ui_order)
        fields['spent_point'] = ui_order.get('spent_point', 0)
        fields['won_point'] = ui_order.get('won_point', 0)
        return fields

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        for order in self.sudo().browse([o['id'] for o in order_ids]):
            if order.partner_id:
                excl_pm_ids = order.payment_ids.mapped('payment_method_id').filtered(lambda pm: pm.payment_method_loyal_ext).mapped('id')
                if not excl_pm_ids and not order.pricelist_id.pricelist_loyal_ext:
                    continue
                #in super odoo do += order.loyality_point ie, we put opposit
                order.partner_id.loyalty_points -= order.loyalty_points
                #if spent we have to deduct from customer
                order.partner_id.loyalty_points -= order.spent_point
                #is exclude by pay method/pricelist and has spent
                if order.spent_point:
                    order.loyalty_points = -order.spent_point
        return order_ids