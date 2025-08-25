import os
import config
from utils import java_utils
from utils import kotlin_utils
import json
from  AndroidManifestAnalyzer import AndroidManifestAnalyzer
def ensure_directory_exists(save_path):
    # 检查路径是否存在，如果不存在则创建
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        print(f"Directory '{save_path}' created.")
    else:
        print(f"Directory '{save_path}' already exists.")

# 读取并解析JSON文件
def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

def get_all_folders_recursively(directory):
    """
    递归获取目标文件夹及其所有子文件夹中的所有文件夹。

    :param directory: 目标文件夹的路径
    :return: 包含所有文件夹路径的列表
    """
    folders = []
    
    # 使用 os.walk 递归遍历目录
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            folders.append(os.path.join(root, dir_name))
    
    return folders

def save_string_as_json(data, file_path):
    """
    将给定的字符串数据保存为JSON格式到指定路径。

    :param data: 要保存的字符串数据，假设它是合法的JSON格式
    :param file_path: 保存JSON的文件路径
    :return: None
    """
    try:
        # 尝试将字符串数据解析为JSON对象
        json_data = json.loads(data)

        # 打开文件并将JSON数据写入文件
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to {file_path}")
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


def extract_json_from_answer(answer):
    return answer.replace("```json", "").replace("```","")

def get_java_and_kt_files(folder_path):
    # 用于存储文件名和路径的字典
    file_dict = {}

    # 遍历文件夹下的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 只处理 .java 和 .kt 文件
            if file.endswith('.java') or file.endswith('.kt'):
                # 获取文件名，不带扩展名
                file_name = os.path.splitext(file)[0]
                # 获取文件的完整路径
                file_path = os.path.join(root, file)
                # 将文件名和路径添加到字典中
                file_dict[file_name] = file_path

    return file_dict

def get_code_files(directory):
    # 获取 Java 文件列表
    java_files = java_utils.get_java_files(directory)
    
    # 获取 Kotlin 文件列表
    kotlin_files = kotlin_utils.get_kotlin_files(directory)

    code_files = []
    for file in java_files:
        code_files.append((file, 'java'))
    for file in kotlin_files:
        code_files.append((file, 'kotlin'))
    
    
    count = 0 
    new_code_files = []
    if config.filter_mode:
        for file, file_type in code_files:
            for package in config.analysis_packages:
                if package in file.replace('/', '.').replace('\\', '.'):
                    count += 1
                    new_code_files.append((file, file_type))
    else:
        new_code_files = code_files
    print(f"Total files processed: {count}")

    return new_code_files

def get_all_method(tree, source_code, file_type):
    if file_type == 'java':
        return java_utils.get_all_method(tree, source_code)
    elif file_type == 'kotlin':
        return kotlin_utils.get_all_method(tree, source_code)
    
def get_tree(file_path):
    if file_path.endswith('.java'):
        return java_utils.get_tree(file_path=file_path)
    elif file_path.endswith('.kt'):
        return kotlin_utils.get_tree(file_path=file_path)

def get_package(tree, source_code, file_type):
    if file_type == 'java':
        return java_utils.get_package(tree, source_code)
    elif file_type == 'kotlin':
        return kotlin_utils.get_package(tree, source_code)  
    
def get_class_interface_name(tree, source_code, file_type):
    if file_type == 'java':
        return java_utils.get_class_interface_name(tree, source_code)
    elif file_type == 'kotlin':
        return kotlin_utils.get_class_interface_name(tree, source_code)  

def get_class_method_map():
    java_class_method_map = java_utils.get_class_method_map()
    kotlin_class_method_map = kotlin_utils.get_class_method_map()
    base_map = java_class_method_map.copy()
    for class_name, class_info in kotlin_class_method_map.items():
        if class_name in base_map:
            # 合并方法列表
            base_map[class_name]['methods'].extend(class_info['methods'])
        else:
            base_map[class_name] = class_info   
    return base_map


def capture_layout_caller(tree, source_code):
    """
    递归遍历 AST，查找所有包含 R.layout 或 R.menu 的表达式。
    """
    layout_references = set()  # 用于存储找到的布局引用

    def recursive_check(node):
        # 如果节点有子节点，则递归检查子节点
        if hasattr(node, 'children') and len(node.children) > 0:
            for child in node.children:
                recursive_check(child)

        # 如果节点有 start_byte 和 end_byte 属性，表示该节点对应源代码中的一部分
        if hasattr(node, 'start_byte') and hasattr(node, 'end_byte') and node.type == 'field_access':

            expr_text = source_code[node.start_byte:node.end_byte].decode('utf-8').strip()
            # 检查表达式中是否包含 R.layout 或 R.menu
            if ("R.layout" in expr_text or "R.menu" in expr_text or "R.xml" in expr_text) and not (expr_text == 'R.layout' or expr_text =='R.menu' or expr_text == 'R.xml'):
                layout_references.add(expr_text)

    # 从根节点开始递归检查
    recursive_check(tree.root_node)
    # 第三种情况，通过ViewBinding进行绑定，这种情况下，ActivitySettingsBinding 是由 ViewBinding 自动生成的一个类，它与布局文件（例如 activity_settings.xml）相关联。

   # 获取 viewBinding 布局列表
    viewBinding_layouts = kotlin_utils.get_viewBinding_layout(tree, source_code)

    # 使用 update() 方法将 list 中的所有元素添加到 set
    layout_references.update(viewBinding_layouts)
    return layout_references


