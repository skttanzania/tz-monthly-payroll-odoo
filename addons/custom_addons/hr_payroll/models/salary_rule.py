from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):
    _name = 'hr.salary.rule'
    _description = 'Salary Rule'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Unique code for the rule")
    sequence = fields.Integer(default=10)
    category_id = fields.Many2one('hr.salary.rule.category', string='Category', required=True)
    active = fields.Boolean(default=True)
    appears_on_payslip = fields.Boolean(default=True, string='Appears on Payslip')
    condition_select = fields.Selection([
        ('none', 'Always True'),
        ('range', 'Range'),
        ('python', 'Python Expression'),
    ], string='Condition', default='none', required=True)
    condition_range = fields.Char(string='Range Based on', help='E.g., contract.wage')
    condition_range_min = fields.Float(string='Min Value')
    condition_range_max = fields.Float(string='Max Value')
    condition_python = fields.Text(string='Python Condition', default='result = True')
    amount_select = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage (%)'),
        ('code', 'Python Code'),
    ], string='Amount Type', default='fixed', required=True)
    amount_fix = fields.Float(string='Fixed Amount')
    amount_percentage = fields.Float(string='Percentage (%)')
    amount_percentage_base = fields.Char(string='Percentage based on', help='E.g., contract.wage')
    amount_python_compute = fields.Text(string='Python Code', default='result = contract.wage')
    note = fields.Text(string='Description')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The salary rule code must be unique!')
    ]

    @api.constrains('amount_percentage')
    def _check_amount_percentage(self):
        for rule in self:
            if rule.amount_select == 'percentage' and not (0 <= rule.amount_percentage <= 100):
                raise ValidationError('Percentage must be between 0 and 100!')

    def compute_rule(self, localdict):
        """
        Compute the salary rule amount based on the rule configuration
        :param localdict: dictionary containing payslip computation variables
        :return: computed amount
        """
        self.ensure_one()

        # Check condition
        if not self._satisfy_condition(localdict):
            return 0.0

        # Compute amount
        if self.amount_select == 'fixed':
            return self.amount_fix
        elif self.amount_select == 'percentage':
            base = self._get_percentage_base(localdict)
            return base * self.amount_percentage / 100
        elif self.amount_select == 'code':
            return self._compute_python_code(localdict)

        return 0.0

    def _satisfy_condition(self, localdict):
        """Check if the rule condition is satisfied"""
        self.ensure_one()
        if self.condition_select == 'none':
            return True
        elif self.condition_select == 'range':
            try:
                value = safe_eval(self.condition_range or '0', localdict)
                return self.condition_range_min <= value <= self.condition_range_max
            except Exception:
                return False
        elif self.condition_select == 'python':
            try:
                # Execute condition code which should set `result` in localdict
                safe_eval(self.condition_python or 'result = False', localdict)
                return bool(localdict.get('result', False))
            except Exception:
                return False
        return True

    def _get_percentage_base(self, localdict):
        """Get the base amount for percentage calculation"""
        if self.amount_percentage_base:
            try:
                return float(safe_eval(self.amount_percentage_base, localdict) or 0.0)
            except Exception:
                return 0.0
        return 0.0

    def _compute_python_code(self, localdict):
        """Execute Python code to compute amount"""
        try:
            safe_eval(self.amount_python_compute or 'result = 0.0', localdict)
            return float(localdict.get('result', 0.0) or 0.0)
        except Exception:
            return 0.0


class HrSalaryRuleCategory(models.Model):
    _name = 'hr.salary.rule.category'
    _description = 'Salary Rule Category'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    parent_id = fields.Many2one('hr.salary.rule.category', string='Parent')
    note = fields.Text(string='Description')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The category code must be unique!')
    ]
