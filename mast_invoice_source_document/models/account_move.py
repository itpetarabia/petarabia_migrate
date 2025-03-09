# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _



class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_origin = fields.Char(string='Origin', readonly=True, states={'draft': [('readonly', False)]}, tracking=True,
                                 help="The document(s) that generated the invoice.")
    
    
    