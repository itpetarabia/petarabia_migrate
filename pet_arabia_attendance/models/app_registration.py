from odoo import _, fields, models


class EmployeeAppRegistration(models.Model):
    _name = "hr.attendance.appregistration"
    _description = "Attendance Tracking App: Registrations"
    _rec_name = "employee_id"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        ondelete='cascade'
    )
    device_id = fields.Char(
        string="Unique Device ID",
        required=True,
    )
    employee_id_num = fields.Integer(
        related='employee_id.id',
        string="Employee ID Number",
        readonly=True
    )

    _sql_constraints = [("unique_employee", "unique(employee_id)", _("This employee has already registered.")),
                    ("unique_device_id", "unique(device_id)", _("Device ID is already linked to another employee")),
    ]
