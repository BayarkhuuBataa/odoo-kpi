# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logger = logging.getLogger(__name__)


class hq_kpiByTeam(models.Model):
    _name = 'hq.kpibyteam'

    @api.model
    def run_kpibyteam_scheduler(self):
        check_current_data(self, "hq_kpibyteam")
        sql = """
            insert into 
                hq_kpibyteam(company_id,team_id,sale_count,gross_profit,gross_margin,back_money,accounts_receivable,stock,belong_date) 
                select 
                    T6.id,T2.id,
                    round(T1.sale_count,2) as sale,round(T1.gross_profit,2) as gross_profit,T1.gross_margin as gross_margin,
                    round(T3.paidback_money,2) as paidback_money,round(T4.openback_money,2) as openback_money,T5.stock::decimal(16,2) as stock,now() - interval '8 h'
                from
                (select 
                    ct.id as id,ct.name,ct.company_id as company_id from crm_team ct
                    where ct.id not in('86','153') group by ct.id
                )T2 
                left join
                (select 
                    sum((l.qty_delivered-l.qty_return) * l.price_unit) as sale_count,
                    sum((l.qty_delivered-l.qty_return) * l.price_unit-l.actual_cost) as gross_profit,
                    case when sum((l.qty_delivered-l.qty_return) * l.price_unit)=0 then NULL else 
                    round(sum((l.qty_delivered-l.qty_return) * l.price_unit-l.actual_cost) / 
                    sum((l.qty_delivered-l.qty_return) * l.price_unit) * 100,2) end as gross_margin,
                    s.team_id as team_id
                from sale_order s,sale_order_line l 
                where s.id = l.order_id and s.partner_id !='1' and s.team_id not in ('86','153')
                and s.state in ('delivered', 'mark_paid', 'done')
                and s.payment_term_id != '8'
                and s.create_date between (now() - interval '1 day 8 h') and now() - interval '8 h'
                group by s.team_id
                )T1 on T1.team_id = T2.id
                left join 
                (select 
                    ct.id as oaiteam,
                    sum(COALESCE(T1.invoiceback_money, 0.0) -COALESCE(T2.refundback_money, 0.0)) as paidback_money
                from 
                    crm_team ct 
                left join 
                    (select 
                        sum(price_unit * quantity) as invoiceback_money,oai.team_id as oaiteam 
                    from account_invoice oai, account_invoice_line oail 
                    where oai.id = oail.invoice_id and oai.state = 'paid' and oai.type='out_invoice'
                        and (oai.team_id not in ('86','153') and oai.team_id is not null)
                        and (oai.payment_term_id != '8' or oai.payment_term_id is null)
                        and oai.payment_done_date between (now() - interval '1 day 8 h') and now() - interval '8 h'
                        and oai.partner_id != '1' and (oai.payment_term_id != '8' or oai.payment_term_id is null)
                    group by oaiteam
                    )T1
                    on ct.id = T1.oaiteam
                    left join 
                    (select 
                        sum(price_unit * quantity) as refundback_money,oai.team_id as oaiteam 
                    from account_invoice oai, account_invoice_line oail 
                    where oai.id = oail.invoice_id and oai.state = 'paid' and oai.type='out_refund'
                        and (oai.team_id not in ('86','153') and oai.team_id is not null)
                        and (oai.payment_term_id != '8' or oai.payment_term_id is null)
                        and oai.payment_done_date between (now() - interval '1 day 8 h') and now() - interval '8 h'
                        and oai.partner_id != '1' and (oai.payment_term_id != '8' or oai.payment_term_id is null)
                    group by oaiteam
                    )T2
                    on ct.id = T2.oaiteam where ct.id not in ('86','153') group by ct.id)
                T3 on T2.id = T3.oaiteam 
                left join
                (select 
                    ct.id as oaiteam,sum(COALESCE(T1.invoiceback_money, 0.0) -COALESCE(T2.refundback_money, 0.0)) AS openback_money
                from 
                    crm_team ct 
                left join 
                    (select 
                        sum(price_unit * quantity) as invoiceback_money,oai.team_id as oaiteam 
                    from account_invoice oai, account_invoice_line oail 
                    where oai.id = oail.invoice_id and oai.state = 'open' and oai.type='out_invoice'
                        and (oai.team_id not in ('86','153') and oai.team_id is not null)
                        and oai.partner_id != '1' and (oai.payment_term_id != '8' or oai.payment_term_id is null)
                    group by oaiteam
                    )T1
                    on ct.id = T1.oaiteam
                    left join 
                    (select 
                        sum(price_unit * quantity) as refundback_money,oai.team_id as oaiteam 
                    from account_invoice oai, account_invoice_line oail 
                    where oai.id = oail.invoice_id and oai.state = 'open' and oai.type='out_refund'
                        and (oai.team_id not in ('86','153') and oai.team_id is not null)
                        and oai.partner_id != '1' and (oai.payment_term_id != '8' or oai.payment_term_id is null)
                    group by oaiteam
                    )T2
                    on ct.id = T2.oaiteam where ct.id not in ('86','153') group by ct.id)
                T4 on T2.id = T4.oaiteam
                left join 
                (
                select 
                    sum(sq.qty* sq.cost) as stock,T.ctid,T.ctname 
                from stock_quant sq,
                (
                    select 
                        T_ware.slid,T_ware.id,T_ware.slname,T_ware.slcn,T_ware.swname,T_ware.swcode,T_team.ctid,T_team.ctname 
                    from
                    (
                        select 
                            T_location.slid as slid,T_location.slname as slname,T_location.slcn as slcn,
                            T_warehouse.id as id,T_warehouse.swname as swname,T_warehouse.swcode as swcode,T_location.slpl
                        from 
                            (select 
                                id as slid,name as slname,complete_name as slcn,parent_left as slpl 
                            from stock_location where usage = 'internal'
                            )T_location,
                            (select 
                                sw.id as id,parent_left as pl,parent_right as pr,sw.code as swcode,sw.name as swname 
                            from stock_location sl,stock_warehouse sw 
                            where sl.id = sw.view_location_id
                            )T_warehouse
                            where T_warehouse.pl <= T_location.slpl and T_warehouse.pr >= T_location.slpl
                    )T_ware left join 
                    (select 
                        sw.id as swid,ct.id as ctid,ct.name as ctname 
                    from crm_team ct,
                    stock_warehouse sw 
                    where sw.team_id = ct.id
                    )T_team
                    on T_team.swid = T_ware.id 
                        where T_ware.id not in ('3','121','127','15','115')
                    group by T_ware.id,T_ware.slname,T_ware.slcn,
                    T_ware.swname,T_ware.swcode,T_team.ctid,T_team.ctname,T_ware.slid
                )T
                where sq.location_id = T.slid 
                group by T.ctid,T.ctname
                )T5
                on T2.id = T5.ctid 
                full join 
                (select name,id from res_company)T6 on T6.id = T2.company_id
                group by T2.id,T1.sale_count,T1.gross_profit,T1.gross_margin,
                T3.paidback_money,T4.openback_money,T5.stock,T6.id
            """
        self.env.cr.execute(sql)

    company_id = fields.Many2one('res.company', string='Company')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    sale_count = fields.Float(digits=dp.get_precision('Product Price'))
    gross_profit = fields.Float(digits=dp.get_precision('Product Price'))
    gross_margin = fields.Float(digits=dp.get_precision('Product Price'))
    back_money = fields.Float(digits=dp.get_precision('Product Price'))
    accounts_receivable = fields.Float(digits=dp.get_precision('Product Price'))
    stock = fields.Float(digits=dp.get_precision('Product Price'))
    belong_date = fields.Datetime('belong date')