def load_info(target_dir):
    info = {}
    class_info_path = target_dir + "class_info.json"
    imports_info_path = target_dir + "imports.json"
    method_calls_path = target_dir + "method_calls.json"
    methods_path = target_dir + "methods.json"
    local_variables_path = target_dir + "local_variables.json"
    global_variables_path = target_dir + "global_variables.json"
    variable_assignment_path = target_dir + "variable_assignment.json"
    if os.path.exists(class_info_path):
        info["class_info"] = read_json(class_info_path)    
    if os.path.exists(imports_info_path):
        info["imports_info"] = read_json(imports_info_path) 
    if os.path.exists(method_calls_path):
        info["method_calls_info"] = read_json(method_calls_path)
    if os.path.exists(methods_path):
        info["methods_info"] = read_json(methods_path)
    if os.path.exists(local_variables_path):
        info["local_variables"] = read_json(local_variables_path)
    if os.path.exists(global_variables_path):
        info["global_variables"] = read_json(global_variables_path)
    if os.path.exists(variable_assignment_path):
        info["variable_assignment"] = read_json(variable_assignment_path)

    return info

def get_method_info(node):
    path = config.save_path + node.replace('.', '/')  + ".json"
    method_info = read_json(path)
    return method_info

def get_global_variables_in_methods(package, class_name, method_name):
    try:
        path = config.save_path + package.replace('.', '/') + '/' + class_name + '/'
        info = load_info(path)
        methods = info["methods_info"]["methods"]
        global_variables = info["global_variables"]["global_variables"]
        local_variables = info["local_variables"]["local_variables"]
        for _m in methods:
            if _m.get("name") == method_name:
                method = _m
        if not method:
            return
        method_start_line = method.get("start_line")
        method_end_line = method.get("end_line")
        local_vars = []
        for local_variable in local_variables:
            local_vars.append(local_variable.get("name"))
        # 这直接给所有的global好了，一般反正也不多。
        global_description = ""
        for variable in global_variables:
            if variable.get("name") and variable.get("type"):
                variable_description = "global variable name: " + variable.get("name") + ", Type: " + variable.get("type")  + '.\n'
                global_description += variable_description

        return global_description
    except Exception as e:
        print(f"Error in get_global_variables_in_methods: {e}")
        return ""

def get_all_global_assignment(package, class_name, method_name):
    try:
        path = config.save_path + package.replace('.', '/') + '/' + class_name + '/'
        info = load_info(path)
        methods = info["methods_info"]["methods"]
        global_variables = info["global_variables"]["global_variables"]
        local_variables = info["local_variables"]["local_variables"]
        variable_assignment = info["variable_assignment"]
        for _m in methods:
            if _m.get("name") == method_name:
                method = _m
        if not method:
            return
        global_vars = []
        for global_variable in global_variables:
            global_vars.append(global_variable.get("name"))

        assignment_description = ""
        for assignment in variable_assignment:
            if assignment.get("left_variable") in global_vars:
                description = "global variable assignment: " + assignment.get("assignment_code")  + '.\n'
                assignment_description += description

        return assignment_description
    except Exception as e:
        print(f"Error in get_all_global_assignment: {e}")
        return ""   

# 该方法用于返回目标文件夹中，已经保存的，activity和fragment的关系
# 返回示例：{'OmniNotes': ['BaseFragment', 'SettingsFragment', 'SketchFragment'], 'MainActivity': ['DetailFragment', 'ListFragment', 'NavigationDrawerFragment', 'SketchFragment'], 'SettingsActivity': ['SettingsFragment']}

