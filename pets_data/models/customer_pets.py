from odoo import api, fields, models


class CustomerPet(models.Model):
    _inherit = 'res.partner'
    pet_ids = fields.One2many('res.pet', 'parent_id', string='Pets')
