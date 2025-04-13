from odoo import api, fields, models
from odoo.tools import float_utils


class StockMovesReport(models.AbstractModel):
    _name = 'report.guazu_stock.report_stock_moves'

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
    def get_lines(self, category_ids, location_ids, attribute_value_ids, product_color_ids, product_sex_ids, product_material_ids,product_template_ids, start_date, end_date, show_variants, access_price):
        # obtener todos los productos que cumplan los atributos, colores, sexos, materiales y las categorias
        where = "TRUE"
        cat_ids = self.get_category_ids(category_ids)
        if len(cat_ids) > 1:
            where = "cat.id in "+str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where = "cat.id = " + str(cat_ids[0])

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
                        uom.name as uom
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
                        product.id, template.name, uom.name, attribute_value.name, product.default_code 
                    ORDER BY
                        product.default_code, attribute_value.name asc
                        """)
            data = self.env.cr.dictfetchall()
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
                template.id, template.name, uom.name, template.default_code
            ORDER BY
                template.default_code""")
            data = self.env.cr.dictfetchall()

        if location_ids:
            locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        else:
            locations = self.env["guazu.stock.location"].search([('type', '=', 'storage')])
        res = []
        if show_variants:
            for d in data:
                product = self.env["product.product"].browse(d["id"])
                product_locations = []
                for location in locations:
                    moves = []
                    where = ""
                    initial = initial_balance = 0.00

                    if start_date and end_date:
                        where = " and sm.done_date >= '" + start_date + "' and sm.done_date <= '" + end_date + "'"

                    if start_date and not end_date:
                        where = " and sm.done_date >= '" + start_date + "'"
                    if not start_date and end_date:
                        where = " and sm.done_date <= '" + end_date + "'"

                    if start_date:

                        self.env.cr.execute("""SELECT sum(l.quantity) as quantity, l.price as price 
                                    from guazu_stock_move as sm inner join
                                        guazu_stock_move_line as l on l.stock_move_id = sm.id
                                    where
                                        sm.location_dest_id = """ + str(location.id) + """ and
                                        l.product_id =""" + str(d['id']) + """ and
                                        sm.state = 'done' and sm.done_date < '""" + start_date + "' group by l.price")
                        fetch = self.env.cr.dictfetchall()
                        for f in fetch:
                            if f['quantity']:
                                initial += f['quantity']
                                initial_balance += float_utils.float_round(f['quantity'] * f['price'],2)

                        self.env.cr.execute("""SELECT sum(l.quantity) as quantity, l.price as price 
                                    from guazu_stock_move as sm inner join
                                        guazu_stock_move_line as l on l.stock_move_id = sm.id
                                    where
                                        sm.location_id = """ + str(location.id) + """ and
                                        l.product_id =""" + str(d['id']) + """ and
                                        sm.state = 'done' and sm.done_date < '""" + start_date + "' group by l.price")
                        fetch = self.env.cr.dictfetchall()
                        for f in fetch:
                            if f['quantity']:
                                initial -= f['quantity']
                                initial_balance -= float_utils.float_round(f['quantity'] * f['price'],2)

                    self.env.cr.execute("""SELECT
                                sm.name as name,
                                sm.done_date as date,
                                l.quantity as quantity,
                                l.price as price,
                                CAST (l.price * l.quantity as numeric(18,2)) as amount,
                                sm.location_id,
                                sm.location_dest_id,
                                loc.name as location_name,
                                loc2.name as location_dest_name
                                FROM
                                guazu_stock_move as sm inner join
                                guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                                guazu_stock_location loc on sm.location_id = loc.id inner join
                                guazu_stock_location loc2 on sm.location_dest_id = loc2.id
                                where
                                (sm.location_id = """ + str(location.id) + """ or
                                sm.location_dest_id = """ + str(location.id) + """) and
                                l.product_id =""" + str(d['id']) + """ and
                                sm.state = 'done'""" + where + """ order by sm.done_date asc""")
                    move_lines = self.env.cr.dictfetchall()

                    existence = initial
                    balance = initial_balance
                    for line in move_lines:
                        if line['location_dest_id'] == location.id:
                            existence += line['quantity']
                            balance = existence * line['price']
                            # balance += float_utils.float_round(line['price'] * line['quantity'],2)
                            moves.append({
                                'name': line['name'],
                                'date': line['date'],
                                'qty': line['quantity'],
                                'price': line['price'],
                                'amount': line['amount'],
                                'existence': float_utils.float_repr(existence,2),
                                'balance': balance,
                                'from_to_location': line['location_name']
                            })
                        if line['location_id'] == location.id:
                            existence -= line['quantity']
                            # balance -= float_utils.float_round(line['price'] * line['quantity'],2)
                            balance = existence * line['price']
                            moves.append({
                                'name': line['name'],
                                'date': line['date'],
                                'qty': line['quantity'] * -1,
                                'price': line['price'],
                                'amount': line['amount'] * -1,
                                'existence': float_utils.float_repr(existence,2),
                                'balance': balance,
                                'from_to_location': line['location_dest_name']
                            })

                    if moves:
                        product_locations.append(
                            {'name': location.name, 'initial': float_utils.float_round(initial,2), 'initial_balance': float_utils.float_round(initial_balance,2),
                             'moves': moves})

                if product_locations:
                    res.append({'product': product.name_get()[0][1], 'locations': product_locations,'access_price':access_price})
        else:
            for d in data:
                product = self.env["product.template"].browse(d["id"])
                product_locations = []
                for location in locations:
                    moves = []
                    where = ""
                    initial = initial_balance = 0

                    if start_date and end_date:
                        where = " and sm.done_date >= '" + start_date + "' and sm.done_date <= '" + end_date + "'"

                    if start_date and not end_date:
                        where = " and sm.done_date >= '" + start_date + "'"
                    if not start_date and end_date:
                        where = " and sm.done_date <= '" + end_date + "'"

                    if start_date:

                        self.env.cr.execute("""
                          SELECT sum(l.quantity) as quantity, l.price as price
                        from guazu_stock_move as sm inner join
                            guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                            product_product as p on l.product_id = p.id inner join 
                            product_template as template on template.id = p.product_tmpl_id
                        where
                            sm.location_dest_id =""" + str(location.id) + """ and
                            template.id =""" + str(d['id']) + """ and
                            sm.state = 'done' and sm.done_date < '""" + start_date + "' group by l.price ")
                        fetch = self.env.cr.dictfetchall()

                        for f in fetch:
                            if f['quantity']:
                                initial += f['quantity']
                                initial_balance += float_utils.float_round(f['quantity'] * f['price'],2)
                        self.env.cr.execute("""SELECT sum(l.quantity) as quantity, l.price as price
                            from guazu_stock_move as sm inner join
                                guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                                product_product as p on l.product_id = p.id inner join 
                                product_template as template on template.id = p.product_tmpl_id
                                where
                                    sm.location_id = """ + str(location.id) + """ and
                                    template.id =""" + str(d['id']) + """ and
                                    sm.state = 'done' and sm.done_date < '""" + start_date + "' group by l.price")
                        fetch = self.env.cr.dictfetchall()
                        for f in fetch:
                            if f['quantity']:
                                initial -= f['quantity']
                                initial_balance -= float_utils.float_round(f['quantity'] * f['price'],2)
                    self.env.cr.execute("""Select sm.name as name,
                        sm.done_date as date,
                        sum(l.quantity) as quantity,
                        l.price as price,
                        CAST (l.price * sum(l.quantity) as numeric(18,2)) as amount,
                        sm.location_id,
                        sm.location_dest_id,
                        loc.name as location_name,
                        loc2.name as location_dest_name
                        FROM
                        guazu_stock_move as sm inner join
                        guazu_stock_move_line as l on l.stock_move_id = sm.id inner join
                        guazu_stock_location loc on sm.location_id = loc.id inner join
                        guazu_stock_location loc2 on sm.location_dest_id = loc2.id inner join 
                        product_product as p on l.product_id = p.id inner join 
                        product_template as template on template.id = p.product_tmpl_id
                        where
                        (sm.location_id = """ + str(location.id) + """ or
                        sm.location_dest_id = """ + str(location.id) + """) and
                        template.id =""" + str(d['id']) + """ and
                        sm.state = 'done'""" + where + """ group by sm.name,sm.done_date,l.price,
                        sm.location_id,
                        sm.location_dest_id,
                        loc.name,
                        loc2.name order by sm.done_date asc""")

                    move_lines = self.env.cr.dictfetchall()

                    existence = initial
                    balance = initial_balance
                    for line in move_lines:
                        if line['location_dest_id'] == location.id:
                            existence += line['quantity']
                            balance = existence * line['price']
                            # balance += float_utils.float_round(line['price'] * line['quantity'],2)
                            moves.append({
                                'name': line['name'],
                                'date': line['date'],
                                'qty': line['quantity'],
                                'price': line['price'],
                                'amount': line['amount'],
                                'existence': float_utils.float_repr(existence,2),
                                'balance': balance,
                                'from_to_location': line['location_name']
                            })
                        if line['location_id'] == location.id:
                            existence -= line['quantity']
                            balance = existence * line['price']
                            # balance -= float_utils.float_round(line['price'] * line['quantity'], 2)
                            moves.append({
                                'name': line['name'],
                                'date': line['date'],
                                'qty': line['quantity'] * -1,
                                'price': line['price'],
                                'amount': line['amount'] * -1,
                                'existence': float_utils.float_repr(existence,2),
                                'balance': balance,
                                'from_to_location': line['location_dest_name']
                            })

                    if moves:
                        product_locations.append(
                            {'name': location.name, 'initial': float_utils.float_round(initial,2), 'initial_balance': float_utils.float_round(initial_balance,2),
                             'moves': moves, 'access_price':access_price})

                if product_locations:
                    res.append({'product': product.name_get()[0][1], 'locations': product_locations,'access_price':access_price})

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
    def get_products(self, product_ids):
        if not product_ids:
            return ['Todos los productos']
        products = self.env["product.product"].search([('id', 'in', product_ids)])
        res = []
        for prod in products:
            res.append(prod.name)

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
        attribute_value_ids = data['form']['attribute_value_ids']
        product_color_ids = data['form']['product_color_ids']
        product_sex_ids = data['form']['product_sex_ids']
        # product_ids = data['form']['product_ids']
        product_template_ids = data['form']['product_template_ids']
        product_material_ids = data['form']['product_material_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        show_variants = data['form']['show_variants']
        access_price = data['access_price']
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
            'product_templates': self.get_product_templates(product_template_ids),
            'materials': self.get_materials(product_material_ids),
            'start_date': start_date,
            'end_date': end_date,
			'access_price':access_price,
            'lines': self.get_lines(category_ids, location_ids, attribute_value_ids,product_template_ids,start_date, end_date, show_variants, access_price)
        }

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
    def render_html(self, docids, data=None):
        category_ids = data['form']['category_ids']
        location_ids = data['form']['location_ids']
        attribute_value_ids = data['form']['attribute_value_ids']
        product_color_ids = data['form']['product_color_ids']
        product_sex_ids = data['form']['product_sex_ids']
        product_material_ids = data['form']['product_material_ids']
        # product_ids = data['form']['product_ids']
        product_template_ids = data['form']['product_template_ids']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        show_variants = data['form']['show_variants']
        access_price = data['access_price']
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
            'show_variants': show_variants,
            'access_price':access_price,
            'lines': self.get_lines(category_ids, location_ids, attribute_value_ids, product_color_ids, product_sex_ids, product_material_ids,product_template_ids,start_date,end_date, show_variants, access_price)
        }
        return self.env['report'].render('guazu_stock.report_stock_moves', values=docargs)