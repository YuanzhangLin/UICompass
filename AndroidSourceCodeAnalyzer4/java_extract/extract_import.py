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


def get_import_info(tree, source_code, output_json_path):
    # 提取 import 语句
    def find_imports(node):
        imports = []
        if node.type == 'import_declaration':
            start_byte = node.start_byte
            end_byte = node.end_byte
            for child in node.children:
                if child.type == 'scoped_identifier':
                    scoped_identifier = child
            import_statement = source_code[start_byte:end_byte].decode('utf-8').strip()
            is_static = any(child.type == 'static' for child in node.children)
            if  is_static:
                scoped_identifier = scoped_identifier.child_by_field_name('scope')
            name_node = scoped_identifier.child_by_field_name('name')
            name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8').strip()
            scope_node = scoped_identifier.child_by_field_name('scope')
            scope = source_code[scope_node.start_byte:scope_node.end_byte].decode('utf-8').strip()
            imports.append((start_byte, end_byte, import_statement, name, scope))
        for child in node.children:
            imports.extend(find_imports(child))
        return imports



    # 从根节点解析 import
    imports = find_imports(tree.root_node)

    # 构建 import 映射
    import_dict = {}
    for start_byte, end_byte, imp, name, scope in imports:
        if imp.startswith("import"):
            # full_class = imp.replace("import", "").replace(";", "").strip()
            # class_name = full_class.split(".")[-1]
            # package_name = ".".join(full_class.split(".")[:-1])
            import_dict[name] = {
                "name": name,
                "scope": scope,
                "start_byte": start_byte,
                "end_byte": end_byte,
                "start_line": tree.root_node.start_point[0] + 1,  # Tree-sitter 行号从 0 开始，转换为从 1 开始
                "end_line": tree.root_node.end_point[0] + 1
            }


    # 将 import 映射和 scoped_identifier 信息转换为 JSON 格式
    import_json = json.dumps(import_dict, indent=4)


    with open(output_json_path, 'w') as json_file:
        json_file.write(import_json)
    print(f"Detailed import statements have been saved to {output_json_path}")