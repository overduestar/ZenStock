"""
this module is for fetch utilities
"""
from urllib import request
from datetime import datetime, date, timedelta
from dateutil import relativedelta, parser
import csv
import os
from os import path
from bs4 import BeautifulSoup
import pandas
import numpy
from enum import Enum

class Type(Enum):
    basic = 0

class Param():
    period = ""


def get_data(data_type, stock_no, param):
    if data_type == Type.basic:
        return get_basic(stock_no, param)


def download_stock_table():
    filename = 'data/stock_list.csv'
    url = 'http://www.emega.com.tw/js/StockTable.htm'
    with request.urlopen(url) as response, \
            open(filename, 'w') as out_file:
        soup = BeautifulSoup(response.read().decode('big5hkscs'), 'lxml')
        table = soup.find('table', attrs = {'class':'TableBorder'})
        rows = []
        for row in table.find_all('tr'):
            rows.append([val.text.replace('\xa0', '') for val in row.find_all('td')])
            rows[-1] = zip(rows[-1][::2], rows[-1][1::2])

        rows = list(zip(*rows))
        res = []
        for row in rows:
            for tpl in row:
                if tpl == ('', ''):
                    break
                elif tpl[0] == '上市' or tpl[0] == '上櫃':
                    append_data1 = tpl[0]
                    append_data2 = tpl[1]
                else:
                    res.append([tpl[0], tpl[1], append_data1, append_data2])

        writer = csv.writer(out_file)
        writer.writerows(res)


def get_basic(stock_no, param):
    """
    get basic data within specified date from file
    download from url first if necessary
    """
    stock_no = str(stock_no)
    addition = 0


    res = str_to_dates(param.period)
    if res != [False]:
        start_dt, end_dt = res
    else:
        return [False]
    res = str_to_dates(param.period, ignore_day=True)
    if res != [False]:
        start_month_dt, end_month_dt = res
    else:
        return [False]

    # be compatible between twse/otc
    if stock_no == 'index':
        skip_rows = 1
        date_label = '日期'
        price_label = '發行量加權股價指數'
        skip_footer = 1
        engine = 'python'
    elif stock_list.loc[stock_no]['TWSE/OTC'] == '上櫃':
        skip_rows = 4
        date_label = '日 期'
        price_label = '收盤'
        skip_footer = 1
        engine = 'python'
    else:
        skip_rows = 1
        date_label = '日期'
        price_label = '收盤價'
        skip_footer = 0
        engine = 'c'

    dt_iter = end_month_dt
    df_list = []
    empty_files = 0
    while dt_iter >= start_month_dt or addition > 0 or not df_list:
        filename = 'data/' + stock_no + '/' + 'price-' + str(dt_iter.year) + \
            '-' + ('%02d') % (dt_iter.month) + '.csv'
        if need_update_price(filename):
            update_price(stock_no, dt_iter.year, dt_iter.month, filename)
        if os.stat(filename).st_size == 0: # empty file
            print(filename, 'is empty')
            empty_files += 1
        else:
            try:
                df = pandas.read_csv(filename, skiprows=skip_rows, 
                                     index_col=date_label, date_parser=mg_to_ad, 
                                     na_values=['--'], thousands=',', 
                                     skipfooter=skip_footer, engine=engine)
                df = df[pandas.notnull(df[price_label])] # to skip data with '--'
                if len(df) == 0: # file with header and column names
                    print(filename, 'has just header and column names')
                    empty_files += 1        
                else:
                    addition -= len(df[df.index < str(start_dt)])
                    df_list.append(df)
            except ValueError: # file with just header... no column names
                # data/3141/price-2014-03.csv would be false alarm
                # but I don't want to handle varied footers just for it
                print(filename, 'has just header')
                empty_files += 1        
                pass

        if empty_files >= 3: # no data for half of a season?
            return [False]
        else:
            dt_iter -= relativedelta.relativedelta(months=1)

    odf = df = pandas.concat(df_list[::-1]) # concat data of different months
    if len(df[str(start_dt):str(end_dt)]) == 0:
        addition += 1 # ensure at least one data between start_dt~end_dt
    df = df[-addition:] # truncate early data
    df = df[df.index <= str(end_dt)] # truncate later data

    #return [True, df]
    return df
    

def get_stock_list():
    """ 'update' should leave to 'download' module """
    if not os.path.exists('data/stock_list.csv'):
        download_stock_table()
    return pandas.read_csv('data/stock_list.csv', 
                                   names=['Number', 'Name', 'TWSE/OTC', 'Catagory'], 
                                   index_col='Number').sort_index() # sort() is deprecated


def str_to_dates(period, ignore_day=False):
    """ convert string to date """
    # FIXME: check before converting?

    # convert string to datetime object
    if '-' in period: # period
        [start, end] = period.split('-')
        try:
            start_dt = datetime.strptime(start, '%Y/%m/%d').date()
            end_dt = datetime.strptime(end, '%Y/%m/%d').date()
        except ValueError:
            return [False]
        if end_dt < start_dt: # why? whatever...
            start_dt, end_dt = end_dt, start_dt
    else: # single day
        if period == 'today':
            start_dt = date.today()
        else:
            start_dt = datetime.strptime(period, '%Y/%m/%d').date()
        end_dt = start_dt

    if ignore_day: # for fetch_revenue()
        start_dt = datetime(start_dt.year, start_dt.month, 1).date()
        end_dt = datetime(end_dt.year, end_dt.month, 1).date()

    # validate dates
    if start_dt > datetime.now().date() or end_dt > datetime.now().date():
        return [False]

    return [start_dt, end_dt]


