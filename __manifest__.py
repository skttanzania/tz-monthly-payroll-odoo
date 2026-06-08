{
    'name': 'Payroll Management',
    'version': '16.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Complete payroll management with salary rules and payslip processing',
    'description': """
        Payroll Management Module
        =========================
        * Manage salary rules and structures
        * Process employee payslips
        * Integration with attendance and contracts
        * Customizable salary calculations
        * Multi-currency support
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'hr_contract',
        'hr_attendance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/salary_rules.xml',
        'views/salary_structure.xml',
        'views/work_entry_types.xml',
        'views/payslip_views.xml',
        'data/salary_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
