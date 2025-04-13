from odoo import api, fields, models
from odoo.tools import float_utils


class StockMovesLocationReport(models.AbstractModel):
    _name = 'report.guazu_stock.report_stock_moves_location'

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
    def get_lines(self, category_ids, location_ids, location_dest_ids, attribute_value_ids, product_color_ids, product_sex_ids, product_material_ids, start_date, end_date,product_template_ids,show_variants, show_moves, access_price, show_products):
        # obtener todos los productos que cumplan los atributos, colores, sexos, materiales y las categorias
        where = "TRUE"
        cat_ids = self.get_category_ids(category_ids)
        if len(cat_ids) > 1:
            where = " cat.id in "+str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where = " cat.id = " + str(cat_ids[0])

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

        if show_variants:
            self.env.cr.execute("""SELECT
                product.id as id,
                product.default_code as default_code,
                template.name as name,
                uom.name as uom,
                attribute_value.name
            FROM
                product_product product
                LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
                LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                LEFT JOIN product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=product.id)
                LEFT JOIN product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
            WHERE """ + where + """
            GROUP BY
                product.id, template.name, uom.name, attribute_value.name,product.default_code,uom.name
            ORDER BY
                product.default_code, attribute_value.name asc
                """)
        else:
            self.env.cr.execute("""
                        SELECT
                            template.id as id,
                            template.default_code as default_code,
                            template.name as name,
                            uom.name as uom
                        FROM
                            product_template template
                            LEFT JOIN product_uom uom ON (template.uom_id=uom.id)
                            LEFT JOIN product_category cat ON (template.categ_id=cat.id)
                            LEFT JOIN guazu_product_color color ON (template.color_id=color.id)
                            LEFT JOIN guazu_product_sex sex ON (template.sex_id=sex.id)
                            LEFT JOIN guazu_product_material material ON (template.material_id=material.id)
                        WHERE """ + where + """
                        GROUP BY
                            template.id, template.name, uom.name, template.default_code, uom.name
                        ORDER BY
                            template.default_code""")
            # data = self.env.cr.dictfetchall()


        data = self.env.cr.dictfetchall()
        product_ids = [d["id"] for d in data]

        if len(location_ids)==0:
            locations = self.env["guazu.stock.location"].search([])
            location_ids = [l.id for l in locations]
        
        if len(location_dest_ids)==0:
            locations_dest = self.env["guazu.stock.location"].search([])
            location_dest_ids = [l.id for l in locations_dest]

        where = " sm.state = 'done' "
        if len(location_ids) > 1:
            where += " and sm.location_id in " + str(tuple(location_ids))
        if len(location_ids) == 1:
            where += " and sm.location_id = " + str(location_ids[0])

        if len(location_dest_ids) > 1:
            where += " and sm.location_dest_id in " + str(tuple(location_dest_ids))
        if len(location_dest_ids) == 1:
            where += " and sm.location_dest_id = " + str(location_dest_ids[0])

        t_prod = " and prod.id in " if show_variants else " and temp.id in "
        if len(product_ids) > 1:
            where += t_prod + str(tuple(product_ids))
        if len(product_ids) == 1:
            where += t_prod + " = " + str(product_ids[0])

        if len(product_template_ids) > 1:
            where += " and temp.id in " + str(tuple(product_template_ids))
        if len(product_template_ids) == 1:
            where += " and temp.id = " + str(product_template_ids[0])

        if start_date and end_date:
            where += " and sm.done_date >= '" + start_date + "' and sm.done_date <= '" + end_date + "'"
            
        if start_date and not end_date:
            where += " and sm.done_date >= '" + start_date + "'"
        if not start_date and end_date:
            where += " and sm.done_date <= '" + end_date + "'"

        cat_ids = self.get_category_ids(category_ids)
        if len(cat_ids) > 1:
            where += " and cat.id in " + str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where += " and cat.id = " + str(cat_ids[0])

        if len(attribute_value_ids) > 1:
            where += " and attribute_value.id in " + str(tuple(attribute_value_ids))
        if len(attribute_value_ids) == 1:
            where += " and attribute_value.id = " + str(attribute_value_ids[0])

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

        self.env.cr.execute("""
            select sum(t.quantity) as quantity, sum(t.amount) as amount from 
                (SELECT
                                sum(l.quantity) as quantity,
                                CAST (l.price * sum(l.quantity) as numeric(18,2)) as amount
                                
                                FROM
                                guazu_stock_move as sm inner join
                                guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                                product_product as prod on l.product_id = prod.id inner join
                                product_template as temp on prod.product_tmpl_id = temp.id
                                LEFT JOIN product_uom uom ON (temp.uom_id=uom.id)  
                                LEFT JOIN product_category cat ON (temp.categ_id=cat.id)
                                LEFT JOIN guazu_product_color color ON (temp.color_id=color.id)
                                LEFT JOIN guazu_product_sex sex ON (temp.sex_id=sex.id)
                                LEFT JOIN guazu_product_material material ON (temp.material_id=material.id) inner join
                                guazu_stock_location loc on sm.location_id = loc.id inner join
                                guazu_stock_location loc2 on sm.location_dest_id = loc2.id 
                                  where """ + where + """
                        group by l.price) t
            """)

        self.total_quantity = 0
        self.total_amount = 0.0
        totales = self.env.cr.dictfetchall()
        for t in totales:
            self.total_quantity = t["quantity"]
            self.total_amount = t["amount"]

        if show_variants:
            if not show_moves:
                self.env.cr.execute("""SELECT
                    sm.name as name,
                    sm.done_date as date,
                    l.quantity as quantity,
                    l.price as price,
                    CAST (l.price * l.quantity as numeric(18,2)) as amount,
                    sm.location_id,
                    sm.location_dest_id,
                    loc.name as location_name,
                    loc2.name as location_dest_name,
                    case when length(attribute_value.name)<>0
                     then concat(temp.name,' (',attribute_value.name,')')
                    else temp.name end as product_name,
                    prod.default_code as default_code,
                    uom.name as uom
                    FROM
                    guazu_stock_move as sm inner join
                    guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                    product_product as prod on l.product_id = prod.id inner join
                    product_template as temp on prod.product_tmpl_id = temp.id 
                    LEFT JOIN product_uom uom ON (temp.uom_id=uom.id)            
                    LEFT JOIN product_category cat ON (temp.categ_id=cat.id)
                    LEFT JOIN guazu_product_color color ON (temp.color_id=color.id)
                    LEFT JOIN guazu_product_sex sex ON (temp.sex_id=sex.id)
                    LEFT JOIN guazu_product_material material ON (temp.material_id=material.id) inner join
                    guazu_stock_location loc on sm.location_id = loc.id inner join
                    guazu_stock_location loc2 on sm.location_dest_id = loc2.id LEFT JOIN 
                    product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=prod.id) LEFT JOIN 
                    product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                    where
                    """ + where +""" order by sm.location_id, sm.location_dest_id, sm.done_date,default_code,attribute_value.name asc""")
            else:
                self.env.cr.execute("""SELECT
                                    sum(l.quantity) as quantity,
                                    l.price as price,
                                    CAST (l.price * sum(l.quantity) as numeric(18,2)) as amount,
                                    sm.location_id,
                                    sm.location_dest_id,
                                    loc.name as location_name,
                                    loc2.name as location_dest_name,
                                    case when length(attribute_value.name)<>0
                                     then concat(temp.name,' (',attribute_value.name,')')
                                    else temp.name end as product_name,
                                    prod.default_code as default_code,
                                    uom.name as uom
                                    FROM
                                    guazu_stock_move as sm inner join
                                    guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                                    product_product as prod on l.product_id = prod.id inner join
                                    product_template as temp on prod.product_tmpl_id = temp.id 
                                    LEFT JOIN product_uom uom ON (temp.uom_id=uom.id)               
                                    LEFT JOIN product_category cat ON (temp.categ_id=cat.id)
                                    LEFT JOIN guazu_product_color color ON (temp.color_id=color.id)
                                    LEFT JOIN guazu_product_sex sex ON (temp.sex_id=sex.id)
                                    LEFT JOIN guazu_product_material material ON (temp.material_id=material.id) inner join
                                    guazu_stock_location loc on sm.location_id = loc.id inner join
                                    guazu_stock_location loc2 on sm.location_dest_id = loc2.id LEFT JOIN 
                                    product_attribute_value_product_product_rel attribute_value_product ON (attribute_value_product.product_product_id=prod.id) LEFT JOIN 
                                    product_attribute_value attribute_value ON (attribute_value_product.product_attribute_value_id=attribute_value.id)
                                    where
                                    """ + where + """ 
                                    group by l.price, sm.location_id,
                                    sm.location_dest_id, loc.name, loc2.name, prod.default_code, attribute_value.name, temp.name, uom.name
                                    order by sm.location_id, sm.location_dest_id,default_code,attribute_value.name asc""")

            move_lines = self.env.cr.dictfetchall()
        elif not show_products:
            if not show_moves:
                self.env.cr.execute("""
                SELECT
                sm.name as name,sm.done_date as date,sum(l.quantity) as quantity,
                l.price as price,CAST (l.price * sum(l.quantity) as numeric(18,2)) as amount,
                sm.location_id,sm.location_dest_id,loc.name as location_name,loc2.name as location_dest_name,
                temp.name as product_name,prod.default_code as default_code,
                uom.name as uom
                FROM
                guazu_stock_move as sm inner join
                guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                product_product as prod on l.product_id = prod.id inner join
                product_template as temp on prod.product_tmpl_id = temp.id
                LEFT JOIN product_uom uom ON (temp.uom_id=uom.id)  
                LEFT JOIN product_category cat ON (temp.categ_id=cat.id)
                LEFT JOIN guazu_product_color color ON (temp.color_id=color.id)
                LEFT JOIN guazu_product_sex sex ON (temp.sex_id=sex.id)
                LEFT JOIN guazu_product_material material ON (temp.material_id=material.id) inner join
                guazu_stock_location loc on sm.location_id = loc.id inner join
                guazu_stock_location loc2 on sm.location_dest_id = loc2.id 
                where
                    """ + where +""" 
               group by sm.name, sm.done_date, l.price, sm.location_id, sm.location_dest_id, loc.name,loc2.name, temp.name, prod.default_code, uom.name
               order by sm.location_id, sm.location_dest_id, sm.done_date,default_code asc
                """)
                move_lines = self.env.cr.dictfetchall()
            else:
                self.env.cr.execute("""
                                SELECT
                                sum(l.quantity) as quantity,
                                l.price as price,CAST (l.price * sum(l.quantity) as numeric(18,2)) as amount,
                                sm.location_id,sm.location_dest_id,loc.name as location_name,loc2.name as location_dest_name,
                                temp.name as product_name,prod.default_code as default_code,
                                uom.name as uom
                                FROM
                                guazu_stock_move as sm inner join
                                guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                                product_product as prod on l.product_id = prod.id inner join
                                product_template as temp on prod.product_tmpl_id = temp.id
                                LEFT JOIN product_uom uom ON (temp.uom_id=uom.id)  
                                LEFT JOIN product_category cat ON (temp.categ_id=cat.id)
                                LEFT JOIN guazu_product_color color ON (temp.color_id=color.id)
                                LEFT JOIN guazu_product_sex sex ON (temp.sex_id=sex.id)
                                LEFT JOIN guazu_product_material material ON (temp.material_id=material.id) inner join
                                guazu_stock_location loc on sm.location_id = loc.id inner join
                                guazu_stock_location loc2 on sm.location_dest_id = loc2.id 
                                where
                                    """ + where + """ 
                               group by l.price, sm.location_id, sm.location_dest_id, loc.name,loc2.name, temp.name, prod.default_code, uom.name
                               order by sm.location_id, sm.location_dest_id,default_code asc
                                """)
                move_lines = self.env.cr.dictfetchall()
        else:
            if not show_moves:
                self.env.cr.execute(""" 
                   select t.name as name,t.date as date, CAST(sum(t.amount) as numeric(18,2)) as amount,
                          t.location_id,t.location_dest_id,t.location_name,t.location_dest_name
                    from
                    (Select 
                                    sm.name as name,sm.done_date as date, CAST (l.price * sum(l.quantity) as numeric(18,2)) as amount,
                                    sm.location_id,sm.location_dest_id,loc.name as location_name,loc2.name as location_dest_name
                                    FROM
                                    guazu_stock_move as sm inner join
                                    guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                                    product_product as prod on l.product_id = prod.id inner join
                                    product_template as temp on prod.product_tmpl_id = temp.id
                                    LEFT JOIN product_uom uom ON (temp.uom_id=uom.id)
                                    LEFT JOIN product_category cat ON (temp.categ_id=cat.id)
                                    LEFT JOIN guazu_product_color color ON (temp.color_id=color.id)
                                    LEFT JOIN guazu_product_sex sex ON (temp.sex_id=sex.id)
                                    LEFT JOIN guazu_product_material material ON (temp.material_id=material.id) inner join
                                    guazu_stock_location loc on sm.location_id = loc.id inner join
                                    guazu_stock_location loc2 on sm.location_dest_id = loc2.id
                                     where """ + where + """ 
                                   group by sm.name, sm.done_date, l.price, sm.location_id, sm.location_dest_id, loc.name,loc2.name
                                   order by sm.location_id, sm.location_dest_id, sm.done_date) t
                    group by t.name,t.date,t.location_id,t.location_dest_id,t.location_name,t.location_dest_name
                    order by t.location_id, t.location_dest_id, t.date
                """)
                move_lines = self.env.cr.dictfetchall()
            else:
                self.env.cr.execute("""
                    select CAST(sum(t.amount) as numeric(18,2)) as amount,
                           t.location_id,t.location_dest_id,t.location_name,t.location_dest_name
                    from
                    (Select 
                        sm.name as name,sm.done_date as date, CAST (l.price * sum(l.quantity) as numeric(18,2)) as amount,
                        sm.location_id,sm.location_dest_id,loc.name as location_name,loc2.name as location_dest_name
                        FROM
                        guazu_stock_move as sm inner join
                        guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                        product_product as prod on l.product_id = prod.id inner join
                        product_template as temp on prod.product_tmpl_id = temp.id
                        LEFT JOIN product_uom uom ON (temp.uom_id=uom.id)
                        LEFT JOIN product_category cat ON (temp.categ_id=cat.id)
                        LEFT JOIN guazu_product_color color ON (temp.color_id=color.id)
                        LEFT JOIN guazu_product_sex sex ON (temp.sex_id=sex.id)
                        LEFT JOIN guazu_product_material material ON (temp.material_id=material.id) inner join
                        guazu_stock_location loc on sm.location_id = loc.id inner join
                        guazu_stock_location loc2 on sm.location_dest_id = loc2.id
                          where """ + where + """ 
                       group by sm.name, sm.done_date, l.price, sm.location_id, sm.location_dest_id, loc.name,loc2.name
                       order by sm.location_id, sm.location_dest_id, sm.done_date) t
                    group by t.location_id,t.location_dest_id,t.location_name,t.location_dest_name
                    order by t.location_id, t.location_dest_id
                                """)
                move_lines = self.env.cr.dictfetchall()
        return move_lines

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
    def get_locations(self, location_ids):
        if not location_ids:
            return ['Todas las ubicaciones']

        locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        res = []
        for loc in locations:
            res.append(loc.name)

        return res
    
    @api.model
    def get_locations_dest(self, location_ids):
        if not location_ids:
            return ['Todas las ubicaciones']

        locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        res = []
        for loc in locations:
            res.append(loc.name)

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
    def get_report_values(self, docids, data=None):
        category_ids = data['form']['category_ids']
        location_ids = data['form']['location_ids']
        location_dest_ids = data['form']['location_dest_ids']
        attribute_value_ids = data['form']['attribute_value_ids']
        product_color_ids = data['form']['product_color_ids']
        product_sex_ids = data['form']['product_sex_ids']
        # product_ids = data['form']['product_ids']
        product_template_ids = data['form']['product_template_ids']
        product_material_ids = data['form']['product_material_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        show_variants = data['form']['show_variants']
        # show_variants = data['form']['show_variants']
        show_moves = data['form']['show_moves']
        show_products = data['form']['show_products']

        access_price = data['access_price']
        # if access_price:
        #     access_price = data['form']['show_import']
        return {
            'data': data,
            'categories': self.get_categories(category_ids),
            'locations': self.get_locations(location_ids),
            'locations_dest': self.get_locations_dest(location_dest_ids),
            'attributes': self.get_attributes(attribute_value_ids),
            'colors': self.get_colors(product_color_ids),
            'sexs': self.get_sexs(product_sex_ids),
            # 'products': self.get_products(product_ids),
            'product_template': self.get_product_templates(product_template_ids),
            'materials': self.get_materials(product_material_ids),
            'start_date': start_date,
            'end_date': end_date,
            'access_price':access_price,
            # show_variants:show_variants,
            'lines': self.get_lines(category_ids, location_ids, location_dest_ids,attribute_value_ids,start_date, end_date,product_template_ids,show_variants,show_moves,access_price, show_products),
            'total_quantity': self.total_quantity,
            'total_amount': self.total_amount
        }
    
    @api.model
    def render_html(self, docids, data=None):
        category_ids = data['form']['category_ids']
        location_ids = data['form']['location_ids']
        location_dest_ids = data['form']['location_dest_ids']
        attribute_value_ids = data['form']['attribute_value_ids']
        product_color_ids = data['form']['product_color_ids']
        product_sex_ids = data['form']['product_sex_ids']
        product_material_ids = data['form']['product_material_ids']
        # product_ids = data['form']['product_ids']
        product_template_ids = data['form']['product_template_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        show_variants = data['form']['show_variants']
        show_products = data['form']['show_products']
        # show_variants = data['form']['show_variants']
        show_moves = data['form']['show_moves']
        show_moves_t = '1'
        if show_moves and not show_products:
            show_moves_t = '2'

        if not show_moves and show_products:
            show_moves_t = '3'

        if not show_moves and not show_products:
            show_moves_t = '4'

        access_price = data['access_price']
        # if access_price:
        #     access_price = data['form']['show_import']
        docargs = {
            'data': data,
            'categories': self.get_categories(category_ids),
            'locations': self.get_locations(location_ids),
            'locations_dest': self.get_locations_dest(location_dest_ids),
            'attributes': self.get_attributes(attribute_value_ids),
            'colors': self.get_colors(product_color_ids),
            'sexs': self.get_sexs(product_sex_ids),
            'materials': self.get_materials(product_material_ids),
            # 'products': self.get_products(product_ids),
            'product_templates': self.get_product_templates(product_template_ids),
            'start_date': start_date,
            'end_date': end_date,
            'show_variants': show_variants,
            'show_moves':show_moves,
            'show_moves_t':show_moves_t,
            'access_price':access_price,
            'lines': self.get_lines(category_ids, location_ids, location_dest_ids, attribute_value_ids, product_color_ids, product_sex_ids, product_material_ids,start_date,end_date,product_template_ids,show_variants, show_moves, access_price, show_products),
            'total_quantity': self.total_quantity,
            'total_amount': self.total_amount
        }
        return self.env['report'].render('guazu_stock.report_stock_moves_location', values=docargs)