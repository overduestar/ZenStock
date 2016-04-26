from enum import IntEnum
import time
import sys
import threading

#
#
# set 32-bit to describe status & command of process and thread
# [bit0  ~ bit7 ] :show process & thread status
# [bit8  ~ bit15] :show thread command or action 
# [bit16 ~ bit23] :show thread type
# [bit24 ~ bit31] :show process state
#
# Main process can depand on "thread type"([[bit16 ~ bit23]])  to excute relative thread_action function. Then, thread_action function depand on "thread command"([bit8  ~ bit15])
# to run relative command function , and info "thread status"([bit0  ~ bit7 ]) for Main process
#
#

class ProcessStateEnum(IntEnum):
	EM_PS_SYS_STABLE          = (0x00)<<24
	EM_PS_SYS_IDEL            = (0x01)<<24
	EM_PS_SYS_INIT            = (0x02)<<24
	EM_PS_SYS_PROGRASS_THREAD = (0x03)<<24
	EM_PS_SYS_DEMAGE          = (0x04)<<24
	EM_PS_SYS_RESET           = (0x05)<<24
	EM_PS_SYS_NOTIFY_SLEEP    = (0x06)<<24
	EM_PS_SYS_TERMINATE       = (0x07)<<24
	EM_PS_SYS_RESECHDEULE     = (0x08)<<24

class ThreadTypeEnum(IntEnum):
	EM_TH_TYPE_NONE                  = (0x00)<<16
	EM_TH_TYPE_ACCESS_PARSE_WEB      = (0x01)<<16
	EM_TH_TYPE_DATABASE_OPERATION    = (0x02)<<16
	EM_TH_TYPE_MAILSERVER_OPERATION  = (0x03)<<16
	EM_TH_TYPE_UI_OPERATION          = (0x04)<<16

class ThreadCMDEnum(IntEnum):
	EM_TH_CMD_NONE                                    = (0x00)<<8
	EM_TH_CMD_INIT                                    = (0x01)<<8
	EM_TH_CMD_CREATE_THREAD                           = (0x02)<<8
	EM_TH_CMD_DESTORY_THREAD                          = (0x03)<<8
	EM_TH_CMD_WAIT_THREAD                             = (0x04)<<8
	EM_TH_CMD_PREEMPT_THREAD                          = (0x05)<<8
	EM_TH_CMD_SET_PROPERTY_THREAD                     = (0x06)<<8
	EM_TH_CMD_NOTIFY_THREAD                           = (0x07)<<8

class StateStatusEnum(IntEnum):
	EM_ST_NORMAL             = (0x00)<<0  #only for EM_PS_SYS_STABLE & EM_PS_SYS_IDEL usage
	EM_ST_SUCESS             = (0x01)<<0
	EM_ST_WARNNING           = (0x02)<<0
	EM_ST_ERROR              = (0x03)<<0
	EM_ST_RETRY              = (0x04)<<0

#
#
# set job priority for process schedule
#
#

class ProcessJobProrityEnum(IntEnum):
	EM_JOB_PRI_SUPERHIGH    = 0
	EM_JOB_PRI_HIGH         = 1
	EM_JOB_PRI_NORMAL       = 2
	EM_JOB_PRI_LOW          = 3
	EM_JOB_PRI_VERYLOW      = 4

# ============================================================
# ============================================================
# 
#              Class & Global Variable 
#
# ============================================================
# ============================================================


