import os
import re

##################################################################################################

def get_file_list(dir):
    # 功能：列出文件夹下所有文件；
    # 输入：文件夹路径；
    # 输出：文件列表；
    # 创建日期：2025-09-5

    # 使用列表生成式，快速统计文件个数
    # os.path.isfile()，筛选，只保留文件，不保留文件夹
    list_of_files = [name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))]
    return list_of_files

##################################################################################################

def get_file_count(dir):
    # 功能：计算文件夹下文件个数；
    # 输入：文件夹路径；
    # 输出：文件个数；
    # 引用函数：get_file_list()
    # 创建日期：2018-09-21

    file_list = get_file_list(dir)
    file_count = len(file_list)
    # print('文件夹', dir, '中文件个数：', file_count)
    return file_count

##################################################################################################

def my_mkdir(folder_path):
    # 功能：创建文件夹，若存在则不重复创建；
    # 输入：文件夹路径；
    # 输出：无；
    # 创建日期：2018-09-21

    if os.path.exists(folder_path):
        print('文件夹', folder_path, '已存在！')
    else:
        os.mkdir(folder_path)
        print('文件夹', folder_path, '创建成功！')

##################################################################################################



