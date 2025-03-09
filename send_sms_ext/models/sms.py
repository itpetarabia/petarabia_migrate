# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools import config

import requests
import logging


_logger = logging.getLogger(__name__)

class SmsMessage(models.AbstractModel):
    _name = "sms.messages.petarabia"
    _description = 'SMS Messages Gateway Extension'

    @api.model
    def _format_ph_numbers(self, receivers):
        output = []
        for r in receivers:
            r = r.replace('+', '').replace('-', '').replace(' ', '')
            if len(r)==8: r = '973' + r
            output.append(r)
        return output

    def send_sms(self, *, messages:list, receivers:list):
        # url = self.env['ir.config_parameter'].sudo().get_param('send_sms_ext.sms_gateway')
        # api_token = self.env['ir.config_parameter'].sudo().get_param('send_sms_ext.sms_api_token')
        
        if config.get('running_env') == 'test':
            _logger.warning('Running `Send SMS` in Test mode is not allowed')
            return
        
        url = config.get('etisalcom_url')
        user = config.get('etisalcom_user')
        passwd = config.get('etisalcom_pwd')
        sender_id = "Pet Arabia"

        if not url or not user or not passwd:
            _logger.error('Gateway URL, User & Password not defined')
            return 

        if not isinstance(messages, list):
            messages = [messages]
        if not isinstance(receivers, list):
            receivers = [receivers]

        receivers = self._format_ph_numbers(receivers)
        _logger.debug((messages, receivers))

        if not receivers or not messages:
            _logger.warning('No messages or receivers mentioned')
            return

        for msg, number in zip(messages, receivers):
            try:
                params={
                    "user": user,
                    "pass": passwd,
                    "from": sender_id,
                    "to": number,
                    "text": msg,
                    }

                response = requests.request("GET", url, headers={}, params=params)
                _logger.info('Etisalcom SMS :' + response.text)
            except Exception as e:
                _logger.error(e)
        
        return

