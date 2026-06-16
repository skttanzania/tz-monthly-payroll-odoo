from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Employee Payslip'
    _order = 'date_from desc, id desc'

    name = fields.Char(required=True, readonly=True)
    number = fields.Char(string='Reference', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True)
    date_from = fields.Date(required=True, readonly=True)
    date_to = fields.Date(required=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', default='draft', readonly=True, copy=False)
    line_ids = fields.One2many('hr.payslip.line', 'slip_id', string='Payslip Lines', readonly=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True)
    struct_id = fields.Many2one('hr.salary.structure', string='Structure', required=True, readonly=True)
    total_amount = fields.Float(compute='_compute_total_amount', store=True, string='Total')
    basic_wage = fields.Float(compute='_compute_basic_wage', store=True, string='Basic Wage')
    net_wage = fields.Float(compute='_compute_net_wage', store=True, string='Net Salary')

    @api.depends('line_ids.total')
    def _compute_total_amount(self):
        for payslip in self:
            payslip.total_amount = sum(payslip.line_ids.mapped('total'))

    @api.depends('contract_id')
    def _compute_basic_wage(self):
        for payslip in self:
            payslip.basic_wage = payslip.contract_id.wage if payslip.contract_id else 0.0

    @api.depends('line_ids.total', 'line_ids.category_id')
    def _compute_net_wage(self):
        for payslip in self:
            net_category = self.env.ref('hr_payroll.NET', raise_if_not_found=False)
            if net_category:
                net_line = payslip.line_ids.filtered(lambda l: l.category_id == net_category)
                payslip.net_wage = sum(net_line.mapped('total'))
            else:
                payslip.net_wage = payslip.total_amount

    @api.model
    def create(self, vals):
        if vals.get('number', False):
            return super(HrPayslip, self).create(vals)
        vals['number'] = self.env['ir.sequence'].next_by_code('salary.slip') or 'New'
        return super(HrPayslip, self).create(vals)

    def action_payslip_draft(self):
        return self.write({'state': 'draft'})

    def action_payslip_done(self):
        for payslip in self:
            if not payslip.line_ids:
                raise UserError('You cannot validate a payslip without lines!')
        return self.write({'state': 'done'})

    def action_payslip_cancel(self):
        return self.write({'state': 'cancel'})

    def compute_sheet(self):
        """Compute the payslip lines based on salary rules"""
        for payslip in self:
            payslip.line_ids.unlink()

            if not payslip.contract_id:
                raise UserError('No contract found for employee %s!' % payslip.employee_id.name)

            # Get salary structure and rules
            struct = payslip.struct_id
            rule_ids = struct.rule_ids.sorted(key=lambda r: r.sequence)

            # Prepare local dictionary for rule computation
            localdict = self._get_localdict(payslip)

            # Process each rule
            line_vals = []
            for rule in rule_ids:
                amount = rule.compute_rule(localdict)
                if amount or rule.appears_on_payslip:
                    line_vals.append({
                        'slip_id': payslip.id,
                        'salary_rule_id': rule.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'amount': amount,
                        'total': amount,
                    })
                    # Update localdict with computed value
                    localdict[rule.code] = amount

            # Create payslip lines
            self.env['hr.payslip.line'].create(line_vals)

        return True

    def _get_localdict(self, payslip):
        """Prepare dictionary for salary rule computation"""
        return {
            'payslip': payslip,
            'employee': payslip.employee_id,
            'contract': payslip.contract_id,
            'rules': {},
            'categories': {},
            'worked_days': {},
            'inputs': {},
        }


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'
    _description = 'Payslip Line'
    _order = 'sequence, id'

    slip_id = fields.Many2one('hr.payslip', string='Payslip', required=True, ondelete='cascade')
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Rule', required=True)
    employee_id = fields.Many2one('hr.employee', related='slip_id.employee_id', store=True)
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    category_id = fields.Many2one('hr.salary.rule.category', string='Category', required=True)
    sequence = fields.Integer(default=10)
    amount = fields.Float(string='Amount')
    quantity = fields.Float(default=1.0)
    rate = fields.Float(default=100.0, string='Rate (%)')
    total = fields.Float(string='Total')

    @api.onchange('amount', 'quantity', 'rate')
    def _onchange_amount(self):
        if self.amount and self.quantity and self.rate:
            self.total = self.amount * self.quantity * self.rate / 100
        else:
            self.total = 0.0
