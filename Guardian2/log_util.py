import logging

# 配置全局 logger
def setup_logger(name='app', log_file='app.log', level=logging.INFO, only_file=False):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handlers
    if not logger.handlers:
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # 添加文件处理器到 logger
        logger.addHandler(file_handler)

        # 如果不是仅文件日志，则添加控制台处理器
        if not only_file:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

    return logger

# 初始化全局日志器
logger = setup_logger(name='regular', log_file='app.log', level=logging.INFO)
important_logger = setup_logger(name='important', log_file='important.log', level=logging.WARNING, only_file=True)


import logging
import os


def setup_logger(log_file='app.log', level=logging.INFO, only_file=False):
    """
    根据传入的文件路径创建 logger
    :param log_file: 日志文件路径
    :param level: 日志级别
    :param only_file: 如果为 True，只记录到文件，不输出到控制台
    :return: 配置好的 logger 对象
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception as e:
            print(f"Error creating log directory: {e}")
            raise

    logger = logging.getLogger(log_file)  # 使用文件路径作为日志名称
    logger.setLevel(level)

    # 避免重复添加 handlers
    if not logger.handlers:
        # 创建文件处理器
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)

            # 设置日志格式
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)

            # 添加文件处理器到 logger
            logger.addHandler(file_handler)

            # 如果不是仅文件日志，则添加控制台处理器
            if not only_file:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
        except Exception as e:
            print(f"Error setting up logging: {e}")
            raise

    return logger


# 接受日志路径并记录日志的函数
def log_message(log_file, message, level=logging.INFO):
    """
    根据给定的日志文件路径，记录日志信息。
    :param log_file: 日志文件路径
    :param message: 要记录的日志信息
    :param level: 日志级别，默认为 INFO
    """
    logger = setup_logger(log_file=log_file, level=level)
    
    # 根据日志级别记录信息
    if level == logging.DEBUG:
        logger.debug(message)
    elif level == logging.INFO:
        logger.info(message)
    elif level == logging.WARNING:
        logger.warning(message)
    elif level == logging.ERROR:
        logger.error(message)
    elif level == logging.CRITICAL:
        logger.critical(message)


# 示例调用
log_message("logs/log1.log", "This is a debug message", logging.DEBUG)
log_message("logs/log2.log", "This is an info message", logging.INFO)
log_message("logs/log3.log", "This is a warning message", logging.WARNING)
