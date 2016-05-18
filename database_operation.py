import threading
import datetime
from enum import IntEnum
from main_state_machine import *
from csv_database_control import *


class DB_Operation(CsvDBStockCompanyInfo, CsvDBStockDailyInfo):
	__aCache_StockSerial = []

	def __init__(self):
		super().init_stockcompany()
		super().init_stockdaily_info()
		self.__aCache_StockSerial.clear()

	def findStockSerialTabIndx(self, sStockSerial):
		try:
			return self.__aCache_StockSerial.index(sStockSerial)
		except:
			return -1

	def getStockSerialTabSize(self):
		return len(self.__aCache_StockSerial)
		
	def getStockSerialTab(self):
		return self.__aCache_StockSerial

	# @overwrite: csvDB_StockCompanyInfo for Cahche Stock Serail to easy find index
	def append_stockcompany(self, aCompanyInfo):
		sStockSerial = aCompanyInfo[0]
		
		if (aCompanyInfo == None or len(sStockSerial) == 0):
			return 0

		intIdx = super().append_stockcompany(self.findStockSerialTabIndx(sStockSerial), aCompanyInfo)

		#dynamic increase __aCache_StockSerial[] for match index
		i = len(self.__aCache_StockSerial)
		while (i <= intIdx):
			self.__aCache_StockSerial.append("")
			i+=1
			
		self.__aCache_StockSerial[intIdx] = sStockSerial
		return 1



def Mapi_DB_Connect_StockCompany(aParam):
	return mdrv_db_connect_stockcompany(aParam)

def Mapi_DB_Update_StockCompany(aStockCompanyInfo):
	return mdrv_db_update_stockcompany(aStockCompanyInfo)

def Mapi_DB_Capture_StockCompany(aParam):
	if (g_DB_Operation. getStockSerialTabSize() == 0):
		aStockCompanyInfo = mdrv_db_capture_stockcompany(aParam)
		for i in range(len(aStockCompanyInfo)):
			g_DB_Operation.append_stockcompany(aStockCompanyInfo[i])
	return g_DB_Operation.getStockSerialTab()
	

def Mapi_DB_init(intThreadType, intThreadCmd, intStateSattus, aParam):
	global g_Mutex_DB
	global g_DB_Operation
	g_Mutex_DB = mt_os_create_mutex("DB Operation")
	g_DB_Operation = DB_Operation()


