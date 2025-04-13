{
     'name': 'Inventario',
     'version': '0.1',
     'sequence': 1,
     'category': 'Guazu',
     "description": """

Guazu
======================================================================


Version 0.1
-------------


    """,
     'author': 'Yerandy Reyes & Vivian Romero',
     'website': '',
     'installable': True,
     'active': False,
     'depends': ["base", "report", "product"],
     'init_xml': [
     ],
     'data': [
         "security/stock_security.xml",
         "security/ir.model.access.csv",
         "data/stock_move_sequence.xml",
         "data/stock_locations.xml",
         "data/uom_data.xml",
         "data/product_attributes_data.xml",
         "data/product_categories_data.xml",
         "data/product_colors_data.xml",
         "data/product_materials_data.xml",
         "data/product_sexs_data.xml",
         #"data/products_mp_data.xml",
         #"data/products_pt_calzado_hombre_data.xml",
         #"data/products_pt_calzado_mujer_data.xml",
         #"data/track_data.xml",
         "data/res_lang.xml",
         "views/menu.xml",
         "views/stock_location_view.xml",
         "views/stock_move_view.xml",
         "views/product_view.xml",
         "report/stock_move_templates.xml",
         "report/stock_existence_templates.xml",
         "report/stock_moves_templates.xml",
         "report/stock_balance_templates.xml",
         "report/stock_balance_cat_templates.xml",
         "report/stock_moves_location_templates.xml",
         "report/stock_move_invoice_templates.xml",
         "report/stock_report_views.xml",
         "report/stock_forecast_report.xml",
         "report/stock_existence_analysis_report.xml",
         "report/stock_moves_resum_template.xml",
         "wizard/stock_existence_wizard_view.xml",
         "wizard/stock_balance_wizard_view.xml",
         "wizard/stock_balance_cat_wizard_view.xml",
         "wizard/stock_moves_wizard_view.xml",
         "wizard/stock_moves_location_wizard_view.xml",
         "wizard/stock_move_done_wizard_view.xml",
         "wizard/stock_moves_resum_wizard_view.xml"
     ],     
     #'test': ['test/test.yml'],
     'application': True
}

