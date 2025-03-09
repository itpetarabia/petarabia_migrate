# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import ast

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    #commission_tax_id = fields.Many2many('account.tax','res_conf_commission_tax_rel','res_conf_id','tax_id', string='Commission Taxes')
    alarm_ids = fields.Many2many('calendar.alarm', string='Reminders')
        
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('appointments.alarm_ids', self.alarm_ids.ids)
        
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        alarm_list = []
        obj_alarm = self.env['calendar.alarm'].sudo()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        alarm_id = []
        if get_param('appointments.alarm_ids'):
            alarm_id = ast.literal_eval(get_param('appointments.alarm_ids'))
            
        for i in alarm_id:
            if obj_alarm.browse(i).exists():
                alarm_list.append(i)
        res['alarm_ids'] = [(6,0,alarm_list)]
        return res