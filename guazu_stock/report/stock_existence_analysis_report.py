# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ReportExistenceAnalysis(models.Model):
    _name = 'guazu.existence.analysis.report'
    _auto = False

    #date = fields.Date(string='Fecha')
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)
    location_id = fields.Many2one('guazu.stock.location', string='Ubicación', readonly=True)
    product_id = fields.Many2one('product.product', string='Variante', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Producto', readonly=True)
    quantity = fields.Float(string='Existencia', readonly=True)
    in_qty = fields.Float(string='Entradas', readonly=True)
    out_qty = fields.Float(string='Salidas', readonly=True)
    uom_id = fields.Many2one('product.uom', string='UdM', readonly=True)
    categ_id = fields.Many2one('product.category', string='Categoría', readonly=True)
    amount = fields.Float(string='Importe', readonly=True)
    price = fields.Float(string='Precio Promedio', digits=(16,5), readonly=True, group_operator="avg")
    sex = fields.Many2one('guazu.product.sex', string='Sexo', readonly=True)
    color = fields.Many2one('guazu.product.color', string='Color', readonly=True)

    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'guazu_existence_analysis_report')
        self._cr.execute("""CREATE or REPLACE VIEW guazu_existence_analysis_report AS (
                    SELECT
                        sm_id as id,
                        al.done_date as date,
                        al.company_id as company_id,
                        al.location_id as location_id,
                        al.quantity,
                        al.product_id as product_id,
                        al.product_tmpl_id as product_tmpl_id,
                        al.uom_id as uom_id,
                        al.categ_id as categ_id,
                        al.amount,
                        al.quantity as in_qty,
                        al.amount as in_amount,
                        0 as out_qty,
                        0 as out_amount,
                        (al.amount/al.quantity) as price,
						al.sex as sex,
						al.color as color
                    FROM (SELECT
                        sm.id as sm_id,
                        
                        sp.location_dest_id as location_id,                        
                        sp.done_date as done_date,
                        sum(sm.quantity * pu2.factor / pu.factor) as quantity,
                        sum(sm.amount) as amount,
                        pt.categ_id as categ_id,
                        sm.product_id as product_id,
                            sp.company_id as company_id,
                            pt.uom_id as uom_id,
                            pt.id as product_tmpl_id,
						pt.sex_id as sex,
						pt.color_id as color
                    FROM
                        guazu_stock_move_line sm
                        LEFT JOIN guazu_stock_move sp ON (sm.stock_move_id=sp.id)
                        LEFT JOIN guazu_stock_location loc ON (sp.location_dest_id=loc.id)
                        LEFT JOIN product_product pp ON (sm.product_id=pp.id)
                        LEFT JOIN product_uom pu ON (sm.uom_id=pu.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu2 ON (pt.uom_id=pu2.id)
						LEFT JOIN guazu_product_sex sx ON (pt.sex_id=sx.id)
                        LEFT JOIN guazu_product_color cl ON (pt.color_id=cl.id)
                    WHERE sp.state = 'done' and loc.type = 'storage' and sm.quantity <> 0
                    GROUP BY
                        sm.id, 
                        sp.location_dest_id,
                        sp.done_date,
                        sm.product_id, pt.id, pt.uom_id, sm.uom_id,
                        sm.product_id, sm.stock_move_id, sm.quantity,
                        sp.company_id, pu.factor, pu2.factor, pt.categ_id,pt.sex_id,pt.color_id)
                    AS al
                    GROUP BY                                                
                        al.sm_id, al.product_id, al.product_tmpl_id, al.uom_id,al.done_date,
                        al.company_id, al.quantity, al.amount, al.categ_id, al.location_id, al.sex,al.color
                UNION ALL(
                SELECT
                        sm_id as id,
                        al.done_date as date,
                        al.company_id as company_id,
                        al.location_id as location_id,
                        al.quantity*-1,
                        al.product_id as product_id,
                        al.product_tmpl_id as product_tmpl_id,
                        al.uom_id as uom_id,
                        al.categ_id as categ_id,
                        al.amount*-1,
                        0 as in_qty,
                        0 as in_amount,
                        al.quantity as out_qty,
                        al.amount as out_amount,
                        (al.amount/al.quantity) as price,
						al.sex as sex,
						al.color as color

                    FROM (SELECT
                        sm.id as sm_id,
                        sp.done_date as done_date,
                        sp.location_id as location_id,
                        sum(sm.quantity * pu2.factor / pu.factor) as quantity,
                        sum(sm.amount) as amount,
                        pt.categ_id as categ_id,
                        sm.product_id as product_id,
                            sp.company_id as company_id,
                            pt.uom_id as uom_id,
                            pt.id as product_tmpl_id,
							pt.sex_id as sex,
							pt.color_id as color
                    FROM
                        guazu_stock_move_line sm
                        LEFT JOIN guazu_stock_move sp ON (sm.stock_move_id=sp.id)
                        LEFT JOIN guazu_stock_location loc ON (sp.location_id=loc.id)
                        LEFT JOIN product_product pp ON (sm.product_id=pp.id)
                        LEFT JOIN product_uom pu ON (sm.uom_id=pu.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu2 ON (pt.uom_id=pu2.id)
						LEFT JOIN guazu_product_sex sx ON (pt.sex_id=sx.id)
                        LEFT JOIN guazu_product_color cl ON (pt.color_id=cl.id)
                    WHERE sp.state = 'done' and loc.type = 'storage' and sm.quantity <> 0
                    GROUP BY
                        sm.id, 
                        sp.done_date, 
                        sp.location_id,
                        sm.product_id, pt.id, pt.uom_id, sm.uom_id,
                        sm.product_id, sm.stock_move_id, sm.quantity,
                        sp.company_id, pu.factor, pu2.factor, pt.categ_id,
						pt.sex_id,pt.color_id)
                    AS al
                    GROUP BY                                                
                        al.sm_id, al.product_id, al.product_tmpl_id, al.uom_id,al.done_date,
                        al.company_id, al.quantity, al.amount, al.categ_id, al.location_id,al.sex,
						al.color)
                    )""")
