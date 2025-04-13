# -*- coding: utf-8 -*-
{
    'name': 'Ventas',
    'version': '0.1',
    'category': 'Guazu',
    "sequence": 2,
    'complexity': "easy",
    'installable': True,
    'description': """

    """,
    'author': "Yerandy Reyes & Vivian Romero",
    'website': '',
    'depends': ["guazu_stock"],
    'init_xml': [
    ],
    'data': [
        "security/sale_security.xml",
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
		#"data/res_country_state_data.xml",
        "data/res_partner_data.xml",
        # "data/ir_sequence_data.xml",
        "data/ir_config_parameter.xml",
		"data/partner_org_data.xml",
        "views/menu.xml",
        "views/sale_views.xml",
		#"views/res_config_settings_views.xml",
		"views/guazu_attach_document_view.xml",
        "report/sale_report_templates.xml",
        "report/sale_report.xml",
        "report/sales_client_templates.xml",
		"views/res_company_.xml",
        "wizard/sale_client_wizard_view.xml"
    ],
    #'demo_xml': [],
    #'test': [
    #],
    #'installable': True,
    # 'auto_install': False,
    'application': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
