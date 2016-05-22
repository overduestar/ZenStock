""" main function """
from main_state_machine import ProcessStateEnum, ProcessJobPriorityEnum
import main_state_machine as msm
import access_parse_web as apw
import ui_operation
import system_info_maintain
import database_operation

def progress_thread_action(int_process_state, int_thread_type, int_thread_cmd,
                           int_state_status, a_param):
    """ progress thread action """
    del int_process_state
    if int_thread_type == msm.ThreadTypeEnum.EM_TH_TYPE_ACCESS_PARSE_WEB:
        apw.mapi_access_parse_web_action(int_thread_type, int_thread_cmd,
                                       int_state_status, a_param)
    elif int_thread_type == msm.ThreadTypeEnum.EM_TH_TYPE_UI_OPERATION:
        ui_operation.mapi_ui_action(int_thread_type, int_thread_cmd, int_state_status, a_param)


def mapi_system_init(int_process_state, int_thread_type, int_thread_cmd, int_state_status, a_param):
    """ init system """
    del int_process_state, a_param
    ui_operation.mapi_ui_init(int_thread_type, int_thread_cmd, int_state_status, None)
    apw.mapi_access_parse_web_init(int_thread_type, int_thread_cmd,
                                 int_state_status, None)
    database_operation.mapi_db_init(int_thread_type, int_thread_cmd, int_state_status, None)
    system_info_maintain.mapi_sysinfo_init()


#if (0):
if __name__ == '__main__':
    msm.mt_os_init()

    INT_PROCESS_BITMAP = (0xFF<<24)
    INT_THREAD_TYPE_BITMAP = (0xFF<<16)
    INT_THREAD_CMD_BITMAP = (0xFF<<8)
    INT_STATE_STATUS_BITMAP = (0xFF<<0)
    while 1: #main loop
        A_CURRENT_STATE = msm.mt_os_schedule()
        INT_PROCESS_STATE = A_CURRENT_STATE[0] & INT_PROCESS_BITMAP
        INT_THREAD_TYPE = A_CURRENT_STATE[0] & INT_THREAD_TYPE_BITMAP
        INT_THREAD_CMD = A_CURRENT_STATE[0] & INT_THREAD_CMD_BITMAP
        INT_STATE_STATUS = A_CURRENT_STATE[0] & INT_STATE_STATUS_BITMAP

        if INT_PROCESS_STATE == msm.ProcessStateEnum.EM_PS_SYS_INIT:
            mapi_system_init(INT_PROCESS_STATE, INT_THREAD_TYPE, INT_THREAD_CMD,
                             INT_STATE_STATUS, A_CURRENT_STATE[1])
        elif INT_PROCESS_STATE == msm.ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD:
            progress_thread_action(INT_PROCESS_STATE, INT_THREAD_TYPE,
                                   INT_THREAD_CMD, INT_STATE_STATUS, A_CURRENT_STATE[1])
        elif INT_PROCESS_STATE == msm.ProcessStateEnum.EM_PS_SYS_IDEL:
            #print("System Idle")
            msm.mt_os_sleep_ms(500)
            msm.mt_os_append_job_pool(int(ProcessJobPriorityEnum.EM_JOB_PRI_NORMAL),
                                      msm.mt_os_trans_state_enum2int(
                                          [ProcessStateEnum.EM_PS_SYS_IDEL, 0, 0, 0]), None)
