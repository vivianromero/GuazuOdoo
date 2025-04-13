# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class StockForecatReport(models.Model):
    _name = 'guazu.stock.forecast.report'
    _auto = False

    date = fields.Date(string='Date')
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)
    location_id = fields.Many2one('guazu.stock.location', string='Origen', readonly=True)
    location_dest_id = fields.Many2one('guazu.stock.location', string='Destino', readonly=True)
    stock_move_id = fields.Many2one('guazu.stock.move', string='Movimiento', readonly=True)
    product_id = fields.Many2one('product.product', string='Variante', readonly=True)
    track_id = fields.Many2one('guazu.stock.track', string='Taller', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Producto', readonly=True)
    quantity = fields.Float(string='Cantidad', readonly=True)
    out_qty = fields.Float(string='Cantidad Saliente', readonly=True)
    in_qty = fields.Float(string='Cantidad Entrante', readonly=True)
    uom_id = fields.Many2one('product.uom', string='UdM', readonly=True)
    categ_id = fields.Many2one('product.category', string='Categoría', readonly=True)
    value = fields.Float(string='Importe', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'guazu_stock_forecast_report')
        self._cr.execute("""CREATE or REPLACE VIEW guazu_stock_forecast_report AS ( SELECT
                        min(sm_id) as id,
                        date_trunc('day',al.done_date) as date,
                        al.curr_year as year,
                        al.curr_month as month,
                        al.curr_day as day,
                        al.curr_day_diff as day_diff,
                        al.track_id as track_id,
                        al.location_id as location_id,
                        al.stock_move_id as stock_move_id,
                        al.company_id as company_id,
                        al.location_dest_id as location_dest_id,
                        al.quantity,
                        al.out_qty as out_qty,
                        al.in_qty as in_qty,
                        al.product_id as product_id,
                        al.product_tmpl_id as product_tmpl_id,
                        al.uom_id as uom_id,
                        al.categ_id as categ_id,
                        sum(al.in_value - al.out_value) as value
                    FROM (SELECT
                        CASE WHEN from_location.type in ('storage') THEN
                            sum(sm.quantity * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS out_qty,
                        CASE WHEN from_location.type in ('storage') THEN
                            sum(sm.quantity * sm.price)
                            ELSE 0.0
                            END AS out_value,
                        CASE WHEN to_location.type in ('storage') THEN
                            sum(sm.quantity * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS in_qty,
                        CASE WHEN to_location.type in ('storage') THEN
                            sum(sm.quantity * sm.price)
                            ELSE 0.0
                            END AS in_value,
                        min(sm.id) as sm_id,
                        sp.done_date as done_date,
                        to_char(date_trunc('day',sp.done_date), 'YYYY') as curr_year,
                        to_char(date_trunc('day',sp.done_date), 'MM') as curr_month,
                        to_char(date_trunc('day',sp.done_date), 'YYYY-MM-DD') as curr_day,
                        avg(date(sp.done_date)-date(sp.emission_date)) as curr_day_diff,
                        sum(sm.quantity) as quantity,
                        pt.categ_id as categ_id,
                        sm.product_id as product_id,
                        sm.track_id as track_id,
                        sm.stock_move_id as stock_move_id,
                            sp.company_id as company_id,
                            sm.uom_id as uom_id,
                            from_location,
                            from_location.id as location_id,
                            to_location,
                            to_location.id as location_dest_id,
                            pt.id as product_tmpl_id
                    FROM
                        guazu_stock_move_line sm
                        LEFT JOIN guazu_stock_move sp ON (sm.stock_move_id=sp.id)
                        LEFT JOIN guazu_stock_location from_location ON (sp.location_id=from_location.id)
                        LEFT JOIN guazu_stock_location to_location ON (sp.location_dest_id=to_location.id)
                        LEFT JOIN product_product pp ON (sm.product_id=pp.id)
                        LEFT JOIN product_uom pu ON (sm.uom_id=pu.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu2 ON (pt.uom_id=pu2.id)
                    WHERE sp.state = 'done'
                    GROUP BY
                        sm.id, sp.done_date,
                        sm.track_id,
                        sm.product_id,pt.id, sm.uom_id,sp.done_date,
                        sm.product_id, sm.stock_move_id, sm.quantity,
                        sp.company_id,from_location.id,to_location.id,pu.factor,pt.categ_id)
                    AS al
                    GROUP BY
                        al.out_qty,al.in_qty,al.curr_year,al.curr_month,
                        al.curr_day,al.curr_day_diff,al.done_date,al.location_id,al.location_dest_id,
                        al.track_id, al.product_id, al.product_tmpl_id, al.uom_id,
                        al.stock_move_id,al.company_id,al.quantity, al.categ_id)""")
