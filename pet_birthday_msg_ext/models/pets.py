import logging
import pytz

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class Pets(models.Model):

    _inherit = 'res.pet'

    @api.model
    def _send_birthday_sms(self):
        _logger.info('Started Birthday SMS Scheduler')
        pets = self.env['res.pet'].search([
            ('active', '=', True),
            ('dob', '!=', False),
            ])

        def is_their_bday(pet):
            today = fields.datetime\
                .now()\
                .astimezone(pytz.timezone('Asia/Bahrain'))\
                .date()
            _logger.debug(today)
            dob = pet.dob
            return dob.month == today.month and dob.day == today.day
        pets_filtered = pets.filtered(is_their_bday)

        if pets_filtered:
            messages = []
            receiver_numbers = []
            for p in pets_filtered:
                phone = p.parent_id.phone or p.parent_id.mobile
                receiver_numbers.append(phone)
                messages.append("From the whole team of Pet Arabia, "
                f"we wish our best client {p.name} a very Happy Birthday!")
                
            _logger.info((receiver_numbers, messages))
            return self.env['sms.messages.petarabia'].send_sms(
                messages=messages,
                receivers=receiver_numbers,
                )
        else:
            _logger.info('No pets available today to send birthday messages')


    