from odoo import models, fields, api

class StockLocation(models.Model):
    _inherit = 'stock.location'

    mt_warehouse_id = fields.Many2one('stock.warehouse',compute="_compute_mt_warehouse_id",store=True,help="Technical field added by mast-it for aging report purpose")

    @api.depends('parent_path')
    def _compute_mt_warehouse_id(self):
        obj_warehouse = self.env['stock.warehouse']
        for rec in self:
            warehouse_id = False
            if rec.parent_path:
                qry = f"select parent_path from stock_location where id = {rec.id}"
                self.env.cr.execute(qry)
                qry_res = self.env.cr.dictfetchall() or [{'parent_path': ''}]
                parent_loc_ids = [int(loc_id) for loc_id in qry_res[0]['parent_path'].split("/") if loc_id]
                warehouse_id = obj_warehouse.search([('view_location_id','in',parent_loc_ids)], limit=1).id
            rec.mt_warehouse_id = warehouse_id
