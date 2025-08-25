import json
from tree_sitter import Language, Parser



def get_import_info(tree, source_code, output_json_path):
    # 提取 import 语句
    def find_imports(node):
        imports = []
        if node.type == 'import_header':
            start_byte = node.start_byte
            end_byte = node.end_byte
            _import_node_list = []
            for child in node.children:
                if child.type == 'identifier':
                    _import_node_list =child.children
                    
            import_statement = source_code[start_byte:end_byte].decode('utf-8').strip()
            # is_static = any(child.type == 'static' for child in node.children)
            # if  is_static:
            # scoped_identifier = scoped_identifier.child_by_field_name('scope')
            # name_node = scoped_identifier.child_by_field_name('name')
            # name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8').strip()
            # scope_node = scoped_identifier.child_by_field_name('scope')
            # scope = source_code[scope_node.start_byte:scope_node.end_byte].decode('utf-8').strip()
            scope_list = []
            for scope_part in _import_node_list[:-1]:
                scope_list.append(source_code[scope_part.start_byte:scope_part.end_byte].decode('utf-8').strip())
            scope = ''.join(scope_list)[:-1]
            name = source_code[_import_node_list[-1].start_byte:_import_node_list[-1].end_byte].decode('utf-8').strip()

            imports.append((start_byte, end_byte, import_statement, name, scope))
        for child in node.children:
            imports.extend(find_imports(child))
        return imports
    _import_node = None
    for child in tree.root_node.children:
        if child.type == 'import_list':
            _import_node = child

    # 从根节点解析 import
    if _import_node :
        imports = find_imports(_import_node)
    else:
        imports =[]

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