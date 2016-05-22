""" system info maintain """
import os
import re

# 1. Provide System to access customerized infromation
# 2. It can not load all system info during init duration;
#    Otherwise, by system request, it is triggered to access system info
# 3. __aInfoTab is clear as init duration; Beside, system trigger access system info requeset,
#    __aInfoTab can cache result info data
# 4. System can choice to direct access __aInfoTab[]  or to re-access system info
# 5. Describe __aInfoTab :
#     (1) element of __aInfoTab , including:
#           <1> system (.ini) file path
#           <2> System Info Title
#           <3> [System Info attributes.......]
#     (2) example:
#        Content of system.ini
#          [Stock Daily Web]
#                 <name> web site </name>
#                 <value> http://www.... </value>
#                 <name> template csv output </name>
#                 <value> ./temp_data/%04d%02d_%s.csv <value>
#
#        --> __aInfoTab = [["system.ini", "Stock Daily Web", ["web site", http://www...],
#                              ["template csv output", ./temp_data/%04d%02d_%s.csv]]
#
#

g_SysInfo_Operation = None

class SystemInfoOperation:
    """ system info operation """
    __aInfoTab = []

    def __init__(self):
        self.__aInfoTab.clear()

    # > 0 : exist of __aInfoTab and return index ;
    # otherwise, return -1 : means no exist of __aInfoTab
    def index_info(self, s_ini_path, s_info_title):
        """ index info """
        for i in range(len(self.__aInfoTab)):
            if self.__aInfoTab[i][0] == s_ini_path and self.__aInfoTab[i][1] == s_info_title:
                return i
        return -1

    def append_info(self, s_ini_path, s_info_title, a_info_attr):
        """ append info """
        if self.index_info(s_ini_path, s_info_title) >= 0:
            return 0  #mean:already exist of __aInfoTab , no need new append

        self.__aInfoTab.append([s_ini_path, s_info_title, a_info_attr])
        return 1

    def update_info_attribute(self, s_ini_path, s_info_title, a_info_attr):
        """ update info attribute """
        if a_info_attr is None:
            return 0

        int_index = self.index_info(s_ini_path, s_info_title)
        if int_index == -1:
            return 0

        a_current_info_attr = self.__aInfoTab[int_index][2]
        if a_current_info_attr is None:
            a_current_info_attr = []

        i = 0
        while i < len(a_info_attr):
            int_flag = 0 #0:add , 1:update
            for j in enumerate(a_current_info_attr):
                if j[1][0] == a_info_attr[i][0]:
                    j[1][1] = a_info_attr[i][1]
                    int_flag = 1
                    break
            if int_flag == 1:
                a_info_attr.pop(i)
                i -= 1
            i += 1

        if len(a_info_attr) > 0:
            a_current_info_attr.append(a_info_attr)

        self.__aInfoTab[int_index][2] = a_current_info_attr
        return 1

    def get_info_attribute_value(self, s_int_path, s_info_title, a_info_attr_name):
        """  get info attribute value """
        if a_info_attr_name is None:
            return None

        int_index = self.index_info(s_int_path, s_info_title)
        if int_index == -1:
            return None

        a_current_info_attr = self.__aInfoTab[int_index][2]
        a_info_attr_value = []
        for i in enumerate(a_info_attr_name):
            for j in enumerate(a_current_info_attr):
                if i[1] == j[1][0]:
                    a_info_attr_value.append(j[1][1])
                    break
        return a_info_attr_value


    def remove_info(self, s_ini_path, s_info_title):
        """ remove info """
        int_index = self.index_info(s_ini_path, s_info_title)
        if int_index == -1:
            return 0

        self.__aInfoTab.pop(int_index)
        return 1

    def print_msg(self):
        """ print message """
        print("SystemInfoOperation Msg: ", len(self.__aInfoTab))
        for i in range(len(self.__aInfoTab)):
            print(self.__aInfoTab[i])


def mapi_sysinfo_init():
    """ init """
    global g_SysInfo_Operation
    g_SysInfo_Operation = SystemInfoOperation()
    mapi_sysinfo_update("system.ini")



def mapi_sysinfo_update(s_ini_path):
    """ update """
    #print ("s_ini_path:", s_ini_path)
    if os.path.exists(s_ini_path) is False:
        print("Warning:[mapi_sysinfo_update] path fail: ", s_ini_path)
        return 0

    f_ini = open(s_ini_path, 'r')

    s_int_content = f_ini.read()
    a_split_content = re.split("\[", s_int_content)
    for i in range(1, len(a_split_content)):
        s_info_title = ""
        a_info_attr = []

        a_split_title = re.split("\]", a_split_content[i])
        s_info_title = a_split_title[0]
        a_split_attr = re.split("\<name\>", a_split_title[1])
        for j in range(1, len(a_split_attr)):
            s_attr_name = ""
            s_attr_value = ""
            a_split_attr_name = re.split("\<name\>", a_split_attr[j])
            s_attr_name = re.split("\<\/name\>", a_split_attr_name[0])[0]
            a_split_value = re.split("\<value\>", a_split_attr_name[0])
            s_attr_value = re.split("\<\/value\>", a_split_value[1])[0]

            a_info_attr.append([s_attr_name, s_attr_value])

        g_SysInfo_Operation.remove_info(s_ini_path, s_info_title)
        g_SysInfo_Operation.append_info(s_ini_path, s_info_title, a_info_attr)

    f_ini.close()


#int_action:  0 --> first direct get __aInfoTab ; if __aInfoTab no data,
#                                                 read s_ini_path and append data into __aInfoTab
#            1 --> direct read s_ini_path and update data into __aInfoTab
def mapi_sysinfo_get_atrribute_value(int_action, s_ini_path, s_info_title, a_info_attr_name):
    """ get attribute value """
    if int_action == 0:
        int_index = g_SysInfo_Operation.index_info(s_ini_path, s_info_title)
        if int_index >= 0:
            return g_SysInfo_Operation.get_info_attribute_value(s_ini_path,
                                                                s_info_title,
                                                                a_info_attr_name)

    mapi_sysinfo_update(s_ini_path)
    return g_SysInfo_Operation.get_info_attribute_value(s_ini_path, s_info_title, a_info_attr_name)
