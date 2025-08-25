import json
from tree_sitter import Language, Parser

# # 加载 Tree-sitter Java 的共享库
# JAVA_LANGUAGE = Language('C:/Users/wongj/D/code/tree-sitter/tree-sitter-java/libtree-sitter-java.so', 'java')

# # 初始化解析器
# parser = Parser()
# parser.set_language(JAVA_LANGUAGE)

# # 读取 Java 文件内容
# file_path = r"C:/Users/wongj/D/data/app_source_code/Omni-Notes/omniNotes/src/main/java/it/feio/android/omninotes/CategoryActivity.java"

# with open(file_path, 'rb') as file:
#     source_code = file.read()

# # 解析语法树
# tree = parser.parse(source_code)
def get_methods_info(tree, source_code, output_json_path):

    # 提取方法信息
    def find_methods(node):
        methods = []
        if node.type == 'function_declaration':  # Tree-sitter 定义方法为 method_declaration
            method_info = {
                "name": None,
                "modifiers": [],
                "return_type": None,
                "parameters": [],
                "annotations": [],
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "start_line": node.start_point[0] + 1,  # 转换为从 1 开始的行号
                "end_line": node.end_point[0] + 1
            }

            # 遍历子节点以获取方法的相关信息
            for child in node.children:
                if child.type == 'modifiers':  # 修饰符
                    modifier = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                    method_info["modifiers"].append(modifier)
                    #注解
                    for c in child.children:
                        if c.type == 'marker_annotation':
                            annotation_text = source_code[c.start_byte:c.end_byte].decode('utf-8').strip()
                            method_info["annotations"].append(annotation_text)
                elif child.type == 'type':  # 返回类型
                    method_info["return_type"] = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                elif child.type == 'simple_identifier':  # 方法名称
                    method_info["name"] = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                elif child.type == 'formal_parameters':  # 参数列表
                    parameters = []
                    for param in child.children:
                        if param.type == 'parameter':  # 单个参数
                            param_type = None
                            param_name = None
                            for param_child in param.children:
                                if param_child.type == 'type':  # 参数类型
                                    param_type = source_code[param_child.start_byte:param_child.end_byte].decode('utf-8').strip()
                                elif param_child.type == 'identifier':  # 参数名称
                                    param_name = source_code[param_child.start_byte:param_child.end_byte].decode('utf-8').strip()
                            if param_type and param_name:
                                parameters.append({"name": param_name, "type": param_type})
                    method_info["parameters"] = parameters


            # 如果方法名称存在，添加到方法列表
            if method_info["name"]:
                methods.append(method_info)

        # 递归检查子节点
        for child in node.children:
            methods.extend(find_methods(child))
        return methods

    # 从语法树中提取方法
    methods = find_methods(tree.root_node)

    # 将结果保存为 JSON
    output_data = {
        "methods": methods
    }

    with open(output_json_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Methods have been saved to {output_json_path}")
