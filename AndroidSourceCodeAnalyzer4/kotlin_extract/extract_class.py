import json
from utils import kotlin_utils

def get_class_info(tree, source_code, output_json_path):
    # 提取类信息
    def find_classes(node):
        classes = []
        if node.type == 'class_declaration':  # Tree-sitter 定义类为 class_declaration
            class_info = {
                "name": None,
                "package": "", 
                "type": "class",
                "annotations": [],
                "modifiers": [],
                "extends": None,
                "implements": [],
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "start_line": node.start_point[0] + 1,  # 转换为从 1 开始的行号
                "end_line": node.end_point[0] + 1
            }

            # 遍历子节点以获取类的相关信息
            for child in node.children:
                if child.type == 'modifier':  # 修饰符
                    modifier = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                    class_info["modifiers"].append(modifier)
                elif child.type == 'type_identifier':  # 类名
                    class_info["name"] = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                elif child.type == 'delegation_specifier':  # 继承的父类
                    construct_list = kotlin_utils.get_child_in_node_list('constructor_invocation', [child])
                    user_type_list = kotlin_utils.get_child_in_node_list('user_type',construct_list )
                    identifier_list = kotlin_utils.get_child_in_node_list('type_identifier', user_type_list)

                    for c in identifier_list:
                            # print(source_code[c.start_byte:c.end_byte].decode('utf-8').strip())
                            class_info["extends"] = source_code[c.start_byte:c.end_byte].decode('utf-8').strip()
                elif child.type == 'super_interfaces':  # 实现的接口列表
                    interfaces = []
                    type_list = child.children[1]
                    for interface in type_list.children:
                        if interface.type == 'type_identifier':  # 接口名称
                            interface_name = source_code[interface.start_byte:interface.end_byte].decode('utf-8').strip()
                            interfaces.append(interface_name)
                        elif interface.type == 'scoped_type_identifier':
                            interface = interface.children[0]
                            interface_name = source_code[interface.start_byte:interface.end_byte].decode('utf-8').strip()
                            interfaces.append(interface_name)
                    class_info["implements"] = interfaces
                elif child.type == 'annotation':  # 类注解
                    annotation_text = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                    class_info["annotations"].append(annotation_text)
            # 如果类名存在，添加到类列表
            if class_info["name"]:
                classes.append(class_info)
    
        # 接口类型
        if node.type == 'interface_declaration':
            class_info = {
                "name": None,
                "package": "", 
                "type": "interface",
                "annotations": [],
                "modifiers": [],
                "extends": None,
                "implements": [],
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "start_line": node.start_point[0] + 1,  # 转换为从 1 开始的行号
                "end_line": node.end_point[0] + 1
            }

            # 遍历子节点以获取类的相关信息
            for child in node.children:
                if child.type == 'modifier':  # 修饰符
                    modifier = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                    class_info["modifiers"].append(modifier)
                elif child.type == 'identifier':  # 类名
                    class_info["name"] = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                elif child.type == 'superclass':  # 继承的父类
                    for c in child.children:
                        if c.type == 'type_identifier':
                            class_info["extends"] = source_code[c.start_byte:c.end_byte].decode('utf-8').strip()
                elif child.type == 'super_interfaces':  # 实现的接口列表
                    interfaces = []
                    type_list = child.children[1]
                    for interface in type_list.children:
                        if interface.type == 'type_identifier':  # 接口名称
                            interface_name = source_code[interface.start_byte:interface.end_byte].decode('utf-8').strip()
                            interfaces.append(interface_name)
                        elif interface.type == 'scoped_type_identifier':
                            interface = interface.children[0]
                            interface_name = source_code[interface.start_byte:interface.end_byte].decode('utf-8').strip()
                            interfaces.append(interface_name)
                    class_info["implements"] = interfaces
                elif child.type == 'annotation':  # 类注解
                    annotation_text = source_code[child.start_byte:child.end_byte].decode('utf-8').strip()
                    class_info["annotations"].append(annotation_text)

            # 如果类名存在，添加到类列表
            if class_info["name"]:
                classes.append(class_info)

        # 递归检查子节点
        for child in node.children:
            classes.extend(find_classes(child))
        return classes
    
    currend_package = kotlin_utils.get_package(tree, source_code)
    # for child in tree.root_node.children:
    #     if child.type == "package_declaration":
    #         for c in child.children:
    #             if c.type == "scoped_identifier":
    #                 currend_package = source_code[c.start_byte:c.end_byte].decode('utf-8').strip()

    # 从语法树中提取类信息
    classes = find_classes(tree.root_node)

    for _class in classes:
        _class["package"] = currend_package

    # 将结果保存为 JSON
    output_data = {
        "classes": classes
    }

    # output_json_path = "classes.json"
    with open(output_json_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Classes have been saved to {output_json_path}")




