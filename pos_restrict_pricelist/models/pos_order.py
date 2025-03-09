# -*- coding: utf-8 -*-
from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _check_group_change_pos_pricelist(self):
        if not self.env.user.has_group('pos_restrict_pricelist.group_change_pos_pricelist'):
            self.is_change_pricelist = False
        else:
            self.is_change_pricelist = True



    is_change_pricelist = fields.Boolean(string='Is Change Pricelist', compute='_check_group_change_pos_pricelist')


    