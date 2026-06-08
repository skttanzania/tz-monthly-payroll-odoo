from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # placeholder for potential future payroll fields
    payroll_notes = fields.Text(string='Payroll Notes')