class hq_kpiByCate(models.Model):
    _name = 'hq.kpibycate'

    @api.model
    def run_kpibycate_scheduler(self):
        check_current_data(self, "hq_kpibycate")
        sql = """
            insert into 
                hq_kpibycate(category_id,sale_count,gross_profit,gross_margin,back_money,accounts_receivable,stock,belong_date) 
            select 
                T1.pcidd as pcid,round(T1.sale_count,2) as sale,round(T1.gross_profit,2) as gross_profit,T1.gross_margin as gross_margin,
                round(COALESCE(T2.paidback, 0.0),2) as back,round(COALESCE(T3.openback, 0.0),2) as open,
                T4.stock::decimal(16,2) as stock,now() - interval '8 h'
            from
                (select 
                    pc.id as pcid,sum((T.qty_delivered-T.qty_return) * T.price_unit) as sale_count,
                    sum((T.qty_delivered-T.qty_return) * T.price_unit-T.actual_cost) as gross_profit,
                    case when sum((T.qty_delivered-T.qty_return) * T.price_unit)=0 then NULL else 
                    round(sum((T.qty_delivered-T.qty_return) * T.price_unit-T.actual_cost) / 
                    sum((T.qty_delivered-T.qty_return) * T.price_unit)*100,2) end as gross_margin,
                    pc.id as pcidd
                from product_category pc 
                left join
                (select 
                    sol.qty_delivered as qty_delivered,sol.qty_return as qty_return,sol.price_unit as price_unit,
                    sol.actual_cost as actual_cost,pt.categ_id as category_id
                from sale_order so right join sale_order_line sol on so.id = sol.order_id  
                left join product_product pp 
                on sol.product_id = pp.id
                left join product_template pt
                on pp.product_tmpl_id = pt.id
                where so.team_id not in ('86','153') and so.partner_id != '1'
                and so.state in ('delivered', 'mark_paid', 'done')
                and so.payment_term_id != '8' 
                and so.create_date between (now() - interval '1 day 8 h') and now() - interval '8 h'
                )T
                on T.category_id = pc.id where pc.id !='4726'
                group by pc.id
                )T1
            left join
                (
                select T_invoice.category_id as category_id,
                    sum(COALESCE(T_INVOICE.openback, 0.0) -COALESCE(T_REFUND.openback, 0.0)) AS paidback
                from
                    (select 
                        sum(price_unit*quantity) as openback,pt.categ_id as category_id
                    from 
                        (select 
                            pail.price_unit as price_unit,pail.quantity as quantity,pail.product_id as product_id 
                        from account_invoice pai,account_invoice_line pail 
                        where pai.id = pail.invoice_id and pai.state = 'paid' and pai.type='out_invoice'
                            and pai.team_id not in ('86','153') 
                            and (pai.partner_id != '1' or pai.partner_id is null) 
                            and pai.payment_done_date between (now() - interval '1 day 8 h') and now() - interval '8 h'
                            and (pai.payment_term_id != '8' or pai.payment_term_id is null)
                        )T1
                        left join product_product pp on T1.product_id = pp.id
                        left join product_template pt on pp.product_tmpl_id = pt.id where pt.categ_id != '4726'
                        group by pt.categ_id
                    )T_INVOICE 
                    left join
                    (select 
                        sum(price_unit*quantity) as openback,pt.categ_id as category_id
                    from 
                        (select 
                            pail.price_unit as price_unit,pail.quantity as quantity,pail.product_id as product_id 
                        from account_invoice pai,account_invoice_line pail 
                        where pai.id = pail.invoice_id and pai.state = 'paid' and pai.type='out_refund'
                        and pai.team_id not in ('86','153')
                        and (pai.partner_id != '1' or pai.partner_id is null) 
                        and pai.payment_done_date between (now() - interval '1 day 8 h') and now() - interval '8 h'
                        and (pai.payment_term_id != '8' or pai.payment_term_id is null)
                        )T1
                        left join product_product pp on T1.product_id = pp.id
                        left join product_template pt on pp.product_tmpl_id = pt.id where pt.categ_id != '4726'
                        group by pt.categ_id
                    )T_REFUND
                    on T_INVOICE.category_id = T_REFUND.category_id group by T_invoice.category_id
                )T2
            on T2.category_id = T1.pcidd  
            left join
                (
                select T_invoice.category_id as category_id,
                     sum(COALESCE(T_INVOICE.openback, 0.0) -COALESCE(T_REFUND.openback, 0.0)) AS openback
                from
                    (select 
                        sum(price_unit*quantity) as openback,pt.categ_id as category_id
                    from 
                        (select 
                            pail.price_unit as price_unit,pail.quantity as quantity,pail.product_id as product_id 
                        from account_invoice pai,account_invoice_line pail 
                        where pai.id = pail.invoice_id and pai.state = 'open' and pai.type='out_invoice'
                            and pai.team_id not in ('86','153') 
                            and (pai.partner_id != '1' or pai.partner_id is null)
                            and (pai.payment_term_id != '8' or pai.payment_term_id is null)
                        )T1
                        left join product_product pp on T1.product_id = pp.id
                        left join product_template pt on pp.product_tmpl_id = pt.id where pt.categ_id !='4726'
                        group by pt.categ_id
                    )T_INVOICE 
                    left join
                    (select 
                        sum(price_unit*quantity) as openback,pt.categ_id as category_id
                    from 
                        (select 
                            pail.price_unit as price_unit,pail.quantity as quantity,pail.product_id as product_id 
                        from account_invoice pai,account_invoice_line pail 
                        where pai.id = pail.invoice_id and pai.state = 'open' and pai.type='out_refund'
                        and pai.team_id not in ('86','153')
                        and (pai.partner_id != '1' or pai.partner_id is null) 
                        and (pai.payment_term_id != '8' or pai.payment_term_id is null)
                        )T1
                        left join product_product pp on T1.product_id = pp.id
                        left join product_template pt on pp.product_tmpl_id = pt.id where pt.categ_id != '4726'
                        group by pt.categ_id
                    )T_REFUND
                    on T_INVOICE.category_id = T_REFUND.category_id group by T_invoice.category_id
                )T3
            on T3.category_id = T1.pcidd
            left join
                (
                select 
                    sum(TT.qty*TT.cost) as stock,pt.categ_id as category_id
                FROM
                    (select 
                        sq.product_id as product_id,sq.qty as qty,sq.cost as cost 
                    from stock_quant sq,
                        (
                        select 
                            T_ware.slid as slid,T_ware.id as id,T_ware.slname as slname,T_ware.slcn as slcn,T_ware.swname as swname,T_ware.swcode as swcode,T_team.ctid as ctid,T_team.ctname as ctname 
                        from
                        (
                            select 
                                T_location.slid as slid,T_location.slname as slname,T_location.slcn as slcn,
                                T_warehouse.id as id,T_warehouse.swname as swname,T_warehouse.swcode as swcode,T_location.slpl
                            from 
                                (select 
                                    id as slid,name as slname,complete_name as slcn,parent_left as slpl 
                                from stock_location where usage = 'internal'
                                )T_location,
                                (select 
                                    sw.id as id,parent_left as pl,parent_right as pr,sw.code as swcode,sw.name as swname 
                                from stock_location sl,stock_warehouse sw 
                                where sl.id = sw.view_location_id
                                )T_warehouse
                                where T_warehouse.pl <= T_location.slpl and T_warehouse.pr >= T_location.slpl
                        )T_ware left join 
                        (select 
                            sw.id as swid,ct.id as ctid,ct.name as ctname 
                        from crm_team ct,
                        stock_warehouse sw 
                        where sw.team_id = ct.id
                        )T_team
                        on T_team.swid = T_ware.id
                            where T_ware.id not in ('3','121','127','15','115')
                        group by T_ware.id,T_ware.slname,T_ware.slcn,
                        T_ware.swname,T_ware.swcode,T_team.ctid,T_team.ctname,T_ware.slid
                    )T
                    where sq.location_id = T.slid
                    )TT
                    left join product_product pp on TT.product_id = pp.id
                    left join product_template pt on pp.product_tmpl_id = pt.id where pt.categ_id != '4726'
                    group by pt.categ_id
               )T4
            on T4.category_id = T1.pcidd
        """
        self.env.cr.execute(sql)

    category_id = fields.Many2one('product.category', string='Product Category')
    sale_count = fields.Float(digits=dp.get_precision('Product Price'))
    gross_profit = fields.Float(digits=dp.get_precision('Product Price'))
    gross_margin = fields.Float(digits=dp.get_precision('Product Price'))
    back_money = fields.Float(digits=dp.get_precision('Product Price'))
    accounts_receivable = fields.Float(digits=dp.get_precision('Product Price'))
    stock = fields.Float(digits=dp.get_precision('Product Price'))
    belong_date = fields.Datetime('belong date')


