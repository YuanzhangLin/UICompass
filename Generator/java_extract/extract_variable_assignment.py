import json

def get_variable_assignment(tree, source_code, output_json_path):

                                                
    # 查找 assignment 语句的递归函数
    def find_assignments(node):
        assignments = []
        # 检查当前节点是否是赋值操作
        if node.type == 'assignment_expression':
            print(node)
            start_byte = node.start_byte
            end_byte = node.end_byte
            assignment_code = source_code[start_byte:end_byte].decode('utf-8').strip()
            # 获取左边的目标变量和右边的值
            left_child = node.children[0] if node.children else None
            right_child = node.children[1] if len(node.children) > 1 else None
            if left_child:
                left_var = source_code[left_child.start_byte:left_child.end_byte].decode('utf-8').strip()
            else:
                left_var = None
            if right_child:
                right_expr = source_code[right_child.start_byte:right_child.end_byte].decode('utf-8').strip()
            else:
                right_expr = None

            # 将赋值操作信息存入列表
            assignments.append({
                "assignment_code": assignment_code,
                "left_variable": left_var,
                "right_expression": right_expr,
                "start_byte": start_byte,
                "end_byte": end_byte,
                "start_line": tree.root_node.start_point[0] + 1,  # 行号转换为从1开始
                "end_line": tree.root_node.end_point[0] + 1
            })
        
        # 递归检查子节点
        for child in node.children:
            assignments.extend(find_assignments(child))
        return assignments

    # 获取所有赋值操作节点
    assignments = find_assignments(tree.root_node)

    # 将赋值操作信息转化为 JSON 格式
    assignments_json = json.dumps(assignments, indent=4)

    # 将结果写入 JSON 文件
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json_file.write(assignments_json)
    print(f"Assignment nodes have been saved to {output_json_path}")

# 假设你已经有了 Tree-sitter 解析树和源代码内容
# tree: Tree-sitter 解析树
# source_code: 源代码字节数据
# output_json_path: 输出 JSON 文件路径
