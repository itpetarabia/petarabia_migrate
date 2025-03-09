from odoo.exceptions import UserError
from odoo import _, fields, models, api
import logging

logger = logging.getLogger(__name__)


class AttendanceLocation(models.Model):
    _name = "hr.attendance.location"
    _description = "Attendance Tracking App: Work Locations"

    active = fields.Boolean(default=True)
    name = fields.Char(
        string="Location",
        required=True,
        index=True,
    )
    latitude = fields.Float(string="Latitude", required=True, digits=(16,7))
    longitude = fields.Float(string="Longitude", required=True, digits=(16,7))
    permitted_radius = fields.Float(
        string="Permitted Radius (in Km)",
        required=True,
        help="Radius Margin for Error in tracking location")

    _sql_constraints = [("unique_name", "unique(name)", _("A Location with that name already exists!")),
    ]

class AttendanceLocationGroup(models.Model):
    _name = "hr.attendance.locationgroup"
    _description = "Attendance Tracking App: Work Location Groups"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    active = fields.Boolean(default=True)
    name = fields.Char(
        string="Group Name",
        required=True,
        index=True,
        tracking=True,
    )
    locations = fields.Many2many('hr.attendance.location',
                                tracking=True,
                                required=True,
                                string='Locations')

    _sql_constraints = [("unique_name", "unique(name)", _("A Location Group with that name already exists!")),
    ]


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    can_checkin_anywhere = fields.Boolean(
        string='CheckIn Anywhere?',
        default=True,
        groups="hr.group_hr_user",
        )
    can_checkout_anywhere = fields.Boolean(
        string='CheckOut Anywhere?',
        default=True,
        groups="hr.group_hr_user",
        )

    permitted_attendance_locations = fields.Many2many('hr.attendance.location',
                                tracking=True,
                                groups="hr.group_hr_user",
                                string='Locations')
    permitted_attendance_location_groups = fields.Many2many('hr.attendance.locationgroup',
                                tracking=True,
                                groups="hr.group_hr_user",
                                string='Location Groups')
