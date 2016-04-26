
import datetime
import time
import threading
from main_state_machine import *
import access_parse_web
import ui_operation
import system_info_mantain
import database_operation

def prograss_thread_action(intProcessSate, intThreadType, intThreadCmd, intStateSattus, aParam):
	if (intThreadType == ThreadTypeEnum.EM_TH_TYPE_ACCESS_PARSE_WEB):
		access_parse_web.Mapi_AccessParseWeb_action(intThreadType, intThreadCmd, intStateSattus, aParam)
	elif (intThreadType == ThreadTypeEnum.EM_TH_TYPE_UI_OPERATION):
		ui_operation.Mapi_UI_action(intThreadType, intThreadCmd, intStateSattus, aParam)

def Mapi_System_Init(intProcessSate, intThreadType, intThreadCmd, intStateSattus, aParam):
	ui_operation.Mapi_UI_init(intThreadType, intThreadCmd, intStateSattus, None)
	access_parse_web.Mapi_AccessParseWeb_init(intThreadType, intThreadCmd, intStateSattus, None)
	database_operation.Mapi_DB_init(intThreadType, intThreadCmd, intStateSattus, None)
	system_info_mantain.Mapi_SysInfo_Init()


#if (0): 
if __name__ == '__main__':
	MT_OS_Init()
	
	intProcessBitMap     = (0xFF<<24)
	intThreadTypeBitMap  = (0xFF<<16)
	intThreadCmdBitMap   = (0xFF<<8)
	intStateStatusBitMap = (0xFF<<0)
	while (1): #main loop 
		aCurrentState = MT_OS_Schedule()
		intProcessSate = aCurrentState[0] & intProcessBitMap
		intThreadType = aCurrentState[0] & intThreadTypeBitMap
		intThreadCmd = aCurrentState[0] & intThreadCmdBitMap
		intStateSattus = aCurrentState[0] & intStateStatusBitMap

		if (intProcessSate == ProcessStateEnum.EM_PS_SYS_INIT):
			Mapi_System_Init(intProcessSate, intThreadType, intThreadCmd, intStateSattus, aCurrentState[1])
		elif (intProcessSate == ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD):
			prograss_thread_action(intProcessSate, intThreadType, intThreadCmd, intStateSattus, aCurrentState[1])
		elif (intProcessSate == ProcessStateEnum.EM_PS_SYS_IDEL):
			#print("System Idle")
			MT_OS_SleepMs(500)
			MT_OS_AppendJobPool(int(ProcessJobProrityEnum.EM_JOB_PRI_NORMAL), MT_OS_TransStateEnum2Int([ProcessStateEnum.EM_PS_SYS_IDEL, 0, 0, 0]), None)

		
		

