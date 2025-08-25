from utils import general_utils
import config
from AndroidManifestAnalyzer import AndroidManifestAnalyzer
from layout_analyzer import LayoutMenuAnalyzer
from CodeMap import CodeMap,Element,Dialog,Fragment
import os
import json
import llm
import concurrent.futures
from utils import general_utils 
from collections import deque # Needed for BFS traversal
from analyzer import is_in_analysis_packages 

# --- Helper Function for Inheritance Check (Provided by you previously) ---
# Ensure this is in your UiMapGeneration.py file or correctly imported
def is_activity_class(class_name: str, class_graph: dict) -> bool:
    """
    检查一个类是否通过继承链是 Activity (继承自 android.app.Activity 或 androidx.appcompat.app.AppCompatActivity)。

    Args:
        class_name: 要检查的类的完整名称。
        class_graph: 类继承关系字典 {class_name: [superclass1, ...], ...}。
                     在 process_project 中，这个参数将是 class_to_extends_map。

    Returns:
        如果是 Activity 类则返回 True，否则返回 False。
    """
    if class_name in {"android.app.Activity", "androidx.appcompat.app.AppCompatActivity"}:
        return True

    queue = deque([class_name])
    visited = {class_name}

    while queue:
        current_class = queue.popleft()
        superclasses = class_graph.get(current_class, [])

        for superclass in superclasses:
            if superclass in {"android.app.Activity", "androidx.appcompat.app.AppCompatActivity"}:
                return True

            if superclass == "java.lang.Object":
                continue

            if superclass not in visited:
                visited.add(superclass)
                queue.append(superclass)

    return False


    # If the queue is empty and we haven't found Activity, it's not an Activity class via this graph
    return False
def load_app_config(app_config):
    config.target_project = '.' + app_config.get("target_project")
    config.target_project_source_code = config.target_project + app_config.get("source_code")
    config.target_package = app_config.get("target_package")
    config.target_project_AndroidManifest = config.target_project + 'AndroidManifest.xml'
    config.save_path = "./program_analysis_results/" + config.target_package.replace('.','_') + '/'


