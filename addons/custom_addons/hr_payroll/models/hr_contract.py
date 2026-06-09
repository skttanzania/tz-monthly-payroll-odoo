from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    struct_id = fields.Many2one('hr.salary.structure', string='Salary Structure',
                                help='Defines salary rules for this contract')
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Payment Schedule', default='monthly', required=True)

    # Allowances
    hra = fields.Float(string='House Rent Allowance (HRA)')
    transport_allowance = fields.Float(string='Transport Allowance')
    meal_allowance = fields.Float(string='Meal Allowance')
    medical_allowance = fields.Float(string='Medical Allowance')
    other_allowance = fields.Float(string='Other Allowances')

    # Deductions
    provident_fund = fields.Float(string='Provident Fund')
    professional_tax = fields.Float(string='Professional Tax')
    income_tax = fields.Float(string='Income Tax')
    insurance = fields.Float(string='Insurance')
    loan_deduction = fields.Float(string='Loan Deduction')

    # Computed fields
    total_allowances = fields.Float(compute='_compute_total_allowances',
                                    string='Total Allowances', store=True)
    total_deductions = fields.Float(compute='_compute_total_deductions',
                                    string='Total Deductions', store=True)
    net_salary = fields.Float(compute='_compute_net_salary',
                              string='Net Salary', store=True)
    weekly_wage = fields.Float(compute='_compute_weekly_wage',
                               string='Weekly Wage', store=True)

    @api.depends('hra', 'transport_allowance', 'meal_allowance',
                 'medical_allowance', 'other_allowance')
    def _compute_total_allowances(self):
        for contract in self:
            contract.total_allowances = (
                contract.hra +
                contract.transport_allowance +
                contract.meal_allowance +
                contract.medical_allowance +
                contract.other_allowance
            )

    @api.depends('provident_fund', 'professional_tax', 'income_tax',
                 'insurance', 'loan_deduction')
    def _compute_total_deductions(self):
        for contract in self:
            contract.total_deductions = (
                contract.provident_fund +
                contract.professional_tax +
                contract.income_tax +
                contract.insurance +
                contract.loan_deduction
            )

    @api.depends('wage', 'total_allowances', 'total_deductions')
    def _compute_net_salary(self):
        for contract in self:
            contract.net_salary = (
                contract.wage +
                contract.total_allowances -
                contract.total_deductions
            )

    @api.depends('wage', 'schedule_pay')
    def _compute_weekly_wage(self):
        for contract in self:
            if contract.schedule_pay == 'weekly':
                contract.weekly_wage = contract.wage
            else:
                # For monthly: assume 4.33 weeks per month (52 weeks / 12 months)
                contract.weekly_wage = contract.wage / 4.33 if contract.schedule_pay == 'monthly' else contract.wage
