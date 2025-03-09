# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz
import re

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    """@api.model
    def _process_order(self, pos_order, draft, existing_order):
        #pos_order = copy.deepcopy(pos_order)
        print("_process_order====", pos_order)
        partner = pos_order["data"]["partner_id"]
        if partner:
            partner_id = self.env['res.partner'].browse(partner)
            phone_no = partner_id.phone or self.partner_id.mobile
            if phone_no:
                partner_name = partner_id.name
                order_loyalty_points = pos_order["data"]["loyalty_points"]
                partner_loyalty_points = partner_id.loyalty_points
                response = self.send_sms_link_pos_done(phone_no, partner_name, order_loyalty_points, partner_loyalty_points)

        #pos_order["partner_name"] = partner_name
        #pos_order["order_loyalty_points"] = order_loyalty_points
        #pos_order["partner_loyalty_points"] = partner_loyalty_points
        order = super(PosOrder, self)._process_order(pos_order, draft, existing_order)
        return order"""

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        for order in self.sudo().browse([o['id'] for o in order_ids]):
            if order.partner_id:
                #print("loyalty point2222==", order.loyalty_points)
                phone_no = order.partner_id.phone or order.partner_id.mobile
                #print("phone_no====",phone_no,order)
                if phone_no and order.loyalty_points:
                    partner_name = order.partner_id.name
                    order_loyalty_points = order.loyalty_points
                    partner_loyalty_points = order.partner_id.loyalty_points
                    #print("partner_name==",partner_name,order_loyalty_points,partner_loyalty_points)
                    response = self.send_sms_link_pos_done(phone_no, partner_name, order_loyalty_points, partner_loyalty_points)
                    #print("close========")
        return order_ids



    ##SMS POS
    def send_sms_link_pos_done(self, phone_num, partner_name, points, total_points):
        #print("send_sms_link_pos_done====",phone_num,partner_name,points,total_points)
        sms_templ_recs = self.env['sms.messages.gateway'].sudo().search(
            [('sms_type', '=', 'point_of_sale'), ('state', '=', 'confirm')])
        if sms_templ_recs:
            gateway_content = sms_templ_recs[-1]
            message = gateway_content.message
            if message:
                message = message.replace('{CUSTOMER}', partner_name) \
                    .replace('{POINT}', str(points)) \
                    .replace('{TOTAL_POINTS}', str(total_points))
                #print("message====", message)
                if phone_num:
                    return self.env['sms.messages.petarabia'].send_sms(
                        messages=message,
                        receivers=phone_num,
                    )


