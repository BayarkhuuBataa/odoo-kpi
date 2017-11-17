# -*- coding: utf-8 -*-
# 后期根据查找的数据条件重构sql代码,也许后期就在明天

from odoo import api, models


def _get_all_data(self, data_area, type):
    sql = ''
    records = None
    if type == 'day':
        if data_area == 'all':
            sql = """
                with table1 as
                    (select 
                        T2.day as day,T2.sale_count as sale_count,T2.gross_profit as gross_profit,
                        T2.gross_margin as gross_margin,T2.back_money as back_money,
                        T1.stock as stock,T2.accounts_receivable as accounts_receivable,
                        T_COM.name as name,T_COM.id as id 
                    from
                        (select id,name from res_company where id !=10)T_COM full JOIN 
                        (
                            select to_char(belong_date,'YYYY-mm-DD') as day,stock as stock,company_id as company_id
                            from hq_stockbyday
                            WHERE to_char(belong_date,'YYYY-MM') = 
                                (SELECT max(to_char(belong_date,'YYYY-mm')) FROM hq_stockbyday) and company_id !=10
                        )T1 
                        ON T_COM.id = T1.company_id 
                        full join
                        (SELECT 
                            to_char(belong_date,'YYYY-mm-DD') AS day,company_id,sum(sale_count) AS sale_count,
                            sum(gross_profit) AS gross_profit,
                            case when sum(sale_count)=0 then NULL else
                            round(sum(gross_profit)/sum(sale_count)*100,2) END AS gross_margin, 
                            sum(back_money) AS back_money,
                            sum(accounts_receivable) AS accounts_receivable
                        FROM hq_kpibyteam 
                        WHERE to_char(belong_date,'YYYY-MM') = 
                            (SELECT max(to_char(belong_date,'YYYY-mm')) FROM hq_kpibyteam) and company_id !=10
                        group by company_id,day
                        )T2 
                        on T1.company_id = T2.company_id and T1.day = T2.day order by T1.day desc,T1.company_id asc)
                    (select 
                        day,sum(sale_count) as sale_count,sum(gross_profit) as gross_profit,
                        case when sum(sale_count)=0 then NULL else
                        round((sum(gross_profit)/sum(sale_count)*100),2) END as gross_margin,sum(back_money) as back_money,
                        sum(stock) as stock,sum(accounts_receivable) as accounts_receivable,
                        '北京人和易行科技有限公司' as name,'1' as id from table1 
                        where id is null or id = '1' group by day)
                     union
                    (select 
                        day,sale_count,gross_profit,
                        case when sale_count=0 then NULL else
                        round((gross_profit/sale_count*100),2) END as gross_margin,back_money,stock,
                        accounts_receivable,name,id from table1 where id !='1' and id is not null) 
                    order by day desc,id asc
            """
        elif data_area == 'team':
            sql = """
                SELECT 
                    T_DAY.day AS day_time,T_TEAM.name AS team_name,T_DAY.sale_count AS day_sale_count,
                    T_DAY.gross_profit AS day_gross_profit,T_DAY.gross_margin AS day_gross_margin,
                    T_DAY.back_money AS day_back_money,T_DAY.accounts_receivable AS day_accounts_receivable,
                    T_DAY.stock AS day_stock,
                    T_MONTH.YEAR AS month_time,T_MONTH.sale_count AS month_sale_count,
                    T_MONTH.gross_profit AS month_gross_profit,T_MONTH.gross_margin AS month_gross_margin,
                    T_MONTH.back_money AS month_back_money,T_MONTH.accounts_receivable AS month_accounts_receivable,
                    T_MONTH.stock AS month_stock,
                    T_TEAM.sale_target AS sale_target,T_TEAM.profit_target AS profit_target,
                    T_TEAM.back_target AS back_target,
                    T_TEAM.turnover_target AS turnover_target,
                    case when T_TEAM.sale_target=0 then 0.0 else
                    round(T_MONTH.sale_count/T_TEAM.sale_target*100,2) end AS sale_rate,
                    case when T_TEAM.profit_target=0 then 0.0 else
                    round(T_MONTH.gross_profit/T_TEAM.profit_target*100,2) end AS profit_rate,
                    case when T_TEAM.back_target=0 then 0.0 else
                    round(T_MONTH.back_money/T_TEAM.back_target*100,2) end AS back_rate,
                    T_TEAM.id AS team_id,
                    T_TEAM.company_id as company_id,
                    T_TEAM.company_name as company_name
                FROM
                    (SELECT 
                        to_char(belong_date,'YYYY-mm-DD') AS day,
                        to_char(belong_date,'YYYY-mm') AS month,
                        sale_count AS sale_count,
                        gross_profit AS gross_profit,
                        gross_margin AS gross_margin, 
                        back_money AS back_money, 
                        accounts_receivable AS accounts_receivable, 
                        stock AS stock,
                        team_id AS team_id
                    FROM hq_kpibyteam 
                    WHERE to_char(belong_date,'YYYY-mm-DD') = 
                        (SELECT max(to_char(belong_date,'YYYY-mm-DD')) FROM hq_kpibyteam) 
                    ORDER BY team_id
                    )t_DAY
                LEFT JOIN
                    (SELECT 
                        T1.year AS year,T1.team_id AS team_id,T1.sale_count AS sale_count,
                        T1.gross_profit AS gross_profit,T1.gross_margin AS gross_margin,
                        T1.back_money AS back_money,T1.stock AS stock,T2.accounts_receivable AS accounts_receivable 
                    FROM
                        (SELECT   
                            to_char(belong_date,'YYYY-mm') AS year,
                            sum(sale_count) AS sale_count,
                            sum(gross_profit) AS gross_profit,
                            case when sum(sale_count)=0 then NULL else
                            round(sum(gross_profit)/sum(sale_count)*100,2) END AS gross_margin, 
                            sum(back_money) AS back_money, 
                            round(sum(stock)/to_number((SELECT max(to_char(belong_date,'DD'))),'99999'),2) AS stock,
                            team_id AS team_id
                        FROM hq_kpibyteam GROUP BY year,team_id ORDER BY year DESC
                        )T1,
                        (SELECT 
                            to_char(belong_date,'YYYY-mm') AS year, 
                            team_id AS team_id, 
                            sum(accounts_receivable) AS accounts_receivable 
                        FROM hq_kpibyteam 
                        WHERE to_char(belong_date,'YYYY-mm-DD') 
                        IN 
                        (
                            SELECT max(to_char(belong_date,'YYYY-mm-DD')) 
                            FROM hq_kpibyteam GROUP BY to_char(belong_date,'YYYY-mm')) 
                            GROUP BY team_id,year ORDER BY year DESC
                        )T2
                        WHERE T1.team_id = t2.team_id AND T1.year = T2.year 
                        )T_MONTH
                ON T_DAY.team_id = T_MONTH.team_id AND T_MONTH.year = T_DAY.month
                LEFT JOIN 
                    (SELECT ct.id as id,ct.name as name,ct.sale_target as sale_target,ct.profit_target as profit_target,
                        ct.back_target as back_target,ct.turnover_target as turnover_target,
                        rc.id as company_id,rc.name as company_name FROM crm_team ct 
                        left join res_company rc on ct.company_id = rc.id ORDER BY company_id DESC)T_TEAM
                ON T_DAY.team_id = T_TEAM.id where T_TEAM.id is not NULL ORDER BY T_TEAM.company_id DESC
            """
        elif data_area == 'type':
            sql = """
                SELECT 
                    T_DAY.day AS day_time,T_CATE.name AS category_name,T_DAY.sale_count AS day_sale_count,
                    T_DAY.gross_profit AS day_gross_profit,T_DAY.gross_margin AS day_gross_margin,
                    T_DAY.back_money AS day_back_money,T_DAY.accounts_receivable AS day_accounts_receivable,
                    T_DAY.stock AS day_stock,T_MONTH.YEAR AS month_time,T_MONTH.sale_count AS month_sale_count,
                    T_MONTH.gross_profit AS month_gross_profit,T_MONTH.gross_margin AS month_gross_margin,
                    T_MONTH.back_money AS month_back_money,T_MONTH.accounts_receivable AS month_accounts_receivable,
                    T_MONTH.stock AS month_stock,T_CATE.id AS category_id
                FROM 
                    (SELECT 
                        to_char(belong_date,'YYYY-mm-DD') AS day,
                        to_char(belong_date,'YYYY-mm') AS month,
                        sale_count AS sale_count,
                        gross_profit AS gross_profit,
                        gross_margin AS gross_margin, 
                        back_money AS back_money, 
                        accounts_receivable AS accounts_receivable,
                        stock AS stock,
                        category_id AS category_id
                    FROM hq_kpibycate 
                    WHERE to_char(belong_date,'YYYY-mm-DD') = 
                        (SELECT max(to_char(belong_date,'YYYY-mm-DD')) FROM hq_kpibycate) 
                    ORDER BY category_id)T_DAY 
                LEFT JOIN
                    (SELECT 
                        T1.year,T1.category_id,T1.sale_count,T1.gross_profit,T1.gross_margin,T1.back_money,
                        T1.stock,T2.accounts_receivable 
                    FROM
                        (SELECT   
                            to_char(belong_date,'YYYY-mm') AS year,
                            sum(sale_count) AS sale_count,
                            sum(gross_profit) AS gross_profit,
                            case when sum(sale_count)=0 then NULL else
                            round(sum(gross_profit)/sum(sale_count)*100,2) END AS gross_margin, 
                            sum(back_money) AS back_money, 
                            round(sum(stock)/to_number((SELECT max(to_char(belong_date,'DD'))),'99999'),2) AS stock,
                            category_id AS category_id
                        FROM hq_kpibycate
                        GROUP BY year,category_id ORDER BY year DESC)T1,
                        (SELECT 
                            to_char(belong_date,'YYYY-mm') AS year, 
                            category_id AS category_id, 
                            sum(accounts_receivable) AS accounts_receivable 
                        FROM hq_kpibycate 
                        WHERE to_char(belong_date,'YYYY-mm-DD') 
                        IN (SELECT max(to_char(belong_date,'YYYY-mm-DD')) FROM hq_kpibycate 
                            GROUP BY to_char(belong_date,'YYYY-mm')) GROUP BY category_id,year ORDER BY year DESC)T2 
                        WHERE T1.category_id = t2.category_id AND T1.year = T2.year)T_MONTH 
                ON T_DAY.category_id = T_MONTH.category_id AND T_MONTH.year = T_DAY.month
                LEFT JOIN (SELECT id,name FROM product_category)T_CATE
                ON T_DAY.category_id = T_CATE.id
            """
    elif type == 'month':
        if data_area == 'all':
            sql = """
                with table1 as
                (SELECT 
                    T1.month,T1.sale_count,T1.gross_profit,T1.gross_margin,
                    T1.back_money,T3.stock,T2.accounts_receivable,T_COM.name,T_COM.id
                    FROM (select id,name from res_company where id !=10)T_COM full JOIN
                    (SELECT 
                        to_char(belong_date,'YYYY-mm') AS month,
                        company_id,
                        sum(sale_count) AS sale_count,
                        sum(gross_profit) AS gross_profit,
                        case when sum(sale_count)=0 then NULL else
                        round(sum(gross_profit)/sum(sale_count)*100,2) END AS gross_margin, 
                        sum(back_money) AS back_money
                    FROM hq_kpibyteam where company_id !=10 GROUP BY month,company_id ORDER BY month DESC
                    )T1 on T1.company_id = T_COM.id 
                    left join
                    (SELECT 
                        to_char(belong_date,'YYYY-mm') AS month,
                        company_id,
                        sum(accounts_receivable) AS accounts_receivable FROM hq_kpibyteam 
                        WHERE to_char(belong_date,'YYYY-mm-DD') 
                        IN (SELECT max(to_char(belong_date,'YYYY-mm-DD')) FROM hq_kpibyteam 
                        GROUP BY to_char(belong_date,'YYYY-mm')) and company_id!=10 GROUP BY month,company_id
                    )T2 
                    on T1.month = T2.month and T1.company_id = T2.company_id
                    left join
                    (select company_id,to_char(belong_date,'YYYY-mm') AS month,
                        round(sum(stock)/to_number((SELECT max(to_char(belong_date,'DD'))),'99999'),2) 
                    AS stock from hq_stockbyday where company_id !=10 GROUP BY month,company_id ORDER BY month DESC
                    )T3
                    on T3.company_id = T1.company_id and T3.month = T1.month 
                order by T1.month desc,T1.company_id asc)
                (select 
                    month,sum(sale_count) as sale_count,sum(gross_profit) as gross_profit,
                    case when sum(sale_count)=0 then NULL else
                    round(sum(gross_profit)/sum(sale_count)*100,2) END as gross_margin,sum(back_money) as back_money,sum(stock) as stock,
                    sum(accounts_receivable) as accounts_receivable,
                    '北京人和易行科技有限公司' as name,'1' as id from table1 where id is null or id = '1' group by month) 
                 union
                 (select 
                     month,sale_count,gross_profit,
                     case when sale_count=0 then NULL else
                     round(gross_profit/sale_count*100,2) END as gross_margin,back_money,stock,
                     accounts_receivable,name,id from table1 where id !='1' and id is not null) 
                 order by month desc,id asc
            """
        elif data_area == 'team':
            sql = """
                SELECT 
                    T1.year,T_TEAM.name,T1.sale_count,T1.gross_profit,T1.gross_margin,T1.back_money,T1.stock,
                    T2.accounts_receivable,T_TEAM.sale_target AS sale_target,T_TEAM.profit_target AS profit_target,
                    T_TEAM.back_target AS back_target,
                    T_TEAM.turnover_target AS turnover_target,
                    case when T_TEAM.sale_target=0 then 0 else
                    round(T1.sale_count/T_TEAM.sale_target*100,2) end AS sale_rate,
                    case when T_TEAM.profit_target=0 then 0 else
                    round(T1.gross_profit/T_TEAM.profit_target*100,2) end AS profit_rate,
                    case when T_TEAM.back_target=0 then 0 else
                    round(T1.back_money/T_TEAM.back_target*100,2) end AS back_rate,
                    T_TEAM.id AS team_id,
                    T_TEAM.company_id AS company_id,
                    T_TEAM.company_name AS company_name
                FROM
                (SELECT   
                    to_char(belong_date,'YYYY-mm') AS year,
                    sum(sale_count) AS sale_count,
                    sum(gross_profit) AS gross_profit,
                    case when sum(sale_count)=0 then NULL else
                    round(sum(gross_profit)/sum(sale_count)*100,2) END AS gross_margin, 
                    sum(back_money) AS back_money, 
                    round(sum(stock)/to_number((SELECT max(to_char(belong_date,'DD'))),'99999'),2) AS stock,
                    team_id AS team_id
                FROM hq_kpibyteam GROUP BY year,team_id ORDER BY year DESC
                )T1 
                LEFT JOIN
                (SELECT 
                    to_char(belong_date,'YYYY-mm') AS year, 
                    team_id AS team_id, 
                    sum(accounts_receivable) AS accounts_receivable 
                FROM hq_kpibyteam WHERE to_char(belong_date,'YYYY-mm-DD') 
                IN (SELECT max(to_char(belong_date,'YYYY-mm-DD')) FROM hq_kpibyteam 
                GROUP BY to_char(belong_date,'YYYY-mm')) 
                GROUP BY team_id,year ORDER BY year DESC)T2 
                ON T1.team_id = t2.team_id AND T1.year = T2.year
                LEFT JOIN 
                (SELECT ct.id as id,ct.name as name,ct.sale_target as sale_target,ct.profit_target as profit_target,
                        ct.back_target as back_target,ct.turnover_target as turnover_target,
                        rc.id as company_id,rc.name as company_name FROM crm_team ct 
                        left join res_company rc on ct.company_id = rc.id ORDER BY company_id DESC )T_TEAM
                ON T1.team_id = T_TEAM.id where T_TEAM.id is not NULL ORDER BY T1.year DESC,T_TEAM.company_id DESC
        """
        elif data_area == 'type':
            sql = """
                SELECT 
                    T1.year,T_CATE.name,T1.sale_count,T1.gross_profit,T1.gross_margin,T1.back_money,
                    T1.stock,T2.accounts_receivable,T_CATE.id 
                FROM
                    (SELECT   
                        to_char(belong_date,'YYYY-mm') AS year,
                        sum(sale_count) AS sale_count,
                        sum(gross_profit) AS gross_profit,
                        case when sum(sale_count)=0 then NULL else
                        round(sum(gross_profit)/sum(sale_count)*100,2) END AS gross_margin, 
                        sum(back_money) AS back_money, 
                        round(sum(stock)/to_number((SELECT max(to_char(belong_date,'DD'))),'99999'),2) AS stock,
                        category_id AS category_id
                    FROM hq_kpibycate GROUP BY year,category_id ORDER BY year DESC
                    )T1 
                    LEFT JOIN
                    (SELECT
                        to_char(belong_date,'YYYY-mm') AS year,
                        category_id AS category_id,
                        sum(accounts_receivable) AS accounts_receivable 
                    FROM hq_kpibycate WHERE to_char(belong_date,'YYYY-mm-DD') 
                        IN (SELECT max(to_char(belong_date,'YYYY-mm-DD')) FROM hq_kpibycate
                        GROUP BY to_char(belong_date,'YYYY-mm')) 
                    GROUP BY category_id,year ORDER BY year DESC
                    )T2 
                    ON T1.category_id = t2.category_id AND T1.year = T2.year 
                    LEFT JOIN 
                    (SELECT id,name FROM product_category)T_CATE
                    ON T1.category_id = T_CATE.id where T_CATE.id is not null ORDER BY T1.year DESC
            """
    if sql is not None:
        self.env.cr.execute(sql)
        records = self.env.cr.fetchall()
    return records


