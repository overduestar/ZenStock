""" main state machine """
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
# Main process can depand on "thread type"([[bit16 ~ bit23]])  to excute
# relative thread_action function. Then, thread_action function depand on
# "thread command"([bit8  ~ bit15])
# to run relative command function , and info "thread status"([bit0  ~ bit7 ]) for Main process
#
#

class ProcessStateEnum(IntEnum):
    """ process state enum """
    EM_PS_SYS_STABLE = (0x00)<<24
    EM_PS_SYS_IDEL = (0x01)<<24
    EM_PS_SYS_INIT = (0x02)<<24
    EM_PS_SYS_PROGRASS_THREAD = (0x03)<<24
    EM_PS_SYS_DEMAGE = (0x04)<<24
    EM_PS_SYS_RESET = (0x05)<<24
    EM_PS_SYS_NOTIFY_SLEEP = (0x06)<<24
    EM_PS_SYS_TERMINATE = (0x07)<<24
    EM_PS_SYS_RESECHDEULE = (0x08)<<24

class ThreadTypeEnum(IntEnum):
    """ thread type enum """
    EM_TH_TYPE_NONE = (0x00)<<16
    EM_TH_TYPE_ACCESS_PARSE_WEB = (0x01)<<16
    EM_TH_TYPE_DATABASE_OPERATION = (0x02)<<16
    EM_TH_TYPE_MAILSERVER_OPERATION = (0x03)<<16
    EM_TH_TYPE_UI_OPERATION = (0x04)<<16

class ThreadCMDEnum(IntEnum):
    """ thread cmd enum """
    EM_TH_CMD_NONE = (0x00)<<8
    EM_TH_CMD_INIT = (0x01)<<8
    EM_TH_CMD_CREATE_THREAD = (0x02)<<8
    EM_TH_CMD_DESTORY_THREAD = (0x03)<<8
    EM_TH_CMD_WAIT_THREAD = (0x04)<<8
    EM_TH_CMD_PREEMPT_THREAD = (0x05)<<8
    EM_TH_CMD_SET_PROPERTY_THREAD = (0x06)<<8
    EM_TH_CMD_NOTIFY_THREAD = (0x07)<<8

class StateStatusEnum(IntEnum):
    """ state status enum """
    EM_ST_NORMAL = (0x00)<<0  #only for EM_PS_SYS_STABLE & EM_PS_SYS_IDEL usage
    EM_ST_SUCESS = (0x01)<<0
    EM_ST_WARNNING = (0x02)<<0
    EM_ST_ERROR = (0x03)<<0
    EM_ST_RETRY = (0x04)<<0

#
#
# set job priority for process schedule
#
#

