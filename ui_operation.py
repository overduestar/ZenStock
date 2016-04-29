import threading
import datetime
from main_state_machine import *

# 1. Provide UI , ex: command line / interface, to filter information for user
#     (1) element of aUI_DataTab, including:
#            <1> start date (format: YYYY/MM/DD) for filter, default start date = present date
#            <2> end date (format: YYYY/MM/DD) for filter, default end date = present date
#            <3> stock number for filter , default stock is {None, 0 , "", "all"} to mean "all search"
#
class UI_Operation:
	aUI_DataTab = []

	def __init__(self):
		self.aUI_DataTab.clear()
		sCurrentDate = datetime.date.today()
		self.aUI_DataTab.append(datetime.date(sCurrentDate.year, sCurrentDate.month, sCurrentDate.day))  ##default start date
		self.aUI_DataTab.append(datetime.date(sCurrentDate.year, sCurrentDate.month, sCurrentDate.day))  ##default end date
		self.aUI_DataTab.append("all")  ##default all

	#transfer string format:"YYYY/MM/DD" to date format	
	def strDate(self, sDate):
		dDate = None
		try:
			dDate = datetime.datetime.strptime(sDate, '%Y/%m/%d').date()
		except:
			pass
		return dDate

	#[pending issue] it can check stock serial which user key is correct	
	def checkStock(self, sStock):
		return sStock

	def updateUIData(self, aUIData):
		self.aUI_DataTab[0] = aUIData[0]  #update start date
		self.aUI_DataTab[1] = aUIData[1]  #update end date
		self.aUI_DataTab[2] = aUIData[2]  #update stock serial

	def getUIData(self):
		return self.aUI_DataTab


def __ui_check_usercommand_warning():
	print("******* Error Fromat *******");
	sCheck = input("any key continue; <1>:re-setting; <q/Q>")
	if (len(sCheck) == 1):
		if (sCheck == '1'):
			return 1
		elif (sCheck.lowercase == 'q'):
			return 2
	return 0

def __ui_operation_default_thread(x, aParam):
	print("__ui_default_thread start:", aParam)

def __ui_operation_polling_usercommand_thread(x, aParam):
	print("__ui_operation_polling_usercommand_thread start:", aParam)
	thd = aParam[-1] #get aParam[] last item to notify thread
	while (1):
		sTags = input('')
		#user key "00112233" as password to insert command
		if (sTags == "00112233"):
			intStep = 0
			dStartDate = None
			dEndDate = None
			sStock = ""
			intWarning = 0
			while (intStep < 3):
				if (intStep == 0):
					sStartDate = input('Please enter Start Date(yyyy/mm/dd) : ')
					if (len(sStartDate) == 0):
						continue
					dStartDate = g_UIOperation.strDate(sStartDate)
					if (dStartDate == None):
						intWarning = __ui_check_usercommand_warning()
						if (intWarning == 1):
							intStep = 0
							continue
						elif (intWarning == 2):
							break
						else:
							continue
					intStep = 1 #notify to next user command setting

				if (intStep == 1):
					sEndDate = input('Please enter End Date(yyyy/mm/dd) : ')
					if (len(sEndDate) == 0):
						continue
					dEndDate = g_UIOperation.strDate(sEndDate)
					if (dEndDate == None):
						intWarning = __ui_check_usercommand_warning()
						if (intWarning == 1):
							intStep = 0
							continue
						elif (intWarning == 2):
							break
						else:
							continue
					intStep = 2 #notify to next user command setting
					
				if (intStep == 2):
					sStock = input('Please enter Stock Number or enter \'all\' : ')
					if (len(sStock) == 0):
						continue
					sStock = g_UIOperation.checkStock(sStock)
					if (sStock == None):
						intWarning = __ui_check_usercommand_warning()
						if (intWarning == 1):
							intStep = 0
							continue
						elif (intWarning == 2):
							break
						else:
							continue
					intStep = 3 #notify to next user command setting
					
			if (intStep == 3): #notify to success finish "while (intStep < 3)"
				aUIData = []
				aUIData.append(dStartDate)
				aUIData.append(dEndDate)
				aUIData.append(sStock)
				g_UIOperation.updateUIData(aUIData)
				
				#send notify to "access_parse_web" with parameter :[aUIData, "UI Request Access"]
				# --> "UI Request Access" is used to notify "access_parse_web" action
				MT_OS_AppendJobPool(int(ProcessJobPriorityEnum.EM_JOB_PRI_HIGH), MT_OS_TransStateEnum2Int([ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD, ThreadTypeEnum.EM_TH_TYPE_ACCESS_PARSE_WEB, ThreadCMDEnum.EM_TH_CMD_NOTIFY_THREAD, 0]), [aUIData, "UI Request Daily Access"])
					

def __ui_create_thread(aParam):
	try:
		if (aParam[0] == 1):
			thd = threading.Thread(target =__ui_operation_polling_usercommand_thread, args = (0, aParam) )
			aParam.append(thd) #aParam last item to notify thread information
			thd.start()
	except:
		thd = threading.Thread(target =__ui_operation_default_thread, args = (0, aParam) )
		thd.start()
		
def Mapi_UI_init(intThreadType, intThreadCmd, intStateSattus, aParam):
	global g_Mutex_UI
	global g_UIOperation
	
	g_Mutex_UI = MT_OS_CreateMutex("UI Operation")
	g_UIOperation = UI_Operation()
	print("Mapi_UI_init", aParam)
	MT_OS_AppendJobPool(int(ProcessJobPriorityEnum.EM_JOB_PRI_HIGH), MT_OS_TransStateEnum2Int([ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD, ThreadTypeEnum.EM_TH_TYPE_UI_OPERATION, ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD, 0]), [1])

def Mapi_UI_action(intThreadType, intThreadCmd, intStateSattus, aParam):
	if (intThreadCmd == ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD):
		__ui_create_thread(aParam)
