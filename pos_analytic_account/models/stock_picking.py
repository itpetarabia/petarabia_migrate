# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        res = super(StockPicking,self)._prepare_stock_move_vals(first_line, order_lines)
        if not self.pos_session_id:
            self.pos_session_id = first_line.order_id.session_id.id
        return res