class ProcessJobPriorityEnum(IntEnum):
    """ process job priority enum """
    EM_JOB_PRI_SUPERHIGH = 0
    EM_JOB_PRI_HIGH = 1
    EM_JOB_PRI_NORMAL = 2
    EM_JOB_PRI_LOW = 3
    EM_JOB_PRI_VERYLOW = 4

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
#           <3> Job Priority --> ProcessJobPriorityEnum
#           <4> sleep duration , unit:ms
#           <5> push to Sleep Pool time
#
class ProcessJobQueue:
    """ process job queue """
    __a_job_pool = []
    __a_job_sleep_pool = []

    __a_current_state = 0
    __a_previous_state = 0
    __int_total_pri_num = 0

    def __init__(self):
        self.__a_current_state = [self.trans_state_enum2int(
            [ProcessStateEnum.EM_PS_SYS_STABLE, ThreadTypeEnum.EM_TH_TYPE_NONE,
             ThreadCMDEnum.EM_TH_CMD_NONE, ThreadCMDEnum.EM_TH_CMD_NONE]), None]
        self.__a_previous_state = self.__a_current_state
        self.__int_total_pri_num = self.trans_priority_enum2int(
            ProcessJobPriorityEnum.EM_JOB_PRI_VERYLOW) + 1
        self.__a_job_pool.clear()
        self.__a_job_sleep_pool.clear()
        self.__a_job_pool = [[] for i in range(self.__int_total_pri_num)]

    def trans_state_enum2int(self, a_state):
        """ trans state enum to int """
        if a_state is None:
            return -1
        int_ps_state = int(a_state[0])
        int_th_type = int(a_state[1])
        int_th_cmd = int(a_state[2])
        int_st_status = int(a_state[3])
        return int_ps_state | int_th_type | int_th_cmd | int_st_status

    def trans_priority_enum2int(self, enum_priority):
        """ trans priority enum to int """
        return int(enum_priority)

    def get_schedule_current_state(self):
        """ get schedule current state """
        return self.__a_current_state

    def get_schedule_previous_state(self):
        """ get schedule previous state """
        return self.__a_previous_state

    def append_job_pool(self, int_priority, int_state, a_param):
        """ append job pool """
        if (int_priority < 0) or (int_priority >= self.__int_total_pri_num):
            return -1
        if int_state < 0:
            return -1

        self.__a_job_pool[int_priority].append([int_state, a_param])
        return 1

    def get_and_remove_job_pool(self):
        """ get and remove job pool """
        a_state = None
        for i in range(self.__int_total_pri_num):
            a_priority_station = self.__a_job_pool[i]
            if len(a_priority_station) > 0:
                a_state = a_priority_station[0]
                a_priority_station.pop(0)
                break

        if a_state != None:
            self.__a_previous_state = self.__a_current_state
            self.__a_current_state = a_state

        return a_state

    def delete_job_pool(self, int_state):
        """ delete job pool """
        for i in range(self.__int_total_pri_num):
            a_priority_station = self.__a_job_pool[i]
            j = 0
            while j < len(a_priority_station):
                if a_priority_station[j][0] == int_state:
                    a_priority_station.pop(j)
                    j -= 1
                j += 1


    def append_sleep_pool(self, a_param):
        """ append sleep pool """
        if a_param is None:
            return -1

        a_param[3] = time.clock() #update time of pushing to Sleep Pool
        self.__a_job_sleep_pool.append(a_param)
        return 1

    def get_sleep_pool_size(self):
        """ get sleep pool size """
        return len(self.__a_job_sleep_pool)

    def push_sleep_pool_to_job_pool(self):
        """ push sleep pool to job pool """
        i = 0
        while i < len(self.__a_job_sleep_pool):
            a_sleep_task = self.__a_job_sleep_pool[i]
            int_state = a_sleep_task[0]
            a_param = a_sleep_task[1]
            int_priority = a_sleep_task[2]
            int_sleep_duration = a_sleep_task[3]
            int_spect_time = a_sleep_task[4]

            int_current_time = time.clock()
            if (int_current_time - int_spect_time)*1000 >= int_sleep_duration:
                self.append_job_pool(int_priority, int_state, a_param)
                self.__a_job_sleep_pool.pop(i)
                i -= 1
            i += 1

    def clear_sleep_pool(self):
        """ clear sleep pool """
        self.__a_job_sleep_pool.clear()

    def force_wake_up_sleep_pool(self, int_state):
        """ force wake up sleep pool """
        for i in range(len(self.__a_job_sleep_pool)):
            if self.__a_job_sleep_pool[i][0] == int_state:
                self.__a_job_sleep_pool[i][3] = 0 #change sleep duration as 0 to force wakeup

        self.push_sleep_pool_to_job_pool()

    def print_msg(self):
        """ print msg """
        print("Current State:", self.__a_current_state, "; Previous State:",
              self.__a_previous_state)
        print("============= Job Pool ======================")
        for i in range(self.__int_total_pri_num):
            print("Prority :", i)
            print("    -->", self.__a_job_pool[i])

        print("============= Sleep Pool ======================")
        for i in range(len(self.__a_job_sleep_pool)):
            print("index", i, "-->", self.__a_job_sleep_pool[i])