def _get_sql_date(self, data_area):
    sql = ''
    all_records = None
    if data_area == 'type':
        sql = """
            SELECT DISTINCT(to_char(belong_date,'YYYY-mm')) AS month FROM hq_kpibycate 
            ORDER BY to_char(belong_date,'YYYY-mm') DESC
        """
    elif data_area == 'team':
        sql = """
            SELECT DISTINCT(to_char(belong_date,'YYYY-mm')) AS month FROM hq_kpibyteam 
            ORDER BY to_char(belong_date,'YYYY-mm') DESC
        """
    if sql is not None:
        self.env.cr.execute(sql)
        all_records = self.env.cr.fetchall()
    return all_records


def _format_type_data(records, all_date):
    data_list = list()
    for date in all_date:
        all_data = dict()
        all_data['time'] = date[0]
        one_data = list()
        for record in records:
            if str(record[0]) == str(date[0]):
                one_data.append(record)
        all_data['value'] = one_data
        data_list.append(all_data)
    return data_list


def _get_all_company(self):
    all_company = None
    sql = """
            select id,name from res_company where id in
            (select distinct(company_id) as company_id 
            from hq_kpibyteam where company_id !=10 and company_id is not null ORDER BY company_id ASC) 
            order by id asc
        """
    if sql is not None:
        self.env.cr.execute(sql)
        all_company = self.env.cr.fetchall()
    return all_company


