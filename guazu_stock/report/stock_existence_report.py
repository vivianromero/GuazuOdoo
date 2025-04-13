from odoo import api, fields, models
from odoo.tools import float_utils



class StockExistenceReport(models.AbstractModel):
    _name = 'report.guazu_stock.report_stock_existence'


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
    def get_lines(self, category_ids, location_ids, attribute_value_ids, product_color_ids, product_sex_ids, product_material_ids, product_template_ids,show_variants, access_price):
        # obtener todos los productos que cumplan los atributos, colores, sexos, materiales y las categorias
        where = "TRUE"
        cat_ids = self.get_category_ids(category_ids)
        if len(cat_ids) > 1:
            where = "cat.id in "+str(tuple(cat_ids))
        if len(cat_ids) == 1:
            where = "cat.id = " + str(cat_ids[0])

        if len(attribute_value_ids) > 1:
            where += " and attribute_value.id in " + str(tuple(attribute_value_ids))
        if len(attribute_value_ids) == 1:
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

        self.env.cr.execute("""SELECT            
            template.id as id,
            template.default_code as default_code,
            cat.name as cat,
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
            template.id, uom.name, cat.name, template.default_code 
        ORDER BY
            template.default_code asc
            """)
        data = self.env.cr.dictfetchall()
        if location_ids:
            locations = self.env["guazu.stock.location"].search([('id', 'in', location_ids)])
        else:
            locations = self.env["guazu.stock.location"].search([('type', '=', 'storage')])
        res = []
        for location in locations:
            total_existence = 0
            total_amount = 0
            products = []
            for d in data:
                template = self.env["product.template"].browse(d["id"])
                existence = 0
                amount = 0
                variants = []

                for product in template.product_variant_ids:
                    #product = self.env["product.product"].browse(d["id"])
                    existence_location, amount_location = product.get_existence_in_location(location.id)[0]
                    existence += existence_location
                    amount += amount_location
                    total_existence += existence_location
                    total_amount += amount_location
                    if existence_location:
                        price_location = float_utils.float_round(amount_location/existence_location, 5)
                        variants.append({
                            'name': product.name_get()[0][1],
                            'uom': d['uom'],
                            'existence': float_utils.float_repr(existence_location, 2),
                            'price': float_utils.float_repr(price_location, 5),
                            'amount': float_utils.float_repr(amount_location, 2),
                            'id':product.id,
                            'att':product.attribute_value_ids.id
                        })

                if attribute_value_ids:
                    variants_remove=[]
                    show_variants = True
                    for prod_var in range(variants.__len__()):
                        if not variants[prod_var]['att'] in attribute_value_ids:
                            existence -= float(variants[prod_var]['existence'])
                            amount -= float(variants[prod_var]['amount'])
                            total_existence -= float(variants[prod_var]['existence'])
                            total_amount -= float(variants[prod_var]['amount'])
                            variants_remove.append(variants[prod_var])
                    [variants.remove(n) for n in variants_remove]

                if existence:
                    price = float_utils.float_round(amount/existence, 5)
                    name = template.name_get()[0][1]
                    if variants.__len__()==1 and show_variants:
                        name=variants[0]['name']
                        variants.pop(0)
                    products.append({
                        'name': name ,
                        'uom': d['uom'], 
                        'existence': float_utils.float_repr(existence, 2),
                        'price': float_utils.float_repr(price, 5),
                        'amount': float_utils.float_repr(amount, 2),
                        'variants': variants
                        })
            # if existence:
            res.append({'location_name': location.name, 'products': products, 'total_existence': float_utils.float_repr(total_existence, 2), 'total_amount': float_utils.float_repr(total_amount,2),'show_variants':show_variants,'access_price':access_price})
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
    
    # @api.model
    # def get_products(self, product_ids):
    #     if not product_ids:
    #         return ['Todas las variantes']
    #     products = self.env["product.product"].search([('id', 'in', product_ids)])
    #     res = []
    #     for prod in products:
    #         res.append(prod.name)
    #
    #     return res
    
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

    # @api.model
    # def get_report_values(self, docids, data=None):
    #     category_ids = data['form']['category_ids']
    #     location_ids = data['form']['location_ids']
    #     attribute_value_ids = data['form']['attribute_value_ids']
    #     product_color_ids = data['form']['product_color_ids']
    #     product_sex_ids = data['form']['product_sex_ids']
    #     product_template_ids = data['form']['product_template_ids']
    #     # product_ids = data['form']['product_ids']
    #     product_material_ids = data['form']['product_material_ids']
    #     show_variants = data['form']['show_variants']
    #     access_price = data['access_price']
    #     if access_price:
    #         access_price = data['form']['show_import']
    #     print "aquiiii"
    #     return {
    #         'data': data,
    #         'categories': self.get_categories(category_ids),
    #         'locations': self.get_locations(location_ids),
    #         'attributes': self.get_attributes(attribute_value_ids),
    #         'colors': self.get_colors(product_color_ids),
    #         'sexs': self.get_sexs(product_sex_ids),
    #         'product_templates': self.get_product_templates(product_template_ids),
    #         # 'products': self.get_products(product_ids),
    #         'materials': self.get_materials(product_material_ids),
    #         'date': fields.Datetime.now(),
    #         'show_variants': show_variants,
    #         'access_price': access_price,
    #         # 'lines': self.get_lines(category_ids, location_ids, attribute_value_ids, product_ids, product_template_ids,show_variants)
    #         'lines': self.get_lines(category_ids, location_ids, attribute_value_ids, product_template_ids,
    #                                 show_variants, access_price)
    #
    #     }

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
            'date': fields.Datetime.now(),
            'show_variants': show_variants,
            'access_price': access_price,
            # 'lines': self.get_lines(category_ids, location_ids, attribute_value_ids, product_color_ids, product_sex_ids, product_material_ids, product_ids, product_template_ids,show_variants)
            'lines': self.get_lines(category_ids, location_ids, attribute_value_ids, product_color_ids, product_sex_ids,
                                    product_material_ids, product_template_ids, show_variants, access_price)
        }
        return self.env['report'].render('guazu_stock.report_stock_existence', values=docargs)