def need_update_price(filename):
    """ 
    update index for each stock to refer to 
    input: filename with date info
    """
    if not os.path.exists(filename):
        return True

    weekday = date.today().weekday()
    if weekday - 5 >= 0: # saturday or sunday
        return False

    [prefix, _, suffix] = filename.split('/')
    filename_dt = datetime.strptime(suffix, 'price-%Y-%m.csv')
    modtime_dt = datetime.fromtimestamp(path.getmtime(filename))
    now = datetime.now()
    valid = modtime_dt + timedelta(hours=4) # modtime + 4 hour, should be enough?
    # cond1: need update(if <), or just in case(if =)
    # cond2: each index update should be valid within 1 hour
    if modtime_dt.year == filename_dt.year and modtime_dt.month == filename_dt.month and now > valid:
        return True

    return False


def update_price(stock, year, month, filename):
    """
    fetch stock price of date from url, and save to filename
    don't expect to parse date info from filename, which may not follow the rule
    date_info is divided into year/month for caller's easy usage
    """
    print('update', filename)
    if stock == 'index':
        url = ('http://www.twse.com.tw' +
               '/ch/trading/exchange/FMTQIK/FMTQIK2.php' +
               '?STK_NO=&myear=%(year)d&mmon=%(month)02d&type=csv') % \
               {'year': year, 'month': month}
    elif stock_list.loc[stock]['TWSE/OTC'] == '上櫃':
        url = ('http://www.tpex.org.tw' + 
               '/web/stock/aftertrading/daily_trading_info/st43_download.php' +
               '?l=zh-tw&d=%(year)d/%(month)02d&stkno=%(stock)s&s=0,asc,0') % \
               {'year': int(year) - 1911, 'month': month, 'stock': stock}
    else:
        url = ('http://www.twse.com.tw' +
               '/ch/trading/exchange/STOCK_DAY/STOCK_DAY_print.php' +
               '?genpage=genpage/Report%(year)d%(month)02d/' +
               '%(year)d%(month)02d_F3_1_8_%(stock)s.php&type=csv') % \
               {'year': year, 'month': month, 'stock': stock}

    # write file after decoding
    if not os.path.exists('data/' + stock):
        os.mkdir('data/' + stock)
    with request.urlopen(url) as response, \
            open(filename, 'w') as out_file:
        try: # unknown decode error... 0xb7
            out_file.write(response.read().decode('big5hkscs')) # for '恒', '碁'
        except UnicodeDecodeError:
            return False
    return True

def mg_to_ad(date_info):
    """ mg: 民國 """
    date_info = date_info.split('/')
    date_info[0] = str(int(date_info[0]) + 1911)
    return parser.parse('/'.join(date_info))

def char_to_slash(date_info):
    return datetime.strptime(date_info, '%Y年%m月')

def need_update_revenue(filename):
    """
    compare with index file so as not to update stock price everytime
    """
    if not os.path.exists(filename):
        return True
    modtime_dt = datetime.fromtimestamp(path.getmtime(filename)).date()
    today_dt = date.today()
    # FIXME: if I got revenue of 10 in November, done
    if modtime_dt.day < today_dt.day: # update at most one time each day
        try:
            df = pandas.read_csv(filename, index_col='年月', date_parser=char_to_slash, thousands=',', nrows=1)
        except ValueError: # e.g. 0056
            print(filename, 'is empty')
            return False
        last = today_dt - relativedelta.relativedelta(months=1)
        # update if data of last month not yet exists
        if df.index[0].date().month != last.month:
            return True
    return False


def update_revenue(stock, filename):
    """ update revenue from url, otc is default available """
    print('update', filename)
    url = ('http://ps01.megatime.com.tw/asp/Basic/GetReportJs.asp?m=&table_name=html\Wsale\&StockID=%s') % (stock)
    
    # write file after decoding
    if not os.path.exists('data/' + stock):
        os.mkdir('data/' + stock)
    with request.urlopen(url) as response, open(filename, 'w') as out_file:
        soup = BeautifulSoup(response.read().decode('big5hkscs'), 'lxml')
        table = soup.find('table', attrs = {'cellpadding':'1', 'width':'85%'})
        if not table: # e.g. 0056
            return False

        rows = []
        for row in table.find_all('tr'):
            rows.append([val.text for val in row.find_all('td')])

        writer = csv.writer(out_file)
        writer.writerows(rows)

    return True


def fetch_revenue(stock, period, addition):
    """
    fetch revenue data within date from file
    download from url first if necessary
    """
    res = str_to_dates(period, ignore_day=True)
    if res != [False]:
        start_dt, end_dt = res

    filename = 'data/' + stock + '/revenue.csv'
    if need_update_revenue(filename):
        update_revenue(stock, filename)
    if os.stat(filename).st_size == 0: # empty file
        return [False]

    df = pandas.read_csv(filename, index_col='年月', date_parser=char_to_slash, thousands=',')[::-1]
    if len(df[str(start_dt):str(end_dt)]) == 0:
        addition += 1 #  ensure at least one date between start_dt~end_dt
    start_dt -= relativedelta.relativedelta(months=addition)
    df = df[str(start_dt) <= df.index] # truncate earlier
    df = df[df.index <= str(end_dt)] # truncate later
    
    return [True, df]


if not os.path.exists('data/'):
    os.mkdir('data/')
stock_list = get_stock_list()

