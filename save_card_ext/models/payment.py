# coding: utf-8

from collections import namedtuple
from datetime import datetime
from hashlib import sha256
import hmac
import json
import logging
import requests
import pprint
from requests.exceptions import HTTPError
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.http import request
from odoo.tools.float_utils import float_round
from odoo.tools import consteq
from odoo.exceptions import ValidationError

from odoo.addons.payment_stripe.controllers.main import StripeController
from datetime import date

_logger = logging.getLogger(__name__)


class PaymentTokenStripe(models.Model):
    _inherit = 'payment.token'

    savecard = fields.Boolean(string='Save Card')
    exp_mm = fields.Char("Exp Month")
    exp_yy = fields.Char("Exp Year")
    fingerp = fields.Char("fingerprint")

    def write(self, vals):
        result = super(PaymentTokenStripe, self).write(vals)
        token1 = self.env['payment.token'].search([('id', '!=', self.id)])
        for token in token1:
            if token.name == self.name and token.exp_mm == self.exp_mm and token.exp_yy == self.exp_yy and token.fingerp == self.fingerp:
                token.unlink()

        return result

class PaymentAcquirerStripe(models.Model):
    _inherit = 'payment.acquirer'

    @api.model
    def stripe_s2s_form_process(self, data):
        rec = super(PaymentAcquirerStripe, self).stripe_s2s_form_process(data)

        for val in rec:
            card = data.get('card', {}).get('last4')
            if not card:
                acquirer_id = self.env['payment.acquirer'].browse(int(data['acquirer_id']))
                pm = data.get('payment_method')
                data = acquirer_id._stripe_request('payment_methods/%s' % pm, data=False, method='GET')
                card = data.get('card', {}).get('last4', '****')
            if card:
                val.exp_mm = data.get('card', {}).get('exp_month')
                val.exp_yy = data.get('card', {}).get('exp_year')
                val.fingerp = data.get('card', {}).get('fingerprint')
            if 'save_card' in data or self.save_token == 'always':
                val.savecard = True
            else:
                val.savecard = False

        return rec


class PaymentTransactionStripe(models.Model):
    _inherit = 'payment.transaction'

    def write(self, vals):
        result = super(PaymentTransactionStripe, self).write(vals)
        for val in self:
            if val.payment_token_id:
                token1 = val.env['payment.token'].search([('id', '!=', val.payment_token_id.id)])
                for token in token1:
                    if val.payment_token_id:
                        if token.name == val.payment_token_id.name and token.exp_mm == val.payment_token_id.exp_mm and token.exp_yy == val.payment_token_id.exp_yy and token.fingerp == val.payment_token_id.fingerp and val.payment_token_id.savecard == True:
                            val.payment_token_id.unlink()
                if val.payment_token_id.savecard == False:
                    val.payment_token_id.unlink()
        return result
