# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_out_stock_alert = fields.Boolean("Out of stock alert", related='company_id.pos_out_stock_alert', readonly=False)
    pos_out_stock_notif = fields.Boolean("Out of stock notification by email", related='company_id.pos_out_stock_notif', readonly=False)
    pos_out_stock_notif_user_ids = fields.Many2many('res.users', string="Out of stock notify",related='company_id.pos_out_stock_notif_user_ids', readonly=False)
