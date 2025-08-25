from tree_sitter import Language, Parser
import os
import config
import json


def get_child_in_node_list(child_type, node_list):
    child_list = []
    for node in node_list:
        for child in node.children :
            print(child.type)

            if child.type == child_type:
                child_list.append(child)
    return child_list

def get_tree(file_path):
    KOTLIN_LANGUAGE = Language('./lib/build/my-languages.so', 'kotlin')
    # 初始化解析器
    parser = Parser()
    parser.set_language(KOTLIN_LANGUAGE)
    with open(file_path, 'rb') as file:
        source_code = file.read()
        tree = parser.parse(source_code)
    return tree, source_code

def get_package(tree, source_code):
    for child in tree.root_node.children:
        if child.type == "package_header":
            for c in child.children:
                if c.type == "identifier":
                    return source_code[c.start_byte:c.end_byte].decode('utf-8').strip()

def get_class_interface_name(tree, source_code):
    for child in tree.root_node.children:
        if child.type == "class_declaration":
            for c in child.children:
                if c.type == "type_identifier":
                    return source_code[c.start_byte:c.end_byte].decode('utf-8').strip()
        if child.type == "interface_declaration":
            for c in child.children:
                if c.type == "identifier":
                    return source_code[c.start_byte:c.end_byte].decode('utf-8').strip()

def get_all_method(tree, source_code):
    methods = []
    for child in tree.root_node.children:
         if child.type == "class_declaration":
            for c in child.children:

                if c.type == 'class_body':
                    for block in c.children:
                        if block.type == 'function_declaration':
                            for method_block in block.children:
                                if method_block.type == 'simple_identifier':
                                    methods.append(source_code[method_block.start_byte:method_block.end_byte].decode('utf-8').strip())
    return methods

def get_class_method_map(source_directory=None):
    if not source_directory:
        source_directory = config.target_project_source_code

    kotlin_files = get_kotlin_files(source_directory)
    file_code = {}
    for file_path in kotlin_files:
        if 'BaseNote' in file_path:
            print(file_path)
        tree, source_code = get_tree(file_path)
        package = get_package(tree, source_code)
        name = get_class_interface_name(tree, source_code)
        if name:
            # 使用字典而不是集合，来存储 tree 和 source_code
            file_code[package + '.' + name] = {
                'tree': tree,
                'source_code': source_code
            }
    class_method_map = {}
    for file in  file_code:
        methods = get_all_method(file_code[file].get('tree'), file_code[file].get('source_code'))
        class_method_map[file] = {
            'methods': methods
        }
    return class_method_map

def ensure_directory_exists(save_path):
    # 检查路径是否存在，如果不存在则创建
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        print(f"Directory '{save_path}' created.")
    else:
        print(f"Directory '{save_path}' already exists.")

def get_kotlin_files(directory):
    kotlin_files = []
    print(f"Attempting to open file: {directory}")  # 输出文件路径
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".kt"):
                kotlin_files.append(os.path.join(root, file))
    return kotlin_files

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


def get_method_body_by_method_name(path, method_name):
    tree, source_code = get_tree(path)
    for child in tree.root_node.children:
         if child.type == "class_declaration":
            for c in child.children:
                if c.type == 'class_body':
                    for block in c.children:
                        if block.type == 'function_declaration' :
                            for child_method in block.children:
                                if child_method.type == 'simple_identifier':
                                    name = source_code[child_method.start_byte:child_method.end_byte].decode('utf-8').strip()
                                    if name == method_name:
                                        return source_code[block.start_byte:block.end_byte].decode('utf-8').strip()


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
                    if "functionality" in data and "responses" in data:
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

def get_viewBinding_layout(tree, source_code):
    # 获取抽象语法树的根节点
    root_node = tree.root_node

    # 递归查找所有 call_expression 节点，标识符为 'viewBinding'
    def find_viewBinding_calls(node):
        result = []

        # 如果当前节点是一个函数调用，并且其标识符是 'viewBinding'
        if node.type == 'call_expression':
            is_view = False
            for call_child in node.children:
                if call_child.type == 'simple_identifier':
                    call_body = source_code[call_child.start_byte:call_child.end_byte].decode('utf-8').strip()
                    if call_body == 'viewBinding':
                        # 找到这个viewBinding了
                        is_view = True
            if is_view:
                for call_child in node.children:
                    if call_child.type == 'call_suffix':
                        for call_suffix_child in call_child.children:
                            for value_arguments_child in call_suffix_child.children:
                                if value_arguments_child.type == 'value_argument':
                                    for value_argument in value_arguments_child.children:
                                        if value_argument.type == 'callable_reference':
                                            for callable_child in value_argument.children:
                                                if callable_child.type == 'type_identifier':
                                                    result.append(source_code[callable_child.start_byte:callable_child.end_byte].decode('utf-8').strip())
                                                    print(source_code[callable_child.start_byte:callable_child.end_byte].decode('utf-8').strip())
        # 如果当前节点有子节点，则递归遍历每个子节点
        for child in node.children:
            result.extend(find_viewBinding_calls(child))
        return result

    # 从根节点开始递归查找
    result =  find_viewBinding_calls(root_node)
    # 转变格式为R.layout.xx
    last_result = []

    for layout in result:
        last_result.append(binding_to_xml(layout))

    return last_result


import re

def binding_to_xml(binding_name):
    # 匹配绑定类的模式
    match = re.match(r'([A-Za-z]+)([A-Za-z]+)Binding$', binding_name)
    
    if not match:
        raise ValueError(f"Invalid binding class name: {binding_name}")
    
    # 提取类名部分 (如 ActivityMain 或 FragmentExample)
    class_name = match.group(1) + match.group(2)
    
    # 将大写字母转换为小写字母，并加上 '_'
    xml_name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', class_name).lower()
    
    # 添加 '.xml' 后缀
    return xml_name + ".xml"


if __name__ == '__main__':
    kotlin_file_path = 'D:\code\AndroidSourceCodeAnalyzer/app_project/Simple-Notes/Simple-Notes/app/src/main/kotlin/com/simplemobiletools/notes/pro/activities/MainActivity.kt'
    kotlin_interface_path = 'D:\code\AndroidSourceCodeAnalyzer/app_project/Simple-Notes/Simple-Notes/app/src/main/kotlin/com/simplemobiletools/notes/pro/activities/SettingsActivity.kt'
    tree, source_code = get_tree(kotlin_file_path)
    # base_dir = r"D:\code\AndroidSourceCodeAnalyzer/app_project/Simple-Notes/Simple-Notes/app/src/"
    # print(get_class_method_map(base_dir))
    print(get_viewBinding_layout(tree,source_code))