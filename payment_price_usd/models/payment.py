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

# The following currencies are integer only, see https://stripe.com/docs/currencies#zero-decimal
INT_CURRENCIES = [
    u'BIF', u'XAF', u'XPF', u'CLP', u'KMF', u'DJF', u'GNF', u'JPY', u'MGA', u'PYG', u'RWF', u'KRW',
    u'VUV', u'VND', u'XOF'
]
STRIPE_SIGNATURE_AGE_TOLERANCE = 600  # in seconds

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def set_to_authorized(self):
        self._set_transaction_authorized()



    def _stripe_form_get_invalid_parameters(self, data):
        original_amount = self.amount
        original_curr = self.currency_id
        print("self.amount==", self.amount,data.get('currency').upper())
        convert_currency = self.env['res.currency'].search([('name', '=', str(data.get('currency').upper()))])
        print("convert_currencyfff==", convert_currency)
        self.amount = self.currency_id.with_context(date=date.today()).compute(self.amount,
                                                                                       convert_currency)
        self.currency_id = convert_currency
        print("testtt", self.amount)
        res = super(PaymentTransaction, self)._stripe_form_get_invalid_parameters(data)
        self.amount = original_amount
        self.currency_id = original_curr
        return res


class PaymentAcquirerStripe(models.Model):
    _inherit = 'payment.acquirer'


    def _stripe_request(self, url, data=False, method='POST', idempotency_key=None):

        print("datastri==", data)


        if data and 'amount' in data and 'currency' in data:
            convert_currency0 = self.env['res.currency'].search([('name', '=', 'USD')])
            old_currency = self.env['res.currency'].search([('name', '=', data['currency'].upper())])
            print("convert_currency0==", convert_currency0,old_currency,convert_currency0.name,data['currency'].upper())
            old_amount = float_round(data['amount'] * 0.01, 2)
            new_amount = old_currency.with_context(date=date.today()).compute(old_amount,convert_currency0)
            print("new_amount==", old_amount,new_amount)
            data['amount'] = int(new_amount if convert_currency0.name in INT_CURRENCIES else float_round(new_amount * 100, 2)),
            data['currency'] = convert_currency0.name
            print("data['amount']00==", data['amount'],data['currency'])

        res = super(PaymentAcquirerStripe, self)._stripe_request(url, data=data, method=method,
                                                                 idempotency_key=idempotency_key)

        return res

    def stripe_form_generate_values(self, tx_values):

        print("tx_values==", tx_values)
        bd_value = tx_values['amount']
        old_currency = tx_values['currency']
        convert_currency = self.env['res.currency'].search([('name', '=', 'USD')])
        print("convert_currency==", convert_currency)

        print("tx_values['currency']==",tx_values['currency'])
        tx_values['amount'] = tx_values['currency'].with_context(date=date.today()).compute(tx_values['amount'],
                                                                                       convert_currency)
        tx_values['currency'] = convert_currency
        print("amount_convert==", tx_values['amount'])

        return super(PaymentAcquirerStripe, self).stripe_form_generate_values(tx_values)

