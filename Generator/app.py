from flask import Flask, request
from layout_analyzer import LayoutMenuAnalyzer
import config
import task_planner
import llm
from utils  import general_utils
import json


app = Flask(__name__)
app_package_map = {}
app_configs = general_utils.read_json('./app_config.json')

def load_app_config(app_package):
    print('*'*30)
    for app_config in app_configs:
        if app_config.get("target_package") == app_package:
            print('-------update config-----------')
            # update config
            config.target_project = '.' + app_config.get("target_project")
            config.target_project_source_code = config.target_project + app_config.get("source_code")
            config.target_package = app_config.get("target_package")
            config.target_project_AndroidManifest = config.target_project + 'AndroidManifest.xml'
            config.save_path = "./program_analysis_results/" + config.target_package.replace('.','_') + '/'
    layout_analyzer = LayoutMenuAnalyzer(config.target_project + "res/layout/", config.target_project + "res/menu/", config.target_project + "res/values/", config.target_project + "res/xml/")
    layout_analyzer.init()
    print('layout_analyzer.layout_files:', layout_analyzer.layout_files)
    print('layout_analyzer.layout_dir:', layout_analyzer.layout_dir)
    atg_analyzer = general_utils.get_atg_analyzer_from_Manifest()
    activity_fragment_mapping = general_utils.get_activity_fragment_mapping(config.save_path)
    app_package_map[app_package] = {
        "layout_analyzer": layout_analyzer,
        "atg_analyzer": atg_analyzer,
        "activity_fragment_mapping": activity_fragment_mapping
    }

# 从文件中加载JSON数据
def load_elements_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            elements = json.load(f)
        return elements
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {file_path}: {e}")
        return []

# 查找元素id对应的action描述
def find_action_by_element_id(elements, element_id):
    # 遍历所有元素，查找匹配的element_id
    element_id = element_id.replace('R.id', '')
    if ':id/' in element_id:
        element_id = element_id.rsplit('/', 1)[1]
    for element in elements:
        if element.get('element_id').replace('R.id.', '') == element_id.replace('R.id.', ''):
            return element.get('action', 'Action not found')  # 返回 action 描述
    return ''

# @app.route('/')
# def index():
#     # 默认的 prompt
#     return task_planner.constrct_code_info_prompt(atg_analyzer, layout_analyzer, activity_fragment_mapping)
    # return "Welcome to Task Planner. Use /prompt1 or /prompt2 to get different prompts."

@app.route('/get_instructions', methods=['POST'])  # 添加 methods=['POST']
def prompt1():
    # 获取 JSON 数据
    data = request.get_json()

    # 从 JSON 数据中获取 target_task
    target_task = data.get('target_task')

    # 如果没有提供 target_task，则返回错误
    if not target_task:
        return "Error: target_task is required", 400

    package = data.get("package")
    if package not in app_package_map:
        load_app_config(package)
        print('app_package_map[package][atg_analyzer]:', app_package_map[package]['atg_analyzer'])
    if config.wtg:
        print('-----------wtg mode-------------')
        prompt = task_planner.construct_prompt_wtg(target_task, 'D://code/AndroidSourceCodeAnalyzer/AndroidSourceCodeAnalyzer/wtg/notes.txt')
    else:
        prompt = task_planner.construct_prompt(target_task, app_package_map[package]['atg_analyzer'], app_package_map[package]['layout_analyzer'], app_package_map[package]['activity_fragment_mapping'], only_layout = False)
    print("构建的 Prompt：\n", prompt)

    # 调用 LLM 获取结果
    print("\n调用 LLM 获取结果...\n")
    response = llm.quert_llm(prompt,role="You are a user of the given app.")
    print('-----------' * 10 )
    print(response)
# 
    # 返回结果
    # response = ".."
    return response

@app.route('/get_activity_layout_prompt', methods=['POST'])
def prompt2():
    # 获取 JSON 数据
    data = request.get_json()

    # 从 JSON 数据中获取 target_task
    target_task = data.get('target_task')
    # 如果没有提供 target_task，则返回错误
    if not target_task:
        return "Error: target_task is required", 400
    package = data.get("package")
    if package not in app_package_map:
        load_app_config(package) 
    prompt = task_planner.construct_prompt(target_task, app_package_map[package]['atg_analyzer'], app_package_map[package]['layout_analyzer'], app_package_map[package]['activity_fragment_mapping'], only_layout = True)
    print("构建的 Prompt：\n", prompt)

    # 调用 LLM 获取结果
    print("\n调用 LLM 获取结果...\n")
    response = llm.quert_llm(prompt)
    print('-----------' * 10 )
    print(response)

    # 返回结果
    return response

@app.route('/get_element_description', methods=['POST'])
def get_element_description():
    # 获取 JSON 数据
    data = request.get_json()
    print(data)
    package = data.get("package")
    file_path = './program_analysis_results/' + package.replace('.', '_') + '/element_lists_output.json'  # 这是之前保存的 JSON 文件
    # 从 JSON 数据中获取 target_task
    element_id = data.get('element_id')
    elements = load_elements_from_json(file_path)

    # 如果没有提供 target_task，则返回错误
    if not element_id:
        return "", 400
    description = find_action_by_element_id(elements, element_id)
    print(description)
    # 返回结果
    return description

if __name__ == '__main__':
    app.run(debug=True)

