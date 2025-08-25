from tree_sitter import Language, Parser
import os
import config
import json
from AndroidManifestAnalyzer import AndroidManifestAnalyzer

def get_tree(file_path):
    # 加载 Tree-sitter Java 的共享库
    JAVA_LANGUAGE = Language('.\lib\libtree-sitter-java.so', 'java')
    # 初始化解析器
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    file_path = './'+os.path.normpath(file_path)  # 自动统一路径分隔符
    print(file_path)
    # 读取 Java 文件内容
    with open(file_path, 'rb') as file:
        source_code = file.read()
        tree = parser.parse(source_code)
    return tree, source_code


def get_package(tree, source_code):
    for child in tree.root_node.children:
        if child.type == "package_declaration":
            for c in child.children:
                if c.type == "scoped_identifier":
                    return source_code[c.start_byte:c.end_byte].decode('utf-8').strip()
                
def get_class_interface_name(tree, source_code):
    for child in tree.root_node.children:
        print(child.type)
        if child.type == "class_declaration":
            for c in child.children:
                if c.type == "identifier":
                    return source_code[c.start_byte:c.end_byte].decode('utf-8').strip()
        if child.type == "interface_declaration":
            for c in child.children:
                if c.type == "identifier":
                    return source_code[c.start_byte:c.end_byte].decode('utf-8').strip()
        if child.type == 'annotation_type_declaration':
            for anotation_child_type in child.children:
                if anotation_child_type.type == 'modifiers':
                    for modifiers_child in anotation_child_type.children:
                        if modifiers_child.type == 'annotation':
                            for annotation_child in modifiers_child.children:
                                if annotation_child.type == 'identifier':
                                    return source_code[annotation_child.start_byte:annotation_child.end_byte].decode('utf-8').strip()

def get_all_method(tree, source_code):
    methods = []
    for child in tree.root_node.children:
         if child.type == "class_declaration":
            for c in child.children:
                if c.type == 'class_body':
                    for block in c.children:
                        if block.type == 'method_declaration':
                            for method_block in block.children:
                                if method_block.type == 'identifier':
                                    methods.append(source_code[method_block.start_byte:method_block.end_byte].decode('utf-8').strip())
    return methods


def get_class_method_map():
    java_files = get_java_files(config.target_project_source_code)
    file_code = {}
    for file_path in java_files:
        try:
            tree, source_code = get_tree(file_path)
            package = get_package(tree, source_code)
            name = get_class_interface_name(tree, source_code)
            # 使用字典而不是集合，来存储 tree 和 source_code
            file_code[package + '.' + name] = {
                'tree': tree,
                'source_code': source_code
            }
        except Exception as e:
            print(e)
    class_method_map = {}
    for file in  file_code:
        methods = get_all_method(file_code[file].get('tree'), file_code[file].get('source_code'))
        class_method_map[file] = {
            'methods': methods
        }
    return class_method_map




def get_java_files(directory):
    java_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))
    return java_files







def get_method_body_by_method_name(path, method_name):
    tree, source_code = get_tree(path)
    for child in tree.root_node.children:
         if child.type == "class_declaration":
            for c in child.children:
                if c.type == 'class_body':
                    for block in c.children:
                        if block.type == 'method_declaration' :
                            for child_method in block.children:
                                if child_method.type == 'identifier':
                                    name = source_code[child_method.start_byte:child_method.end_byte].decode('utf-8').strip()
                                    if name == method_name:
                                        return source_code[block.start_byte:block.end_byte].decode('utf-8').strip()





