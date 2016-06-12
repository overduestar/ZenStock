import filecmp
import fetch
import os
from datetime import datetime, date, timedelta
from urllib import request
import time
import pandas


def need_update_stock_table_test(expect):
    """ test module for need_update_stock_table() """
    res = fetch.need_update_stock_table()
    if res == expect:
        print('pass')
    else:
        print('fail')


def need_update_stock_table_tests():
    """ unit test cases for need_update_stock_table() """
    print('need_update_stock_table_tests:')

    # test for file that doesn't exist
    filename = 'data/stock-table.csv'
    if os.path.exists(filename):
        os.remove(filename)
    need_update_stock_table_test(True)
    
    # test for file that exists
    filename = 'data/stock-table.csv'
    open(filename, 'w').close 
    need_update_stock_table_test(False)
    os.remove(filename)


def update_stock_table_tests():
    """ unit test cases for update_stock_table_tests() """
    print('update_stock_table_tests:')

    # test for file download
    filename = 'data/stock-table.csv'
    if os.path.exists(filename):
        os.remove(filename)
    fetch.update_stock_table()
    if os.path.exists(filename) and os.stat(filename).st_size > 0:
        print('pass')
    else:
        print('fail')

def fetch_stock_table_tests():
    """ unit test cases for fetch_stock_table_tests() """
    print('fetch_stock_table_tests:')
    
    df = fetch.fetch_stock_table()
    if len(df) > 1500: # actually, 1546, 2015/11/28
        print('pass')
    else:
        print('fail')

def update_price_test(input_param, expect_url, expect_filename):
    """ test module for update_price() """

    stock, year, month, filename = input_param

    # output
    if os.path.exists(filename):
        os.remove(filename)
    res = fetch.update_price(stock, year, month, filename)
    if res == False:
        print('pass') # correctly handle decode error exception
        return

    # expect
    if os.path.exists(expect_filename):
        os.remove(expect_filename)
    with request.urlopen(expect_url) as response, \
            open(expect_filename, 'w') as expect_file:
        expect_file.write(response.read().decode('big5hkscs'))

    if filecmp.cmp(filename, expect_filename): # same
        print('pass')
    else:
        print('fail')


def update_price_tests():
    """ unit test cases for update_price() """
    print('update_price_tests:')

    # trivial test
    url = 'http://www.twse.com.tw' + \
            '/ch/trading/exchange/STOCK_DAY/STOCK_DAY_print.php' + \
            '?genpage=genpage/Report201511/201511_F3_1_8_2415.php&type=csv'
    update_price_test(['2415', 2015, 11, '/tmp/2415.output'],
                      url, '/tmp/2415.expect')

    # test for index
    url = 'http://www.twse.com.tw' + \
            '/ch/trading/exchange/FMTQIK/FMTQIK2.php' + \
            '?STK_NO=&myear=2015&mmon=11&type=csv'
    update_price_test(['index', 2015, 11, '/tmp/index.output'],
                      url, '/tmp/index.expect')

    # test for 'T' in '01002T'
    url = 'http://www.twse.com.tw' + \
            '/ch/trading/exchange/STOCK_DAY/STOCK_DAY_print.php' + \
            '?genpage=genpage/Report201511/201511_F3_1_8_01002T.php&type=csv'
    update_price_test(['01002T', 2015, 11, '/tmp/01002T.output'],
                      url, '/tmp/01002T.expect')

    # test for six numbers in '911616'
    url = 'http://www.twse.com.tw' + \
            '/ch/trading/exchange/STOCK_DAY/STOCK_DAY_print.php' + \
            '?genpage=genpage/Report201511/201511_F3_1_8_911616.php&type=csv'
    update_price_test(['911616', 2015, 11, '/tmp/911616.output'],
                      url, '/tmp/911616.expect')

    # test for '恒', '碁' in content
    url = 'http://www.twse.com.tw' + \
            '/ch/trading/exchange/STOCK_DAY/STOCK_DAY_print.php' + \
            '?genpage=genpage/Report201511/201511_F3_1_8_910708.php&type=csv'
    update_price_test(['910708', 2015, 11, '/tmp/910708.output'],
                      url, '/tmp/910708.expect')

    # test for otc
    url = 'http://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_download.php?l=zh-tw&d=104/11&stkno=8942&s=0,asc,0'
    update_price_test(['8942', 2015, 11, '/tmp/8942.output'],
                      url, '/tmp/8942.expect')

    # test for unknown decode error
    url = 'http://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_download.php?l=zh-tw&d=103/11&stkno=1558&s=0,asc,0'
    update_price_test(['1558', 2014, 11, '/tmp/1558.output'],
                      url, '/tmp/1558.expect')

    # test for index
    url = 'http://www.twse.com.tw/ch/trading/exchange/FMTQIK/FMTQIK2.php?STK_NO=&myear=2015&mmon=01&type=csv'
    update_price_test(['index', 2015, 1, '/tmp/index.output'],
                      url, '/tmp/index.expect')


