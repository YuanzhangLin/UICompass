from utils import general_utils
import config
from AndroidManifestAnalyzer import AndroidManifestAnalyzer
import task_planner
from layout_analyzer import LayoutMenuAnalyzer
from CodeMap import CodeMap,Element,Dialog,Fragment,Layout
import os
import json
import llm


def load_app_config(app_config):
    config.target_project = '.' + app_config.get("target_project")
    config.target_project_source_code = config.target_project + app_config.get("source_code")
    config.target_package = app_config.get("target_package")
    config.target_project_AndroidManifest = config.target_project + 'AndroidManifest.xml'
    config.save_path = "./program_analysis_results/" + config.target_package.replace('.','_') + '/'


def process_project(code_map_path):
    with open(code_map_path, 'r', encoding='utf-8') as file:
        code_map = json.load(file)
        # code_map = CodeMap.from_dict(code_map)

    for activity in code_map["activities"]:
        get_total_name(activity["name"], config.save_path, activity)
    return code_map


def get_total_name(part_name, directory, activity):
    print(part_name)
    if '.' in part_name:
        part_name = part_name.rsplit('.', 1)[1]

   # 递归遍历文件夹
    for root, dirs, files in os.walk(directory):
       for file in files:
           if file == 'class_info.json':
               file_path = os.path.join(root, file)
               try:
                   with open(file_path, 'r', encoding='utf-8') as f:
                       data = json.load(f)
                       # 提取classes信息
                       classes = data.get('classes', [])
                       for cls in classes:
                           name = cls.get('name')
                           if name == part_name:
                               # 找到了目标文件夹。
                                activity_file_path = file_path.rsplit("\\", 1)[0]
                                print(activity_file_path)
                                  # 递归遍历文件夹
                                for root, dirs, files in os.walk(activity_file_path):
                                    for file in files:
                                        print(activity_file_path + '/'+ file)
                                        try:
                                            with open(activity_file_path + '/'+ file, 'r') as f:
                                                method_data = json.load(f)  # 读取JSON文件
                                                # 检查"activity_migrations"键是否在JSON数据中
                                                print(method_data)
                                                if "element_list" in method_data and method_data["element_list"]:
                                                    layout = Layout()
                                                    layout.name = "from_code"
                                                    index = 0
                                                    for element in method_data["element_list"]:
                                                        e = Element()
                                                        e.name = index
                                                        e.add_static_property("tag", element.get("type"))
                                                        e.add_static_property("id", element.get("element_id"))
                                                        e.add_dynamic_property("", element.get("action"))
                                                        layout.add_element(e)
                                                    activity.get("layouts").append(layout.to_dict())

                                        except Exception as e:
                                            print(e)
                                            pass


               except Exception as e:
                   print(f"Error reading {file_path}: {e}")
    return part_name


def save_code_map(code_map, save_path):
    # 保存为 JSON
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(code_map, f, ensure_ascii=False, indent=4)
        # f.write(code_map.to_json())






if __name__ == '__main__':
    app_configs = general_utils.read_json('./app_config.json')
    finished = ['applaucher','clock','camera','calendar','dialer','contracts','filemanger','musicplayer','notes','smsmessenger','voicerecorder']
    for app_config in app_configs:
        load_app_config(app_config)
        if 'voicerecorder' not in config.target_package:
            continue
        # for app in finished:
            # if app in config.target_package:
                # continue
        # if 'applauncher' in config.target_package:
            # continue
        # print(config.target_project)
        print('--------')
        appname = config.target_package.rsplit('.',1)[1]
        code_map = process_project('./code_maps/' + appname + ".json")
        save_code_map(code_map,'./code_maps/' + appname + "2.json")
