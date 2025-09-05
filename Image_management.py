import shutil
import os
from PIL import Image
from tools_file import *

def get_image_size(file_path):
    """获取图片文件的大小（KB）"""
    try:
        with Image.open(file_path) as img:
            return os.path.getsize(file_path) / 1024
    except:
        return 0

def organize_images_by_size(source_dir, size_threshold=1000, max_files_per_folder=0):
    """
    按照图片大小分类，大小差值在阈值内的放一个文件夹，并可设置每个文件夹最大照片数
    
    参数:
    source_dir: 源目录路径
    size_threshold: 大小阈值(KB)，默认1000KB
    max_files_per_folder: 每个文件夹最大文件数，0表示无限制
    """
    # 获取所有图片文件
    image_files = []
    for file in get_file_list(source_dir):
        file_path = os.path.join(source_dir, file)
        if os.path.isfile(file_path):
            size_kb = get_image_size(file_path)
            if size_kb > 0:
                image_files.append((file, size_kb))
    
    # 按大小排序
    image_files.sort(key=lambda x: x[1])
    
    if not image_files:
        print("未找到图片文件")
        return
    
    current_folder = None
    current_folder_size = None
    folder_count = 0
    current_file_count = 0  # 当前文件夹中的文件计数
    
    for file_name, file_size in image_files:
        file_path_old = os.path.join(source_dir, file_name)
        
        # 检查是否需要创建新文件夹（基于大小或文件数量）
        need_new_folder = False
        
        # 条件1：第一个文件或大小差异超过阈值
        if (current_folder is None or 
            current_folder_size is None or 
            abs(file_size - current_folder_size) > size_threshold):
            need_new_folder = True
        
        # 条件2：如果设置了最大文件数限制，且当前文件夹文件数已达上限
        if (max_files_per_folder > 0 and 
            current_file_count >= max_files_per_folder):
            need_new_folder = True
            print(f"当前文件夹文件数已达上限 {max_files_per_folder}，创建新文件夹")
        
        # 如果需要创建新文件夹
        if need_new_folder:
            folder_count += 1
            current_folder = os.path.join(source_dir, f"size_group_{folder_count}")
            my_mkdir(current_folder)
            current_folder_size = file_size
            current_file_count = 0  # 重置文件计数器
            print(f"创建新文件夹: {current_folder}, 基准大小: {current_folder_size:.2f}KB")
        
        # 移动文件
        shutil.move(file_path_old, os.path.join(current_folder, file_name))
        current_file_count += 1  # 增加文件计数
        print(f'文件 {file_name} (大小: {file_size:.2f}KB) 已移动至 {current_folder}，当前文件夹文件数: {current_file_count}')
    
    print(f"整理完成，共创建 {folder_count} 个文件夹")

# 使用示例
dir = r'D:\zhuomian\ce_shi'
SIZE_THRESHOLD = 100  # 大小差值阈值，单位KB
MAX_FILES_PER_FOLDER = 50  # 每个文件夹最多50张照片

organize_images_by_size(dir, SIZE_THRESHOLD, MAX_FILES_PER_FOLDER)