def need_update_index_test(filename, expect):
    """ test module for need_update_index() """
    output = fetch.need_update_price(filename)

    if output == expect:
        print('pass')
    else:
        print('fail', output)


def need_update_price_tests():
    """ unit test cases for need_update_price() """
    print('need_update_price_tests:')

    # test for index file that does not exist
    filename = 'data/index/price-2010-10.csv'
    if os.path.exists(filename):
        os.remove(filename)
    need_update_index_test(filename, True)

    # test for modtime_dt != filename_dt but now > expire(modtime + 1 hour)
    filename = 'data/index/price-2010-10.csv'
    fetch.update_price('index', 2010, 10, filename)
    os.utime(filename, (0, 0))
    need_update_index_test(filename, False)

    # test for modtime_dt == filename_dt but now < expire(modtime + 1 hour)
    now = datetime.now()
    filename = 'data/index/price-' + str(now.year) + \
        '-' + ('%02d') % (now.month) + '.csv'
    fetch.update_price('index', now.year, now.month, filename)
    need_update_index_test(filename, False)


def str_to_dates_test(period, exp):
    """ test module for str_to_dates() """
    res = fetch.str_to_dates(period)
    if res == exp:
        print('pass')
    else:
        print('fail')


def str_to_dates_tests():
    """ unit test cases for str_to_dates() """

    # trivial test
    start_dt = datetime(1911, 1, 2).date()
    end_dt = datetime(1911, 2, 1).date()
    str_to_dates_test('1911/1/2-1911/2/1', [start_dt, end_dt])

    # test for future case
    str_to_dates_test('2100/1/2-2100/2/1', [False])

    # test for invalid date, e.g. 2015/2/31
    str_to_dates_test('2100/2/1-2100/2/31', [False])

def mg_to_ad_test(date_str, expect):
    """ test module for need_update_index() """
    res = fetch.mg_to_ad(date_str)
    if res == expect:
        print('pass')
    else:
        print('fail')


def mg_to_ad_tests():
    """ unit test cases for mg_to_ad_tests() """
    print('md_to_ad_tests::')

    # trivial tests
    mg_to_ad_test('104/2/3', datetime(2015, 2, 3))
    mg_to_ad_test('89/11/13', datetime(2000, 11, 13))
    mg_to_ad_test('88/6/8', datetime(1999, 6, 8))
    

def fetch_price_test(stock, period, addition, column, expect):
    """
    test module for fetch_data('stock price')
    """
    res = fetch.fetch_price(stock, period, addition)
    if res[0] == expect[0] == False:
        print('pass')
    elif res[0] == expect[0] == True and list(res[1][column]) == expect[1]:
        print('pass')
    else:
        print('fail')
        print(list(res[1][column]))
        print(expect[1])


def fetch_price_tests():
    """
    unit test cases for fetch_data('stock price')
    """
    print('fetch_price_tests:')

    # both period date & addtion step across month
    expect = [196.50, 194.50, 190.50, 193.50, 194.00, 195.50, \
              197.50, 195.00, 197.00, 202.50, 200.00, 190.50, \
              186.50, 186.50, 184.50, 187.00, 183.50, 181.50, \
              182.00, 183.50, 180.50, 182.50, 180.00, 177.00, \
              174.00, 178.50, 179.50, 187.50]
    fetch_price_test('9914', '2015/10/1-2015/11/3', 5, '收盤價', [True, expect[::-1]])

    # single date
    expect = [180.00]
    fetch_price_test('9914', '2015/10/1', 0, '收盤價', [True, expect[::-1]])

    # single date, addition steps across month
    expect = [180.00, 177.00, 174.00]
    fetch_price_test('9914', '2015/10/1', 2, '收盤價', [True, expect[::-1]])

    # period date, addition steps across month
    expect = [180.50, 182.50, 180.00, 177.00, 174.00]
    fetch_price_test('9914', '2015/10/1-2015/10/5', 2, '收盤價', [True, expect[::-1]])

    # period date steps across month, addition
    expect = [180.50, 182.50, 180.00, 177.00, 174.00, 178.50, \
               179.50, 187.50]
    fetch_price_test('9914', '2015/9/25-2015/10/5', 3, '收盤價', [True, expect[::-1]])

    # period date steps across month
    expect = [180.50, 182.50, 180.00, 177.00, 174.00]
    fetch_price_test('9914', '2015/9/25-2015/10/5', 0, '收盤價', [True, expect[::-1]])

    # period date
    expect = [180.50, 182.50, 180.00]
    fetch_price_test('9914', '2015/10/1-2015/10/5', 0, '收盤價', [True, expect[::-1]])

    # test for empty file
    expect = [27.2]
    fetch_price_test('2833', '2015/11/1-2015/11/5', 0, '收盤價', [True, expect[::-1]])

    # test for otc
    expect = [95.6, 94.0, 94.9, 98.4]
    fetch_price_test('8942', '2015/11/3-2015/11/5', 1, '收盤', [True, expect])

    # test for index
    expect = [8614.77, 8713.19, 8857.02, 8850.18]
    fetch_price_test('index', '2015/11/3-2015/11/5', 1, '發行量加權股價指數', [True, expect])

    # test for file with just header
    fetch_price_test('4720', '2015/2/3-2015/2/5', 0, '收盤', [False])
    fetch_price_test('3141', '2014/2/1-2014/2/5', 0, '收盤', [False])



