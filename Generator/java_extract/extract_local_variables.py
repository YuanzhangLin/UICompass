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

def get_local_variables_info(tree, source_code, output_json_path):
    # 提取局部变量定义
    def find_local_variables(node):
        variables = []
        if node.type == 'local_variable_declaration':  # Tree-sitter 定义变量为 variable_declaration
            # 遍历子节点以获取变量的类型和名称
            var_type = None
            var_names = []

            for child in node.children:
                if child.type == 'type_identifier':  # 变量类型
                    var_type = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                elif child.type == 'variable_declarator':  # 变量名称
                    var_name_node = child.child_by_field_name('name')
                    var_name = source_code[var_name_node.start_byte:var_name_node.end_byte].decode('utf-8').strip()
                    var_names.append(var_name)
            # 将变量信息添加到列表
            if var_type and var_names:
                for var_name in var_names:
                    variables.append({
                        "name": var_name,
                        "type": var_type,
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte,
                        "start_line": node.start_point[0] + 1,  # 转换为从 1 开始的行号
                        "end_line": node.end_point[0] + 1
                    })

        # 递归检查子节点
        for child in node.children:
            variables.extend(find_local_variables(child))
        return variables

    # 从语法树中提取局部变量
    local_variables = find_local_variables(tree.root_node)

    # 将结果保存为 JSON
    output_data = {
        "local_variables": local_variables
    }

    with open(output_json_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Local variables have been saved to {output_json_path}")
