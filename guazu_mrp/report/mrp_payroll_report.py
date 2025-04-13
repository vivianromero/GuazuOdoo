# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_utils


class MrpPayrollReport(models.AbstractModel):
    _name = 'report.guazu_mrp.report_mrp_payroll'

    @api.model
    def get_analysis(self, initial_date, final_date, workshop_ids):
        datas = []
        workshop = "Todas las áreas de producción"
        if not workshop_ids:
            query = """SELECT
                e.name_related,
                sum(line.amount) as amount,
                sum(line.amount*0.1) as tax,
                sum(line.amount - line.amount*0.1) as value
            FROM
                guazu_mrp_order_line line
                LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                LEFT JOIN hr_employee e ON (line.employee_id=e.id)
            WHERE o.state = 'done' and o.production_date >= '""" + initial_date + """' and
                o.production_date <= '""" + final_date + """'
            GROUP BY
                e.name_related
            ORDER BY
                e.name_related asc
                """

        if len(workshop_ids) == 1:
            query = """SELECT
                e.name_related,
                sum(line.amount) as amount,
                sum(line.amount*0.1) as tax,
                sum(line.amount - line.amount*0.1) as value
            FROM
                guazu_mrp_order_line line
                LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                LEFT JOIN hr_employee e ON (line.employee_id=e.id)
            WHERE o.state = 'done' and o.production_date >= '""" + initial_date + """' and
                o.production_date <= '""" + final_date + """' and
                o.workshop_id = """+str(workshop_ids[0])+"""
            GROUP BY
                e.name_related
            ORDER BY
                e.name_related asc
                """
            workshop = self.env["guazu.mrp.workshop"].browse(workshop_ids[0]).location_id.name

        if len(workshop_ids) > 1:
            query = """SELECT
                e.name_related,
                sum(line.amount) as amount,
                sum(line.amount*0.1) as tax,
                sum(line.amount - line.amount*0.1) as value
            FROM
                guazu_mrp_order_line line
                LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                LEFT JOIN hr_employee e ON (line.employee_id=e.id)
            WHERE o.state = 'done' and o.production_date >= '""" + initial_date + """' and
                o.production_date <= '""" + final_date + """' and
                o.workshop_id in """ + str(tuple(workshop_ids)) + """
            GROUP BY
                e.name_related
            ORDER BY
                e.name_related asc
                """

            workshops = self.env["guazu.mrp.workshop"].search([('id', 'in', workshop_ids)])
            workshop = ""
            for ws in workshops:
                workshop += ws.location_id.name + ", "
            workshop = workshop[0: -2]

        self.env.cr.execute(query)
        items = self.env.cr.dictfetchall()
        total_amount = total_tax = total_value = 0
        for d in items:
            total_amount += d['amount']
            total_tax += d['tax']
            total_value += d['value']

            d.update({'amount': float_utils.float_repr(d['amount'], 2),
                      'tax': float_utils.float_repr(d['tax'], 2),
                      'value': float_utils.float_repr(d['value'], 2)})

        datas.append({"workshop": workshop,
                      "items": items,
                      "total_amount": float_utils.float_repr(total_amount, 2),
                      "total_tax": float_utils.float_repr(total_tax, 2),
                      "total_value": float_utils.float_repr(total_value, 2)})

        return datas

    @api.model
    def get_grouped_analysis(self, initial_date, final_date, workshop_ids):
        datas = []

        if not workshop_ids:
            workshops = self.env["guazu.mrp.workshop"].search([])
            for ws in workshops:
                workshop_ids.append(ws.id)

        for workshop_id in workshop_ids:
            query = """SELECT
                e.name_related,
                sum(line.amount) as amount,
                sum(line.amount*0.1) as tax,
                sum(line.amount - line.amount*0.1) as value
            FROM
                guazu_mrp_order_line line
                LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                LEFT JOIN guazu_mrp_workshop w ON (o.workshop_id=w.id)
                LEFT JOIN hr_employee e ON (line.employee_id=e.id)
            WHERE o.state = 'done' and o.production_date >= '""" + initial_date + """' and
                o.production_date <= '""" + final_date + """'
                and w.id = """ + str(workshop_id) + """
            GROUP BY
                e.name_related
            ORDER BY
                e.name_related asc"""

            self.env.cr.execute(query)
            items = self.env.cr.dictfetchall()
            total_amount = total_tax = total_value =0
            for d in items:
                total_amount += d['amount']
                total_tax += d['tax']
                total_value += d['value']

                d.update({'amount': float_utils.float_repr(d['amount'], 2),
                          'tax': float_utils.float_repr(d['tax'], 2),
                          'value': float_utils.float_repr(d['value'], 2)})

            workshop = self.env["guazu.mrp.workshop"].browse(workshop_id)
            datas.append({"workshop": workshop.location_id.name,
                          "items": items,
                          "total_amount": float_utils.float_repr(total_amount, 2),
                          "total_tax": float_utils.float_repr(total_tax, 2),
                          "total_value": float_utils.float_repr(total_value, 2)})

        return datas

    @api.model
    def get_total(self, initial_date, final_date, workshop_ids):
        if not len(workshop_ids):
            self.env.cr.execute("""SELECT
                    sum(line.amount) as amount,
                    sum(line.amount*0.1) as tax,
                    sum(line.amount - line.amount*0.1) as value
                FROM
                    guazu_mrp_order_line line
                    LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                WHERE o.state = 'done' and o.production_date >= '""" + initial_date + """' and
                    o.production_date <= '""" + final_date + """'
                """)
            data = self.env.cr.dictfetchall()
        if len(workshop_ids) == 1:
            self.env.cr.execute("""SELECT
                    sum(line.amount) as amount,
                    sum(line.amount*0.1) as tax,
                    sum(line.amount - line.amount*0.1) as value
                FROM
                    guazu_mrp_order_line line
                    LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                WHERE o.state = 'done' and o.production_date >= '""" + initial_date + """'
                    and o.production_date <= '""" + final_date + """'
                    and o.workshop_id = """+str(workshop_ids[0]))

            data = self.env.cr.dictfetchall()
        if len(workshop_ids) > 1:
            self.env.cr.execute("""SELECT
                    sum(line.amount) as amount,
                    sum(line.amount*0.1) as tax,
                    sum(line.amount - line.amount*0.1) as value
                FROM
                    guazu_mrp_order_line line
                    LEFT JOIN guazu_mrp_order o ON (line.order_id=o.id)
                WHERE o.state = 'done' and o.production_date >= '""" + initial_date + """'
                    and o.production_date <= '""" + final_date + """'
                    and o.workshop_id in """ + str(tuple(workshop_ids)))

            data = self.env.cr.dictfetchall()

        total_amount = total_tax = total_value = 0
        for d in data:
            amount = d['amount'] and d['amount'] or 0
            tax = d['tax'] and d['tax'] or 0
            value = d['value'] and d['value'] or 0

            total_amount += amount
            total_tax += tax
            total_value += value
            d.update({'amount': float_utils.float_repr(amount, 2),
                      'tax': float_utils.float_repr(tax, 2),
                      'value': float_utils.float_repr(value, 2)})

        return float_utils.float_repr(total_amount, 2), float_utils.float_repr(total_tax, 2), float_utils.float_repr(total_value, 2)

    @api.model
    def get_report_values(self, docids, data=None):
        initial_date = data['form']['initial_date']
        final_date = data['form']['final_date']
        group_by_workshop = data['form']['group_by_workshop']
        workshop_ids = data['form']['workshop_ids']

        if group_by_workshop:
            return {
                'data': data,
                'analysis': self.get_grouped_analysis(initial_date, final_date, workshop_ids),
                'total': self.get_total(initial_date, final_date, workshop_ids)
            }
        else:
            return {
                'data': data,
                'analysis': self.get_analysis(initial_date, final_date, workshop_ids),
                'total': self.get_total(initial_date, final_date, workshop_ids)
            }

    @api.model
    def render_html(self, docids, data=None):
        initial_date = data['form']['initial_date']
        final_date = data['form']['final_date']
        group_by_workshop = data['form']['group_by_workshop']
        workshop_ids = data['form']['workshop_ids']

        if group_by_workshop:
            docargs = {
                'data': data,
                'analysis': self.get_grouped_analysis(initial_date, final_date, workshop_ids),
                'total': self.get_total(initial_date, final_date, workshop_ids)
            }
        else:
            docargs = {
                'data': data,
                'analysis': self.get_analysis(initial_date, final_date, workshop_ids),
                'total': self.get_total(initial_date, final_date, workshop_ids)
            }
        
        return self.env['report'].render('guazu_mrp.report_mrp_payroll', values=docargs)