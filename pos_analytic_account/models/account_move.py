# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        posted = super()._post(soft)
        obj_pos_order = self.env['pos.order'].sudo()
        for rec in self.sudo():
            pos_order = obj_pos_order.search([('account_move','=',rec.id)])
            if pos_order and pos_order.session_id.config_id.analytic_account_id:
                rec.line_ids.write({'analytic_account_id': pos_order.session_id.config_id.analytic_account_id.id})
        return posted

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        obj_pos_session = self.env['pos.session'].sudo()
        for vals in vals_list:
            move = self.env['account.move'].browse(vals['move_id'])
            pos_session = False
            if not move.stock_move_id:
                pos_session = obj_pos_session.search([('move_id','=',vals['move_id'])],limit=1,order='id asc')
            elif move.stock_move_id.picking_id.pos_session_id:
                pos_session = move.stock_move_id.picking_id.pos_session_id
            if pos_session and pos_session.config_id.analytic_account_id:
                vals['analytic_account_id'] = pos_session.config_id.analytic_account_id.id
        return super(AccountMoveLine, self).create(vals_list)


