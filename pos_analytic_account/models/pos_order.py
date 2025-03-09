# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    analytic_account_id = fields.Many2one('account.analytic.account')

    @api.model
    def _order_fields(self, ui_order):
        data = super(PosOrder,self)._order_fields(ui_order)
        data['analytic_account_id'] = self.env['pos.session'].browse(data['session_id']).config_id.analytic_account_id.id
        return data

    def _create_invoice(self, move_vals):
        new_move = super(PosOrder, self)._create_invoice(move_vals)
        self.write({'account_move': new_move.id, 'state': 'invoiced'})
        new_move.sudo().with_company(self.company_id)._post()
        if self.session_id.config_id.analytic_account_id:
            new_move.line_ids.write({'analytic_account_id':self.session_id.config_id.analytic_account_id.id})
        return new_move