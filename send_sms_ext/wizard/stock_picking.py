# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#from collections import namedtuple
#import json
#import time
#from datetime import date
#from itertools import groupby
#from odoo import api, fields, models, _, SUPERUSER_ID
#from odoo.osv import expression
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
#from odoo.tools.float_utils import float_compare, float_is_zero, float_round
#from odoo.exceptions import UserError
#from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
#from operator import itemgetter

from odoo import _, api, fields, models, tools
from odoo.exceptions import except_orm, UserError, Warning, ValidationError
import requests
import urllib
import re
import logging
from odoo.http import content_disposition, Controller, request, route

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def send_sms_link(self,rendered_sms_to,partner_name,branch):
        #if request.env['gateway_setup'].sudo().search([('name', '=', 'send_delivery_note_sms')]):
        #    sms_rendered_content = request.env['gateway_setup'].sudo().search([('name', '=', 'send_delivery_note_sms')])[-1].message
        if self.env['sms.messages.gateway'].sudo().search([('sms_type', '=', 'delivery'),('state', '=', 'confirm')]):
            gateway_content = self.env['sms.messages.gateway'].sudo().search([('sms_type', '=', 'delivery'),('state', '=', 'confirm')])[-1]
            sms_rendered_content = gateway_content.message
            if sms_rendered_content:
                sms_rendered_content = sms_rendered_content.replace('{NAME}',partner_name).replace('{BRANCH}',branch)
                #print("sms_rendered_content",sms_rendered_content)
                sms_rendered_content = sms_rendered_content.encode('ascii', 'ignore')
                sms_rendered_content_msg = urllib.parse.quote_plus(sms_rendered_content)
                if rendered_sms_to:
                    rendered_sms_to = re.sub(r' ', '', rendered_sms_to)
                    if '+' in rendered_sms_to:
                        rendered_sms_to = rendered_sms_to.replace('+', '')
                    if '-' in rendered_sms_to:
                        rendered_sms_to = rendered_sms_to.replace('-', '')
        
                if rendered_sms_to:
                    usr=self.env['ir.config_parameter'].sudo().get_param('send_sms_ext.sms_username')
                    password=self.env['ir.config_parameter'].sudo().get_param('send_sms_ext.sms_password')
                    gateway=self.env['ir.config_parameter'].sudo().get_param('send_sms_ext.sms_gateway')
                    api_token = self.env['ir.config_parameter'].sudo().get_param('send_sms_ext.sms_api_token')
                    sid=gateway_content.name
                    if usr and password and gateway:
                        send_url='%s?username=%s&password=%s&to=%s&text=%s&from=%s' % (gateway,usr,password,rendered_sms_to,sms_rendered_content_msg,sid)
                        #send_url = request.env['gateway_setup'].sudo().search([('name', '=', 'send_delivery_note_sms')])[-1].gateway_url
                        #send_link = send_url.replace('{mobile}',rendered_sms_to).replace('{message}',sms_rendered_content_msg)
                        try:
                            #response = requests.request("GET", url = send_url)
                            headers = {'Authorization': f'App {api_token}'}
                            response = requests.request("GET", url=send_url, headers=headers)
                            #print("response000",response)
                            return response
                        except Exception as e:
                            return e
                    else:
                        raise ValidationError(_("Set username, password, gateway in Confiquration."))
        else:
            raise ValidationError(_("SMS Template not found, create SMS template first then confirm."))
    #@api.one
    def action_send_sms(self):
        self.ensure_one()
        if self.partner_id:
            if self.partner_id.mobile or self.partner_id.phone:
                mobile_no = self.partner_id.mobile
                if mobile_no:
                    mobile_no = mobile_no.replace('+973 ', '').replace('973 ', '').replace(' ', '').strip()
                    mobile_no='973%s' % (int(mobile_no))
                    #print("mobile_no11",mobile_no)
                elif self.partner_id.phone:
                    mobile_no = self.partner_id.phone
                    mobile_no = mobile_no.replace('+973 ', '').replace('973 ', '').replace(' ', '').strip()
                    mobile_no = '973%s' % (int(mobile_no))
                partner_name = self.partner_id.name
                branch = self.location_id.name
                response = self.send_sms_link(mobile_no,partner_name,branch)
                #print("response",response.text)
                #print("response.status_code",response.status_code)
                if 200 <= response.status_code <= 299:
                    raise Warning("SMS sent successfully")
                else:
                    raise Warning("SMS sending failed")
                
            else:
                raise ValidationError(_("Fill Partner Mobile."))
        else:
            raise ValidationError(_("Select Partner."))
            
        

