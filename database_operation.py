import threading
import datetime
#from enum import IntEnum
from main_state_machine import *
from csv_database_control import *


class DBOperation(CsvDBStockCompanyInfo, CsvDBStockDailyInfo):
    """ DBOperation public class """
    __a_cache_stockserial = []

    def __init__(self):
        """ public function """
        super().init_stockcompany()
        super().init_stockdaily_info()

    def find_stockserialtab_index(self, s_stockserial):
        """ public function """
        try:
            return self.__a_cache_stockserial.index(s_stockserial)
        except:
            return -1

    def get_stockserialtab_size(self):
        """ public function """
        return len(self.__a_cache_stockserial)

    def get_stockserialtab(self):
        """ public function """
        return self.__a_cache_stockserial

    # @overwrite: csvDB_StockCompanyInfo for Cahche Stock Serail to easy find index
    def append_stockcompany(self, a_company_info):
        """ public function """
        s_stockserial = a_company_info[0]

        if a_company_info == None or len(s_stockserial) == 0:
            return 0

        int_index = super().append_stockcompany(self.find_stockserialtab_index(s_stockserial), a_company_info)

        #dynamic increase __a_cache_stockserial[] for match index
        i = len(self.__a_cache_stockserial)
        while i <= int_index:
            self.__a_cache_stockserial.append("")
            i = i + 1

        self.__a_cache_stockserial[int_index] = s_stockserial
        return 1



def mapi_db_connect_stockcompany(a_param):
    """ public function """
    return mdrv_db_connect_stockcompany(a_param)

def mapi_db_update_stockcompany(a_stockcompany_info):
    """ public function """
    return mdrv_db_update_stockcompany(a_stockcompany_info)

def mapi_db_capture_stockcompany(a_param):
    """ public function """
    if g_db_operation.get_stockserialtab_size() == 0:
        a_stockcompany_info = mdrv_db_capture_stockcompany(a_param)
        for i in range(len(a_stockcompany_info)):
            g_db_operation.append_stockcompany(a_stockcompany_info[i])
    return g_db_operation.get_stockserialtab()


def mapi_db_init(int_thread_type, int_thread_cmd, int_state_status, a_param):
    """ public function """
    global g_mutex_db
    global g_db_operation
    g_mutex_db = mt_os_create_mutex("DB Operation")
    g_db_operation = DBOperation()