# 1. Provide mutex operation,
#     (1) element of __aMutexPool[] , including:
#          <1> mutex name --> prime key to notify how to get lock
#          <2> lock for platform  acquire() & relase()
#
#
class ProcessCommunication:
    """ process communication """
    __aMutexPool = []

    def __init__(self):
        self.__aMutexPool.clear()

    def create_mutex(self, s_mutex_name):
        """ create mutex """
        if len(s_mutex_name) <= 0:
            return None

        int_idx = self.find_mutex(s_mutex_name)
        if int_idx >= 0:
            return self.__aMutexPool[int_idx][1]
        else:
            lock = threading.Lock()
            self.__aMutexPool.append([s_mutex_name, lock])
            return lock

    def find_mutex(self, s_mutex_name):
        """ find mutex """
        for i in range(len(self.__aMutexPool)):
            s_name = self.__aMutexPool[i][0]
            if len(s_name) == len(s_mutex_name):
                if s_name.find(s_mutex_name) >= 0:
                    return i
        return -1

    def acquire_mutex(self, lock):
        """ acquire mutex """
        if lock is None:
            return -1
        lock.acquire()
        return 1

    def release_mutex(self, lock):
        """ release mutex """
        if lock is None:
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

def mt_os_init():
    """ init """
    mt_os_append_job_pool(int(ProcessJobPriorityEnum.EM_JOB_PRI_NORMAL),
                          mt_os_trans_state_enum2int(
                              [ProcessStateEnum.EM_PS_SYS_INIT, 0, 0, 0]), None)
    mt_os_append_job_pool(int(ProcessJobPriorityEnum.EM_JOB_PRI_NORMAL),
                          mt_os_trans_state_enum2int(
                              [ProcessStateEnum.EM_PS_SYS_IDEL, 0, 0, 0]), None)

def mt_os_schedule():
    """ schedule """
    mt_os_acquire_mutex(G_MUTEX_JOB_POOL)
    mt_os_acquire_mutex(G_MUTEX_SLEEP_POOL)
    G_PROCESS_SCHEDULE.get_and_remove_job_pool()
    a_state = G_PROCESS_SCHEDULE.get_schedule_current_state()
    mt_os_release_mutex(G_MUTEX_SLEEP_POOL)
    mt_os_release_mutex(G_MUTEX_JOB_POOL)
    return a_state

def mt_os_append_job_pool(int_priority, int_state, a_param):
    """ append job pool """
    mt_os_acquire_mutex(G_MUTEX_JOB_POOL)
    int_ret_value = G_PROCESS_SCHEDULE.append_job_pool(int_priority, int_state, a_param)
    mt_os_release_mutex(G_MUTEX_JOB_POOL)
    return int_ret_value

def mt_os_append_sleep_pool(a_sleep_param):
    """ append sleep pool """
    mt_os_acquire_mutex(G_MUTEX_SLEEP_POOL)
    int_ret_value = G_PROCESS_SCHEDULE.append_sleep_pool(a_sleep_param)
    mt_os_release_mutex(G_MUTEX_SLEEP_POOL)
    return int_ret_value

def mt_os_trans_state_enum2int(a_state):
    """ trans state enum to int """
    return G_PROCESS_SCHEDULE.trans_state_enum2int(a_state)

def mt_os_sleep_ms(int_ms):
    """ sleep in ms """
    sys.stdout.flush() #stdout.flush() to slove conflict between print and sleep
    time.sleep((int_ms/1000))

def mt_os_create_mutex(s_mutex_name):
    """ create mutex """
    return G_PROCESS_COMMUNICATION.create_mutex(s_mutex_name)

def mt_os_acquire_mutex(lock):
    """ acquire mutex """
    return G_PROCESS_COMMUNICATION.acquire_mutex(lock)

def mt_os_release_mutex(lock):
    """ release mutex """
    return G_PROCESS_COMMUNICATION.release_mutex(lock)


G_PROCESS_SCHEDULE = ProcessJobQueue()
G_PROCESS_COMMUNICATION = ProcessCommunication()
G_MUTEX_JOB_POOL = mt_os_create_mutex("Process Schedule Job Pool")
G_MUTEX_SLEEP_POOL = mt_os_create_mutex("Process Schedule Sleep Pool")
