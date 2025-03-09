
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models



class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    def _send_mail_to_attendees(self, template_xmlid, force_send=False, ignore_recurrence=False):
        # If it's an appointment, then use another template or don't send it
        if self.event_id.appointment_id:
            # template_xmlid = 'appointments.appointments_template_meeting_invitation'
            return
        super()._send_mail_to_attendees(template_xmlid, force_send, ignore_recurrence)

