# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class Warehouse(models.Model):
    _inherit = "stock.warehouse"
    
    reordering_warehouse = fields.Boolean(string='Transfer Request source')

    @api.model
    def create(self, vals):
        line = super(Warehouse, self).create(vals)
        w_house = self.env['stock.warehouse'].search(
            [('reordering_warehouse', '=', True), ('company_id', '=', self.company_id.id)])
        if w_house and len(w_house) > 1:
            raise UserError(_('Set the field \'Is Reordering\' to True only for one warehouse of the company!.'))
        return line

    #@api.multi
    def write(self, vals):
        result = super(Warehouse, self).write(vals)
        for record in self:
            w_house = self.env['stock.warehouse'].search([('reordering_warehouse', '=', True), ('company_id', '=', record.company_id.id)])
            if w_house and len(w_house)>1:
                raise UserError(_('Set the field \'Is Reordering\' to True only for one warehouse of the company!.'))
        return result
class StockMove(models.Model):
    _inherit = 'stock.move'

    reordering_line_id = fields.Many2one('reordering.request.line',
        'Reordering Line', ondelete='set null', index=True, readonly=True)
    created_reordering_line_id = fields.Many2one('reordering.request.line',
                                               'Created Reordering Line', ondelete='set null', readonly=True,
                                               copy=False)


    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields += ['reordering_line_id', 'created_reordering_line_id']
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted += [move.reordering_line_id.id, move.created_reordering_line_id.id]
        return keys_sorted
    def _clean_merged(self):
        super(StockMove, self)._clean_merged()
        self.write({'created_reordering_line_id': False})
    def _get_upstream_documents_and_responsibles(self, visited):
        if self.created_reordering_line_id and self.created_reordering_line_id.state not in ('done', 'cancel'):
            return [(self.created_reordering_line_id.request_id, self.created_reordering_line_id.request_id.user_id, visited)]
        else:
            return super(StockMove, self)._get_upstream_documents_and_responsibles(visited)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    reordering_req_id = fields.Many2one('reordering.request', related='move_lines.reordering_line_id.request_id',
        string="Transfer Request", readonly=True)