# 1. Provide for setting job priority  with aJobPool
#     (1) if same priority , first in first out
#     (2) as current job finish, it re-schedule accroding of job priority
# 2. aJobPool[] is for jobs which is will be executed according priority + first in first out
#     (1) the elment of aJobPool, including:
#           <1> Job State --> ProcessStateEnum | ThreadTypeEnum | ThreadCMDEnum | StateStatusEnum
#           <2> Job Parameter
# 3. aJobSleepPool[] is for jobs which want to sleep some seconds then to execute
#     (1) the element of aJobSleepPool[] , including:
#           <1> Job State --> ProcessStateEnum | ThreadTypeEnum | ThreadCMDEnum | StateStatusEnum
#           <2> Job Parameter
#           <3> Job Priority --> ProcessJobProrityEnum
#           <4> sleep duration , unit:ms 
#           <5> push to Sleep Pool time
#
class Process_JobQueue:
	__aJobPool = []
	__aJobSleepPool = []
	
	__aCurrentState = 0
	__aPreviousState = 0
	__intTotalPriNum = 0

	def __init__(self):
		self.__aCurrentState = [self.transStateEnum2Int([ProcessStateEnum.EM_PS_SYS_STABLE, ThreadTypeEnum.EM_TH_TYPE_NONE, ThreadCMDEnum.EM_TH_CMD_NONE, ThreadCMDEnum.EM_TH_CMD_NONE]), None]
		self.__aPreviousState = self.__aCurrentState
		self.__intTotalPriNum = self.transPriorityEnum2Int(ProcessJobProrityEnum.EM_JOB_PRI_VERYLOW) + 1
		self.__aJobPool.clear()
		self.__aJobSleepPool.clear()
		for i in range(self.__intTotalPriNum):
			aPriorityStation = []
			self.__aJobPool.append(aPriorityStation)

	def transStateEnum2Int(self, aState):
		if (aState == None):
			return -1
		intPS_State = int(aState[0])
		intTH_Type = int(aState[1])
		intTH_Cmd = int(aState[2])
		intST_Status = int(aState[3])
		return (intPS_State | intTH_Type | intTH_Cmd | intST_Status)

	def transPriorityEnum2Int(self, enumPriority):
		return int(enumPriority)

	def getScheduleCurrentState(self):
		return self.__aCurrentState;

	def getSchedulePreviousState(self):
		return self.__aPreviousState;

	def appendJobPool(self, intPriority, intState, aParam):
		if ((intPriority < 0) or (intPriority >= self.__intTotalPriNum)):
			return -1
		if (intState < 0):
			return -1

		self.__aJobPool[intPriority].append([intState, aParam])
		return 1

	def get_and_removeJobPool(self):
		aState = None
		for i in range(self.__intTotalPriNum):
			aPriorityStation = self.__aJobPool[i]
			if (len(aPriorityStation) > 0):
				aState =  aPriorityStation[0]
				aPriorityStation.pop(0)
				break
				
		if (aState != None):
			self.__aPreviousState = self.__aCurrentState
			self.__aCurrentState = aState
		
		return aState

	def deleteJobPool(self, intState):
		for i in range(self.__intTotalPriNum):
			aPriorityStation = self.__aJobPool[i]
			j = 0
			while (j < len(aPriorityStation)):
				if (aPriorityStation[j][0] == intState):
					aPriorityStation.pop(j)
					j-=1
				j+=1


	def appendSleepPool(self, aParam):
		if (aParam == None):
			return -1

		aParam[3] = time.clock() #update time of pushing to Sleep Pool
		self.__aJobSleepPool.append(aParam)
		return 1

	def getSleepPoolSize(self):
		return len(self.__aJobSleepPool)

	def pushSleepPoolToJobPool(self):
		i = 0
		while (i < len(self.__aJobSleepPool)):
			aSleepTask = self.__aJobSleepPool[i]
			intState = aSleepTask[0]
			aParam = aSleepTask[1]
			intPriority = aSleepTask[2]
			intSleepDuration = aSleepTask[3]
			intSpectTime = aSleepTask[4]

			intCurrentTime = time.clock()
			if ((intCurrentTime - intSpectTime)*1000 >= intSleepDuration):
				self.appendJobPool(intPriority, intState, aParam)
				self.__aJobSleepPool.pop(i)
				i-=1
			i+=1

	def clearSleepPool(self):
		self.__aJobSleepPool.clear()

	def force_wakeupSleepPool(self, intState):
		for i in range(len(self.__aJobSleepPool)):
			if (self.__aJobSleepPool[i][0] == intState):
				self.__aJobSleepPool[i][3] = 0 #change sleep duration as 0 to force wakeup

		self.pushSleepPoolToJobPool()

	def printMsg(self):
		print("Current State:", self.__intCurrentState, "; Previous State:", self.__intPreviousState)
		print("============= Job Pool ======================")
		for i in range(self.__intTotalPriNum):
			print ("Prority :" , i)
			print ("    -->", self.__aJobPool[i])

		print("============= Sleep Pool ======================")
		for i in range(len(self.__aJobSleepPool)):
			print("index" , i, "-->", self.__aJobSleepPool[i])

