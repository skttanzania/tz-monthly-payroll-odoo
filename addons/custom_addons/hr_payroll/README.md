HR Payroll (custom)
====================

This module provides basic payroll functionality including weekly schedule and overtime calculations (values in TZS).

Quick test plan:
1. Install module `hr_payroll`.
2. Create an employee and a contract with `schedule_pay` = Weekly and `weekly_wage` = 800 (TZS).
3. Create attendance records for a week with 5 hours overtime (e.g., one day with 13 hours instead of 8).
4. Create a payslip for that week and click `Compute Sheet`.
5. Verify basic = 800, overtime = 150, net = 950.
