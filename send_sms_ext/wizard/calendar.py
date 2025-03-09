# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo import api, fields, models, tools, _
import datetime
from odoo.exceptions import except_orm, UserError, Warning, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime , timedelta

from pytz import timezone, UTC
import pytz

from odoo.addons.send_sms_ext.tools.format import format_pet_name

_logger = logging.getLogger(__name__)

class Meeting(models.Model):
    _inherit = 'calendar.event'

    def get_date_with_timezone(self, date_appointment):
        local = pytz.timezone("Asia/Bahrain")
        date = date_appointment.astimezone(local)
        # Custom format
        today = datetime.now().astimezone(local).replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = today + timedelta(days=1)
        end_of_tmrow = today + timedelta(days=2)

        if date < end_of_day:
            # If Today
            return date.strftime(f"today at %-I:%M%p")
        elif date < end_of_tmrow:
            # If Tomorrow
            return date.strftime(f"tomorrow at %-I:%M%p")
        else:
            # any other day
            day = date.day 
            if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]
            return date.strftime(f"%-I:%M%p on %-d{suffix} of %B")
        

    
    def send_sms_link(self, event):
        allday = False
        for partner in event.partner_ids:
            if not partner: continue
            
            phone_no = partner.phone or partner.mobile
            if not phone_no: continue

            date_appointment = event.start
            if event.allday:
                allday = True
            
            location = event.location or '--'
            partner_name = partner.name
            pet_name = format_pet_name(event.appointment_id.pet_ids)
            sms_msgs = self.env['sms.messages.gateway'].sudo().search([
                ('sms_type', '=', 'appointment'),
                ('state', '=', 'confirm')])
            if not sms_msgs: continue

            gateway_content = sms_msgs[-1]
            message = gateway_content.message
            if not message: return # exit

            d2 = self.get_date_with_timezone(date_appointment)
            if d2 and allday == True:
                d2 = datetime.strptime(d2, '%d %b %Y, %H:%M:%S')
                d2 = d2.strftime('%d %b %Y')
                        
            message = message\
                    .replace('{NAME}',partner_name)\
                    .replace('{DATE}',d2)\
                    .replace('{LOCATION}', location)\
                    .replace('{PETNAME}', pet_name)

            self.env['sms.messages.petarabia'].send_sms(
                messages=message,
                receivers=phone_no,
                )


    @api.model
    def _run_appointment_sms(self):
        print("run_appointment_sms")
        ''' This method is called from a cron job. '''
        ############
        events = self.search([
            ('start', '>=', fields.Datetime.now()),
        ])
        time_plus_5min = fields.Datetime.now() + relativedelta(minutes=5)
        for event in events:
            if event.alarm_ids:
                for alarm in event.alarm_ids:
                    remainder_begin = event.start - relativedelta(minutes=alarm.duration_minutes)
                    if fields.Datetime.now() <= remainder_begin and time_plus_5min >= remainder_begin:
                        response = self.send_sms_link(event)



    @api.model
    def _backup_run_appointment_sms(self):
        print("backup_run_appointment_sms")
        ''' This method is called from a cron job for appointments that don't have reminders.
        So we send one at the start of the day. '''
        ############
        events = self.search([
            ('start', '>=', fields.Datetime.now()),
        ])

        local = pytz.timezone("Asia/Bahrain")
        today = datetime.now().astimezone(local).date()
        for event in events:
            event_start = event.start.astimezone(local).date()
            if (not event.alarm_ids) and (event_start==today):
                response = self.send_sms_link(event)

        ############
        """allday = False
        dt = date.today() + relativedelta(days=1)
        date_from = datetime.combine(dt, datetime.min.time())
        date_to = datetime.combine(dt, datetime.max.time())
        check = self.search([
            ('start', '<=', fields.Datetime.to_string(date_to)),
            ('start', '>=', fields.Datetime.to_string(date_from)),
        ])
        #print("check000",check)
        if check:
            for i in check:
                for partner in i.partner_ids:
                    if partner:
                        if partner.mobile or partner.phone:
                            location = "--"
                            start_time = i.start
                            #print("start_time000",start_time)
                            if i.allday:
                                allday = True
                            if i.location:
                                location = i.location
                            phone_no = partner.mobile
                            if phone_no:
                                phone_no = phone_no.replace('+973 ', '').replace('973 ', '').replace(' ', '').strip()
                            elif partner.phone:
                                phone_no = partner.phone
                                phone_no = phone_no.replace('+973 ', '').replace('973 ', '').replace(' ', '').strip()
                                phone_no = '973%s' % (int(phone_no))
                            partner_name = partner.name
                            print("ggggggg",phone_no,partner_name,start_time,location,allday)
                            response = self.send_sms_link(phone_no,partner_name,start_time,location,allday)
                            #raise Warning(response)
                            #print("response",response)
                        #else:
                        #    raise ValidationError(_("Fill Mobile for Partner: %s" % partner.name))"""
                    
    
 
