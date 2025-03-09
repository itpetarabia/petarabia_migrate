# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import Counter

from odoo import _, api, fields, tools, models



class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    qty_demand = fields.Float(related='move_id.product_uom_qty', string='Demand', default=0.0, digits='Product Unit of Measure', copy=False)


    