# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    discount_fixed = fields.Float('Discount Fixed', default=0)


    @api.onchange('discount_fixed')
    def change_discount_fixed_line(self):
        if self.discount_fixed:
            self.discount = 0.0


    @api.onchange('discount')
    def change_discount_line(self):
        if self.discount:
            self.discount_fixed = 0.0

    def _compute_amount_line_all(self):
        self.ensure_one()
        fpos = self.order_id.fiscal_position_id
        tax_ids_after_fiscal_position = fpos.map_tax(self.tax_ids, self.product_id, self.order_id.partner_id)
        #price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        if self.discount_fixed != 0:
            price = self.price_unit - self.discount_fixed/self.qty
        else:
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = tax_ids_after_fiscal_position.compute_all(price, self.order_id.pricelist_id.currency_id, self.qty, product=self.product_id, partner=self.order_id.partner_id)
        return {
            'price_subtotal_incl': taxes['total_included'],
            'price_subtotal': taxes['total_excluded'],
        }

class PosOrder(models.Model):
    _inherit = "pos.order"

    # replace function
    def _prepare_invoice_line(self, order_line):
        disc = 0.0
        if order_line.discount:
            disc = order_line.discount
        if order_line.discount_fixed:
            disc = (order_line.discount_fixed*100)/order_line.price_unit
        return {
            'product_id': order_line.product_id.id,
            'quantity': order_line.qty if self.amount_total >= 0 else -order_line.qty,
            'discount': disc,
            'price_unit': order_line.price_unit,
            'name': order_line.product_id.display_name,
            'tax_ids': [(6, 0, order_line.tax_ids_after_fiscal_position.ids)],
            'product_uom_id': order_line.product_uom_id.id,
            #'discount_fixed': order_line.discount_fixed,
        }

    #replace function
    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id)
        taxes = fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
        #price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        if line.discount_fixed:
            price = line.price_unit - line.discount_fixed / line.qty
        else:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = taxes.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id,
                                  partner=line.order_id.partner_id or False)['taxes']
        return sum(tax.get('amount', 0.0) for tax in taxes)

