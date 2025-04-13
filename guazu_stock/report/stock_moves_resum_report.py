from odoo import api, fields, models
from odoo.tools import float_utils
from datetime import datetime, timedelta


class StockMovesLocationReport(models.AbstractModel):
    _name = 'report.guazu_stock.report_stock_moves_resum'

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
    def get_lines(self, category_ids, location_ids, product_sex_ids,group_by):
        where=""
        if group_by == 'sex':
            category_ids = []
        elif group_by == 'categ':
            product_sex_ids = []
        else:
            category_ids = []
            product_sex_ids = []


        # obtener todos los productos que cumplan los atributos, colores, sexos, materiales y las categorias
        cat_ids = self.get_category_ids(category_ids)
        if len(cat_ids) > 1:
            where = " cat.id in "+str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where = " cat.id = " + str(cat_ids[0])

        if len(product_sex_ids) > 1:
            where += " and sexo.id in " + str(tuple(product_sex_ids))
        if len(product_sex_ids) == 1:
            where += " and sexo.id = " + str(product_sex_ids[0])
        if len(location_ids)==0:
            locations = self.env["guazu.stock.location"].search([])
            location_ids = [l.id for l in locations]

        where = " sm.state = 'done' "

        if len(location_ids) > 1:
            where += " and (sm.location_id in " + str(tuple(location_ids)) + " or  sm.location_dest_id in " + str(tuple(location_ids))+")"
        if len(location_ids) == 1:
            where += " and (sm.location_id = " + str(location_ids[0]) + " or sm.location_dest_id = "+str(location_ids[0])+")"

        cat_ids = self.get_category_ids(category_ids)
        if len(cat_ids) > 1:
            where += " and cat.id in " + str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where += " and cat.id = " + str(cat_ids[0])

        if len(product_sex_ids) > 1:
            where += " and sexo.id in " + str(tuple(product_sex_ids))
        if len(product_sex_ids) == 1:
            where += " and sexo.id = " + str(product_sex_ids[0])

        if group_by == "sex":
            self.env.cr.execute("""
                        SELECT sm.name as name,sm.done_date as date,loc.name as location_name,loc2.name as location_dest_name,
                        case when sexo.name is not null then
                           sexo.name
                        else 'Sin Sexo' end as campo_agrupar,
                        case when sm.location_dest_id = """+ str(location_ids[0])+ """ then
			              sum(coalesce(l.quantity,0.00)) 
			            end as quantity_in,
                        case when sm.location_dest_id <> """+ str(location_ids[0])+  """ then
                          sum(coalesce(l.quantity,0.00)) 
                        end as quantity_out,
                        case when sm.location_dest_id = """+ str(location_ids[0])+""" then
                          loc.name 
                        else loc2.name end as clave,
                        case when sm.location_dest_id = """+ str(location_ids[0])+  """ then
			              0 
                         else  1 end as es_salida                      
	                FROM
                        guazu_stock_move as sm inner join
                        guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                        guazu_stock_location loc on sm.location_id = loc.id inner join
                        guazu_stock_location loc2 on sm.location_dest_id = loc2.id inner join 
                        product_product as p on l.product_id = p.id inner join
                        product_template as template on template.id = p.product_tmpl_id left outer join
                        guazu_product_sex as sexo on template.sex_id = sexo.id 
                        where """ + where + """ 
                       group by sm.name,sm.done_date,
                        sm.location_id,
                        sm.location_dest_id,
                        loc.name, template.sex_id,
                        loc2.name, sexo.name
                        order by sexo.name,sm.done_date, case when sm.location_dest_id = """+ str(location_ids[0])+  """ then
			              0 
                         else  1 end,sm.name asc
                            """)
        elif group_by == 'categ':
            self.env.cr.execute("""
                        SELECT sm.name as name,sm.done_date as date,loc.name as location_name,loc2.name as location_dest_name,
                        case when cat.name is not null then
                           cat.name
                        else 'Sin Categoria' end as campo_agrupar,
                        case when sm.location_dest_id = """+ str(location_ids[0])+ """ then
			              sum(coalesce(l.quantity,0.00))  
			            end as quantity_in,
                        case when sm.location_dest_id <> """+ str(location_ids[0])+ """ then
                          sum(coalesce(l.quantity,0.00))  
                        end as quantity_out,
                        case when sm.location_dest_id = """+ str(location_ids[0])+ """ then
                          loc.name 
                        else loc2.name end as clave,
                        case when sm.location_dest_id = """+ str(location_ids[0])+  """ then
			              0 
                         else  1 end as es_salida                      
	                FROM
                        guazu_stock_move as sm inner join
                        guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                        guazu_stock_location loc on sm.location_id = loc.id inner join
                        guazu_stock_location loc2 on sm.location_dest_id = loc2.id inner join 
                        product_product as p on l.product_id = p.id inner join
                        product_template as template on template.id = p.product_tmpl_id left outer join
                        product_category as cat on template.categ_id = cat.id 
                        where """ + where + """ 
                       group by sm.name,sm.done_date,
                        sm.location_id,
                        sm.location_dest_id,
                        loc.name, template.categ_id,
                        loc2.name, cat.name
                        order by cat.name,sm.done_date,sm.name asc
                            """)

        move_lines = self.env.cr.dictfetchall()
        field_key = ''
        saldo = 0.0
        products = []
        res = []
        pk = 0
        t_in = 0.0
        t_out = 0.0
        t_existence = 0.0
        total_general_in = 0.0
        total_general_out = 0.0
        total_general_existence = 0.0

        for line in move_lines:
            pk += 1
            if field_key.__len__() == 0:
                field_key = line['campo_agrupar']
            if field_key == line['campo_agrupar']:
                t_in += float_utils.float_round(0.00 if line['quantity_in']==None else line['quantity_in'], 3)
                t_out += float_utils.float_round(0.00 if line['quantity_out'] == None else line['quantity_out'], 3)
                saldo = saldo + float_utils.float_round(0.00 if line['quantity_in']==None else line['quantity_in'], 3)- float_utils.float_round(0.00 if line['quantity_out']==None else line['quantity_out'], 3)
                t_existence = saldo

            else:
                products.append({
                    'name': 'Total ' + field_key,
                    'fecha': '',
                    'in_qty': t_in,
                    'out_qty': t_out,
                    'group': '',
                    'clave': '',
                    'saldo': t_existence,
                    'is_total_grupo': True
                })
                total_general_in += t_in
                total_general_out += t_out
                total_general_existence += t_existence

                t_in = float_utils.float_round(0.00 if line['quantity_in'] == None else line['quantity_in'], 3)
                t_out = float_utils.float_round(0.00 if line['quantity_out'] == None else line['quantity_out'], 3)
                saldo = float_utils.float_round(0.00 if line['quantity_in']==None else line['quantity_in'], 3) + float_utils.float_round(0.00 if line['quantity_out']== None else line['quantity_out'], 3)
                t_existence = saldo
                field_key = line['campo_agrupar']



            products.append({
                'name': line['name'],
                'fecha': line['date'],
                'in_qty': float_utils.float_repr(float_utils.float_round(0.00 if line['quantity_in']==None else line['quantity_in'] , 3), 3),
                'out_qty': float_utils.float_repr(float_utils.float_round(0.00 if line['quantity_out']==None else line['quantity_out'], 3), 3),
                'group': line['campo_agrupar'],
                'clave':line['clave'],
                'saldo': float_utils.float_repr(saldo,3),
                'is_total_grupo': False
            })
        products.append({
            'name': 'Total ' + field_key,
            'fecha': '',
            'in_qty': t_in,
            'out_qty': t_out,
            'group': '',
            'clave': '',
            'saldo': t_existence,
            'is_total_grupo': True
        })
        total_general_in += t_in
        total_general_out += t_out
        total_general_existence += t_existence
        products.append({
            'name': 'Total General ',
            'fecha': '',
            'in_qty': total_general_in,
            'out_qty': total_general_out,
            'group': '',
            'clave': '',
            'saldo': total_general_existence,
            'is_total_grupo': True
        })
        res.append({'products': products})
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
    def get_locations(self, location_ids):
        locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        res = []
        for loc in locations:
            res.append(loc.name)
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
    def get_report_values(self, docids, data=None):
        category_ids = data['form']['category_ids']
        location_ids = data['form']['location_ids']
        group_by = data['form']['show']
        product_sex_ids = data['form']['product_sex_ids']

        return {
            'data': data,
            'group_by': group_by,
            'categories': self.get_categories(category_ids),
            'locations': self.get_locations(location_ids),
            'sexs': self.get_sexs(product_sex_ids),
            'lines': self.get_lines(category_ids, location_ids, product_sex_ids, group_by)
        }

    @api.model
    def render_html(self, docids, data=None):
        category_ids = data['form']['category_ids']
        location_ids = data['form']['location_ids']
        group_by = data['form']['group_by']
        product_sex_ids = data['form']['product_sex_ids']
        docargs = {
            'data': data,
            'group_by' : data['form']['group_by'],
            'categories': self.get_categories(category_ids),
            'locations': self.get_locations(location_ids),
            'sexs': self.get_sexs(product_sex_ids),
            'date_print': datetime.now().strftime("%d-%m-%Y"),
            'lines': self.get_lines(category_ids, location_ids, product_sex_ids, group_by)
        }
        return self.env['report'].render('guazu_stock.report_stock_moves_resum', values=docargs)