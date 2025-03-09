# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models
#from odoo.exceptions import UserError

class Property(models.Model):
    _inherit = 'ir.property'

    loyalty_updated = fields.Boolean(default=False)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Float(company_dependent=False)

    def update_old_loyalty_points(self):
        #raise UserError("test")
        loyalty_field = self.env.ref('pos_loyalty.field_res_partner__loyalty_points')
        lm = 3000
        domain = [('fields_id','=',loyalty_field.id),
                ('res_id','!=',False),
                ('value_float','!=',0),
                  ('loyalty_updated','=',False)
                  ]
        ir_properties = self.env['ir.property'].search(domain,limit=lm)
        obj_partner = self.env['res.partner']
        for ip in ir_properties:
            res_id_split = ip.res_id.split(',')
            if len(res_id_split) == 2:
                customer = obj_partner.browse(int(res_id_split[1]))
                customer.loyalty_points += ip.value_float
        ir_properties.write({'loyalty_updated':True})