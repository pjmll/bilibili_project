import sys
import os


# 解决模块内部导入正常（如在ftp中 from log import Logger），但是外部调用的时候由于工作路径的改变导致的找不到包的问题
sys.path.append(os.path.dirname(__file__))  # sys.path 是一个包含 Python 解释器在导入模块时搜索模块的路径列表，新增仅在运行时有效