def get_activity_fragment_mapping(directory):
    seen = set()  # 将 seen 集合移到函数外部，确保整个目录的文件都能去重
    activity_fragment_mapping = {}

    # 打开输出文件用于写入
    class_name_set = set()

    # 获取所有的class名
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):  # 只处理.json文件
                file_path = os.path.join(root, file)
                try:
                    # 打开并读取 JSON 文件
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if 'class_info' in file_path:
                        # print(file_path)
                        # print(data["classes"][0].get('name'))
                        for _class in data["classes"]:
                            if _class.get('name'):
                                class_name_set.add(_class.get('name'))
                except (json.JSONDecodeError, KeyError) as e:
                    print(e)

    # 遍历目标文件夹及子文件夹中的所有文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):  # 只处理.json文件
                file_path = os.path.join(root, file)
                try:
                    # 打开并读取 JSON 文件
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # 检查是否包含 "functionality" 和 "responses" 字段
                    if "functionality" in data :
                        functionality = data["functionality"]
                        responses = data["fragment_activity_relationships"]
                        for response in responses:
                            fragment = response.get("fragment", "")
                            activity = response.get("activity", "")

                            # 检查 fragment 是否包含 "Fragment" 并且首字母大写
                            # 检查 activity 是否包含 "Activity" 且首字母大写
                            if fragment  in class_name_set and activity in class_name_set:
                                
                                # 使用 (fragment, activity) 组合来过滤重复
                                if (fragment, activity) not in seen:
                                    seen.add((fragment, activity))  # 记录已经处理过的组合

                                    if activity not in activity_fragment_mapping:
                                        activity_fragment_mapping[activity] = []
                                    activity_fragment_mapping[activity].append(fragment)

                except (json.JSONDecodeError, KeyError) as e:
                    print(e)
    return activity_fragment_mapping


# 该方法用于返回目标文件夹中，已经保存的，给定activity相关layout。这部分是由LLM分析出来的，可以弥补更多缺漏。
def get_activity_xml_relationships(directory, activity_name):
    # 保留activity末尾名字：
    if '.' in activity_name:
        activity_name = activity_name.rsplit('.', 1)[1]
    xml_set = set()  # 将 seen 集合移到函数外部，确保整个目录的文件都能去重


    # 遍历目标文件夹及子文件夹中的所有文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):  # 只处理.json文件
                file_path = os.path.join(root, file)
                try:
                    # 打开并读取 JSON 文件
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # 检查是否包含 "functionality" 和 "responses" 字段
                    if "functionality" in data :
                        xml_relationships = data["xml_relationships"]
                        for relationship in xml_relationships:
                            associated_activity = relationship.get("associated_with")
                            if '.' in associated_activity:
                                associated_activity = associated_activity.rsplit('.', 1)[1]#获取活动名。
                            if associated_activity == activity_name:
                                xml_set.add(relationship.get("xml_file"))
                except (json.JSONDecodeError, KeyError) as e:
                    print(e)
    return xml_set

def get_atg_analyzer_from_Manifest():
    manifest_path = config.target_project_AndroidManifest
    atg_analyzer = AndroidManifestAnalyzer(manifest_path)
    return atg_analyzer 

def split_method_node(node):
    package = node.rsplit('.',2)[0]
    class_name = node.rsplit('.',2)[1]
    method_name = node.rsplit('.',2)[2] 
    return package, class_name, method_name


def get_method_body_by_method_name(package, class_name, method_name):
    java_path = config.target_project_source_code + package.replace('.', '/') + '/' + class_name + '.java'
    kotlin_path = config.target_project_source_code + package.replace('.', '/') + '/' + class_name + '.kt'
    if os.path.exists(java_path):
        # is a java file:
        return java_utils.get_method_body_by_method_name(java_path, method_name)
    elif os.path.exists(kotlin_path):
        return kotlin_utils.get_method_body_by_method_name(kotlin_path, method_name)


def get_activity_methods_analysis(activity):
    directory = config.save_path + activity.replace('.', '/') + '/'
    methods_analysis = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):  # 只处理.json文件
                file_path = os.path.join(root, file)
                try:
                    # 打开并读取 JSON 文件
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    file_path = file_path.replace('\\','/')
                    method_name = file_path.replace(".json", "").rsplit("/",1)[1]

                    # 检查是否包含 "functionality" 和 "responses" 字段
                    if "functionality" in data and "responses" in data:
                        # if method_name not in  methods_analysis:
                            # methods_analysis[method_name] =
                        methods_analysis[method_name] = data
                        
                except (json.JSONDecodeError, KeyError) as e:
                    # output.write(f"Error processing file {file_path}: {e}\n")

                    print(file_path)
    return methods_analysis



if __name__ == '__main__':
    # 示例使用
    folder_path = config.target_project_source_code
    result = get_java_and_kt_files(folder_path)

    # 输出结果
    for file_name, file_path in result.items():
        print(f"{file_name}: {file_path}")

    path = result.get('NoteFragment')
    path = path.replace('/', '.').replace('\\','.')
    path = path.rsplit(config.target_package, 1)[1]
    path = config.target_package + path.replace('.kt', '')
    print(path)

