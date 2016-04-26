import os
import re
import csv
import system_info_mantain
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
class csvDB_StockCompanyInfo:
	aStockCompanyTab = []

	def initStockCompanyInfo(self):
		self.aStockCompanyTab.clear()

	def appendStockCompanyInfo(self, intIdx, aCompanyInfo):
		if (intIdx < len(self.aStockCompanyTab) and intIdx >= 0):
			self.aStockCompanyTab[intIdx] = aCompanyInfo
			return intIdx
		else:
			self.aStockCompanyTab.append(aCompanyInfo)
			return (len(self.aStockCompanyTab) - 1)

	def updateStockComapny(self, intIdx):
		if (intIdx >= 0 and intIdx < len(self.aStockCompanyTab)):
			return self.aStockCompanyTab[intIdx]
		else:
			return None

	def getStockCompanyInfo(self, intIdx):
		if (intIdx < len(self.aStockCompanyTab)):
			return self.aStockCompanyTab[intIdx]
		return None

	def removeStockCompanyInfo(self, intIdx):
		if (intIdx < len(self.aStockCompanyTab)):
			self.aStockCompanyTab.pop(intIdx)
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
#    (1) very imporant, index "must" match with csvDB_StockCompanyInfo.aStockCompanyTab[] for easy fetching
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
class csvDB_StockDailyInfo:
	aStockDailyTab = []

	def initStockDailyInfo(self):
		self.aStockDailyTab.clear()


def __drv_db_get_pathformat_stockcommpany():
	aFile_Format = system_info_mantain.Mapi_SysInfo_GetAtrributeValue(0, "system.ini", "Stock Company Info", ["file path", "file name"])
	return (aFile_Format[0]+aFile_Format[1])

# 1. read "./data/stock/stock_company.csv" , which of file path is mantained by system.ini , "Stock Company Info"
# 2. (1) if "./data/stock/stock_company.csv" does not exist, then return 0;
#    (2) otherwise , if "./data/stock/stock_company.csv" exists, return 1
#
def Mdrv_DB_Connect_StockCompany(aParam):
	sFilePath = __drv_db_get_pathformat_stockcommpany()
	if (os.path.isfile(sFilePath) == False):
		sDicPath = os.path.dirname(sFilePath)
		if not os.path.isdir(sDicPath):
			os.makedirs(sDicPath)
		return 0
	else:
		if (os.path.getsize(sFilePath) == 0):
			return 0
	return 1

def Mdrv_DB_Update_StockCompany(aStockCompanyInfo):
	if (aStockCompanyInfo == None):
		return 0

	sFilePath = __drv_db_get_pathformat_stockcommpany()
	fpSCompany = open(sFilePath ,'w')

	fpSCompany.write("Number,Name\n")
	for i in range(len(aStockCompanyInfo)):
		sStockSerial = aStockCompanyInfo[i][0]
		sStockName = aStockCompanyInfo[i][1]
		sLine = sStockSerial + "," + sStockName + "\n"
		fpSCompany.write(sLine)

	fpSCompany.close()
	return 1

def Mdrv_DB_Capture_StockCompany(aParam):
	aStockCompanyInfo = []
	sFilePath = __drv_db_get_pathformat_stockcommpany()

	with open(sFilePath, 'r') as fpSCompany:
		for row in csv.reader(fpSCompany):
			if (row[0] == "Number"):
				continue
				
			aCompany = []
			for i in range(len(row)):
				aCompany.append(row[i])
			if (len(aCompany) > 0):
				aStockCompanyInfo.append(aCompany)

	return aStockCompanyInfo

	
	



