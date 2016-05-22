""" access parse web """
import threading
import datetime
from enum import IntEnum
import urllib.request
import urllib
import codecs
import re
import main_state_machine as msm
import system_info_mantain
import database_operation as do

G_MUTEX_WEB = 0
G_WEB_NOTIFY = 0

class WebNotifyEnum(IntEnum):
    """ web notify enum """
    em_web_ui_nothing = 0x0000
    em_web_ui_request_dail = 0x0001
    em_web_autorun_dail = 0x0002
    em_web_autorun_dail_history = 0x0003
    em_web_sys_request_stock_company = 0x0004

# 1. Provide other thread or process to notify signal for access web
#     (1) element of __aNotifyQueue, including:
#            <1> WebNotifyEnum
#            <2> notify Parameter
#     (2) always first in first out , no support preempt
#
class WebNotifyOperation:
    """ web noitfy operation """
    __aNotifyQueue = []

    def __init__(self):
        self.__aNotifyQueue.clear()

    def append_notify(self, e_notify_type, a_param):
        """ append notify """
        self.__aNotifyQueue.append([e_notify_type, a_param])

    def get_notify(self):
        """ get notify """
        if len(self.__aNotifyQueue) == 0:
            return None
        return self.__aNotifyQueue[0]

    def remove_notify(self):
        """ remove notify """
        if len(self.__aNotifyQueue) > 0:
            self.__aNotifyQueue.pop(0)



def __web_access_parse_stock_comapny(a_param):
    """ web access parse stock compnay """
    _ = a_param
    a_stock_compan_info = []
    a_url_path = system_info_mantain.Mapi_SysInfo_GetAtrributeValue(0, "system.ini",
                                                                    "Stock Serail List Web",
                                                                    ["web site"])
    s_url_path = a_url_path[0]
    s_url_info = codecs.decode(urllib.request.urlopen(s_url_path).read(), 'big5', errors='ignore')
    if len(s_url_info) == 0:
        return a_stock_compan_info

    a_split_url_info = re.split("<td", s_url_info)
    int_item_flag = 0
    s_stock_serial = ""
    s_stock_name = ""
    for info in a_split_url_info:
        s_data = ""
        if info[1].find("td") >= 0:
            s_data = info[1].split('>')[1].replace("&nbsp;", "").split('<')[0]
        if len(s_data > 0):
            if int_item_flag == 0:
                s_stock_serial = s_data
                int_item_flag = 1
            elif int_item_flag == 1:
                s_stock_name = s_data
                a_stock_compan_info.append([s_stock_serial, s_stock_name])
                int_item_flag = 0
    return a_stock_compan_info

def __web_access_stock_company(a_param):
    int_ret = do.Mapi_DB_Connect_StockCompany(a_param)
    if int_ret == 0: #connect stock company fail
        a_stock_company_info = __web_access_parse_stock_comapny(a_param)
        do.Mapi_DB_Update_StockCompany(a_stock_company_info)

    return do.Mapi_DB_Capture_StockCompany(a_param)


def __web_access_parse_stock_daily(d_start_date, d_end_date, s_stock_list):
    print("__web_access_parse_daily: start")
    #check start & end date
    if d_end_date is None:
        d_end_date = datetime.date(datetime.date.today().year,
                                   datetime.date.today().month,
                                   datetime.date.today().day)
    if (d_start_date is None) or (d_start_date > d_end_date):
        d_start_date = d_end_date

    a_stock_list = []
    if s_stock_list == "all":
        a_stock_list = __web_access_stock_company(None)
    else:
        a_stock_list.append(s_stock_list)




def __web_default_thread(xxx, a_param):
    print("__web_default_thread start:", a_param)
    _ = xxx

def __web_access_parse_thread(xxx, a_param):
    print("__web_access_parse_thread start:", a_param)

    _ = xxx
    _ = a_param
    #thd = a_param[-1] #get a_param[] last item to notify thread
    a_notify_info = None
    while 1:
        msm.mt_os_acquire_mutex(G_MUTEX_WEB)
        a_notify_info = G_WEB_NOTIFY.get_notify()
        msm.mt_os_release_mutex(G_MUTEX_WEB)

        if a_notify_info != None:
            msm.mt_os_acquire_mutex(G_MUTEX_WEB)

            int_notify_action = a_notify_info[0]
            a_notify_param = a_notify_info[1]
            if int_notify_action == WebNotifyEnum.em_web_ui_request_dail:
                __web_access_parse_stock_daily(a_notify_param[0],
                                               a_notify_param[1], a_notify_param[2])
            elif int_notify_action == WebNotifyEnum.em_web_sys_request_stock_company:
                __web_access_stock_company(a_notify_param)

            G_WEB_NOTIFY.remove_notify()
            msm.mt_os_release_mutex(G_MUTEX_WEB)

        msm.mt_os_sleep_ms(100)



def __web_create_thread(a_param):
    try:
        if a_param[0] == 1:
            thd = threading.Thread(target=__web_access_parse_thread, args=(0, a_param))
            a_param.append(thd) #a_param last item to notify thread information
            thd.start()
    except:
        thd = threading.Thread(target=__web_default_thread, args=(0, a_param))
        thd.start()

def __web_notify_action(a_param):
    if (a_param != None) and len(a_param) > 0:
        a_notify_param = a_param[0]
        s_notify_str = a_param[1]

        #parse Notify String to decide what action
        int_notify_action = WebNotifyEnum.em_web_ui_nothing
        #depand on "ui_operatin" send notify action string
        if s_notify_str == "UI Request Daily Access":
            int_notify_action = WebNotifyEnum.em_web_ui_request_dail

        msm.mt_os_acquire_mutex(G_MUTEX_WEB)
        G_WEB_NOTIFY.append_notify(int_notify_action, a_notify_param)
        msm.mt_os_release_mutex(G_MUTEX_WEB)

def mapi_access_parse_web_init(int_thread_type, int_thread_cmd, int_state_status, a_param):
    """ access parse web init """
    global G_MUTEX_WEB
    global G_WEB_NOTIFY

    _ = int_thread_type
    _ = a_param
    _ = int_state_status
    _ = int_thread_cmd
    G_MUTEX_WEB = msm.mt_os_create_mutex("Access Parse Web")
    G_WEB_NOTIFY = WebNotifyOperation()
    msm.mt_os_append_job_pool(int(msm.ProcessJobPriorityEnum.EM_JOB_PRI_HIGH),
                              msm.mt_os_trans_state_enum2int(
                                  [msm.ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD,
                                   msm.ThreadTypeEnum.EM_TH_TYPE_ACCESS_PARSE_WEB,
                                   msm.ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD, 0]), [1])

def mapi_access_parse_web_action(int_thread_type, int_thread_cmd, int_state_status, a_param):
    """ access parse web action """
    _ = int_thread_type
    _ = int_state_status
    if int_thread_cmd == msm.ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD:
        __web_create_thread(a_param)
    elif int_thread_cmd == msm.ThreadCMDEnum.EM_TH_CMD_NOTIFY_THREAD:
        __web_notify_action(a_param)
