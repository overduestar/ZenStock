import datetime
import os
import re

# 1. Provide System to access customerized infromation 
# 2. It can not load all system info during init duration;Otherwise, by system request, it is triggered to access system info
# 3. __aInfoTab is clear as init duration; Beside, system trigger access system info requeset , __aInfoTab can cache result info data
# 4. System can choice to direct access __aInfoTab[]  or to re-access system info
# 5. Describe __aInfoTab :
#     (1) element of __aInfoTab , including:
#     		<1> system (.ini) file path
#           <2> System Info Title
#           <3> [System Info attributes.......]
#     (2) example:
#        Content of system.ini
#          [Stock Daily Web]
# 	              <name> web site </name>
#	              <value> http://www.twse.com.tw/ch/trading/exchange/STOCK_DAY/STOCK_DAY_print.php?genpage=genpage/Report%04d%02d/%04d%02d_F3_1_8_%s.php&type=csv </value>
#	              <name> template csv output </name>
#	              <value> ./temp_data/%04d%02d_%s.csv <value>
#
#        --> __aInfoTab = [["system.ini", "Stock Daily Web", ["web site", http://www.twse.com.tw/ch/trading/exchange/STOCK_DAY/STOCK_DAY_print.php?genpage=genpage/Report%04d%02d/%04d%02d_F3_1_8_%s.php&type=csv], ["template csv output", ./temp_data/%04d%02d_%s.csv ] ]
#
#

class System_Info_Operation:
	__aInfoTab = []

	def __init__(self):
		self.__aInfoTab.clear()

	# > 0 : exist of __aInfoTab and return index ; otherwise, return -1 : means no exist of __aInfoTab
	def indexInfo(self, sIni_Path, sInfo_Title):
		for i in range(len(self.__aInfoTab)):
			if (self.__aInfoTab[i][0] == sIni_Path and self.__aInfoTab[i][1] == sInfo_Title):
				return i
		return -1

	def appendInfo(self, sIni_Path, sInfo_Title, aInfo_Attr):
		if (self.indexInfo(sIni_Path, sInfo_Title) >= 0):
			return 0  #mean:already exist of __aInfoTab , no need new append

		self.__aInfoTab.append([sIni_Path, sInfo_Title, aInfo_Attr])
		return 1

	def updateInfoAttribute(self, sIni_Path, sInfo_Title, aInfo_Attr):
		if (aInfo_Attr == None):
			return 0
	
		intIndex = self.indexInfo(sIni_Path, sInfo_Title)
		if (intIndex == -1):
			return 0

		aCurrent_InfoAttr = self.__aInfoTab[intIndex][2]
		if (aCurrent_InfoAttr == None):
			aCurrent_InfoAttr = []
			
		i = 0
		while (i < len(aInfo_Attr)):
			intFlag = 0 #0:add , 1:update
			for j in range(len(aCurrent_InfoAttr)):
				if (aCurrent_InfoAttr[j][0] == aInfo_Attr[i][0]):
					aCurrent_InfoAttr[j][1] = aInfo_Attr[i][1]
					intFlag = 1
					break
			if (intFlag == 1):
				aInfo_Attr.pop(i)
				i-=1
			i+=1

		if (len(aInfo_Attr) > 0):
			aCurrent_InfoAttr.append(aInfo_Attr)

		self.__aInfoTab[intIndex][2] = aCurrent_InfoAttr
		return 1

	def getInfoAttributeValue(self, sIni_Path, sInfo_Title, aInfo_AttrName):
		if (aInfo_AttrName == None):
			return None

		intIndex = self.indexInfo(sIni_Path, sInfo_Title) 
		if (intIndex == -1):
			return None

		aCurrent_InfoAttr = self.__aInfoTab[intIndex][2]
		aInfo_AttrValue = []
		for i in range(len(aInfo_AttrName)):
			for j in range(len(aCurrent_InfoAttr)):
				if (aInfo_AttrName[i] == aCurrent_InfoAttr[j][0]):
					aInfo_AttrValue.append(aCurrent_InfoAttr[j][1])
					break
		return aInfo_AttrValue
		

	def removeInfo(self, sIni_Path, sInfo_Title):
		intIndex = self.indexInfo(sIni_Path, sInfo_Title)
		if (intIndex == -1):
			return 0

		self.__aInfoTab.pop(intIndex)
		return 1

	def printMsg(self):
		print("System_Info_Operation Msg: ", len(self.__aInfoTab))
		for i in range(len(self.__aInfoTab)):
			print(self.__aInfoTab[i])


def Mapi_SysInfo_Init():
	global g_SysInfo_Operation
	g_SysInfo_Operation = System_Info_Operation()
	Mapi_SysInfo_Update("system.ini")
	


def Mapi_SysInfo_Update(sIni_Path):
	#print ("sIni_Path:", sIni_Path)
	if (os.path.exists(sIni_Path) == False):
		print("Warning:[Mapi_SysInfo_Update] path fail: ", sIni_Path)
		return 0

	fIni = open(sIni_Path, 'r')
	
	sIniContent = fIni.read()
	aSplitContent = re.split("\[", sIniContent)
	for i in range(1, len(aSplitContent)):
		sInfo_Title = ""
		aInfo_Attr = []
		
		aSplitTitle = re.split("\]", aSplitContent[i])
		sInfo_Title = aSplitTitle[0]
		aSplitAttr = re.split("\<name\>", aSplitTitle[1])
		for j in range(1, len(aSplitAttr)):
			sAttrName = ""
			sAttrValue = ""
			aSplitAttrName = re.split("\<name\>", aSplitAttr[j])
			sAttrName = re.split("\<\/name\>", aSplitAttrName[0])[0]
			aSplitAttrValue = re.split("\<value\>", aSplitAttrName[0])
			sAttrValue = re.split("\<\/value\>", aSplitAttrValue[1])[0]

			aInfo_Attr.append([sAttrName, sAttrValue])

		g_SysInfo_Operation.removeInfo(sIni_Path, sInfo_Title)
		g_SysInfo_Operation.appendInfo(sIni_Path, sInfo_Title, aInfo_Attr)

	fIni.close()


#intAction:  0 --> first direct get __aInfoTab ; if __aInfoTab no data, read sIni_Path and append data into __aInfoTab
#            1 --> direct read sIni_Path and update data into __aInfoTab
def Mapi_SysInfo_GetAtrributeValue(intAction, sIni_Path, sInfo_Title, aInfo_AttrName):
	if (intAction == 0):
		intIndex = g_SysInfo_Operation.indexInfo(sIni_Path, sInfo_Title)
		if (intIndex >= 0):
			return g_SysInfo_Operation.getInfoAttributeValue(sIni_Path, sInfo_Title, aInfo_AttrName)

	Mapi_SysInfo_Update(sIni_Path)
	return g_SysInfo_Operation.getInfoAttributeValue(sIni_Path, sInfo_Title, aInfo_AttrName)


		