# 1. Provide mutex operation,
#     (1) element of __aMutexPool[] , including:
#          <1> mutex name --> prime key to notify how to get lock
#          <2> lock for platform  acquire() & relase()
#
#
class Process_Communication:
	__aMutexPool = []

	def __init__(self):
		self.__aMutexPool.clear()

	def	createMutex(self, sMutexName):
		if (len(sMutexName) <= 0):
			return None

		intIdx = self.findMutex(sMutexName)
		if ( intIdx >= 0):
			return self.__aMutexPool[intIdx][1]
		else:
			lock = threading.Lock()
			self.__aMutexPool.append([sMutexName, lock])
			return lock

	def findMutex(self, sMutexName):
		for i in range(len(self.__aMutexPool)):
			sName = self.__aMutexPool[i][0]
			if (len(sName) == len(sMutexName)):
				if (sName.find(sMutexName) >= 0):
					return i
		return -1

	def acquireMutex(self, lock):
		if (lock == None):
			return -1
		lock.acquire()
		return 1

	def releaseMutex(self, lock):
		if (lock == None):
			return -1
			
		lock.release()
		return 1
			
			
# ============================================================
# ============================================================
# 
#              Function Section 
#
# ============================================================
# ============================================================

def MT_OS_Init():
	global g_ProcessSchedule
	global g_ProcessCommunication
	global g_Mutex_JobPool
	global g_Mutex_SleepPool
	
	g_ProcessSchedule = Process_JobQueue()
	g_ProcessCommunication = Process_Communication()

	g_Mutex_JobPool = MT_OS_CreateMutex("Process Schedule Job Pool")
	g_Mutex_SleepPool = MT_OS_CreateMutex("Process Schedule Sleep Pool")
	
	MT_OS_AppendJobPool(int(ProcessJobProrityEnum.EM_JOB_PRI_NORMAL) , MT_OS_TransStateEnum2Int([ProcessStateEnum.EM_PS_SYS_INIT, 0, 0, 0]), None)
	MT_OS_AppendJobPool(int(ProcessJobProrityEnum.EM_JOB_PRI_NORMAL) , MT_OS_TransStateEnum2Int([ProcessStateEnum.EM_PS_SYS_IDEL, 0, 0, 0]), None)

def MT_OS_Schedule():
	MT_OS_AcquireMutex(g_Mutex_JobPool)
	MT_OS_AcquireMutex(g_Mutex_SleepPool)
	g_ProcessSchedule.get_and_removeJobPool()
	aState = g_ProcessSchedule.getScheduleCurrentState()
	MT_OS_ReleaseMutex(g_Mutex_SleepPool)
	MT_OS_ReleaseMutex(g_Mutex_JobPool)
	return aState

def MT_OS_AppendJobPool(intPriority, intState, aParam):
	MT_OS_AcquireMutex(g_Mutex_JobPool)
	intRetValue = g_ProcessSchedule.appendJobPool(intPriority, intState, aParam)
	MT_OS_ReleaseMutex(g_Mutex_JobPool)
	return intRetValue

def MT_OS_AppendSleepPool(aSleepParam):
	MT_OS_AcquireMutex(g_Mutex_SleepPool)
	intRetValue = g_ProcessSchedule.appendSleepPool(aSleepParam)
	MT_OS_ReleaseMutex(g_Mutex_SleepPool)
	return intRetValue

def MT_OS_TransStateEnum2Int(aState):
	return g_ProcessSchedule.transStateEnum2Int(aState)

def MT_OS_SleepMs(intMs):
	sys.stdout.flush() #stdout.flush() to slove conflict between print and sleep 
	time.sleep((intMs/1000))

def MT_OS_CreateMutex(sMutexName):
	return g_ProcessCommunication.createMutex(sMutexName)

def MT_OS_AcquireMutex(lock):
	return g_ProcessCommunication.acquireMutex(lock)

def MT_OS_ReleaseMutex(lock):
	return g_ProcessCommunication.releaseMutex(lock)


