# image_organizer_multilingual.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import argparse
import sys
import os
import shutil
import logging
from datetime import datetime
import hashlib
from concurrent.futures import ThreadPoolExecutor
import threading
from PIL import Image
from io import StringIO
import locale

# 检测系统语言
def get_system_language():
    try:
        # 获取系统默认语言
        system_lang, _ = locale.getdefaultlocale()
        if system_lang:
            if 'zh' in system_lang.lower():  # 中文系统
                return 'zh'
            elif 'en' in system_lang.lower():  # 英文系统
                return 'en'
    except:
        pass
    return 'en'  # 默认英文

# 多语言文本
LANGUAGES = {
    'zh': {
        'title': '智能图片整理工具',
        'source_dir': '源目录:',
        'browse': '浏览...',
        'mode': '整理模式:',
        'modes': ['按大小', '按分辨率', '按日期', '按格式', '查找重复'],
        'size_threshold': '大小阈值(KB):',
        'resolution_threshold': '分辨率差阈值:',
        'max_files': '最大文件数:',
        'move_duplicates': '移动重复文件到文件夹',
        'start': '开始整理',
        'stop': '停止',
        'clear_log': '清空日志',
        'log': '操作日志:',
        'select_dir': '选择目录',
        'error': '错误',
        'select_source_dir': '请选择源目录',
        'invalid_number': '请输入有效的数字',
        'complete': '完成',
        'organization_complete': '图片整理完成！',
        'organization_failed': '图片整理失败！',
        'stopping': '正在停止操作...',
        'menu_language': '语言',
        'menu_help': '帮助',
        'menu_about': '关于',
        'about_title': '关于',
        'about_content': '智能图片整理工具\n版本 1.0.0\n支持多种图片整理模式',
        'help_content': '帮助信息:\n1. 选择源目录\n2. 选择整理模式\n3. 设置参数\n4. 点击开始整理',
        'resolution_tooltip': '分辨率差在设定值范围内的图片会被分到同一文件夹\n0表示精确匹配，10表示宽高差在10像素内的归为一组'
    },
    'en': {
        'title': 'Smart Image Organizer',
        'source_dir': 'Source Directory:',
        'browse': 'Browse...',
        'mode': 'Organization Mode:',
        'modes': ['By Size', 'By Resolution', 'By Date', 'By Format', 'Find Duplicates'],
        'size_threshold': 'Size Threshold(KB):',
        'resolution_threshold': 'Resolution Threshold:',
        'max_files': 'Max Files per Folder:',
        'move_duplicates': 'Move duplicate files to folder',
        'start': 'Start Organization',
        'stop': 'Stop',
        'clear_log': 'Clear Log',
        'log': 'Operation Log:',
        'select_dir': 'Select Directory',
        'error': 'Error',
        'select_source_dir': 'Please select source directory',
        'invalid_number': 'Please enter a valid number',
        'complete': 'Complete',
        'organization_complete': 'Image organization completed!',
        'organization_failed': 'Image organization failed!',
        'stopping': 'Stopping operation...',
        'menu_language': 'Language',
        'menu_help': 'Help',
        'menu_about': 'About',
        'about_title': 'About',
        'about_content': 'Smart Image Organizer\nVersion 1.0.0\nSupports multiple image organization modes',
        'help_content': 'Help Information:\n1. Select source directory\n2. Choose organization mode\n3. Set parameters\n4. Click Start Organization',
        'resolution_tooltip': 'Images with resolution difference within the threshold will be grouped together\n0 means exact match, 10 means within 10 pixels difference'
    }
}

# 获取当前语言文本
def get_text(key):
    return LANGUAGES[CURRENT_LANGUAGE].get(key, key)

