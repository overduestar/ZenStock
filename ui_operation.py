""" ui operation """
import threading
import datetime
import main_state_machine as msm
import stockalgo_pick_point as pick_point_algo

g_Mutex_UI = None
g_UIOperation = None

# 1. Provide UI , ex: command line / interface, to filter information for user
#     (1) element of aUI_DataTab, including:
#            <1> start date (format: YYYY/MM/DD) for filter, default start date = present date
#            <2> end date (format: YYYY/MM/DD) for filter, default end date = present date
#            <3> stock number for filter,
#                default stock is {None, 0 , "", "all"} to mean "all search"
#
class UIOperation:
    """ ui operation """
    aUI_DataTab = []

    def __init__(self):
        self.aUI_DataTab.clear()
        s_current_date = datetime.date.today()
        self.aUI_DataTab.append(datetime.date(s_current_date.year,
                                              s_current_date.month,
                                              s_current_date.day))  ##default start date
        self.aUI_DataTab.append(datetime.date(s_current_date.year,
                                              s_current_date.month,
                                              s_current_date.day))  ##default end date
        self.aUI_DataTab.append("all")  ##default all

    #transfer string format:"YYYY/MM/DD" to date format
    def str_date(self, s_date):
        """ stringify date """
        d_date = None
        try:
            d_date = datetime.datetime.strptime(s_date, '%Y/%m/%d').date()
        except:
            pass
        return d_date

    #[pending issue] it can check stock serial which user key is correct
    def check_stock(self, s_stock):
        """ check stock """
        return s_stock

    def update_ui_data(self, a_ui_data):
        """ update ui data """
        self.aUI_DataTab[0] = a_ui_data[0]  #update start date
        self.aUI_DataTab[1] = a_ui_data[1]  #update end date
        self.aUI_DataTab[2] = a_ui_data[2]  #update stock serial

    def get_ui_data(self):
        """ get ui data """
        return self.aUI_DataTab


def __ui_check_usercommand_warning():
    print("******* Error Fromat *******")
    s_check = input("any key continue; <1>:re-setting; <q/Q>")
    if len(s_check) == 1:
        if s_check == '1':
            return 1
        elif s_check.lowercase == 'q':
            return 2
    return 0

def __ui_operation_default_thread(xxx, a_param):
    _ = xxx
    print("__ui_default_thread start:", a_param)


def __ui_operation_case_cmd_inquire_during_stockinfo():
    int_step = 0
    d_start_date = None
    d_end_date = None
    s_stock = ""
    int_warning = 0
    while int_step < 3:
        if int_step == 0:
            s_start_date = input('Please enter Start Date(yyyy/mm/dd) : ')
            if len(s_start_date) == 0:
                continue
            d_start_date = g_UIOperation.str_date(s_start_date)
            if d_start_date is None:
                int_warning = __ui_check_usercommand_warning()
                if int_warning == 1:
                    int_step = 0
                    continue
                elif int_warning == 2:
                    break
                else:
                    continue
            int_step = 1 #notify to next user command setting

        if int_step == 1:
            s_end_date = input('Please enter End Date(yyyy/mm/dd) : ')
            if len(s_end_date) == 0:
                continue
            d_end_date = g_UIOperation.str_date(s_end_date)
            if d_end_date is None:
                int_warning = __ui_check_usercommand_warning()
                if int_warning == 1:
                    int_step = 0
                    continue
                elif int_warning == 2:
                    break
                else:
                    continue
            int_step = 2 #notify to next user command setting

        if int_step == 2:
            s_stock = input('Please enter Stock Number or enter \'all\' : ')
            if len(s_stock) == 0:
                continue
            s_stock = g_UIOperation.check_stock(s_stock)
            if s_stock is None:
                int_warning = __ui_check_usercommand_warning()
                if int_warning == 1:
                    int_step = 0
                    continue
                elif int_warning == 2:
                    break
                else:
                    continue
            int_step = 3 #notify to next user command setting

    if int_step == 3: #notify to success finish "while (int_step < 3)"
        a_ui_data = []
        a_ui_data.append(d_start_date)
        a_ui_data.append(d_end_date)
        a_ui_data.append(s_stock)
        g_UIOperation.update_ui_data(a_ui_data)

        #send notify to "access_parse_web" with parameter :[a_ui_data, "UI Request Access"]
        # --> "UI Request Access" is used to notify "access_parse_web" action
        msm.mt_os_append_job_pool(int(msm.ProcessJobPriorityEnum.EM_JOB_PRI_HIGH),
                                  msm.mt_os_trans_state_enum2int(
                                      [msm.ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD,
                                       msm.ThreadTypeEnum.EM_TH_TYPE_ACCESS_PARSE_WEB,
                                       msm.ThreadCMDEnum.EM_TH_CMD_NOTIFY_THREAD, 0]),
                                  [a_ui_data, "UI Request Daily Access"])

def __ui_operation_case_cmd_pickalgo_anchor_pressure():
    print("__ui_operation_case_cmd_pickalgo_anchor_pressure start")
    s_date = input('Please enter query Date(yyyy/mm/dd) : ')
    d_date = g_UIOperation.str_date(s_date)
    pick_point_algo.mapi_pointalgo_query(d_date)
    

def __ui_operation_polling_usercommand_thread(xxx, a_param):
    _ = xxx
    print("__ui_operation_polling_usercommand_thread start:", a_param)
    thd = a_param[-1] #get a_param[] last item to notify thread
    _ = thd
    while 1:
        s_tags = input('')
        #user key "00112233" as password to insert command
        if s_tags == "00112233":
            __ui_operation_case_cmd_inquire_during_stockinfo()
        elif s_tags == "x":
            __ui_operation_case_cmd_pickalgo_anchor_pressure()

def __ui_create_thread(a_param):
    try:
        if a_param[0] == 1:
            thd = threading.Thread(target=__ui_operation_polling_usercommand_thread,
                                   args=(0, a_param))
            a_param.append(thd) #a_param last item to notify thread information
            thd.start()
    except:
        thd = threading.Thread(target=__ui_operation_default_thread, args=(0, a_param))
        thd.start()

def mapi_ui_init(int_thread_type, int_thread_cmd, int_state_status, a_param):
    """ ui init """
    global g_Mutex_UI
    global g_UIOperation

    _ = int_state_status
    _ = int_thread_type
    _ = int_thread_cmd
    g_Mutex_UI = msm.mt_os_create_mutex("UI Operation")
    g_UIOperation = UIOperation()
    print("mapi_ui_init", a_param)
    msm.mt_os_append_job_pool(int(msm.ProcessJobPriorityEnum.EM_JOB_PRI_HIGH),
                              msm.mt_os_trans_state_enum2int(
                                  [msm.ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD,
                                   msm.ThreadTypeEnum.EM_TH_TYPE_UI_OPERATION,
                                   msm.ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD, 0]), [1])

def mapi_ui_action(int_thread_type, int_thread_cmd, int_state_status, a_param):
    """ ui action """
    _ = int_state_status
    _ = int_thread_type
    if int_thread_cmd == msm.ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD:
        __ui_create_thread(a_param)