def process_project():
    code_map = CodeMap()

    manifest = general_utils.get_atg_analyzer_from_Manifest()
    activity_fragment_mapping = general_utils.get_activity_fragment_mapping(config.save_path)

    # 首先要弄好继承关系，因为有的是simpleActivity之类的，实际上继承之后仍然会保留这个activity的fragment和布局信息。

    print('save_path', config.save_path)

    class_to_extends_map = scan_and_extract_class_info(config.save_path)
    print('class_to_extends_map: ', class_to_extends_map)
    # add fragment and dialog:
    print('activity_fragment_mapping": ', activity_fragment_mapping)

    layout_analyzer = LayoutMenuAnalyzer(config.target_project + "res/layout/", config.target_project + "res/menu/", config.target_project + "res/values/", config.target_project + "res/xml/")
    layout_analyzer.init()
    # >>>>>>>>>>>>>>>> FIX: Define analysis_scopes here <<<<<<<<<<<<<<<<<<
    # Determine analysis scopes for filtering Activities based on config (used in both if and else)
    analysis_scopes = getattr(config, 'analysis_packages', [])
    if not analysis_scopes and hasattr(config, 'target_package'):
        analysis_scopes = [config.target_package]
    # >>>>>>>>>>>>>>>>>> End FIX <<<<<<<<<<<<<<<<<<
    if config.manifest:
        for activity in manifest.activities:
            name = activity.get('{http://schemas.android.com/apk/res/android}name')
            if name.startswith('.'):
                name = config.target_package + name
            activity = code_map.add_activity(name)
            capture_layout(name, layout_analyzer, activity)
    else: # config.manifest is False or not set
        print("config.manifest is False. Identifying activities using inheritance and name heuristic from scan results.")
        identified_activities = set()
        if class_to_extends_map:
            # Iterate through all classes for which we have inheritance info
            for class_full_name in class_to_extends_map.keys(): # Assuming keys are full names
                # Check if this class is a potential Activity using EITHER inheritance OR name heuristic
                is_activity_by_inheritance = is_activity_class(class_full_name, class_to_extends_map) # Use the original is_activity_class
                is_activity_by_name_heuristic = class_full_name.lower().endswith("activity") # Use lowercase for robustness

                # Combine the criteria: Is it an Activity by inheritance OR by name heuristic?
                is_potential_activity = is_activity_by_inheritance or is_activity_by_name_heuristic

                # If it's a potential activity by either method, then apply the package scope filtering
                if is_potential_activity:
                    # is_in_analysis_packages needs to be available
                    if not analysis_scopes or is_in_analysis_packages(class_full_name, analysis_scopes):
                        identified_activities.add(class_full_name)
                        # print(f"  > Identified Activity '{class_full_name}' (inheritance: {is_activity_by_inheritance}, name: {is_activity_by_name_heuristic}) and scope match.") # Debugging
                    # else:
                        # print(f"  > Skipping potential Activity '{class_full_name}' (inheritance: {is_activity_by_inheritance}, name: {is_activity_by_name_heuristic}) outside analysis scope.") # Debugging skipped
                # else:
                    # print(f"  > Skipping class '{class_full_name}' (not identified as Activity by inheritance or name heuristic).") # Debugging skipped

            print(f"找到 {len(identified_activities)} 个继承自 Activity 或名称以 Activity 结尾且符合范围的类.")

            if not identified_activities:
                 print("警告: 未找到任何符合范围的继承自 Activity 或名称以 Activity 结尾的类。将跳过 Activity 和布局捕获。")
            else:
                # Now add these identified Activities to code_map and capture layouts
                for activity_name in identified_activities: # activity_name is a full class name here
                    # Add the activity to the code map
                    activity_obj = code_map.add_activity(activity_name)
                    # Capture layout information for this activity
                    # Assuming capture_layout exists
                    capture_layout(activity_name, layout_analyzer, activity_obj)
                print(f"已将 {len(code_map.get_activities())} 个 Activity 添加到 CodeMap 并捕获布局。")

        else:
             print("警告: 未获取到类继承关系信息 (class_to_extends_map)。无法通过继承和名称启发式识别 Activity。")


    for activity in activity_fragment_mapping:
        for part_name in activity_fragment_mapping.get(activity):
            if 'Dialog' in part_name:
                try:
                    # dialog
                    dialog =  Dialog(part_name)
                    capture_layout(part_name, layout_analyzer, dialog)

                    # add dialog
                    if activity in code_map.activities_name:
                        code_map.get_activity(activity).add_dialog(dialog)
                    for class_name in class_to_extends_map:
                        if activity in class_to_extends_map.get(class_name) and class_name in code_map.activities_name:
                            if code_map.get_activity(class_name):
                                code_map.get_activity(class_name).add_dialog(dialog)
                except Exception as e :
                    print(e)
            elif 'Fragment' in part_name:
                try:
                    # dialog
                    fragment =  Fragment(part_name)
                    capture_layout(part_name, layout_analyzer, fragment)
                    if activity in code_map.activities_name:
                        code_map.get_activity(activity).add_fragment(fragment)
                    for class_name in class_to_extends_map:
                        if activity == class_to_extends_map.get(class_name) :
                            if code_map.get_activity(class_name):
                                code_map.get_activity(class_name).add_fragment(fragment)
                except Exception as e:
                    print(e)
    print(code_map.activities_name)
    # 扫描所有文件夹，获得活动之间的迁移关系。
    transfer_relationship = scan_and_extract_transfer_relationship(config.save_path)
    print('-----------transfer_relationship---------')
    print(transfer_relationship)
    print('-----------============---------')
    # 添加迁移关系。
    for transfer in transfer_relationship:
        if transfer[0] in code_map.activities_name and transfer[1] in code_map.activities_name:
            code_map.get_activity(transfer[0]).add_transfer(transfer[1])



    return code_map


