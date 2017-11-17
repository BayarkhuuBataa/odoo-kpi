# -*- coding: utf-8 -*-
{
    'name': "hq_kpi",

    'summary': """
        整合业务上产生的销售、库存数据，结构化的展示各业务的经营状况，以辅助决策
        """,

    'description': """
        根据团队，产品品类获取销售额，毛利，毛利率，回款，应收账款，库存，动态周转等数据，
        高效的获取业务中的各个关键指标，了解经营状况
    """,

    'author': "zhaohe",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'zhaohe',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/report_view.xml',
        'views/templates.xml',
        'report/kpi_report.xml',
        'report/kpi_report_templates.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}