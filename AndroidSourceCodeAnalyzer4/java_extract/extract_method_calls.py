import json
from tree_sitter import Language, Parser

# # 加载 Tree-sitter Java 的共享库
# JAVA_LANGUAGE = Language('.\lib\libtree-sitter-java.so', 'java')

# # 初始化解析器
# parser = Parser()
# parser.set_language(JAVA_LANGUAGE)

# # 读取 Java 文件内容
# file_path = r"./java_code/CategoryActivity.java"

# with open(file_path, 'rb') as file:
#     source_code = file.read()

# # 解析语法树
# tree = parser.parse(source_code)

def get_method_calls_info(tree, source_code, output_json_path):
    # 提取方法调用信息
    def find_method_calls(node):
        method_calls = []
        
        if node.type == 'method_invocation':  # Tree-sitter 定义方法调用为 method_invocation
            method_call_info = {
                "method_name": None,
                "caller": None,
                "arguments": [],
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "start_line": node.start_point[0] + 1,  # 转换为从 1 开始的行号
                "end_line": node.end_point[0] + 1
            }

            point_index = -1
            # 遍历子节点以获取方法调用的相关信息
            for child in node.children:
                if child.type == 'identifier':  # 方法名
                    method_call_info["method_name"] = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                elif child.type == 'argument_list':  # 方法参数
                    arguments = []
                    for arg in child.children:
                        if arg.type not in {'(', ')', ','}:  # 忽略括号和逗号
                            argument_text = source_code[arg.start_byte:arg.end_byte].decode('utf-8').strip()
                            arguments.append(argument_text)
                    method_call_info["arguments"] = arguments
                # elif child.type == 'field_access':  # 调用者（可能是某个对象或变量）
                    # caller_node = child.child_by_field_name("object")
                    # if caller_node:
                        # method_call_info["caller"] = source_code[caller_node.start_byte:caller_node.end_byte].decode('utf-8').strip()
                elif child.type == 'scoped_identifier':  # 另一个形式的调用者
                    method_call_info["caller"] = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
            for index in range(0, len(node.children)):
                if node.children[index].type == '.':
                    point_index = index
            if point_index >=1:
                method_call_info["caller"] = source_code[node.children[point_index-1].start_byte:node.children[point_index-1].end_byte].decode('utf-8').strip()
            # 如果方法名存在，添加到方法调用列表
            if method_call_info["method_name"]:
                method_calls.append(method_call_info)

        # 递归检查子节点
        for child in node.children:
            method_calls.extend(find_method_calls(child))
        return method_calls

    # 从语法树中提取方法调用信息
    method_calls = find_method_calls(tree.root_node)

    # 将结果保存为 JSON
    output_data = {
        "method_calls": method_calls
    }

    with open(output_json_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Method calls have been saved to {output_json_path}")