def process_single_activity(activity):
    """
    为单个activity生成摘要。此函数在一个独立的线程中运行。
    它自己负责在任务完成后打印成功或失败的日志。
    """
    print(f"INFO: Starting summary generation for {activity.name}...")
    try:
        # 1. 构建 Prompt (这部分与你原来的一样)
        summary_prompt = f"You are a code summary assistant. You need to analyze the functionality summary of the activity based on the code content I provide (activity name, brief description of methods in the activity, elements in the activity). Additionally, you also need to provide a functional description summary of the elements.\nactivity name: {activity.name}\n"
        activity_path = config.save_path + activity.name.replace('.','/')
        for root, dirs, files in os.walk(activity_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            method_name = os.path.splitext(os.path.basename(file_path))[0]
                            if "functionality" in data and data["functionality"]:
                                functionality = data["functionality"]
                                summary_prompt += f"Method {method_name}: {functionality}\n"
                    except Exception:
                        pass
        summary_prompt += "\n element in the activity: \n"
        for layout in activity.layouts:
            summary_prompt += f"\n layout name: {layout.name}"
            element_index = 0
            for element in layout.elements:
                summary_prompt += f"\n element index: {element_index} "
                for prop, value in element.static_properties.items():
                    summary_prompt += f"\"{prop}\":\"{value}\" "
                summary_prompt += ""
                element_index += 1
        summary_prompt += """
        Now you should output in the following JSON format. **Do not output any others except the json format**:
        Note that, tell me the summary of the activity and tell me the summary of each element with element id.
        {
            "activitySummary":"A brief summary of the activity's functionality.For example:this activity is used for setting, which include set theme,color,size."
             "elementSummaries": [
            {   
                "layoutname": "layout1",
                "element_id": "@+id/config_holder",
                "functionDescription": {
                    "action": "click",
                    "effect": "open the config activitiy".
                }
            },
            {
                "layoutname": "layout1",
                "element_id": "@+id/login",
                "functionDescription": {
                    "action": "click",
                    "effect": "open the MainActivity".
                }
            }
            ]        
        }
        """

        # 2. 调用LLM (llm.py里的函数现在是静默的)
        answer = llm.query_llm_and_parse(summary_prompt)
        
        # 3. 在任务完成后打印日志并返回结果
        if answer:
            print(f"INFO: Successfully generated summary for {activity.name}.")
            return activity, answer
        else:
            print(f"WARNING: Failed to get summary for {activity.name} after retries.")
            return activity, None

    except Exception as e:
        print(f"ERROR: An exception occurred while processing {activity.name}: {e}")
        return activity, None


def add_activity_summary(code_map):
    """
    使用线程池并发地为所有Activity生成摘要。
    """
    MAX_WORKERS = 8 
    print(f"\nStarting parallel summary generation for {len(code_map.activities)} activities with up to {MAX_WORKERS} workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_activity = {executor.submit(process_single_activity, activity): activity for activity in code_map.activities}
        
        for future in concurrent.futures.as_completed(future_to_activity):
            try:
                processed_activity, data = future.result()
                
                if not data:
                    continue

                # 将LLM返回的数据更新到对应的Activity对象中
                processed_activity.summary = data.get('activitySummary', '')
                
                element_summaries = data.get('elementSummaries', [])
                if not element_summaries:
                    continue

                for e_summary in element_summaries:
                    layout_name_summary = e_summary.get("layoutname")
                    element_id_summary = e_summary.get("element_id")
                    func_desc_summary = e_summary.get("functionDescription")

                    if not all([layout_name_summary, element_id_summary, func_desc_summary]):
                        continue

                    for layout in processed_activity.layouts:
                        layout_name = layout.name
                        if "." in layout_name:
                            layout_name = layout_name.rsplit('.', 1)[1]
                        
                        if layout_name == layout_name_summary:
                            for element in layout.elements:
                                if "id" in element.static_properties and element.static_properties["id"] == element_id_summary:
                                    element.dynamic_properties = [func_desc_summary]
                                    break 
                            else:
                                continue
                            break 

            except Exception as e:
                print(f"ERROR: A task generated an exception: {e}")

    print("\nParallel summary generation finished.")

def save_code_map(code_map, save_path):
    # 保存为 JSON
    with open(save_path, 'w') as f:
        f.write(code_map.to_json())


def get_total_name(part_name, directory):
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
                           package = cls.get('package')
                           if name == part_name:
                               return package + '.' + name

               except Exception as e:
                   print(f"Error reading {file_path}: {e}")
    return part_name



def scan_and_extract_transfer_relationship(directory):
   transfer_relationship = []

   def recursive_scan(current_directory):
       for entry in os.scandir(current_directory):
           if entry.is_dir():
               recursive_scan(entry.path)  # 递归遍历子目录
           elif entry.is_file() and entry.name.endswith('.json'):
               file_path = entry.path
               try:
                   with open(file_path, 'r') as f:
                       data = json.load(f)  # 读取JSON文件
                       # 检查"activity_migrations"键是否在JSON数据中
                       if "activity_migrations" in data:
                           for migration in data["activity_migrations"]:
                            transfer = []
                            transfer.append(migration["from_activity_or_fragment"])
                            transfer.append(migration["to_activity_or_fragment"])
                            transfer_relationship.append(transfer)
               except Exception as e:
                   pass

   recursive_scan(directory)  # 从指定目录开始递归遍历
   return transfer_relationship


def scan_and_extract_class_info(directory):
    name_to_extends_map = {} 
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == 'class_info.json':
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        classes = data.get('classes', [])
                        imports_info = data.get('imports_info', {}) # Need imports to resolve names

                        for cls in classes:
                           simple_name = cls.get('name')
                           full_name = cls.get('package') + '.' + simple_name if cls.get('package') else simple_name # Try to get full name
                           extends_simple_name = cls.get('extends') # This seems to be a single string

                           if full_name and extends_simple_name:
                               full_class_name = cls.get('package') + '.' + cls.get('name') if cls.get('package') else cls.get('name')
                               extends_list = [cls.get('extends')] if cls.get('extends') else [] # Assuming extends is single string
                               resolved_extends_list = extends_list # Placeholder - needs real resolution

                               if full_class_name:
                                    name_to_extends_map[full_class_name] = resolved_extends_list

                except Exception as e:
                   print(f"Error reading {file_path}: {e}")

    # Return the map where keys are full class names and values are lists of full superclass names
    return name_to_extends_map


def capture_layout(activity_name, layout_analyzer, activity):
    print("---------------------------capture layout")
    if not activity_name.startswith(config.target_package):
        return 
    target_source_code_path = config.target_project_source_code + activity_name.replace('.', '/') + '.java'
    if not os.path.exists(target_source_code_path):
        target_source_code_path = config.target_project_source_code + activity_name.replace('.', '/') + '.kt'
    tree, source_code = general_utils.get_tree(target_source_code_path)
    layout_references =  general_utils.capture_layout_caller(tree, source_code) # ['widget_config_monthly.xml',...]
    layout_references.update(general_utils.get_activity_xml_relationships(config.save_path, activity_name))
    print(layout_references)
    print('aaaaaaaaa')
    for reference in layout_references:
        # 如果没有，一般视为R.layout
        if '.xml.' not in reference and '.layout.' not in reference:
            if reference.endswith('.xml'):
                reference = reference.replace('.xml', '')
            reference = 'R.layout.' + reference
        activity.add_layout(layout_analyzer.get_layout(reference))


if __name__ == '__main__':
    app_configs = general_utils.read_json('./app_config.json')
    finished = ['applaucher','clock','camera','calendar','dialer','contracts','filemanger','musicplayer','notes','smsmessenger','voicerecoder', 'audiorecorder','broccoli']
    for app_config in app_configs:
        load_app_config(app_config)
        # if 'gallery' not in config.target_package:
        #     continue
        has_finished = False
        for app in finished:
            if app in config.target_package:
                has_finished = True
                break
        if has_finished:
            continue
        # if 'applauncher' in config.target_package:
            # continue
        # print(config.target_project)
        code_map = process_project()
        add_activity_summary(code_map)
        print('*'*20)
        print("save path : ",config.target_package)
        appname = config.target_package#.rsplit('.',1)[1]
        save_code_map(code_map,'./code_maps/' + appname + ".json")
        break