# 全局变量
CURRENT_LANGUAGE = get_system_language()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_organizer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ImageOrganizer:
    def __init__(self):
        self.lock = threading.Lock()
        self.stop_requested = False
        
    def get_image_size(self, file_path):
        """获取图片文件的大小（KB）"""
        try:
            return os.path.getsize(file_path) / 1024
        except Exception as e:
            logger.error(f"获取文件大小失败 {file_path}: {e}")
            return 0

    def get_image_dimensions(self, file_path):
        """获取图片分辨率"""
        try:
            with Image.open(file_path) as img:
                return img.size  # (width, height)
        except Exception as e:
            logger.error(f"获取图片分辨率失败 {file_path}: {e}")
            return (0, 0)

    def get_image_hash(self, file_path):
        """计算图片的哈希值用于去重"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"计算图片哈希值失败 {file_path}: {e}")
            return None

    def get_creation_date(self, file_path):
        """获取文件创建日期"""
        try:
            timestamp = os.path.getctime(file_path)
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"获取创建日期失败 {file_path}: {e}")
            return "unknown_date"

    def safe_move(self, src, dst):
        """安全的文件移动操作"""
        if self.stop_requested:
            return False
            
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            # 如果目标文件已存在，重命名
            if os.path.exists(dst):
                base, ext = os.path.splitext(dst)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                dst = f"{base}_{counter}{ext}"
            
            shutil.move(src, dst)
            logger.info(f"成功移动: {src} -> {dst}")
            return True
            
        except PermissionError as e:
            logger.error(f"权限错误: 无法移动 {src} -> {dst}: {e}")
        except Exception as e:
            logger.error(f"移动文件失败 {src} -> {dst}: {e}")
        return False

    def organize_images(self, source_dir, mode='size', **kwargs):
        """
        整理图片的主函数
        """
        if not os.path.exists(source_dir):
            logger.error(f"源目录不存在: {source_dir}")
            return False

        self.stop_requested = False
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        image_files = []
        
        logger.info(f"开始扫描目录: {source_dir}")
        
        # 收集所有图片文件
        for root, _, files in os.walk(source_dir):
            for file in files:
                if self.stop_requested:
                    return False
                if os.path.splitext(file.lower())[1] in image_extensions:
                    file_path = os.path.join(root, file)
                    image_files.append(file_path)
        
        logger.info(f"找到 {len(image_files)} 张图片")
        
        if not image_files:
            logger.warning("未找到图片文件")
            return True

        # 根据模式选择整理方法
        mode_mapping = {
            'size': self._organize_by_size,
            'resolution': self._organize_by_resolution,
            'date': self._organize_by_date,
            'format': self._organize_by_format,
            'duplicate': self._find_duplicates
        }
        
        if mode in mode_mapping:
            return mode_mapping[mode](image_files, source_dir, **kwargs)
        else:
            logger.error(f"不支持的整理模式: {mode}")
            return False

    def _organize_by_size(self, image_files, source_dir, size_threshold=1000, max_files_per_folder=0):
        """按大小整理"""
        logger.info("开始按大小整理图片...")
        
        files_with_size = []
        for file_path in image_files:
            if self.stop_requested:
                return False
            size_kb = self.get_image_size(file_path)
            if size_kb > 0:
                files_with_size.append((file_path, size_kb))
        
        files_with_size.sort(key=lambda x: x[1])
        
        if not files_with_size:
            return True

        current_folder = None
        current_folder_size = None
        folder_count = 0
        current_file_count = 0
        
        for file_path, file_size in files_with_size:
            if self.stop_requested:
                return False
                
            need_new_folder = False
            
            if (current_folder is None or 
                current_folder_size is None or 
                abs(file_size - current_folder_size) > size_threshold):
                need_new_folder = True
            
            if (max_files_per_folder > 0 and 
                current_file_count >= max_files_per_folder):
                need_new_folder = True
                logger.info(f"当前文件夹文件数已达上限 {max_files_per_folder}，创建新文件夹")
            
            if need_new_folder:
                folder_count += 1
                current_folder = os.path.join(source_dir, f"size_group_{folder_count}")
                os.makedirs(current_folder, exist_ok=True)
                current_folder_size = file_size
                current_file_count = 0
                logger.info(f"创建新文件夹: {current_folder}, 基准大小: {current_folder_size:.2f}KB")
            
            filename = os.path.basename(file_path)
            target_path = os.path.join(current_folder, filename)
            if self.safe_move(file_path, target_path):
                current_file_count += 1
        
        logger.info("按大小整理完成")
        return True

    def _organize_by_resolution(self, image_files, source_dir, resolution_threshold=0, max_files_per_folder=0):
        """按分辨率整理"""
        logger.info("开始按分辨率整理图片...")
        
        # 获取所有图片的分辨率
        resolutions = []
        for file_path in image_files:
            if self.stop_requested:
                return False
            dimensions = self.get_image_dimensions(file_path)
            if dimensions != (0, 0):
                resolutions.append((file_path, dimensions))
        
        if not resolutions:
            return True
        
        # 分组分辨率
        groups = []
        for file_path, (width, height) in resolutions:
            if self.stop_requested:
                return False
                
            found_group = False
            for group in groups:
                # 检查是否在某个组的容差范围内
                group_width, group_height = group['resolution']
                if (abs(width - group_width) <= resolution_threshold and 
                    abs(height - group_height) <= resolution_threshold):
                    group['files'].append(file_path)
                    found_group = True
                    break
            
            if not found_group:
                # 创建新组
                groups.append({
                    'resolution': (width, height),
                    'files': [file_path]
                })
        
        logger.info(f"按分辨率分组完成，共 {len(groups)} 个分组")
        
        # 移动文件
        for i, group in enumerate(groups):
            if self.stop_requested:
                return False
                
            width, height = group['resolution']
            folder_name = f"resolution_{width}x{height}"
            if resolution_threshold > 0:
                folder_name += f"_±{resolution_threshold}"
                
            target_dir = os.path.join(source_dir, folder_name)
            
            for j, file_path in enumerate(group['files']):
                if self.stop_requested:
                    return False
                    
                # 如果设置了最大文件数限制，创建子文件夹
                if max_files_per_folder > 0 and j % max_files_per_folder == 0:
                    sub_folder = os.path.join(target_dir, f"group_{j//max_files_per_folder + 1}")
                    os.makedirs(sub_folder, exist_ok=True)
                else:
                    sub_folder = target_dir
                
                filename = os.path.basename(file_path)
                target_path = os.path.join(sub_folder, filename)
                self.safe_move(file_path, target_path)
        
        logger.info("按分辨率整理完成")
        return True

    def _organize_by_date(self, image_files, source_dir, max_files_per_folder=0):
        """按创建日期整理"""
        logger.info("开始按创建日期整理图片...")
        
        date_groups = {}
        
        for file_path in image_files:
            if self.stop_requested:
                return False
            date_str = self.get_creation_date(file_path)
            if date_str not in date_groups:
                date_groups[date_str] = []
            date_groups[date_str].append(file_path)
        
        for date_str, files in date_groups.items():
            if self.stop_requested:
                return False
            target_dir = os.path.join(source_dir, f"date_{date_str}")
            
            for i, file_path in enumerate(files):
                if self.stop_requested:
                    return False
                filename = os.path.basename(file_path)
                target_path = os.path.join(target_dir, filename)
                self.safe_move(file_path, target_path)
        
        logger.info("按创建日期整理完成")
        return True

    def _organize_by_format(self, image_files, source_dir, max_files_per_folder=0):
        """按图片格式整理"""
        logger.info("开始按图片格式整理...")
        
        format_groups = {}
        
        for file_path in image_files:
            if self.stop_requested:
                return False
            _, ext = os.path.splitext(file_path)
            format_key = ext.lower().lstrip('.')
            if format_key not in format_groups:
                format_groups[format_key] = []
            format_groups[format_key].append(file_path)
        
        for format_key, files in format_groups.items():
            if self.stop_requested:
                return False
            target_dir = os.path.join(source_dir, f"format_{format_key}")
            
            for i, file_path in enumerate(files):
                if self.stop_requested:
                    return False
                filename = os.path.basename(file_path)
                target_path = os.path.join(target_dir, filename)
                self.safe_move(file_path, target_path)
        
        logger.info("按图片格式整理完成")
        return True

    def _find_duplicates(self, image_files, source_dir, move_to_folder=True):
        """查找并处理重复图片"""
        logger.info("开始查找重复图片...")
        
        hash_dict = {}
        duplicates = []
        
        # 多线程计算哈希值
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(
                lambda fp: (fp, self.get_image_hash(fp)), 
                image_files
            ))
        
        for file_path, file_hash in results:
            if self.stop_requested:
                return False
            if file_hash:
                if file_hash in hash_dict:
                    duplicates.append(file_path)
                    hash_dict[file_hash].append(file_path)
                else:
                    hash_dict[file_hash] = [file_path]
        
        logger.info(f"找到 {len(duplicates)} 张重复图片")
        
        if duplicates and move_to_folder:
            duplicates_dir = os.path.join(source_dir, "duplicates")
            for dup_file in duplicates:
                if self.stop_requested:
                    return False
                filename = os.path.basename(dup_file)
                target_path = os.path.join(duplicates_dir, filename)
                self.safe_move(dup_file, target_path)
            logger.info(f"重复图片已移动到: {duplicates_dir}")
        
        return True
    
    def stop(self):
        """停止当前操作"""
        self.stop_requested = True
        logger.info("停止操作请求已发送")

class ImageOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.update_ui_texts()
        
        self.organizer = ImageOrganizer()
        self.setup_gui()
        self.setup_menu()
        
        # 重定向日志到GUI
        self.log_capture = StringIO()
        self.setup_logging()
        
    def update_ui_texts(self):
        """更新UI文本"""
        self.root.title(get_text('title'))
        
    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 语言菜单
        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=get_text('menu_language'), menu=language_menu)
        language_menu.add_command(label="中文", command=lambda: self.change_language('zh'))
        language_menu.add_command(label="English", command=lambda: self.change_language('en'))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=get_text('menu_help'), menu=help_menu)
        help_menu.add_command(label=get_text('menu_about'), command=self.show_about)
        help_menu.add_command(label=get_text('help_content').split('\n')[0], command=self.show_help)
        
    def change_language(self, lang):
        """切换语言"""
        global CURRENT_LANGUAGE
        CURRENT_LANGUAGE = lang
        self.update_all_texts()
        
    def update_all_texts(self):
        """更新所有界面文本"""
        self.root.title(get_text('title'))
        
        # 更新标签
        self.source_dir_label.config(text=get_text('source_dir'))
        self.mode_label.config(text=get_text('mode'))
        self.log_label.config(text=get_text('log'))
        
        # 更新按钮
        self.browse_button.config(text=get_text('browse'))
        self.start_button.config(text=get_text('start'))
        self.stop_button.config(text=get_text('stop'))
        self.clear_button.config(text=get_text('clear_log'))
        
        # 更新模式选择框
        current_mode = self.mode_var.get()
        mode_display_values = get_text('modes')
        mode_values = ['size', 'resolution', 'date', 'format', 'duplicate']
        
        self.mode_combo['values'] = mode_display_values
        
        # 保持当前选择
        if current_mode in mode_values:
            index = mode_values.index(current_mode)
            self.mode_combo.set(mode_display_values[index])
        
        # 更新参数框架
        self.setup_parameters()
        
        # 更新菜单
        self.update_menu_texts()
        
    def update_menu_texts(self):
        """更新菜单文本"""
        # 这里需要重新创建菜单来更新文本
        self.setup_menu()
        
    def setup_logging(self):
        """设置日志重定向"""
        class GuiLogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
        
        handler = GuiLogHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)
        
    def setup_gui(self):
        """设置GUI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 源目录选择
        self.source_dir_label = ttk.Label(main_frame, text=get_text('source_dir'))
        self.source_dir_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.source_dir_var = tk.StringVar()
        self.source_dir_entry = ttk.Entry(main_frame, textvariable=self.source_dir_var, width=50)
        self.source_dir_entry.grid(row=0, column=1, padx=5)
        
        self.browse_button = ttk.Button(main_frame, text=get_text('browse'), command=self.browse_source)
        self.browse_button.grid(row=0, column=2)
        
        # 整理模式
        self.mode_label = ttk.Label(main_frame, text=get_text('mode'))
        self.mode_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.mode_var = tk.StringVar(value='size')
        mode_display_values = get_text('modes')
        self.mode_combo = ttk.Combobox(main_frame, textvariable=self.mode_var, 
                                      values=mode_display_values)
        self.mode_combo.grid(row=1, column=1, sticky=tk.W, padx=5)
        self.mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
        # 参数设置
        self.param_frame = ttk.Frame(main_frame)
        self.param_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.setup_parameters()
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(button_frame, text=get_text('start'), command=self.start_organization)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text=get_text('stop'), command=self.stop_organization)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text=get_text('clear_log'), command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # 日志显示
        self.log_label = ttk.Label(main_frame, text=get_text('log'))
        self.log_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=80)
        self.log_text.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_text.config(state=tk.DISABLED)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
    def setup_parameters(self):
        """根据模式设置参数控件"""
        for widget in self.param_frame.winfo_children():
            widget.destroy()
            
        mode = self.mode_var.get()
        mode_display = self.mode_combo.get()
        
        # 映射显示文本到内部值
        mode_mapping = dict(zip(get_text('modes'), ['size', 'resolution', 'date', 'format', 'duplicate']))
        internal_mode = mode_mapping.get(mode_display, 'size')
        
        row = 0
        if internal_mode == 'size':
            ttk.Label(self.param_frame, text=get_text('size_threshold')).grid(row=row, column=0, sticky=tk.W)
            self.size_threshold = tk.StringVar(value="1000")
            ttk.Entry(self.param_frame, textvariable=self.size_threshold, width=10).grid(row=row, column=1, padx=5)
            
            ttk.Label(self.param_frame, text=get_text('max_files')).grid(row=row, column=2, sticky=tk.W, padx=10)
            self.max_files = tk.StringVar(value="0")
            ttk.Entry(self.param_frame, textvariable=self.max_files, width=10).grid(row=row, column=3)
            
        elif internal_mode == 'resolution':
            # 分辨率差阈值
            ttk.Label(self.param_frame, text=get_text('resolution_threshold')).grid(row=row, column=0, sticky=tk.W)
            self.resolution_threshold = tk.StringVar(value="0")
            resolution_entry = ttk.Entry(self.param_frame, textvariable=self.resolution_threshold, width=10)
            resolution_entry.grid(row=row, column=1, padx=5)
            
            # 添加提示信息
            from tkinter import Label
            tooltip_label = Label(self.param_frame, text=get_text('resolution_tooltip'), 
                                 fg="gray", font=("Arial", 8), wraplength=400, justify=tk.LEFT)
            tooltip_label.grid(row=row+1, column=0, columnspan=4, sticky=tk.W, pady=(2, 5))
            
            # 最大文件数
            ttk.Label(self.param_frame, text=get_text('max_files')).grid(row=row, column=2, sticky=tk.W, padx=10)
            self.max_files = tk.StringVar(value="0")
            ttk.Entry(self.param_frame, textvariable=self.max_files, width=10).grid(row=row, column=3)
            
        elif internal_mode == 'duplicate':
            self.move_duplicates = tk.BooleanVar(value=True)
            ttk.Checkbutton(self.param_frame, text=get_text('move_duplicates'), 
                           variable=self.move_duplicates).grid(row=row, column=0, sticky=tk.W)
        else:
            ttk.Label(self.param_frame, text=get_text('max_files')).grid(row=row, column=0, sticky=tk.W)
            self.max_files = tk.StringVar(value="0")
            ttk.Entry(self.param_frame, textvariable=self.max_files, width=10).grid(row=row, column=1, padx=5)
    
    def on_mode_change(self, event):
        """模式改变时的回调"""
        self.setup_parameters()
    
    def browse_source(self):
        """浏览源目录"""
        directory = filedialog.askdirectory(title=get_text('select_dir'))
        if directory:
            self.source_dir_var.set(directory)
    
    def start_organization(self):
        """开始整理"""
        if not self.source_dir_var.get():
            messagebox.showerror(get_text('error'), get_text('select_source_dir'))
            return
            
        # 获取参数
        mode_mapping = dict(zip(get_text('modes'), ['size', 'resolution', 'date', 'format', 'duplicate']))
        selected_mode = mode_mapping.get(self.mode_combo.get(), 'size')
        
        params = {
            'source_dir': self.source_dir_var.get(),
            'mode': selected_mode
        }
        
        if selected_mode == 'size':
            try:
                params['size_threshold'] = float(self.size_threshold.get())
                params['max_files_per_folder'] = int(self.max_files.get())
            except ValueError:
                messagebox.showerror(get_text('error'), get_text('invalid_number'))
                return
        elif selected_mode == 'resolution':
            try:
                params['resolution_threshold'] = int(self.resolution_threshold.get())
                params['max_files_per_folder'] = int(self.max_files.get())
            except ValueError:
                messagebox.showerror(get_text('error'), get_text('invalid_number'))
                return
        elif selected_mode == 'duplicate':
            params['move_to_folder'] = self.move_duplicates.get()
        else:
            try:
                params['max_files_per_folder'] = int(self.max_files.get())
            except ValueError:
                messagebox.showerror(get_text('error'), get_text('invalid_number'))
                return
        
        # 在新线程中运行整理操作
        self.progress.start()
        self.start_button.config(state=tk.DISABLED)
        self.thread = threading.Thread(target=self.run_organization, args=(params,))
        self.thread.daemon = True
        self.thread.start()
    
    def run_organization(self, params):
        """运行整理操作"""
        try:
            success = self.organizer.organize_images(**params)
            if success:
                self.show_message(get_text('complete'), get_text('organization_complete'))
            else:
                self.show_message(get_text('error'), get_text('organization_failed'))
        except Exception as e:
            self.show_message(get_text('error'), f"{get_text('organization_failed')}: {e}")
        finally:
            self.progress.stop()
            self.start_button.config(state=tk.NORMAL)
    
    def stop_organization(self):
        """停止整理"""
        self.organizer.stop()
        messagebox.showinfo(get_text('info'), get_text('stopping'))
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def show_message(self, title, message):
        """显示消息"""
        self.root.after(0, lambda: messagebox.showinfo(title, message))
    
    def show_about(self):
        """显示关于信息"""
        messagebox.showinfo(get_text('about_title'), get_text('about_content'))
    
    def show_help(self):
        """显示帮助信息"""
        messagebox.showinfo(get_text('menu_help'), get_text('help_content'))

def main():
    root = tk.Tk()
    app = ImageOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()