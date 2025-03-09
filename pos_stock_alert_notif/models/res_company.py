from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    pos_out_stock_alert = fields.Boolean("POS Out of stock alert")
    pos_out_stock_notif = fields.Boolean("POS Out of stock notification by email")
    pos_out_stock_notif_user_ids = fields.Many2many('res.users','res_comp_pos_out_stk_notif_usr_rel', 'company_id', 'user_id', string="POS Out of stock notify")