def _format_team_month_data(all_data_team, all_company, all_date):
    data_list = list()
    for date in all_date:
        all_data = dict()
        all_data['time'] = date[0]
        aa = list()
        # no_company = list()
        for company in all_company:
            # no_company_recode = None
            one_company_data = dict()
            one_company_data['company'] = company[1]
            one_data = list()
            for record in all_data_team:
                # if record[16] is None and str(record[0]) == str(date[0]):
                #     no_company_recode = record
                if record[16] is not None:
                    if record[16] == company[0] and str(record[0]) == str(date[0]):
                        one_data.append(record)
            # if company[0] == 1:
            #     one_data.append(no_company_recode)
            one_company_data['value'] = one_data
            aa.append(one_company_data)
        # all_data1 = dict()
        # all_data1['company'] = '未定义公司'
        # all_data1['value'] = no_company
        # aa.append(all_data1)
        all_data['value'] = aa
        data_list.append(all_data)
    return data_list


def _format_team_day_data(records, all_company):
    data_list = list()
    # no_company_record = None
    for company in all_company:
        all_data = dict()
        all_data['company'] = company[1]
        one_data = list()
        for record in records:
            # if record[23] is None:
            #     no_company_record = record
            if record[23] is not None:
                if str(record[23]) == str(company[0]):
                    one_data.append(record)
        # if company[0] == 1:
        #     one_data.append(no_company_record)
        all_data['value'] = one_data
        data_list.append(all_data)
    return data_list


