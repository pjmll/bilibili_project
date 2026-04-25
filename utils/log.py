import logging
import os
from logging import handlers, getLevelName
from logging import LogRecord as _LogRecord
import time
import sys
from multiprocessing import Lock as _Lock
from typing import Callable
import traceback

from colorama import Fore, Style, init

"""Python日志模块封装，支持多进程、多线程，支持输出到控制台和文件，支持debug模式，支持多种日志级别
Author: zyb
Date: unknown

By: Yun Xiaoxi (@ycte)
Date: 2024-08-17
Description: 为不同级别增加样式
"""


# 初始化 colorama
init(autoreset=True)


# 自定义日志格式
class CustomFormatter(logging.Formatter):
    # 定义日志颜色
    LOG_COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Style.BRIGHT + Fore.RED,
        logging.CRITICAL: Style.BRIGHT + Fore.RED,
    }

    UNDERLINE = "\033[4m"

    def format(self, record):
        log_color = self.LOG_COLORS.get(record.levelno)
        log_msg = super().format(record)
        log_msg = log_msg.replace(
            f"{record.asctime}",
            f"{Fore.LIGHTGREEN_EX}{record.asctime}{Style.RESET_ALL}",
        )
        log_msg = log_msg.replace(
            f"line {record.lineno}", f"line {Fore.BLUE}{record.lineno}{Style.RESET_ALL}"
        )
        log_msg = log_msg.replace(
            f"{record.module}.{record.funcName}",
            f"{record.module}.{record.funcName}{Style.RESET_ALL}",
        )
        log_msg = log_msg.replace(
            f"{record.levelname}",
            f"{self.UNDERLINE if record.levelno in [logging.ERROR, logging.CRITICAL] else ''}{log_color}{record.levelname}{Style.RESET_ALL}",
        )
        return log_msg


def simple_log_with_time(message: str, output=True):
    """简单的日志输出函数，不同于Logger类，这里只是print到控制台并附加了时间戳，但提供了一个是否输出的控制选项

    :param message: 输出消息
    :param output: 是否输出
    """
    if output:
        timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S ", time.localtime(time.time())
        )  # 旧版python不能直接在此包含中文，改拼接
        print(timestamp + message)


