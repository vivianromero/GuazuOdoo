from odoo import api, fields, models
from odoo.tools import float_utils


class StockBalanceCatReport(models.AbstractModel):
    _name = 'report.guazu_stock.report_stock_balance_cat'

           
    @api.model
    def get_lines(self, location_ids, start_date, end_date,category_ids,access_price):
        if location_ids:
            locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        else:
            locations = self.env["guazu.stock.location"].search([('type', '=', 'storage')])

        cat_ids = self.get_category_ids(category_ids)
        where_cat=""
        if len(cat_ids) > 1:
            where_cat += " and categ.id in " + str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where_cat += " and categ.id = " + str(cat_ids[0])
        res = []

        for location in locations:
            categories = []
            sexo_cat = []
            # initial
            if start_date:
                self.env.cr.execute("""SELECT categ_id, sum(quantity) as initial_qty, sum(amount) as initial_balance, 
                    coalesce(sex,0) as sex,coalesce(categ.name,'') as categ_name, coalesce(psex.name,'') as sex_name 
                    from guazu_existence_analysis_report analy
                       LEFT JOIN product_category categ on analy.categ_id=categ.id
                       LEFT JOIN guazu_product_sex psex on analy.sex=psex.id 
                        where location_id = """ + str(location.id)+""" and
                        date < '""" + start_date +"""'"""+ where_cat + """
                    group by categ_id, sex, categ.name, psex.name
                    order by psex.name,categ.name asc""")
                initial = self.env.cr.dictfetchall()
            else:
                initial = []

            for line in initial:
                # name = self.env['product.category'].browse(line['categ_id']).name
                # sexo = "" if line['sex']== 0 else "-"+self.env['guazu.product.sex'].browse(line['sex']).name
                name = line['categ_name']
                sexo = line['sex_name']
                if not sexo in sexo_cat:
                    sexo_cat.append(line['sex_name'])

                categories.append({
                    'name_search': name if sexo.__len__()==0 else name+"-"+sexo,
                    'name':name,
                    'sexo':sexo,
                    'id': line['categ_id'],
                    'initial_qty': float_utils.float_repr(float_utils.float_round(line['initial_qty'], 3), 3), 
                    'initial_balance': float_utils.float_repr(float_utils.float_round(line['initial_balance']/1000, 2), 2),
                    'in_qty': '0.000', 
                    'in_balance': '0.00',
                    'out_qty': '0.000', 
                    'out_balance': '0.00',
                    'final_qty': '0.000', 
                    'final_balance': '0.00'
                })
            # in / out
            if start_date and end_date:
                self.env.cr.execute("""SELECT categ_id, sum(in_qty) as in_qty, sum(in_amount) as in_balance, sum(out_qty) as out_qty, sum(out_amount) as out_balance, 
                                      coalesce(sex,0) as sex,coalesce(categ.name,'') as categ_name, coalesce(psex.name,'') as sex_name
                                    from guazu_existence_analysis_report analy
                                       LEFT JOIN product_category categ on analy.categ_id=categ.id
                                       LEFT JOIN guazu_product_sex psex on analy.sex=psex.id
                                       where
                                        location_id = """ + str(location.id)+""" and
                                        date <= '""" + end_date +"""' and
                                        date >= '""" + start_date +"""'""" + where_cat + """
                                    group by categ_id, sex, categ.name, psex.name
                                    order by psex.name,categ.name asc""")
                moves = self.env.cr.dictfetchall()
            elif start_date:
                self.env.cr.execute("""SELECT categ_id, sum(in_qty) as in_qty, sum(in_amount) as in_balance, sum(out_qty) as out_qty, 
                    sum(out_amount) as out_balance, coalesce(sex,0) as sex,coalesce(categ.name,'') as categ_name, coalesce(psex.name,'') as sex_name 
                    from guazu_existence_analysis_report analy
                      LEFT JOIN product_category categ on analy.categ_id=categ.id
                      LEFT JOIN guazu_product_sex psex on analy.sex=psex.id
                    where
                        location_id = """ + str(location.id)+""" and
                        date >= '""" + start_date +"""'""" + where_cat + """
                     group by categ_id, sex, categ.name, psex.name
                                    order by psex.name,categ.name asc""")
                moves = self.env.cr.dictfetchall()
            elif end_date:
                self.env.cr.execute("""SELECT categ_id, sum(in_qty) as in_qty, sum(in_amount) as in_balance, sum(out_qty) as out_qty, 
                      sum(out_amount) as out_balance, coalesce(sex,0) as sex,coalesce(categ.name,'') as categ_name, coalesce(psex.name,'') as sex_name 
                    from guazu_existence_analysis_report analy
                      LEFT JOIN product_category categ on analy.categ_id=categ.id
                      LEFT JOIN guazu_product_sex psex on analy.sex=psex.id
                    where
                        location_id = """ + str(location.id)+""" and
                        date <= '""" + end_date +"""'""" + where_cat + """ 
                   group by categ_id, sex, categ.name, psex.name
                                    order by psex.name,categ.name asc""")
                moves = self.env.cr.dictfetchall()
            else:
                self.env.cr.execute("""SELECT categ_id, sum(in_qty) as in_qty,  sum(in_amount) as in_balance, sum(out_qty) as out_qty, 
                      sum(out_amount) as out_balance, coalesce(sex,0) as sex,coalesce(categ.name,'') as categ_name, coalesce(psex.name,'') as sex_name  
                    from guazu_existence_analysis_report analy
                      LEFT JOIN product_category categ on analy.categ_id=categ.id
                      LEFT JOIN guazu_product_sex psex on analy.sex=psex.id
                    where
                        location_id = """ + str(location.id) + where_cat + """
                    group by categ_id, sex, categ.name, psex.name
                                    order by psex.name,categ.name asc""")
                moves = self.env.cr.dictfetchall()
            # mix the dicts
            for line in moves:
                found = False
                name_ = line['categ_name']
                sexo = line['sex_name']
                name = name_ if sexo.__len__() == 0 else name_ + "-" + sexo
                if not line['sex_name'] in sexo_cat:
                    sexo_cat.append(line['sex_name'])
                for it in categories:
                    if name == it['name_search']:
                        found = True
                        it.update({
                            'in_qty': float_utils.float_repr(float_utils.float_round(line['in_qty'], 3), 3),
                            'in_balance': float_utils.float_repr(float_utils.float_round(line['in_balance']/1000, 2), 2),
                            'out_qty': float_utils.float_repr(float_utils.float_round(line['out_qty'], 3), 3),
                            'out_balance': float_utils.float_repr(float_utils.float_round(line['out_balance']/1000, 2), 2)
                        })
                        break
                if not found:
                    # name = self.env['product.category'].browse(line['categ_id']).name
                    # sexo = "" if line['sex']== 0 else "-"+self.env['guazu.product.sex'].browse(line['sex']).name
                    name = line['categ_name']
                    sexo = line['sex_name']
                    if not sexo in sexo_cat:
                        sexo_cat.append(line['sex_name'])
                    categories.append({
                        'name_search': name if sexo.__len__()==0 else name+"-"+sexo,
                        'name':name,
                        'sexo':sexo,
                        'id': line['categ_id'],
                        'initial_qty': '0.000', 
                        'initial_balance': '0.00',
                        'in_qty': float_utils.float_repr(float_utils.float_round(line['in_qty'], 3), 3), 
                        'in_balance': float_utils.float_repr(float_utils.float_round(line['in_balance']/1000, 2), 2), 
                        'out_qty': float_utils.float_repr(float_utils.float_round(line['out_qty'], 3), 3), 
                        'out_balance': float_utils.float_repr(float_utils.float_round(line['out_balance']/1000, 2), 2), 
                        'final_qty': '0.000', 
                        'final_balance': '0.00'
                    })
            # final
            if end_date:
                self.env.cr.execute("""SELECT categ_id, sum(in_qty) as in_qty, sum(out_qty) as out_qty, sum(quantity) as final_qty, 
                      sum(amount) as final_balance, coalesce(sex,0) as sex,coalesce(categ.name,'') as categ_name, coalesce(psex.name,'') as sex_name  
                    from guazu_existence_analysis_report analy
                      LEFT JOIN product_category categ on analy.categ_id=categ.id
                      LEFT JOIN guazu_product_sex psex on analy.sex=psex.id
                    where
                        location_id = """ + str(location.id)+""" and
                        date <= '""" + end_date +"""'""" + where_cat + """ 
                    group by categ_id, sex, categ.name, psex.name
                                    order by psex.name,categ.name asc""")
                final = self.env.cr.dictfetchall()
            else:
                self.env.cr.execute("""SELECT categ_id, sum(in_qty) as in_qty, sum(out_qty) as out_qty, sum(quantity) as final_qty, 
                      sum(amount) as final_balance, coalesce(sex,0) as sex,coalesce(categ.name,'') as categ_name, coalesce(psex.name,'') as sex_name  
                    from guazu_existence_analysis_report analy
                      LEFT JOIN product_category categ on analy.categ_id=categ.id
                      LEFT JOIN guazu_product_sex psex on analy.sex=psex.id
                    where
                        location_id = """ + str(location.id)+ where_cat + """
                    group by categ_id, sex, categ.name, psex.name
                                    order by psex.name,categ.name asc""")
                final = self.env.cr.dictfetchall()
                
            # mix the dicts
            for line in final:
                found = False
                name_ = line['categ_name']
                sexo = line['sex_name']
                name = name_ if sexo.__len__() == 0 else name_ + "-" + sexo
                if not sexo in sexo_cat:
                    sexo_cat.append(line['sex_name'])
                for it in categories:
                    if name == it['name_search']:
                        found = True
                        it.update({
                            'final_qty': float_utils.float_repr(float_utils.float_round(line['final_qty'], 3), 3), 
                            'final_balance': float_utils.float_repr(float_utils.float_round(line['final_balance']/1000, 2), 2)
                        })
                        break
                if not found:
                    name = self.env['product.categories'].browse(line['categ_id']).name
                    sexo = "" if line['sex']== 0 else "-"+self.env['guazu.product.sex'].browse(line['sex']).name
                    if not sexo in sexo_cat:
                        sexo_cat.append(line['sex_name'])
                    categories.append({
                        'name_search': name if sexo.__len__()==0 else name+"-"+sexo,
                        'name':name,
                        'sexo':sexo,
                        'id': line['categ_id'],
                        'initial_qty': '0.000', 
                        'initial_balance': '0.00',
                        'in_qty': '0.000', 
                        'in_balance': '0.00',
                        'out_qty': '0.000', 
                        'out_balance': '0.00',
                        'final_qty': float_utils.float_repr(float_utils.float_round(line['final_qty'], 3), 3), 
                        'final_balance': float_utils.float_repr(float_utils.float_round(line['final_balance']/1000, 2), 2)
                    })
            sex_data=[]
            tot_initial_qty = 0
            tot_initial_balance = 0
            tot_in_qty = 0
            tot_in_balance = 0
            tot_out_qty = 0
            tot_out_balance = 0
            tot_final_qty = 0
            tot_final_balance = 0
            for k in sexo_cat:
                sex_ = []
                t_initial_qty = 0
                t_initial_balance = 0
                t_in_qty = 0
                t_in_balance = 0
                t_out_qty = 0
                t_out_balance = 0
                t_final_qty = 0
                t_final_balance = 0

                for cat in categories:
                    if cat['sexo']==k:
                        t_initial_qty += float(cat['initial_qty'])
                        t_initial_balance += float(cat['initial_balance'])
                        t_in_qty += float(cat['in_qty'])
                        t_in_balance += float(cat['in_balance'])
                        t_out_qty += float(cat['out_qty'])
                        t_out_balance += float(cat['out_balance'])
                        t_final_qty += float(cat['final_qty'])
                        t_final_balance += float(cat['final_balance'])
                        sex_.append({'name': cat['name'],
                                    'id': cat['id'],
                                    'initial_qty': cat['initial_qty'],
                                    'initial_balance': cat['initial_balance'],
                                    'in_qty': cat['in_qty'],
                                    'in_balance': cat['in_balance'],
                                    'out_qty': cat['out_qty'],
                                    'out_balance': cat['out_balance'],
                                    'final_qty': cat['final_qty'],
                                    'final_balance': cat['final_balance']})
                tot_initial_qty += t_initial_qty
                tot_initial_balance += t_initial_balance
                tot_in_qty += t_in_qty
                tot_in_balance += t_in_balance
                tot_out_qty += t_out_qty
                tot_out_balance += t_out_balance
                tot_final_qty += t_final_qty
                tot_final_balance += t_final_balance
                sex_data.append({'sexo':'Total '+k,
                                 't_initial_qty':float_utils.float_repr(float_utils.float_round(t_initial_qty, 3), 3),
                                 't_initial_balance':float_utils.float_repr(float_utils.float_round(t_initial_balance, 2), 2),
                                 't_in_qty':float_utils.float_repr(float_utils.float_round(t_in_qty, 3), 3),
                                 't_in_balance':float_utils.float_repr(float_utils.float_round(t_in_balance, 2), 2),
                                 't_out_qty':float_utils.float_repr(float_utils.float_round(t_out_qty, 3), 3),
                                 't_out_balance':float_utils.float_repr(float_utils.float_round(t_out_balance, 2), 2),
                                 't_final_qty':float_utils.float_repr(float_utils.float_round(t_final_qty, 3), 3),
                                 't_final_balance':float_utils.float_repr(float_utils.float_round(t_final_balance, 2), 2),
                                'data':sex_})
            if sex_data:
                res.append({'location': location.name_get()[0][1],
                            'categories': sex_data,'tot_initial_qty':float_utils.float_repr(float_utils.float_round(tot_initial_qty, 3), 3),
				            'tot_initial_balance':float_utils.float_repr(float_utils.float_round(tot_initial_balance, 2), 2),
                            'tot_in_qty':float_utils.float_repr(float_utils.float_round(tot_in_qty, 3), 3),
							'tot_in_balance':float_utils.float_repr(float_utils.float_round(tot_in_balance, 2), 2),
							'tot_out_qty':float_utils.float_repr(float_utils.float_round(tot_out_qty, 3), 3),
							'tot_out_balance':float_utils.float_repr(float_utils.float_round(tot_out_balance, 3), 3),
                            'tot_final_qty':float_utils.float_repr(float_utils.float_round(tot_final_qty, 3), 3),
                            'tot_final_balance':float_utils.float_repr(float_utils.float_round(tot_final_balance, 2), 2),
							'access_price':access_price})

        return res

    @api.model
    def get_locations(self, location_ids):
        if not location_ids:
            return ['Todos los almacenes']

        locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        res = []
        for loc in locations:
            res.append(loc.name)

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
        location_ids = data['form']['location_ids']
        category_ids = data['form']['category_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        access_price =  data['access_price']
        # if access_price:
        #     access_price = data['form']['show_import']

        return {
            'data': data,
            'locations': self.get_locations(location_ids),
            'start_date': start_date,
            'end_date': end_date,
            'categories': self.get_categories(category_ids),
            'access_price': access_price,
            'lines': self.get_lines(location_ids, start_date, end_date,access_price)
        }
    
    @api.model
    def render_html(self, docids, data=None):
        location_ids = data['form']['location_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        category_ids = data['form']['category_ids']
        access_price =  data['access_price']
        # if access_price:
        #     access_price = data['form']['show_import']
        docargs = {
            'data': data,
            'locations': self.get_locations(location_ids),
            'start_date': start_date,
            'end_date': end_date,
            'category_ids': self.get_category_ids(category_ids),
            'access_price': access_price,
            'lines': self.get_lines(location_ids, start_date, end_date, category_ids,access_price)
        }
        
        return self.env['report'].render('guazu_stock.report_stock_balance_cat', values=docargs)