class kpi_Report(models.AbstractModel):
    _name = 'report.hq_kpi.kpi_report'

    def render_html(self, docids, data):
        Report = self.env['report']
        report = Report._get_report_from_name('hq_kpi.kpi_day_team_report')
        data_area = data['data']
        type = data['type']
        all_data = _get_all_data(self, data_area, type)
        all_date = ''
        if (data_area == 'team' and type == 'month') or (data_area == 'type' and type == 'month'):
            all_date = _get_sql_date(self, data_area)
        all_company = _get_all_company(self)
        if data_area == 'type' and type == 'month':
            all_data = _format_type_data(all_data, all_date)
        if data_area == 'team' and type == 'month':
            all_data = _format_team_month_data(all_data, all_company, all_date)
        if data_area == 'team' and type == 'day':
            all_data = _format_team_day_data(all_data,all_company)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'title': "KPI报表",
            'docs': all_data,
            'data': data,
            'get_turn_over': self._get_turn_data
        }
        return Report.render('hq_kpi.kpi_report', docargs)

    def _get_turn_data(self, type, time, company=None, team_id=None, category_id=None):
        sql = ''
        if company is None:
            company = ''
        turnover = None
        if type == 'day' and team_id == '' and category_id == '':
            sql = """
                select 
                    case when T4.stock=0 then NULL else 
                    round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)),2) end
                from
                    (select sum(sale_count) as sale_count from hq_kpibyteam 
                        where to_char(belong_date,'YYYY-mm-DD') = {} and company_id = {}
                    )T1,
                    (select 
                        to_number(to_char(EXTRACT(DAY from date_trunc('month', 
                        (select distinct(belong_date) from hq_kpibyteam 
                        where to_char(belong_date,'YYYY-mm-DD') = {} and company_id = {})+interval '1 month') 
                        - interval '0 month'- interval '1 day'),'99999'),'99999') as month_num
                    )T2,
                    (select 
                        to_number(to_char((
                            select distinct(belong_date) from hq_kpibyteam 
                            where to_char(belong_date,'YYYY-mm-DD')={} and company_id = {}),'DD'),'99999') as current_day
                    )T3,
                    (select sum(stock) as stock from hq_stockbyday
                        where to_char(belong_date,'YYYY-mm') = 
                        to_char((select distinct(belong_date) from hq_kpibyteam 
                                 where to_char(belong_date,'YYYY-mm-DD') = {} and company_id = {}),'YYYY-mm')
                    )T4
            """.format("'" + str(time) + "'", "'" + str(company) + "'", "'" + str(time) + "'",
                       "'" + str(company) + "'", "'" + str(time) + "'", "'" + str(company) + "'",
                       "'" + str(time) + "'", "'" + str(company) + "'")
        if type == 'month' and team_id == '' and category_id == '':
            sql = """
               select 
               case when T4.stock=0 then NULL else 
                   round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)),2) end
               from
                   (select sum(sale_count) as sale_count from hq_kpibyteam 
                       where to_char(belong_date,'YYYY-mm') = {} and company_id = {}
                   )T1,
                   (select 
                       to_number(to_char(EXTRACT(DAY from date_trunc('month', 
                       (select max(distinct(belong_date)) from hq_kpibyteam 
                       where to_char(belong_date,'YYYY-mm') = {} and company_id = {})+interval '1 month')
                       - interval '0 month'- interval '1 day'),'99999'),'99999') as month_num
                   )T2,
                   (select 
                       to_number(to_char((
                       select max(distinct(belong_date)) from hq_kpibyteam 
                       where to_char(belong_date,'YYYY-mm') = {} and company_id = {}),'DD'),'99999') as current_day
                   )T3,
                   (select sum(stock) as stock from hq_stockbyday
                       where to_char(belong_date,'YYYY-mm') = {} and company_id = {}
                   )T4 
            """.format("'" + str(time) + "'", "'" + str(company) + "'", "'" + str(time) + "'", "'" + str(company) + "'",
                       "'" + str(time) + "'", "'" + str(company) + "'", "'" + str(time) + "'", "'" + str(company) + "'")
        if type == 'day' and team_id != '' and category_id == '':
            sql = """
                select 
                    case when T4.stock=0 then NULL else 
                        round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)),2) end,
                    case when T4.stock=0 then NULL when T5.turnover_target=0 then NULL else 
                        round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)
                            /T5.turnover_target)*100,2) end
                    as turnover_target 
                from
                    (select sum(sale_count) as sale_count from hq_kpibyteam 
                        where to_char(belong_date,'YYYY-mm-DD') = {} and team_id = {}
                    )T1,
                    (select 
                        to_number(to_char(EXTRACT(DAY from date_trunc('month', 
                        (select distinct(belong_date) from hq_kpibyteam where to_char(belong_date,'YYYY-mm-DD') = {})
                        +interval '1 month')- interval '0 month'- interval '1 day'),'99999'),'99999') as month_num
                    )T2,
                    (select to_number(to_char((
                        select distinct(belong_date) from hq_kpibyteam 
                        where to_char(belong_date,'YYYY-mm-DD') = {}),'DD'),'99999') as current_day
                    )T3,
                    (select sum(stock) as stock from hq_kpibyteam where to_char(belong_date,'YYYY-mm') = 
                        to_char((select distinct(belong_date) from hq_kpibyteam 
                                 where to_char(belong_date,'YYYY-mm-DD') = {}),'YYYY-mm')  and team_id = {}
                    )T4,
                    (select turnover_target from crm_team where id = {})T5
            """.format("'" + str(time) + "'", "'" + str(team_id) + "'", "'" + str(time) + "'",
                       "'" + str(time) + "'", "'" + str(time) + "'", "'" + str(team_id) + "'", "'" + str(team_id) + "'")
        if type == 'month' and team_id != '' and category_id == '':
            sql = """
                select 
                    case when T4.stock=0 then NULL else 
                        round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)),2) end,
                    case when T4.stock=0 then NULL when T5.turnover_target=0 then NULL else
                        round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)
                    /T5.turnover_target)*100,2) end
                from
                    (select sum(sale_count) as sale_count from hq_kpibyteam 
                        where to_char(belong_date,'YYYY-mm') = {} and team_id = {}
                    )T1,
                    (select 
                        to_number(to_char(EXTRACT(DAY from date_trunc('month', 
                            (select max(distinct(belong_date)) from hq_kpibyteam 
                            where to_char(belong_date,'YYYY-mm') = {})+interval '1 month')
                            - interval '0 month'- interval '1 day'),'99999'),'99999') as month_num
                    )T2,
                    (select to_number(to_char((
                        select max(distinct(belong_date)) from hq_kpibyteam 
                        where to_char(belong_date,'YYYY-mm') = {}),'DD'),'99999') as current_day
                    )T3,
                    (select sum(stock) as stock from hq_kpibyteam 
                        where to_char(belong_date,'YYYY-mm') = {} and team_id = {}
                    )T4,
                    (select turnover_target from crm_team where id = {})T5
            """.format("'" + str(time) + "'", "'" + str(team_id) + "'", "'" + str(time) + "'",
                       "'" + str(time) + "'", "'" + str(time) + "'", "'" + str(team_id) + "'", "'" + str(team_id) + "'")
        if type == 'day' and team_id == '' and category_id != '':
            sql = """
                select 
                case when T4.stock=0 then NULL else 
                    round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)),2) end
                from
                    (select sum(sale_count) as sale_count from hq_kpibycate 
                        where to_char(belong_date,'YYYY-mm-DD') = {} and category_id = {}
                    )T1,
                    (select 
                        to_number(to_char(EXTRACT(DAY from date_trunc('month', 
                        (select distinct(belong_date) from hq_kpibycate 
                        where to_char(belong_date,'YYYY-mm-DD') = {})+interval '1 month')- 
                        interval '0 month'- interval '1 day'),'99999'),'99999') as month_num
                    )T2,
                    (select to_number(to_char((
                        select distinct(belong_date) from hq_kpibycate 
                        where to_char(belong_date,'YYYY-mm-DD') = {}),'DD'),'99999') 
                        as current_day
                    )T3,
                    (select sum(stock) as stock from hq_kpibycate 
                        where to_char(belong_date,'YYYY-mm') = 
                        to_char((select distinct(belong_date) from hq_kpibyteam where 
                        to_char(belong_date,'YYYY-mm-DD') = {}),'YYYY-mm') and category_id = {}
                    )T4
            """.format("'" + str(time) + "'", "'" + str(category_id) + "'", "'" + str(time) + "'",
                       "'" + str(time) + "'", "'" + str(time) + "'", "'" + str(category_id) + "'")
        if type == 'month' and team_id == '' and category_id != '':
            sql = """
                select 
                case when T4.stock=0 then NULL else 
                    round(((T1.sale_count * month_num/T3.current_day)*12/(T4.stock/T3.current_day)),2) end
                from
                    (select sum(sale_count) as sale_count from hq_kpibycate 
                        where to_char(belong_date,'YYYY-mm') = {} and category_id = {}
                    )T1,
                    (select 
                        to_number(to_char(EXTRACT(DAY from date_trunc('month', 
                        (select max(distinct(belong_date)) from hq_kpibycate where 
                        to_char(belong_date,'YYYY-mm') = {})+interval '1 month')- 
                        interval '0 month'- interval '1 day'),'99999'),'99999') as month_num
                    )T2,
                    (select to_number(to_char((
                        select max(distinct(belong_date)) from hq_kpibycate where 
                        to_char(belong_date,'YYYY-mm') = {}),'DD'),'99999') as current_day
                    )T3,
                    (select sum(stock) as stock from hq_kpibycate 
                        where to_char(belong_date,'YYYY-mm') = {} and category_id = {}
                    )T4
            """.format("'" + str(time) + "'", "'" + str(category_id) + "'", "'" + str(time) + "'",
                       "'" + str(time) + "'", "'" + str(time) + "'", "'" + str(category_id) + "'")
        if sql is not None:
            self.env.cr.execute(sql)
            turnover = self.env.cr.fetchone()
        return turnover
