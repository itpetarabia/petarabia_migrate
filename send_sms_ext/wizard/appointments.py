# -*- coding: utf-8 -*-
import logging
import pytz
from odoo import fields, models, _, api
from odoo.exceptions import except_orm, UserError, Warning, ValidationError

from odoo.addons.send_sms_ext.tools.format import format_pet_name

_logger = logging.getLogger(__name__)

class PosAppointments(models.Model):
    _inherit = "pos.appointments"

    def get_date_with_timezone(self, date_appointment):
        local = pytz.timezone("Asia/Bahrain")
        date = date_appointment.astimezone(local)

        day = date.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]

        return date.strftime(f"%-I:%M%p on %-d{suffix} of %B")

    def send_sms_link(self, phone_num, partner_name, pet_names, date_appointment, location):
        sms_templ_recs = self.env['sms.messages.gateway'].sudo().search(
                            [('sms_type', '=', 'appointment_confirm'), ('state', '=', 'confirm')])
        if sms_templ_recs:
            gateway_content = sms_templ_recs[-1]
            message = gateway_content.message
            if message:
                date = " "
                if date_appointment:
                    date = self.get_date_with_timezone(date_appointment)
                message = message.replace('{NAME}', partner_name)\
                    .replace('{DATE}', date)\
                    .replace('{LOCATION}', location)\
                    .replace('{PETNAME}', pet_names)
                    
                if phone_num:
                    return self.env['sms.messages.petarabia'].send_sms(
                        messages=message,
                        receivers=phone_num,
                        )
        
    def action_confirm(self):
        self.ensure_one()
        super().action_confirm()
        
        if not self.partner_id:
            raise ValidationError(_("Select Partner."))

        phone_no = self.partner_id.phone or self.partner_id.mobile
        if not phone_no:
            raise ValidationError(_("Fill Partner Mobile or Phone"))

        partner_name = self.partner_id.name
        pet_names = format_pet_name(self.pet_ids)
        location = self.config_id.name or self.location or ''
        start_time = self.start_datetime
        response = self.send_sms_link(phone_no, partner_name, pet_names, start_time, location)
        return response

    ##Ready for Pickup
    def send_sms_link_pickup(self, phone_num, partner_name, pet_names, date_appointment, location):
        # print("send_sms_link_pickup",self, phone_num, partner_name, pet_names, date_appointment, location)
        sms_templ_recs = self.env['sms.messages.gateway'].sudo().search(
            [('sms_type', '=', 'appointment_pickup'), ('state', '=', 'confirm')])
        if sms_templ_recs:
            gateway_content = sms_templ_recs[-1]
            message = gateway_content.message
            if message:
                date = " "
                if date_appointment:
                    date = self.get_date_with_timezone(date_appointment)
                message = message.replace('{NAME}', partner_name) \
                    .replace('{DATE}', date) \
                    .replace('{LOCATION}', location) \
                    .replace('{PETNAME}', pet_names)
                print("message", message)
                if phone_num:
                    return self.env['sms.messages.petarabia'].send_sms(
                        messages=message,
                        receivers=phone_num,
                    )

    def action_ready_for_pickup(self):
        self.ensure_one()
        super().action_ready_for_pickup()
        if not self.partner_id:
            raise ValidationError(_("Select Partner."))

        phone_no = self.partner_id.phone or self.partner_id.mobile
        if not phone_no:
            raise ValidationError(_("Fill Partner Mobile or Phone"))

        partner_name = self.partner_id.name
        pet_names = format_pet_name(self.pet_ids)
        location = self.config_id.name or self.location or ''
        start_time = self.start_datetime
        response = self.send_sms_link_pickup(phone_no, partner_name, pet_names, start_time, location)
        return response


