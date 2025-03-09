# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_is_zero
from odoo.tools import float_round
from odoo.exceptions import UserError

class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def get_won_points(self,order,loyalty,partner):
        if not loyalty or not partner:
            return 0
        total_points = 0;
        for line in order.lines:
            #if line.get_reward():  # Reward products are ignored
            #    continue
            line_points = 0
            for rule in loyalty.rule_ids:
                rule_points = 0
                if rule.valid_product_ids.filtered(lambda product_id: product_id.id == line.product_id.id):
                    rule_points += rule.points_quantity * line.qty;
                rule_points += rule.points_currency * line.price_subtotal_incl;
                if rule_points > line_points:
                    line_points = rule_points
            total_points += line_points
        total_points += order.amount_total * loyalty.points
        return float_round(total_points, precision_rounding=1)

    def get_new_points(self, order):
        if order.partner_id and order.config_id and order.config_id.module_pos_loyalty and order.config_id.loyalty_id:
            loyalty = order.config_id.loyalty_id
            partner = order.partner_id
            return float_round(self.get_won_points(order,loyalty,partner), precision_rounding=1)
        else:
            return 0

    #@api.multi
    def check(self):
        super(PosMakePayment, self).check()
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        if order.appointment_id:
            #appoint = self.env['pos.appointments'].browse(order.appointment_id.id)
            if order.state == 'paid' and order.partner_id:
                #appoint._action_paid()
                init_data = self.read()[0]
                pymt_method = self.env['pos.payment.method'].sudo().browse(init_data['payment_method_id'][0])
                if self.env['ir.module.module'].sudo().search([('name', '=', 'pos_loyalty_ext'), ('state', '=', 'installed')]):
                    if not pymt_method.payment_method_loyal_ext and not order.pricelist_id.pricelist_loyal_ext:
                        if self.get_new_points(order):
                            order.loyalty_points = float_round(self.get_new_points(order), precision_rounding=1)
                            order.partner_id.loyalty_points += float_round(self.get_new_points(order), precision_rounding=1)
                elif self.get_new_points(order):
                    order.loyalty_points = float_round(self.get_new_points(order), precision_rounding=1)
                    order.partner_id.loyalty_points += float_round(self.get_new_points(order), precision_rounding=1)

