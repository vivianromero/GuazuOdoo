# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class MrpAnalysis(models.Model):
    _name = 'report.guazu.mrp.analysis'
    _auto = False

    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True)
    date = fields.Date(string='Date')
    workshop_id = fields.Many2one('guazu.mrp.workshop', string='Área de Producción', readonly=True)
    activity_id = fields.Many2one('guazu.mrp.activity', string='Actividad', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', readonly=True)
    price = fields.Float(string='Precio', readonly=True)
    quantity = fields.Float(string='Cantidad', readonly=True)
    amount = fields.Monetary(string='Importe', readonly=True)
    tax = fields.Monetary(string='Impuesto', readonly=True)
    value = fields.Monetary(string='Pago Neto', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_guazu_mrp_analysis')
        self._cr.execute("""CREATE or REPLACE VIEW report_guazu_mrp_analysis AS (SELECT
                        min(line_id) as id,
                        date_trunc('day',al.production_date) as date,
                        al.curr_year as year,
                        al.company_id as company_id,
                        al.currency_id as currency_id,
                        al.curr_month as month,
                        al.curr_day as day,
                        al.workshop_id as workshop_id,
                        al.activity_id as activity_id,
                        al.employee_id as employee_id,
                        al.quantity,
                        al.price as price,
                        (al.quantity * al.price) as amount,
                        (al.quantity * al.price * 0.1) as tax,
                        (al.quantity * al.price) - (al.quantity * al.price * 0.1) as value
                    FROM (SELECT
                        min(line.id) as line_id,
                        o.production_date as production_date,
                        to_char(date_trunc('day',o.production_date), 'YYYY') as curr_year,
                        to_char(date_trunc('day',o.production_date), 'MM') as curr_month,
                        to_char(date_trunc('day',o.production_date), 'YYYY-MM-DD') as curr_day,
                        line.quantity as quantity,
                        line.price as price,
                        line.employee_id as employee_id,
                        line.activity_id as activity_id,
                        o.workshop_id as workshop_id,
                        o.company_id as company_id,
                        c.currency_id as currency_id

                    FROM
                        guazu_mrp_order_line line
                        LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                        LEFT JOIN res_company c ON (o.company_id=c.id)
                        LEFT JOIN guazu_mrp_activity act ON (line.activity_id=act.id)
                        LEFT JOIN guazu_mrp_workshop workshop ON (o.workshop_id=workshop.id)
                        LEFT JOIN hr_employee emp ON (line.employee_id=emp.id)
                    WHERE o.state = 'done'
                    GROUP BY
                        line.id, o.production_date,
                        line.employee_id,line.activity_id,
                        line.price, line.order_id, line.quantity,
                        o.workshop_id, o.company_id, c.currency_id)
                    AS al
                    GROUP BY
                        al.quantity,al.price,al.curr_year,al.curr_month,
                        al.curr_day,al.production_date,al.workshop_id, al.company_id, al.currency_id, al.employee_id,
                        al.activity_id, al.quantity, al.price)""")