def char_to_slash_test(date_str, expect):
    """ test module """
    res = fetch.char_to_slash(date_str)
    if res == expect:
        print('pass')
    else:
        print('fail')


def need_update_revenue_test(filename, expect):
    """ test module """
    output = fetch.need_update_revenue(filename)

    if output == expect:
        print('pass')
    else:
        print('fail', output)


def need_update_revenue_tests():
    """ test cases """
    print('need_update_revenue_tests:')

    # test for file that does not exist
    filename = 'data/2023/revenue.csv'
    if os.path.exists(filename):
        os.remove(filename)
    need_update_revenue_test(filename, True)

    # test for modtime date is today
    filename = 'data/2023/revenue.csv'
    fetch.update_revenue('2023', filename)
    need_update_revenue_test(filename, False)
    os.remove(filename)


def update_revenue_test(stock, filename, expect):
    """ test module """
    if fetch.update_revenue(stock, filename) == expect:
        print('pass')
    else:
        print('fail')


def update_revenue_tests():
    """ test cases """
    print('update_revenue_tests:')

    # trivial tests
    update_revenue_test('9914', '/tmp/9914-revenue.csv', True)
    update_revenue_test('2454', '/tmp/2454-revenue.csv', True)

    # test for empty table, e.g. 0056
    update_revenue_test('0056', '/tmp/0056-revenue.csv', False)


def char_to_slash_tests():
    """ test cases """
    print('char_to_slash_tests:')

    # trivial tests
    char_to_slash_test('2015年2月', datetime(2015, 2, 1))
    char_to_slash_test('2000年11月', datetime(2000, 11, 1))
    char_to_slash_test('1999年6月', datetime(1999, 6, 1))


def fetch_revenue_test(stock, period, addition, column, expect):
    """ test module """
    res = fetch.fetch_revenue(stock, period, addition)
    if res[0] == expect[0] and list(res[1][column]) == expect[1]:
        print('pass')
    else:
        print('fail')


def fetch_revenue_tests():
    """ test cases """
    print('fetch_revenue_tests:')    

    # test for period and addition
    expect = [1763, 2143, 2047, 2097, 2617, 2954, 2405, 2368, 2483, 2070, 2515, 2040, 1731, 2423, 2337, 2133, 2565, 3269, 2598, 2634, 2315]
    fetch_revenue_test('9914', '2015/1/1-2015/10/1', 11, '營業收入', [True, expect])

    # test for single month and addition
    expect = [2040, 1731, 2423, 2337, 2133, 2565, 3269, 2598, 2634, 2315]
    fetch_revenue_test('9914', '2015/10/1-2015/10/1', 9, '營業收入', [True, expect])

    # test for period without addition
    expect = [2040, 1731, 2423, 2337, 2133, 2565, 3269, 2598, 2634, 2315]
    fetch_revenue_test('9914', '2015/1/1-2015/10/1', 0, '營業收入', [True, expect])


if __name__ == '__main__':
    need_update_stock_table_tests()
    update_stock_table_tests()
    fetch_stock_table_tests()
    update_price_tests()
    need_update_price_tests()
    str_to_dates_tests()
    mg_to_ad_tests()
    fetch_price_tests()
    need_update_revenue_tests()
    update_revenue_tests()
    char_to_slash_tests()
    fetch_revenue_tests()


