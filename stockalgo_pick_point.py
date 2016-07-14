""" stock algoithm to pick  pressure point and  anchor """
from data_pool import Type
import data_pool
import threading
import datetime
import main_state_machine as msm

def mapi_pointalgo_query(d_date):
    d_end_date = d_date
    d_start_date =d_end_date - datetime.timedelta(days=1)
    param = data_pool.Param()
    param.period = d_start_date.strftime('%Y/%m/%d')
    param.period = param.period + "-"
    param.period = param.period + d_end_date.strftime('%Y/%m/%d')
    print (param.period)
    a_test = data_pool.get_data(Type.basic, "2371", param)
    print(a_test)

