from odoo import api, fields, models


class SalaryStructure(models.Model):
    _name = 'hr.salary.structure'
    _description = 'Salary Structure'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string='Company')
    rule_ids = fields.Many2many('hr.salary.rule', string='Salary Rules')
    parent_id = fields.Many2one('hr.salary.structure', string='Parent Structure')
