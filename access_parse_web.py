import threading
import datetime
from enum import IntEnum
import system_info_mantain
from main_state_machine import *
from database_operation import *
import urllib.request
import urllib
from os import path
import codecs
import sys
import csv
import os 
import re

class WebNotifyEnum(IntEnum):
	EM_WEB_UI_NOTHING                = 0x0000
	EM_WEB_UI_REQUEST_DAIL           = 0x0001
	EM_WEB_AUTORUN_DAIL              = 0x0002
	EM_WEB_AUTORUN_DAIL_HISTORY      = 0x0003
	EM_WEB_SYS_REQUEST_STOCK_COMPANY = 0x0004

# 1. Provide other thread or process to notify signal for access web
#     (1) element of __aNotifyQueue, including:
#            <1> WebNotifyEnum
#            <2> notify Parameter
#     (2) always first in first out , no support preempt
#
class Web_Notify_Operation:
	__aNotifyQueue = []

	def __init__(self):
		self.__aNotifyQueue.clear()

	def appendNotify(self, eNotifyType, aParam):
		self.__aNotifyQueue.append([eNotifyType, aParam])

	def getNotify(self):
		if (len(self.__aNotifyQueue) == 0):
			return None
		return self.__aNotifyQueue[0]

	def removeNotify(self):
		if (len(self.__aNotifyQueue) > 0):
			self.__aNotifyQueue.pop(0)	



def __web_access_parse_stock_comapny(aParam):
	aStockCompanInfo = []
	aUrlPath = system_info_mantain.Mapi_SysInfo_GetAtrributeValue(0, "system.ini", "Stock Serail List Web", ["web site"])
	sUrlPath = aUrlPath[0]
	sUrlInfo = codecs.decode(urllib.request.urlopen(sUrlPath).read(), 'big5', errors='ignore')
	if (len(sUrlInfo)  == 0):
		return aStockCompanInfo
		
	aSplitUrlInfo = re.split("<td", sUrlInfo)
	intItemFlag = 0
	sStockSerial = ""
	sStockName = ""
	for i in range(len(aSplitUrlInfo)):
		sData = ""
		if (aSplitUrlInfo[i].find("td") >= 0):
			sData = aSplitUrlInfo[i].split('>')[1].replace("&nbsp;", "").split('<')[0]
		if (len(sData) > 0):
			if (intItemFlag == 0):
				sStockSerial = sData
				intItemFlag = 1
			elif (intItemFlag == 1):
				sStockName = sData
				aStockCompanInfo.append([sStockSerial, sStockName])
				intItemFlag = 0
	return aStockCompanInfo

def __web_access_stock_company(aParam):
	intRet = mapi_db_connect_stockcompany(aParam)
	if (intRet == 0): #connect stock company fail
		aStockCompanyInfo = __web_access_parse_stock_comapny(aParam)
		mapi_db_update_stockcompany(aStockCompanyInfo)

	return mapi_db_capture_stockcompany(aParam)
	
			
def __web_access_parse_stock_daily(dStartDate, dEndDate, sStocklist):
	print("__web_access_parse_daily: start")
	#check start & end date
	if (dEndDate == None):
		dEndDate = datetime.date(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day)
	if ((dStartDate == None) or (dStartDate>dEndDate)):
		dStartDate = dEndDate

	aStocklist = []
	if (sStocklist == "all"):
		aStocklist = __web_access_stock_company(None)
	else:
		aStocklist.append(sStocklist)

	
		

def __web_default_thread(x, aParam):
	print("__web_default_thread start:", aParam)

def __web_access_parse_thread(x, aParam):
	print("__web_access_parse_thread start:", aParam)
	
	thd = aParam[-1] #get aParam[] last item to notify thread
	aNotifyInfo = None
	while(1):
		mt_os_acquire_mutex(g_Mutex_Web)
		aNotifyInfo = g_Web_Notify.getNotify()
		mt_os_release_mutex(g_Mutex_Web)

		if (aNotifyInfo != None):
			mt_os_acquire_mutex(g_Mutex_Web)

			intNotifyAction = aNotifyInfo[0]
			aNotifyParam = aNotifyInfo[1]
			if (intNotifyAction == WebNotifyEnum.EM_WEB_UI_REQUEST_DAIL):
				__web_access_parse_stock_daily(aNotifyParam[0], aNotifyParam[1], aNotifyParam[2])
			elif (intNotifyAction == WebNotifyEnum.EM_WEB_SYS_REQUEST_STOCK_COMPANY):
				__web_access_stock_company(aNotifyParam)
			
			g_Web_Notify.removeNotify()
			mt_os_release_mutex(g_Mutex_Web)

		mt_os_sleep_ms(100)


		
def __web_create_thread(aParam):
	try:
		if (aParam[0] == 1):
			thd = threading.Thread(target =__web_access_parse_thread, args = (0, aParam) )
			aParam.append(thd) #aParam last item to notify thread information
			thd.start()
	except:
		thd = threading.Thread(target =__web_default_thread, args = (0, aParam) )
		thd.start()
		
def __web_notify_action(aParam):
	if ((aParam != None) and len(aParam)>0):
		aNotifyParam =  aParam[0]
		sNotifyStr = aParam[1]

		#parse Notify String to decide what action
		intNotifyAction = WebNotifyEnum.EM_WEB_UI_NOTHING
		if (sNotifyStr == "UI Request Daily Access"):  #depand on "ui_operatin" send notify action string
			intNotifyAction = WebNotifyEnum.EM_WEB_UI_REQUEST_DAIL

		mt_os_acquire_mutex(g_Mutex_Web)
		g_Web_Notify.appendNotify(intNotifyAction, aNotifyParam)
		mt_os_release_mutex(g_Mutex_Web)

def Mapi_AccessParseWeb_init(intThreadType, intThreadCmd, intStateSattus, aParam):
	global g_Mutex_Web
	global g_Web_Notify
	
	g_Mutex_Web = mt_os_create_mutex("Access Parse Web")
	g_Web_Notify = Web_Notify_Operation()
	mt_os_append_job_pool(int(ProcessJobPriorityEnum.EM_JOB_PRI_HIGH), mt_os_trans_state_enum2int([ProcessStateEnum.EM_PS_SYS_PROGRASS_THREAD, ThreadTypeEnum.EM_TH_TYPE_ACCESS_PARSE_WEB, ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD, 0]), [1])

def Mapi_AccessParseWeb_action(intThreadType, intThreadCmd, intStateSattus, aParam):
	if (intThreadCmd == ThreadCMDEnum.EM_TH_CMD_CREATE_THREAD):
		__web_create_thread(aParam)
	elif (intThreadCmd == ThreadCMDEnum.EM_TH_CMD_NOTIFY_THREAD):
		__web_notify_action(aParam)
