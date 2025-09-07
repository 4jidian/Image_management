# ImageOrganization
为满足个人日常图片管理需求而诞生的实用小工具库，非常简单，图片分类目前只能按照大小和数量分类，更多功能正在开发
## 一、基本用法
### 1、前提
已安装python，可直接在cmd下使用
### 2、执行方法
简单修改代码设置参数后，直接在cmd下执行.py文件即可，如`python Image_management.py`，可根据需要选择要执行的文件
## 二、工程简介
### 1、image_organizer_multilingual.py
#### 需求背景
图片文件过多，需要简单整理
#### 参数设置：
##### ①指定要整理的文件夹路径
<s>修改文件`Image_management.py`中的`dir = r'E:\Paper'`</s>
请查看更新
##### ②设置文件夹容量
修改文件`Image_management.py`中的`max_files_per_folder=0`，该参数指定每个文件夹下文件个数上限，0表示无限制

### 示例1：仅按大小分类（无数量限制）

python

```
organize_images_by_size(dir, size_threshold=100, max_files_per_folder=0)
```



### 示例2：按大小分类，每个文件夹最多20张

python

```
organize_images_by_size(dir, size_threshold=100, max_files_per_folder=20)
```



### 示例3：仅按数量分类（忽略大小差异）

python

```
organize_images_by_size(dir, size_threshold=1000000, max_files_per_folder=30)
# 设置很大的阈值，让大小差异条件基本不会触发
```



#### 整理前：
<img width="1463" height="402" alt="屏幕截图 2025-09-05 151416" src="https://github.com/user-attachments/assets/86e4f7f6-cf64-4879-be0a-e596dcb9bc1f" />


#### 整理后：
<img width="914" height="138" alt="屏幕截图 2025-09-05 151530" src="https://github.com/user-attachments/assets/d271e659-88f5-45c2-b70c-6b42f1e51d47" />


#### 更新：2025.9.27
重大更新：新增了GUI界面，现在只需要在选择模式和地址即可
<img width="594" height="570" alt="屏幕截图 2025-09-07 232646" src="https://github.com/user-attachments/assets/606cdc44-b70d-4399-b1da-b18656be1b5f" />

