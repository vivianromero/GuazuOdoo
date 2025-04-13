from odoo import api, fields, models
from odoo.tools import float_utils
import datetime

class StockBalanceReport(models.AbstractModel):
    _name = 'report.guazu_stock.report_stock_balance'

    @api.model
    def get_lines(self, category_ids, location_ids, attribute_value_ids,
                                    product_color_ids, product_sex_ids, product_material_ids, start_date, end_date,
                                    product_template_ids,show_variants, access_price):
        if location_ids:
            locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        else:
            locations = self.env["guazu.stock.location"].search([('type', '=', 'storage')])

        res = []
        where_date = ""
        if start_date:
            where_date = """ and date <= '""" + start_date +"""'"""
        if start_date and end_date:
            where_date = """ and date <= '""" + end_date + """' and date >= '""" + start_date + """'"""
        elif start_date:
            where_date = """ and date >= '""" + start_date + """'"""
        elif end_date:
            where_date = """ and date <= '""" + end_date + """'"""
        # where = " AND TRUE"
        where=" TRUE "
        cat_ids = self.get_category_ids(category_ids)
        if len(cat_ids) > 1:
            where += " and cat.id in " + str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where += " and cat.id = " + str(cat_ids[0])

        if len(attribute_value_ids) > 1:
            show_variants = True
            where += " and attribute_value.id in " + str(tuple(attribute_value_ids))
        if len(attribute_value_ids) == 1:
            show_variants = True
            where += " and attribute_value.id = " + str(attribute_value_ids[0])

        if len(product_template_ids) > 1:
            where += " and template.id in " + str(tuple(product_template_ids))
        if len(product_template_ids) == 1:
            where += " and template.id = " + str(product_template_ids[0])

        if len(product_color_ids) > 1:
            where += " and color.id in " + str(tuple(product_color_ids))
        if len(product_color_ids) == 1:
            where += " and color.id = " + str(product_color_ids[0])

        if len(product_sex_ids) > 1:
            where += " and sex.id in " + str(tuple(product_sex_ids))
        if len(product_sex_ids) == 1:
            where += " and sex.id = " + str(product_sex_ids[0])

        if len(product_material_ids) > 1:
            where += " and material.id in " + str(tuple(product_material_ids))
        if len(product_material_ids) == 1:
            where += " and material.id = " + str(product_material_ids[0])
        model="product.template" if not show_variants else "product.product"
        data = []
        sex_ = ""
        cat_ = ""
        sql_initial_no_variant, sql_initial_variant, sql_in_out_no_variant, sql_in_out_variant, sql_final_no_variant, sql_final_variant = '','','','','', ''
        for location in locations:
            products = []
            # initial
            if start_date:
                if not show_variants:
                    sql_initial_no_variant="""SELECT product_tmpl_id, 
                      anlys.categ_id, 
                      anlys.uom_id, 
                      sum(quantity) as initial_qty,
                      sum(amount) as initial_balance,
                      0.0 as in_qty,  
                      0.0 as in_balance, 
                      0.0 as out_qty,
                      0.0 as out_balance,
                      0.0 as final_qty,
                      0.0 as final_balance,
                      cat.name as category,
                      '' as attr, 
                      sex.name as sexo
                        from guazu_existence_analysis_report anlys
                            LEFT JOIN product_template template ON (anlys.product_tmpl_id=template.id)
                            LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                            LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                            LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                            LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                            LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                            LEFT JOIN product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=anlys.product_id)
                            LEFT JOIN product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                        where
                            anlys.location_id = """ + str(location.id)+""" and
                            date < '""" + start_date + """' AND """ + where + """ 
                        group by product_tmpl_id, anlys.categ_id, anlys.uom_id, template.default_code, cat.name, sex.name
                        """
                else:
                    sql_initial_variant="""SELECT product_id as product_tmpl_id, anlys.categ_id, anlys.uom_id, sum(quantity) as initial_qty, 
                                               sum(amount) as initial_balance,template.default_code as default_code, 
                                               cat.name as category, COALESCE (attribute_value.name,'') as attr, sex.name as sexo
                                            from guazu_existence_analysis_report anlys
                                                LEFT JOIN product_template template ON (anlys.product_tmpl_id=template.id)
                                                LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                                                LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                                                LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                                                LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                                                LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                                                LEFT JOIN product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=anlys.product_id)
                                                LEFT JOIN product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                                            where
                                                anlys.location_id = """ + str(location.id) + """ and
                                                date < '""" + start_date + """' AND """ + where + """ 
                                            group by product_id, anlys.categ_id, anlys.uom_id, template.default_code, cat.name,  
                                                     attribute_value.name, sex.name
                                            order by sex.name desc, cat.name asc,template.default_code asc,attribute_value.name asc"""

            # in / out
            if not show_variants:
                sql_in_out_no_variant="""SELECT product_tmpl_id, 
                                      anlys.categ_id, 
                                      anlys.uom_id, 
                                      0.0 as initial_qty,
                                      0.0 as initial_balance,
                                      sum(in_qty) as in_qty,  
                                      sum(in_amount) as in_balance, 
                                      sum(out_qty) as out_qty,
                                      sum(out_amount) as out_balance,
                                      0.0 as final_qty,
                                      0.0 as final_balance,
                                      cat.name as category, 
                                      '' as attr,sex.name as sexo
                                     from guazu_existence_analysis_report anlys
                                        LEFT JOIN product_template template ON (anlys.product_tmpl_id=template.id)
                                        LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                                        LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                                        LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                                        LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                                        LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                                        LEFT JOIN product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=anlys.product_id)
                                        LEFT JOIN product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                                     where
                                         anlys.location_id = """ + str(location.id) + where_date + """ AND """ +where + """ 
                                     group by product_tmpl_id, anlys.categ_id, anlys.uom_id, template.default_code, cat.name, sex.name
                                     """
            else:
                sql_in_out_variant="""SELECT product_id as product_tmpl_id, anlys.categ_id, anlys.uom_id, sum(in_qty) as in_qty,  sum(in_amount) as in_balance, sum(out_qty) as out_qty,
                                                    sum(out_amount) as out_balance,cat.name as category, 
                                                    COALESCE (attribute_value.name,'') as attr, sex.name as sexo
                                                 from guazu_existence_analysis_report anlys
                                                    LEFT JOIN product_template template ON (anlys.product_tmpl_id=template.id)
                                                    LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                                                    LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                                                    LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                                                    LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                                                    LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                                                    LEFT JOIN product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=anlys.product_id)
                                                    LEFT JOIN product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                                                 where
                                                     anlys.location_id = """ + str(location.id) + where_date + """ AND """ + where + """ 
                                                 group by product_id, anlys.categ_id, anlys.uom_id, template.default_code, cat.name, 
                                                          attribute_value.name, sex.name
                                                  order by sex.name desc,cat.name asc ,template.default_code asc,attribute_value.name asc"""

            # final
            where_date = ""
            final = []

            if not end_date:
                end_date=datetime.datetime.now().strftime("%Y-%m-%d")
            where_date = """ and date <= '""" + end_date +"""'"""
            if not show_variants:
                sql_final_no_variant="""SELECT product_tmpl_id, 
                                       anlys.categ_id, 
                                       anlys.uom_id, 
                                       0.0 as initial_qty,
                                       0.0 as initial_balance, 
                                       0.0 as in_qty,
                                       0.0 as in_balance,
                                       0.0 as out_qty, 
                                       0.0 as out_balace,
                                       sum(quantity) as final_qty, 
                                       sum(amount) as final_balance,
                                       cat.name as category,
                                       '' as attr, 
                                       sex.name as sexo
                                    from guazu_existence_analysis_report anlys
                                        LEFT JOIN product_template template ON (anlys.product_tmpl_id=template.id)
                                        LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                                        LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                                        LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                                        LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                                        LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                                        LEFT JOIN product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=anlys.product_id)
                                        LEFT JOIN product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                                    where
                                        anlys.location_id = """ + str(location.id)  + where_date + """ AND """+where + """
                                    group by product_tmpl_id, anlys.categ_id, anlys.uom_id, sex.name, cat.name
                                    """
            else:
                sql_final_variant="""SELECT product_id as product_tmpl_id, anlys.categ_id, anlys.uom_id, sum(in_qty) as in_qty, sum(out_qty) as out_qty, 
                                       sum(quantity) as final_qty, sum(amount) as final_balance, COALESCE (attribute_value.name,'') as attr,
                                       sex.name as sexo
                                                from guazu_existence_analysis_report anlys
                                                    LEFT JOIN product_template template ON (anlys.product_tmpl_id=template.id)
                                                    LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                                                    LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                                                    LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                                                    LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                                                    LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                                                    LEFT JOIN product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=anlys.product_id)
                                                    LEFT JOIN product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                                                where
                                                    anlys.location_id = """ + str(location.id) + where_date + """ AND """ + where + """
                                                group by product_id, anlys.categ_id, anlys.uom_id, attribute_value.name, cat.name, template.default_code, sex.name
                                                        order by sex.name desc, cat.name asc ,template.default_code asc,attribute_value.name asc"""

            if not show_variants:
                if sql_initial_no_variant.__len__()!=0:
                    sql=sql_initial_no_variant + " union all "+ sql_in_out_no_variant + " union all "+sql_final_no_variant
                else:
                    sql=sql_in_out_no_variant + " union all " + sql_final_no_variant
                sql_final = """select
                                        datas.product_tmpl_id, datas.categ_id,
                                        datas.uom_id,
                                        sum(datas.initial_qty) as initial_qty,
                                        sum(datas.initial_balance) as initial_balance,
                                        sum(datas.in_qty) as in_qty,
                                        sum(datas.in_balance) as in_balance,
                                        sum(datas.out_qty) as out_qty,
                                        sum(datas.out_balance) as out_balance,
                                        sum(datas.final_qty) as final_qty,
                                        sum(datas.final_balance) as final_balance,
                                        datas.category as category,
                                        datas.attr, datas.sexo
                                        from (""" + sql + """) as datas group by product_tmpl_id, categ_id, uom_id, sexo, category, attr
                                       order by sexo desc, category asc, product_tmpl_id asc"""
                self.env.cr.execute(sql_final)
                final = self.env.cr.dictfetchall()
            else:
                if sql_initial_variant.__len__()!=0:
                    sql=sql_initial_variant + " union all "+ sql_in_out_variant + " union all "+sql_final_variant
                else:
                    sql=sql_in_out_variant + " union all " + sql_final_variant

            for line in final:
                name = self.env[model].browse(line['product_tmpl_id']).name if line['attr'].__len__() == 0 else \
                self.env[model].browse(line['product_tmpl_id']).name + " (" + line['attr'] + ")"
                uom = self.env['product.uom'].browse(line['uom_id']).name
                products.append({
                    'name': name,
                    'id': line['product_tmpl_id'],
                    'uom': uom,
                    'uom_id': line['uom_id'],
                    'initial_qty': float_utils.float_repr(float_utils.float_round(line['initial_qty'], 3), 3),
                    'initial_balance': float_utils.float_repr(float_utils.float_round(line['initial_balance']/1000, 2), 2),
                    'in_qty': float_utils.float_repr(float_utils.float_round(line['in_qty'], 3), 3),
                    'in_balance':  float_utils.float_repr(float_utils.float_round(line['in_balance']/1000, 2), 2),
                    'out_qty': float_utils.float_repr(float_utils.float_round(line['out_qty'], 3), 3),
                    'out_balance': float_utils.float_repr(float_utils.float_round(line['out_balance']/1000, 2), 2),
                    'final_qty': float_utils.float_repr(float_utils.float_round(line['final_qty'], 3), 3),
                    'final_balance': float_utils.float_repr(float_utils.float_round(line['final_balance']/1000, 2), 2),
                    'sexo': line['sexo'],
                    'category': line['category']
                })

            if products:
                # total categoria
                t_cat_initial_qty = 0
                t_cat_initial_balance = 0
                t_cat_in_qty = 0
                t_cat_in_balance = 0
                t_cat_out_qty = 0
                t_cat_out_balance = 0
                t_cat_final_qty = 0
                t_cat_final_balance = 0
                #total sexo
                t_sex_initial_qty = 0
                t_sex_initial_balance = 0
                t_sex_in_qty = 0
                t_sex_in_balance = 0
                t_sex_out_qty = 0
                t_sex_out_balance = 0
                t_sex_final_qty = 0
                t_sex_final_balance = 0

                #total general
                t_initial_qty = 0
                t_initial_balance = 0
                t_in_qty = 0
                t_in_balance = 0
                t_out_qty = 0
                t_out_balance = 0
                t_final_qty = 0
                t_final_balance = 0

                sex_=""
                cat_=""
                data=[]
                for k in products:
                    if sex_ == "":
                        sex_ = k['sexo']
                    if cat_ == "":
                        cat_ = k['category']
                    if cat_ != k['category']:
                        data.append({
                            'name': 'Total ' + cat_,
                            'id': k['id'],
                            'uom': k['uom'],
                            'uom_id': k['uom_id'],
                            'initial_qty': float_utils.float_repr(float_utils.float_round(t_cat_initial_qty, 3), 3),
                            'initial_balance': float_utils.float_repr(float_utils.float_round(t_cat_initial_balance, 2), 2),
                            'in_qty': float_utils.float_repr(float_utils.float_round(t_cat_in_qty, 3), 3),
                            'in_balance': float_utils.float_repr(float_utils.float_round(t_cat_in_balance, 2), 2),
                            'out_qty': float_utils.float_repr(float_utils.float_round(t_cat_out_qty, 3), 3),
                            'out_balance': float_utils.float_repr(float_utils.float_round(t_cat_out_balance, 2), 2),
                            'final_qty': float_utils.float_repr(float_utils.float_round(t_cat_final_qty, 3), 3),
                            'final_balance': float_utils.float_repr(float_utils.float_round(t_cat_final_balance, 2), 2),
                            'is_total':True
                        })

                        t_cat_initial_qty = 0
                        t_cat_initial_balance = 0
                        t_cat_in_qty = 0
                        t_cat_in_balance = 0
                        t_cat_out_qty = 0
                        t_cat_out_balance = 0
                        t_cat_final_qty = 0
                        t_cat_final_balance = 0
                        cat_ = k['category']
                    if sex_ != k['sexo']:
                        data.append({
                            'name': 'Total Sin Sexo' if sex_ ==  None else 'Total ' + sex_,
                            'id': k['id'],
                            'uom': k['uom'],
                            'uom_id': k['uom_id'],
                            'initial_qty': float_utils.float_repr(float_utils.float_round(t_sex_initial_qty, 3), 3),
                            'initial_balance': float_utils.float_repr(float_utils.float_round(t_sex_initial_balance, 2),2),
                            'in_qty': float_utils.float_repr(float_utils.float_round(t_sex_in_qty, 3), 3),
                            'in_balance': float_utils.float_repr(float_utils.float_round(t_sex_in_balance, 2),2),
                            'out_qty': float_utils.float_repr(float_utils.float_round(t_sex_out_qty, 3), 3),
                            'out_balance': float_utils.float_repr(float_utils.float_round(t_sex_out_balance, 2),2),
                            'final_qty': float_utils.float_repr(float_utils.float_round(t_sex_final_qty, 3), 3),
                            'final_balance': float_utils.float_repr(float_utils.float_round(t_sex_final_balance, 2),2),
                            'is_total':True
                        })

                        t_sex_initial_qty = 0
                        t_sex_initial_balance = 0
                        t_sex_in_qty = 0
                        t_sex_in_balance = 0
                        t_sex_out_qty = 0
                        t_sex_out_balance = 0
                        t_sex_final_qty = 0
                        t_sex_final_balance = 0
                        sex_ = k['sexo']

                    # total categoria
                    t_cat_initial_qty += float(k['initial_qty'])
                    t_cat_initial_balance += float(k['initial_balance'])
                    t_cat_in_qty += float(k['in_qty'])
                    t_cat_in_balance += float(k['in_balance'])
                    t_cat_out_qty += float(k['out_qty'])
                    t_cat_out_balance += float(k['out_balance'])
                    t_cat_final_qty += float(k['final_qty'])
                    t_cat_final_balance += float(k['final_balance'])
                    # total sexo
                    t_sex_initial_qty += float(k['initial_qty'])
                    t_sex_initial_balance += float(k['initial_balance'])
                    t_sex_in_qty += float(k['in_qty'])
                    t_sex_in_balance += float(k['in_balance'])
                    t_sex_out_qty += float(k['out_qty'])
                    t_sex_out_balance += float(k['out_balance'])
                    t_sex_final_qty += float(k['final_qty'])
                    t_sex_final_balance += float(k['final_balance'])

                    #total general
                    t_initial_qty += float(k['initial_qty'])
                    t_initial_balance += float(k['initial_balance'])
                    t_in_qty += float(k['in_qty'])
                    t_in_balance += float(k['in_balance'])
                    t_out_qty += float(k['out_qty'])
                    t_out_balance += float(k['out_balance'])
                    t_final_qty += float(k['final_qty'])
                    t_final_balance += float(k['final_balance'])
                    data.append({
                        'name': k['name'],
                        'id': k['id'],
                        'uom': k['uom'],
                        'uom_id': k['uom_id'],
                        'initial_qty': k['initial_qty'],
                        'initial_balance': k['initial_balance'],
                        'in_qty': k['in_qty'],
                        'in_balance': k['in_balance'],
                        'out_qty': k['out_qty'],
                        'out_balance': k['out_balance'],
                        'final_qty': k['final_qty'],
                        'final_balance': k['final_balance'],
                        'is_total': False
                    })
                data.append({
                    'name': 'Total ' + cat_,
                    'id': k['id'],
                    'uom': k['uom'],
                    'uom_id': k['uom_id'],
                    'initial_qty': float_utils.float_repr(float_utils.float_round(t_cat_initial_qty, 3), 3),
                    'initial_balance': float_utils.float_repr(float_utils.float_round(t_cat_initial_balance, 2), 2),
                    'in_qty': float_utils.float_repr(float_utils.float_round(t_cat_in_qty, 3), 3),
                    'in_balance': float_utils.float_repr(float_utils.float_round(t_cat_in_balance, 2), 2),
                    'out_qty': float_utils.float_repr(float_utils.float_round(t_cat_out_qty, 3), 3),
                    'out_balance': float_utils.float_repr(float_utils.float_round(t_cat_out_balance, 2), 2),
                    'final_qty': float_utils.float_repr(float_utils.float_round(t_cat_final_qty, 3), 3),
                    'final_balance': float_utils.float_repr(float_utils.float_round(t_cat_final_balance, 2), 2),
                    'is_total': True
                })
                data.append({
                    'name': 'Total Sin Sexo' if sex_ == None else 'Total ' + sex_,
                    'id': k['id'],
                    'uom': k['uom'],
                    'uom_id': k['uom_id'],
                    'initial_qty': float_utils.float_repr(float_utils.float_round(t_sex_initial_qty, 3), 3),
                    'initial_balance': float_utils.float_repr(float_utils.float_round(t_sex_initial_balance, 2), 2),
                    'in_qty': float_utils.float_repr(float_utils.float_round(t_sex_in_qty, 3), 3),
                    'in_balance': float_utils.float_repr(float_utils.float_round(t_sex_in_balance, 2), 2),
                    'out_qty': float_utils.float_repr(float_utils.float_round(t_sex_out_qty, 3), 3),
                    'out_balance': float_utils.float_repr(float_utils.float_round(t_sex_out_balance, 2), 2),
                    'final_qty': float_utils.float_repr(float_utils.float_round(t_sex_final_qty, 3), 3),
                    'final_balance': float_utils.float_repr(float_utils.float_round(t_sex_final_balance, 2), 2),
                    'is_total': True
                })

                data.append({
                    'name': 'Total General',
                    'id': k['id'],
                    'uom': k['uom'],
                    'uom_id': k['uom_id'],
                    'initial_qty': float_utils.float_repr(float_utils.float_round(t_initial_qty, 3), 3),
                    'initial_balance': float_utils.float_repr(float_utils.float_round(t_initial_balance, 2), 2),
                    'in_qty': float_utils.float_repr(float_utils.float_round(t_in_qty, 3), 3),
                    'in_balance': float_utils.float_repr(float_utils.float_round(t_in_balance, 2), 2),
                    'out_qty': float_utils.float_repr(float_utils.float_round(t_out_qty, 3), 3),
                    'out_balance': float_utils.float_repr(float_utils.float_round(t_out_balance, 2), 2),
                    'final_qty': float_utils.float_repr(float_utils.float_round(t_final_qty, 3), 3),
                    'final_balance': float_utils.float_repr(float_utils.float_round(t_final_balance, 2), 2),
                    'is_total': True
                })
            res.append({'location': location.name_get()[0][1], 'products': data})
        return res

    def get_category_ids(self, category_ids):
        cat_ids = []
        for cat in category_ids:
            cat_ids.append(cat)
            category = self.env["product.category"].browse(cat)
            children_ids = []
            for child in category.child_id:
                children_ids.append(child.id)
            cat_ids += self.get_category_ids(children_ids)
        return cat_ids


    @api.model
    def get_locations(self, location_ids):
        if not location_ids:
            return ['Todos los almacenes']

        locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        res = []
        for loc in locations:
            res.append(loc.name)

        return res

    @api.model
    def get_products(self, product_ids):
        if not product_ids:
            return ['Todos los productos']
        products = self.env["product.product"].search([('id', 'in', product_ids)])
        res = []
        for prod in products:
            res.append(prod.name)
        return res

    @api.model
    def get_product_templates(self, product_template_ids):
        if not product_template_ids:
            return ['Todos los productos']
        products = self.env["product.template"].search([('id', 'in', product_template_ids)])
        res = []
        for prod in products:
            res.append(prod.name)
        return res

    @api.model
    def get_attributes(self, attribute_value_ids):
        if not attribute_value_ids:
            return ['Todos los atributos']

        attributes = self.env["product.attribute.value"].search([('id', 'in', attribute_value_ids)])
        res = []
        for att in attributes:
            res.append(att.name_get()[0][1])

        return res

    @api.model
    def get_colors(self, product_color_ids):
        if not product_color_ids:
            return ['Todos los colores']
        colors = self.env["guazu.product.color"].search([('id', 'in', product_color_ids)])
        res = []
        for color in colors:
            res.append(color.name_get()[0][1])
        return res

    @api.model
    def get_sexs(self, product_sex_ids):
        if not product_sex_ids:
            return ['Todos los sexos']

        sexs = self.env["guazu.product.sex"].search([('id', 'in', product_sex_ids)])
        res = []
        for sex in sexs:
            res.append(sex.name_get()[0][1])

        return res

    @api.model
    def get_materials(self, product_material_ids):
        if not product_material_ids:
            return ['Todos los materiales']

        materials = self.env["guazu.product.material"].search([('id', 'in', product_material_ids)])
        res = []
        for material in materials:
            res.append(material.name_get()[0][1])

        return res

    @api.model
    def get_categories(self, category_ids):
        if not category_ids:
            return ['Todos los productos']
        categories = self.env["product.category"].search([('id', 'in', category_ids)])
        res = []
        for cat in categories:
            res.append(cat.name)
        return res

    @api.model
    def get_report_values(self, docids, data=None):
        category_ids = data['form']['category_ids']
        location_ids = data['form']['location_ids']
        attribute_value_ids = data['form']['attribute_value_ids']
        product_color_ids = data['form']['product_color_ids']
        product_sex_ids = data['form']['product_sex_ids']
        # product_ids = data['form']['product_ids']
        product_template_ids = data['form']['product_template_ids']
        product_material_ids = data['form']['product_material_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        access_price =  data['access_price']
        # if access_price:
        #     access_price = data['form']['show_import']

        return {
            'data': data,
            'categories': self.get_categories(category_ids),
            'locations': self.get_locations(location_ids),
            'attributes': self.get_attributes(attribute_value_ids),
            'colors': self.get_colors(product_color_ids),
            'sexs': self.get_sexs(product_sex_ids),
            # 'products': self.get_products(product_ids),
            'product_template': self.get_product_templates(product_template_ids),
            'materials': self.get_materials(product_material_ids),
            'start_date': start_date,
            'end_date': end_date,
            'show_variants': show_variants,
			'access_price': access_price,
            'lines': self.get_lines(category_ids, location_ids, attribute_value_ids,
                                    product_color_ids, product_sex_ids, product_material_ids, start_date, end_date,
                                    product_template_ids,show_variants,access_price)
        }
    
    @api.model
    def render_html(self, docids, data=None):
        category_ids = data['form']['category_ids']
        location_ids = data['form']['location_ids']
        attribute_value_ids = data['form']['attribute_value_ids']
        product_color_ids = data['form']['product_color_ids']
        product_sex_ids = data['form']['product_sex_ids']
        product_material_ids = data['form']['product_material_ids']
        product_template_ids = data['form']['product_template_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        show_variants = data['form']['show_variants']
        access_price =  data['access_price']
        # if access_price:
        #     access_price = data['form']['show_import']
        docargs = {
            'data': data,
            'categories': self.get_categories(category_ids),
            'locations': self.get_locations(location_ids),
            'attributes': self.get_attributes(attribute_value_ids),
            'colors': self.get_colors(product_color_ids),
            'sexs': self.get_sexs(product_sex_ids),
            'materials': self.get_materials(product_material_ids),
            # 'products': self.get_products(product_ids),
            'product_templates': self.get_product_templates(product_template_ids),
            'start_date': start_date,
            'end_date': end_date,
            'show_variants' : show_variants,
			'access_price': access_price,
            'lines': self.get_lines(category_ids, location_ids, attribute_value_ids,
                                    product_color_ids, product_sex_ids, product_material_ids, start_date, end_date,
                                    product_template_ids,show_variants, access_price)
        }
        return self.env['report'].render('guazu_stock.report_stock_balance', values=docargs)