class Logger:
    def __init__(
        self,
        output_to_console=True,
        output_to_file=False,
        log_dir=os.path.join(os.path.dirname(__file__), "log"),
        log_file_prefix="",
        multi_process=False,
        multi_thread=False,
    ):
        """日志类，与logging相同共有五个日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL。
        所有日志消息都自带时间戳及消息类型，对于DEBUG及以上的级别都会额外附加模块名、函数名、行号。
        若参数指定多进程或多线程还会附带进程/线程号和进程/线程名，因此在并发情况下使用的话，建议为进程/线程指定名字。
        可选是否输出到控制台，DEBUG消息一定输出到控制台，其他级别的可选。
        可选是否输出到文件，若输出到文件则除了DEBUG以外所有级别都会被记录。
        可以调用实例方法选择是否开启debug模式，请注意默认未开启debug模式，所有debug消息语句会被忽略。

        补充：经过测试本类的实例无法直接传递给子进程使用，如果传给子进程子进程将无法输出内容，要在子进程使用需在子进程内部创建实例。

        :param output_to_console: 是否输出到控制台，默认True，对于DEBUG消息一定会输出到控制台
        :param output_to_file: 是否输出到文件中保存，默认False，为True的情况下后面参数log_dir与log_file_prefix才有意义
        :param log_file_prefix: 日志文件名前缀，若未给定默认以日期"xxxx-xx-xx.log"命名，给定的话则是命名为"前缀_xxxx-xx-xx.log"，该日期代表文件创建日期
        :param log_dir: 日志文件夹，默认为当前位置下创建log文件夹；若给定路径不存在将逐级自动创建
        :param multi_process: 是否多进程下使用，若是的话日志消息会附带进程号和进程名，且会保证进程安全。注意，如果多进程使用需要把本类的实例作为参数传给子进程
        :param multi_thread: 是否多线程下使用，若是的话日志消息会附带线程号和线程名，且会保证线程安全
        :return:
        """
        self.__multi_process = multi_process
        # 是否开启debug模式，开启的话debug语句会输出，关闭的话所有debug语句都会被忽略，免去添加和删除debug消息相关代码的麻烦
        self.__debug_mode = False

        if output_to_file:
            if os.path.exists(log_dir):
                if not os.path.isdir(log_dir):
                    logging.error("Filepath must be a directory!", stack_info=True)
                    sys.exit(-1)
            else:
                os.makedirs(log_dir)
        # 设定不同种类消息的输出格式
        info_fmt = "%(asctime)s %(levelname)s"
        debug_fmt = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d"
        key_fmt = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d"

        multi_info = ""  # 多线程和多进程情况下需要附加的线程/进程号 线程/进程名
        if multi_process:  # 多进程处理：加锁、格式化
            self.__lock = (
                _Lock()
            )  # 进程锁；logger已经自带线程安全，这里是为了保证进程安全
            multi_info += ", process<%(process)d %(processName)s>"
        if multi_thread:  # 多线程处理: 格式化。有可能既是多进程又是多线程
            multi_info += ", thread<%(thread)d %(threadName)s>"

        info_fmt = info_fmt + multi_info.lstrip(",") + " - %(message)s"
        debug_fmt = debug_fmt + multi_info + " - %(message)s"
        key_fmt = key_fmt + multi_info + " - %(message)s"

        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.DEBUG)

        """设定过滤器、格式器"""
        info_filter = self.__InfoFilter()
        info_formatter = CustomFormatter(info_fmt, datefmt="%Y-%m-%d %H:%M:%S")

        debug_filter = self.__DebugFilter()
        debug_formatter = CustomFormatter(debug_fmt, datefmt="%Y-%m-%d %H:%M:%S")

        key_formatter = CustomFormatter(key_fmt, datefmt="%Y-%m-%d %H:%M:%S")

        # handler = logging.StreamHandler()
        # formatter = CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # handler.setFormatter(formatter)
        # self.__logger.addHandler(handler)

        """控制台输出"""
        if output_to_console:
            # 处理消息日志输出：INFO
            info_stream_handler = logging.StreamHandler(stream=sys.stdout)
            info_stream_handler.setLevel(logging.INFO)
            info_stream_handler.addFilter(info_filter)
            info_stream_handler.setFormatter(info_formatter)
            self.__logger.addHandler(info_stream_handler)

            # 关键消息输出，比如各种错误和警告：WARNING、ERROR、CRITICAL
            key_stream_handler = logging.StreamHandler(stream=sys.stderr)
            key_stream_handler.setLevel(logging.WARNING)
            key_stream_handler.setFormatter(key_formatter)
            self.__logger.addHandler(key_stream_handler)

        # 处理DEBUG级别的消息
        debug_stream_handler = logging.StreamHandler(stream=sys.stdout)
        debug_stream_handler.setLevel(logging.DEBUG)
        debug_stream_handler.addFilter(debug_filter)
        debug_stream_handler.setFormatter(debug_formatter)
        self.__logger.addHandler(debug_stream_handler)

        """文件输出，处理DEBUG级别以外的所有级别的消息，生成轮换日志，文件名的日期是创建日期"""
        if output_to_file:
            # 日志文件名
            log_file = os.path.join(
                log_dir,
                f"{log_file_prefix}_{time.strftime('%Y-%m-%d', time.localtime())}.log".lstrip(
                    "_"
                ),
            )

            # 处理消息日志输出：INFO
            info_file_handler = handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
            )
            info_file_handler.setLevel(logging.INFO)
            info_file_handler.addFilter(info_filter)
            info_file_handler.setFormatter(info_formatter)

            # 关键消息输出，比如各种错误和警告：WARNING、ERROR、CRITICAL
            key_file_handler = handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=10, encoding="utf-8"
            )
            key_file_handler.setLevel(logging.WARNING)
            key_file_handler.setFormatter(key_formatter)

            self.__logger.addHandler(info_file_handler)
            self.__logger.addHandler(key_file_handler)

    def __log(self, f: Callable, kwargs: dict):
        if sys.version_info < (3, 8):  # python3.7及以下版本不支持指定栈层级
            kwargs.pop("stacklevel", None)
        if self.__multi_process and self.__lock.acquire():
            f(**kwargs)
            self.__lock.release()
        else:
            f(**kwargs)

    def debug(self, message):
        if self.__debug_mode:  # 仅在debug模式下才输出debug消息
            self.__log(self.__logger.debug, {"msg": message, "stacklevel": 3})

    def info(self, message):
        self.__log(self.__logger.info, {"msg": message})

    def warning(self, message):
        self.__log(self.__logger.warning, {"msg": message, "stacklevel": 3})

    def error(self, message, print_exc=False):
        self.__log(
            self.__logger.error, {"msg": message, "stacklevel": 3}
        )  # 'stack_info': True,
        if print_exc:
            traceback.print_exc()

    def critical(self, message, print_exc=False):
        self.__log(
            self.__logger.critical, {"msg": message, "stacklevel": 3}
        )  # 'stack_info': True,
        if print_exc:
            traceback.print_exc()

    def set_debug_mode(self):  # 开启debug模式，会输出debug消息
        self.__debug_mode = True

    def close_debug_mode(self):  # 关闭debug模式，所有debug消息都会被忽略
        self.__debug_mode = False

    class __InfoFilter(logging.Filter):  # 设置过滤器，只处理INFO级别的消息
        def filter(self, record: _LogRecord) -> bool:
            return record.levelno == logging.INFO

    class __DebugFilter(logging.Filter):  # 设置过滤器，只处理DEBUG级别的消息
        def filter(self, record: _LogRecord) -> bool:
            return record.levelno == logging.DEBUG
