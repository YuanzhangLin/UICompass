import os
import json

# 定义函数来递归地遍历文件夹并获取element_list
def extract_element_list_from_json_files(folder_path):
    all_elements = []
    
    # 遍历文件夹中的所有文件
    for root, _, files in os.walk(folder_path):
        for file in files:
            # 只处理json文件
            if file.endswith('.json'):
                json_file_path = os.path.join(root, file)
                try:
                    # 读取并解析JSON文件
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # 检查是否存在element_list字段
                        if 'element_list' in data:
                            # 将该文件中的所有元素追加到all_elements中
                            all_elements.extend(data['element_list'])
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading {json_file_path}: {e}")
    
    return all_elements


def generate(folder_path, output_file):
    # 将提取的数据保存到一个新的JSON文件
    def save_elements_to_json(elements, output_file):
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(elements, f, indent=4, ensure_ascii=False)
            print(f"Data successfully saved to {output_file}")
        except IOError as e:
            print(f"Error saving to {output_file}: {e}")

    # 使用示例
    # folder_path = r'D:\code\AndroidSourceCodeAnalyzer/program_analysis_results/com_simplemobiletools_notes_pro'  # 替换为你的文件夹路径
    # output_file = r'element_lists_output.json'  # 输出文件名，可以根据需要修改

    # 获取所有的element_list（合并为一个列表）
    all_elements = extract_element_list_from_json_files(folder_path)

    # 保存结果到新的JSON文件
    save_elements_to_json(all_elements, output_file)
