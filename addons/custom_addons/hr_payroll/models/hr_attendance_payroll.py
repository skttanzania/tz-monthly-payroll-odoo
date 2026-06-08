from odoo import models, fields, api
from datetime import timedelta


class HrAttendancePayroll(models.Model):
    _name = 'hr.attendance.payroll'
    _description = 'Attendance Payroll Integration'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    total_hours = fields.Float(compute='_compute_attendance_hours',
                               string='Total Hours', store=True)
    overtime_hours = fields.Float(compute='_compute_overtime_hours',
                                  string='Overtime Hours', store=True)
    leave_days = fields.Float(compute='_compute_leave_days',
                              string='Leave Days', store=True)
    working_days = fields.Float(compute='_compute_working_days',
                                string='Working Days', store=True)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_attendance_hours(self):
        for record in self:
            if not (record.employee_id and record.date_from and record.date_to):
                record.total_hours = 0.0
                continue

            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', record.employee_id.id),
                ('check_in', '>=', record.date_from),
                ('check_in', '<=', record.date_to),
            ])

            total = 0.0
            for att in attendances:
                if att.check_out and att.check_in:
                    try:
                        delta = att.check_out - att.check_in
                        total += delta.total_seconds() / 3600.0
                    except Exception:
                        total += 0.0

            record.total_hours = total

    @api.depends('total_hours', 'working_days')
    def _compute_overtime_hours(self):
        for record in self:
            standard_hours = record.working_days * 8.0  # 8 hours per day
            record.overtime_hours = max(0, record.total_hours - standard_hours)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_leave_days(self):
        for record in self:
            if not (record.employee_id and record.date_from and record.date_to):
                record.leave_days = 0.0
                continue

            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'validate'),
                ('date_from', '<=', record.date_to),
                ('date_to', '>=', record.date_from),
            ])

            record.leave_days = sum(leaves.mapped('number_of_days'))

    @api.depends('date_from', 'date_to', 'leave_days')
    def _compute_working_days(self):
        for record in self:
            if not (record.date_from and record.date_to):
                record.working_days = 0.0
                continue

            # Calculate business days between dates
            total_days = (record.date_to - record.date_from).days + 1
            weekends = 0
            current_date = record.date_from

            while current_date <= record.date_to:
                if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    weekends += 1
                current_date += timedelta(days=1)

            business_days = total_days - weekends
            record.working_days = business_days - record.leave_days