def check_current_data(self, table_name):
    sql = """
        select count(*) from %s WHERE to_char(belong_date,'YYYY-mm-DD') = TO_CHAR(now() - interval '8 h','YYYY-mm-DD') 
    """ % table_name
    self.env.cr.execute(sql)
    num = self.env.cr.fetchone()[0]
    if num != 0:
        raise ValidationError("今日统计报表数据已存在,不能再次生成数据(测试人员可以删除数据测试)")



class hq_stockByDay(models.Model):
    _name = "hq.stockbyday"

    @api.model
    def run_stockbyday_scheduler(self):
        check_current_data(self, "hq_stockbyday")
        sql = """
            insert into hq_stockbyday(company_id,stock,belong_date)
            select 
                rc.id,A.stock,now() - interval '8 h'
            from res_company rc 
            left join
               (select 
                   sq.company_id as company_id,(sum(sq.qty* sq.cost))::decimal(16,2) as stock
               from stock_quant sq,
               (
                   select 
                       T_ware.slid as slid,T_ware.id as id
                   from
                   (
                       select 
                           T_location.slid as slid,T_warehouse.id as id
                       from 
                           (select 
                               id as slid,name as slname,complete_name as slcn,parent_left as slpl 
                           from stock_location where usage = 'internal'
                           )T_location,
                           (select 
                               sw.id as id,parent_left as pl,parent_right as pr,sw.code as swcode,sw.name as swname 
                           from stock_location sl,stock_warehouse sw 
                           where sl.id = sw.view_location_id 
                           and sw.id not in ('3','121','127','15','115')
                           )T_warehouse
                           where T_warehouse.pl <= T_location.slpl and T_warehouse.pr >= T_location.slpl
                    )T_ware 
                )T
            where sq.location_id = T.slid 
            group by sq.company_id)A on rc.id = A.company_id
        """
        self.env.cr.execute(sql)

    company_id = fields.Many2one('res.company', string='Company')
    stock = fields.Float(digits=dp.get_precision('Product Price'))
    belong_date = fields.Datetime('belong date')



