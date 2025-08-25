import json
from guardian import Guardian
from  Infra import util
import configs
import argparse

def read_config(config_file):
    """读取配置文件并返回配置字典"""
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def run_task(app_name, apk_name, testing_objective, max_test_step):
    """根据配置执行任务"""
    # 创建 Guardian 实例
    guardian = Guardian(app_name, apk_name, testing_objective, configs.device_port , max_test_step)
    
    # 生成测试用例
    test_case = guardian.genTestCase()
    
    # 打印生成的测试用例
    # print(test_case)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Guardian')
    parser.add_argument('--port', type=str, default="emulator-5554", help='Device port')
    args = parser.parse_args()

    configs.device_port = args.port
    # 读取配置文件
    config = read_config("task.json")
    # "emulator-5554"
    # 固定 max_test_step
    max_test_step = 15
    
    # 获取 task_names 列表
    task_names = config["task_names"]
    
    # 遍历 task_names 并依次执行任务
    for task_name in task_names:
        app_name = config["app_name"]
        apk_name = config["apk_name"]
        testing_objective = task_name  # 假设 testing_objective 对应 task_name
        util.restart_app(apk_name, apk_name)
        run_task(app_name, apk_name, testing_objective, max_test_step)
