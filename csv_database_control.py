#!/usr/bin/env python

import os
import re
import csv
import system_info_maintain
# [csvDB_StockCompanyInfo ===================]
# 1. Provide to descibe  Company info , including:
#    (1) company stock serial number
#    (2) company name
#    (3) company relative product type
#    (4) company relative supply chain
#     etc.....
#
# 2. Describe __aStockCompanyTab[] :
#    (1) elements of __aStockCompanyTab , including:
#         <1> company stock  serial number
#         <2> company name
#
class CsvDBStockCompanyInfo(object):
    """ CsvDBStcokCompanyInfo public class """
    aStockCompanyTab = []

    def __init__(self):
        pass

    def init_stockcompany(self):
        """ init public class function """
        pass

    def append_stockcompany(self, int_index, a_company_info):
        """ append public class function """
        if int_index < len(self.aStockCompanyTab) and int_index >= 0:
            self.aStockCompanyTab[int_index] = a_company_info
            return int_index
        else:
            self.aStockCompanyTab.append(a_company_info)
            return len(self.aStockCompanyTab)-1

    def update_stockcomapny(self, int_index):
        """ append public class function """
        if int_index >= 0 and int_index < len(self.aStockCompanyTab):
            return self.aStockCompanyTab[int_index]
        else:
            return None

    def get_stockcompany(self, int_index):
        """ append public class function """
        if int_index < len(self.aStockCompanyTab):
            return self.aStockCompanyTab[int_index]
        return None

    def remove_stockcompany(self, int_index):
        """ append public class function """
        if int_index < len(self.aStockCompanyTab):
            self.aStockCompanyTab.pop(int_index)
            return 1
        return 0

# [csvDB_StockDailyInfo ===================]
# 1. Provide to store  Stock Company Daily Report , including:
#    (1) Date
#    (2) Trading Volume
#    (3) Turnover
#    (4) Opening Price
#     etc.....
#
# 2. Describe aStockDailyTab[] :
#    (1) very imporant, index "must" match with
#        csvDB_StockCompanyInfo.aStockCompanyTab[] for easy fetching
#    (2) elements of __aStockCompanyTab , including:
#         <1> Date
#         <2> Trading Volume
#         <3> Turnover
#         <4> Opening Price
#         <5> Highest Price
#         <6> Floor price
#         <7> Closing price
#         <8> Spread
#         <9> Auction items
#
class CsvDBStockDailyInfo(object):
    """ CsvDBStockDailyInfo public class """
    aStockDailyTab = []

    def __init__(self):
        pass

    def init_stockdaily_info(self):
        """ init public class function """
        pass


def __drv_db_get_pathformat_stockcommpany():
    a_file_format = system_info_maintain.mapi_sysinfo_get_atrribute_value(0, "system.ini", \
                "Stock Company Info", ["file path", "file name"])
    return a_file_format[0]+a_file_format[1]

# 1. read "./data/stock/stock_company.csv" ,
# which of file path is mantained by system.ini , "Stock Company Info"
# 2. (1) if "./data/stock/stock_company.csv" does not exist, then return 0;
#    (2) otherwise , if "./data/stock/stock_company.csv" exists, return 1
#
def mdrv_db_connect_stockcompany(a_param):
    """ public function """
    s_file_path = __drv_db_get_pathformat_stockcommpany()
    if not os.path.isfile(s_file_path):
        s_dic_path = os.path.dirname(s_file_path)
        if not os.path.isdir(s_dic_path):
            os.makedirs(s_dic_path)
        return 0
    else:
        if os.path.getsize(s_file_path) == 0:
            return 0
    return 1

def mdrv_db_update_stockcompany(a_stockcompany):
	if (a_stockcompany == None):
		return 0

	s_file_path = __drv_db_get_pathformat_stockcommpany()
	fp_stockcompany = open(s_file_path ,'w')

	fp_stockcompany.write("Number,Name\n")
	for i in range(len(a_stockcompany)):
		s_stock_serial = a_stockcompany[i][0]
		s_stock_name = a_stockcompany[i][1]
		s_line = s_stock_serial + "," + s_stock_name + "\n"
		fp_stockcompany.write(s_line)

	fp_stockcompany.close()
	return 1

def mdrv_db_capture_stockcompany(a_param):
    a_stocckcompany = []
    s_file_path = __drv_db_get_pathformat_stockcommpany()

    with open(s_file_path, 'r') as fp_stockcompany:
        for row in csv.reader(fp_stockcompany):
            if row[0] == "Number":
                continue
            a_company = []
            for i in range(len(row)):
                a_company.append(row[i])
            if len(a_company) > 0:
                a_stockcompnay.append(a_company)

    return a_stockcompany
