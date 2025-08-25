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
def get_global_variables_info(tree, source_code, output_json_path):
    # 提取全局变量（类级别字段）
    def find_global_variables(node):
        variables = []
        if node.type == 'property_declaration':  # Tree-sitter 定义字段为 field_declaration
            # 获取字段修饰符、类型和名称
            modifiers = []
            var_type = None
            var_name = None
            for child in node.children:
                if child.type == 'modifiers':
                    modifier_text = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                    modifiers.append(modifier_text)
                # elif child.type == 'type_identifier':  # 变量类型
                #     var_type = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                elif child.type == 'variable_declaration':  # 变量名称
                    for variable_child in child.children:
                        if variable_child.type == 'simple_identifier':
                            # var_name_node = child.child_by_field_name('name')
                            var_name = source_code[variable_child.start_byte:variable_child.end_byte].decode('utf-8').strip()
                        if variable_child.type =='user_type':
                            for vc in variable_child.children:
                                if vc.type == 'type_identifier':
                                    var_type = source_code[vc.start_byte:vc.end_byte].decode('utf-8').strip()

        
            # 如果变量名称和类型都存在，则记录变量信息
            if var_name:
                variables.append({
                    "name": var_name,
                    "type": var_type,
                    "modifiers": modifiers,
                    "start_byte": node.start_byte,
                    "end_byte": node.end_byte,
                    "start_line": node.start_point[0] + 1,  # 转换为从 1 开始的行号
                    "end_line": node.end_point[0] + 1
                })

        # 递归检查子节点
        for child in node.children:
            variables.extend(find_global_variables(child))
        return variables

    # 从语法树中提取全局变量
    global_variables = find_global_variables(tree.root_node)

    # 将结果保存为 JSON
    output_data = {
        "global_variables": global_variables
    }

    # output_json_path = "global_variables.json"
    with open(output_json_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Global variables have been saved to {output_json_path}")
