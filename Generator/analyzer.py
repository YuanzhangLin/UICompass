import json
import config
from utils import general_utils
import os
from  dependency_graph import DependencyGraph





def analyze_extend_relationship(java_analyzed_path, package_name, info, dep_graph):
    if not info["class_info"].get("classes"):
        return
    class_info = info["class_info"].get("classes")[0]
    current_package = class_info.get("package")
    # 1. 它继承的文件，如果不是android里面的，就应先分析继承的文件。
    extended_class = class_info.get("extends")
    # 1.1 从import中寻找
    for _import in info["imports_info"]:
        if _import == extended_class:
            # 找到了目标类的import
            if package_name in info["imports_info"][_import].get("scope"):
                # 正常从源代码是可以读入package name的。
                #是该项目的自定义类。
                dep_graph.add_class_dependency(current_package + '.' + class_info.get("name"), info["imports_info"][_import].get("scope") + '.' + info["imports_info"][_import].get("name"))
              
            # else:
                # print('是第三方类，或者是android的官方类')
    # 1.2 如果不在import里面，那么肯定就是再当前文件夹中了。
    java_analyzed_path = java_analyzed_path.replace('\\','/')
    if java_analyzed_path.endswith('/'):
        parent_path = java_analyzed_path.rsplit('/', 2)[0]
    else:
        parent_path = java_analyzed_path.rsplit('/', 1)[0]
    # 获取目标路径下的所有条目（文件和文件夹）
    all_entries = os.listdir(parent_path)
    # 过滤出文件夹
    folders = [entry for entry in all_entries if os.path.isdir(os.path.join(parent_path, entry))]
    # 用于存储存在 class.json 文件的文件夹路径
    folders_with_class_json = []
    # 检查每个文件夹中是否存在 class.json 文件
    for folder in folders:
        folder_path = os.path.join(parent_path, folder)
        class_json_path = os.path.join(folder_path, 'class_info.json')
        if os.path.isfile(class_json_path):
            folders_with_class_json.append(folder_path)
    for folder in folders_with_class_json :
        if os.path.basename(folder) == extended_class:
            dep_graph.add_class_dependency(current_package + '.' + class_info.get("name"), current_package + '.' +  extended_class)



# --- Function to scan and extract class info (Copy from your UiMapGeneration.py) ---
# Ensure this function is present in analyzer.py or correctly imported.
# Assuming it returns {full_class_name: [full_superclass_name, ...]} structure (based on is_activity_class needs)
# If your scanner returns {full_class_name: [simple_superclass_name, ...]} or {full_class_name: simple_superclass_name},
# then the is_activity_class function *must* be adapted to handle that structure correctly.
# Let's assume for now it returns {full_class_name: [full_superclass_name, ...]} as needed by is_activity_class.
def scan_and_extract_class_info(directory):
   name_to_extends_map = {} # This name might be misleading if it's full names

   # Assuming your analysis results format requires this parsing
   for root, dirs, files in os.walk(directory):
       for file in files:
           if file == 'class_info.json':
               file_path = os.path.join(root, file)
               try:
                   with open(file_path, 'r', encoding='utf-8') as f:
                       data = json.load(f)
                       classes = data.get('classes', [])
                       # imports_info = data.get('imports_info', {}) # Needed for resolving names if extends are simple

                       for cls in classes:
                           # *** Critical: Ensure you get FULL names here for class and extends ***
                           # This often requires using import info or package name.
                           # This parsing logic is complex and depends heavily on your scanner output format.
                           # Let's assume for this fix that your analysis results JSON
                           # contains 'full_name' for the class and a list of 'full_extends_names'.
                           # If not, this scanner or the is_activity_class needs adaptation.

                           full_class_name = cls.get('full_name') # Assuming scanner provides full_name
                           # Assuming extends is a list of full names
                           full_extends_list = cls.get('extends', []) # Assuming scanner provides list of full extends names

                           # If scanner doesn't provide full_name or list of full_extends_names,
                           # you need to modify the scanner or implement name resolution here.
                           # Example if scanner gives 'name', 'package', 'extends' (simple string):
                           # full_class_name = f"{cls.get('package', '')}.{cls.get('name', '')}"
                           # simple_extends_name = cls.get('extends')
                           # resolved_full_extends_list = [resolve_full_name(simple_extends_name, imports_info, cls.get('package', ''))] # Need resolve_full_name helper

                           if full_class_name: # Ensure we got a valid full name
                               # Ensure value is a list, even if it was a single string in scanner output
                               if not isinstance(full_extends_list, list):
                                   full_extends_list = [full_extends_list] if full_extends_list else []
                               name_to_extends_map[full_class_name] = full_extends_list

               except Exception as e:
                   print(f"Error reading {file_path} for class info: {e}")
                   # traceback.print_exc() # Optional: print full traceback

   # Return the map where keys are full class names and values are lists of full superclass names
   return name_to_extends_map



def analyze_method_relationship(java_analyzed_path, package_name, info, dep_graph):
    if not info["class_info"].get("classes"):
        return
    class_info = info["class_info"].get("classes")[0]
    method_calls_info = info['method_calls_info']
    method_calls = method_calls_info.get("method_calls")
    methods_info = info['methods_info'].get("methods")
    local_variable = info['local_variables'].get("local_variables")
    global_variables = info['global_variables'].get("global_variables")
    imports = info["imports_info"]

    # 查看这个调用是属于哪个方法的。
    method_calls_location = {}
    for method_call in method_calls:
        for method in methods_info:
            if method.get("start_line") <= method_call.get("start_line") and method.get("end_line") >= method_call.get("end_line"):
                if method.get("name") not in method_calls_location:
                    method_calls_location[method.get("name")] = []
                method_calls_location[method.get("name")].append(method_call)



    non_caller_method = []
    called_method = []
    for method_call in method_calls:
        if method_call.get("caller"):
            called_method.append(method_call)
        else:
            non_caller_method.append(method_call)
    # 第一种，没有caller，这种方法很可能是 
    # 2） 继承的类的
    # 剩余情况不予考虑
    for method_call in non_caller_method:
        # 1） 定义在当前类的。
        # 寻找
        # 首先应该是确认这个method_call 是哪个method调用的：
        method_call_in_method = ""
        for location in method_calls_location :
            for method_c in method_calls_location[location]:
                if method_c.get("method_name") == method_call.get("method_name") and method_c.get("start_byte") == method_call.get("start_byte") and  method_c.get("end_byte") == method_call.get("end_byte") :
                    method_call_in_method = location
        find = False
        for method in methods_info:
            if method.get("name") == method_call.get("method_name"):
                # print("方法定义在当前类中： ", method.get("name") )
                dep_graph.add_method_dependency(class_info.get("package") + "." + class_info.get("name") + "." + method_call_in_method, class_info.get("package") + "." + class_info.get("name") + "." + method.get("name"))
                find = True
        # if not find:
            # print("没有找到方法: ", method.get("name"))
    
    # 第二种，有caller，意味着是某个变量调用的，我们需要找到变量的定义，并发现变量的类型。
    # 如果都不是，那就不管了
    for method_call in called_method:
        method_call_in_method = ""
        for location in method_calls_location :
            for method_c in method_calls_location[location]:
                if method_c.get("method_name") == method_call.get("method_name") and method_c.get("start_byte") == method_call.get("start_byte") and  method_c.get("end_byte") == method_call.get("end_byte") :
                    method_call_in_method = location
        for variable in local_variable:
            if method_call.get("caller")  == variable.get("name"):
                variable_type = variable.get("type")
                for _import in imports:
                    if _import == variable_type: 
                        variable_class = str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))
                        if package_name in variable_class:
                            # print("方法定义在局部变量中：", str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))+ "." + method_call.get("method_name"))
                            dep_graph.add_method_dependency(class_info.get("package") + "." + class_info.get("name") + "." + method_call_in_method,str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))+ "." + method_call.get("method_name"))
        for variable in global_variables:
            if method_call.get("caller")  == variable.get("name"):
                variable_type = variable.get("type")
                for _import in imports:
                    if _import == variable_type:
                        variable_class = str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))
                        if package_name in variable_class:
                            # print("方法定义在全局变量中 ",  str(imports[_import].get("scope")) + "." + str(imports[_import].get("name")) + "." + method_call.get("method_name"))
                            dep_graph.add_method_dependency(class_info.get("package") + "." + class_info.get("name") + "." + method_call_in_method,str(imports[_import].get("scope")) + "." + str(imports[_import].get("name"))+ "." + method_call.get("method_name"))


def analyze_file(java_analyzed_path, package_name, dep_graph):
    info = general_utils.load_info(java_analyzed_path)
    analyze_extend_relationship(java_analyzed_path, package_name, info, dep_graph)

    # 2. 它调用的所有的方法，如果方法不是当前文件的，则应该先分析那些方法（如果不是这个project自定义的方案，就不用分析了）。
    #   2.1 如果是当前文件的方法，那么就先分析当前文件的其他方法。
    analyze_method_relationship(java_analyzed_path, package_name, info, dep_graph)



def get_class_method_map():
    code_files = general_utils.get_code_files(config.target_project)
    file_code= {} 

    for file_path, file_type in code_files:
        try:
            tree, source_code = general_utils.get_tree(file_path)
            package = general_utils.get_package(tree, source_code, file_type)
            name = general_utils.get_class_interface_name(tree, source_code, file_type)
            if name :
                # 使用字典而不是集合，来存储 tree 和 source_code
                file_code[package + '.' + name] = {
                    'tree': tree,
                    'source_code': source_code,
                    'file_type': file_type
                }
        except Exception as e :
            print(e)

    class_method_map = {}
    for file in  file_code:
        methods = general_utils.get_all_method(file_code[file].get('tree'), file_code[file].get('source_code'), file_code[file].get('file_type'))
        class_method_map[file] = {
            'methods': methods
        }
    return class_method_map


import os
# 假设 config, DependencyGraph, general_utils, analyze_file, get_class_method_map 都已经在其他地方定义和导入



# Helper function to check if a class/method name belongs to the analysis packages
def is_in_analysis_packages(name: str, analysis_packages: list[str]) -> bool:
    """
    检查给定的类名或方法签名是否属于分析包列表中的任何一个。

    Args:
        name: 类名 (如 "com.package.ClassName") 或方法签名 (如 "com.package.ClassName.methodName").
        analysis_packages: 允许的包名前缀列表 (如 ["com.google.android.apps.youtube", "com.android.billingclient"]).

    Returns:
        如果 name 以 analysis_packages 中的任何一个前缀开头，则返回 True，否则返回 False。
        如果 analysis_packages 为空或 None，则始终返回 False (表示不允许任何包)。
    """
    if not analysis_packages:
        return False
    for package_prefix in analysis_packages:
        # 检查是否以包名前缀开头
        if name.startswith(package_prefix):
            return True
    return False

def filter_dependency_graph_by_package(dep_graph: DependencyGraph, analysis_packages: list[str]):
    """
    根据指定的分析包列表过滤依赖图 (class_graph 和 method_graph)。

    - 对于 class_graph:
        - 如果类名本身不在 analysis_packages 中，则移除该类的整个条目。
        - 如果类名在 analysis_packages 中，则移除其继承/实现的超类/接口列表中
          不在 analysis_packages 中的条目。
    - 对于 method_graph:
        - 如果调用方法的类不在 analysis_packages 中，则移除该方法调用的整个条目。
        - 如果调用方法的类在 analysis_packages 中，则移除其被调方法列表中
          被调方法所在的类不在 analysis_packages 中的条目。

    Args:
        dep_graph: 要过滤的 DependencyGraph 对象。
        analysis_packages: 允许的包名前缀列表。
    """
    print("\n--- 开始根据包列表过滤依赖图 ---")
    if not analysis_packages:
        print("警告: config.analysis_packages 为空。将移除所有类和方法条目。")
    else:
         print(f"分析包列表: {analysis_packages}")


    # --- 过滤 Class Graph ---
    print("阶段 1/2: 过滤类图 (class_graph)...")
    original_class_count = len(dep_graph.class_graph)
    filtered_class_graph = {}
    removed_class_entry_count = 0
    removed_superclass_count = 0 # 跟踪从保留的类中移除的超类数量

    # 迭代原始图的副本，以便安全修改
    for class_name, superclasses in list(dep_graph.class_graph.items()):
        # 规则 1: 如果类名本身不在分析包中，移除整个条目
        if not is_in_analysis_packages(class_name, analysis_packages):
            # print(f"  > 移除类条目 (自身不在分析包): {class_name}") # 调试用，可选
            removed_class_entry_count += 1
            continue # 跳过，不添加到 filtered_class_graph

        # 规则 2: 如果类名在分析包中，过滤其超类列表
        filtered_superclasses = []
        removed_count_for_this_class = 0
        for superclass in superclasses:
            if is_in_analysis_packages(superclass, analysis_packages):
                filtered_superclasses.append(superclass)
            else:
                # print(f"  > 移除超类 (不在分析包): {class_name} -> {superclass}") # 调试用，可选
                removed_count_for_this_class += 1

        # 保留类条目，使用过滤后的超类列表 (即使列表为空)
        filtered_class_graph[class_name] = filtered_superclasses
        removed_superclass_count += removed_count_for_this_class

    # 用过滤后的图替换原始图
    dep_graph.class_graph = filtered_class_graph
    print(f"类图过滤完成。原始类条目数: {original_class_count}, 移除的类条目数: {removed_class_entry_count}, 保留的类条目数: {len(dep_graph.class_graph)}.")
    print(f"从保留的类中移除了 {removed_superclass_count} 个超类/接口。")


    # --- 过滤 Method Graph ---
    print("\n阶段 2/2: 过滤方法图 (method_graph)...")
    original_method_count = len(dep_graph.method_graph)
    filtered_method_graph = {}
    removed_method_entry_count = 0
    removed_called_method_count = 0 # 跟踪从保留的调用方法中移除的被调方法数量

    # 迭代原始图的副本
    for calling_method, called_methods in list(dep_graph.method_graph.items()):
        # 从方法签名中提取类名 (假设格式如 ClassName.methodName)
        parts = calling_method.rsplit('.', 1)
        if len(parts) > 1:
            calling_class_name = parts[0]
        else:
            # 如果方法签名没有点 (不常见，但处理一下)，则整个名字当作类名
            calling_class_name = calling_method

        # 规则 1: 如果调用方法所在的类不在分析包中，移除整个条目
        if not is_in_analysis_packages(calling_class_name, analysis_packages):
            # print(f"  > 移除方法条目 (调用方类不在分析包): {calling_method}") # 调试用，可选
            removed_method_entry_count += 1
            continue # 跳过，不添加到 filtered_method_graph

        # 规则 2: 如果调用方法所在的类在分析包中，过滤其被调方法列表
        filtered_called_methods = []
        removed_count_for_this_method = 0
        for called_method in called_methods:
             # 从被调方法签名中提取类名
            parts = called_method.rsplit('.', 1)
            if len(parts) > 1:
                called_class_name = parts[0]
            else:
                # 如果被调方法签名没有点，整个名字当作类名
                called_class_name = called_method

            if is_in_analysis_packages(called_class_name, analysis_packages):
                filtered_called_methods.append(called_method)
            else:
                # print(f"  > 移除被调方法 (被调方类不在分析包): {calling_method} -> {called_method}") # 调试用，可选
                removed_count_for_this_method += 1

        # 保留方法条目，使用过滤后的被调方法列表 (即使列表为空)
        filtered_method_graph[calling_method] = filtered_called_methods
        removed_called_method_count += removed_count_for_this_method


    # 用过滤后的图替换原始图
    dep_graph.method_graph = filtered_method_graph
    print(f"方法图过滤完成。原始方法条目数: {original_method_count}, 移除的方法条目数: {removed_method_entry_count}, 保留的方法条目数: {len(dep_graph.method_graph)}.")
    print(f"从保留的调用方法中移除了 {removed_called_method_count} 个被调方法。")

    print("\n--- 依赖图根据包列表过滤完毕 ---")

# Helper function to check if a class/method name is in the exclusion packages
def is_in_exclusion_packages(name: str, exclusion_packages: list[str]) -> bool:
    """
    检查给定的类名或方法签名是否属于排除包列表中的任何一个。

    Args:
        name: 类名 (如 "com.package.ClassName") 或方法签名 (如 "com.package.ClassName.methodName").
        exclusion_packages: 要排除的包名前缀列表.

    Returns:
        如果 name 以 exclusion_packages 中的任何一个前缀开头，则返回 True，否则返回 False。
    """
    if not exclusion_packages:
        return False # 如果排除列表为空，则什么都不排除
    for package_prefix in exclusion_packages:
        if name.startswith(package_prefix):
            return True
    return False

def get_class_name_from_signature(name: str) -> str:
    """从方法签名中提取类名 (假设格式如 ClassName.methodName 或 ClassName)."""
    parts = name.rsplit('.', 1)
    if len(parts) > 1:
        # 可能是 ClassName.methodName
        return parts[0]
    else:
        # 可能是 ClassName
        return name

def filter_dependency_graph_by_exclusion(dep_graph: DependencyGraph, exclusion_packages: list[str]):
    """
    根据指定的排除包列表过滤依赖图 (class_graph 和 method_graph)。

    Args:
        dep_graph: 要过滤的 DependencyGraph 对象。
        exclusion_packages: 要排除的包名前缀列表。
    """
    print("\n--- 开始根据排除列表过滤依赖图 ---")
    if not exclusion_packages:
        print("警告: 排除包列表为空。将不进行任何过滤。")
        return

    print(f"排除包列表包含 {len(exclusion_packages)} 个前缀.")

    # --- 过滤 Class Graph ---
    print("阶段 1/2: 过滤类图 (class_graph)...")
    original_class_count = len(dep_graph.class_graph)
    filtered_class_graph = {}
    removed_class_entry_count = 0
    removed_superclass_count = 0

    # 迭代原始图的副本
    for class_name, superclasses in list(dep_graph.class_graph.items()):
        # 规则 1: 如果类名本身在排除包中，移除整个条目
        if is_in_exclusion_packages(class_name, exclusion_packages):
            # print(f"  > 移除类条目 (自身在排除包): {class_name}") # 调试用，可选
            removed_class_entry_count += 1
            continue

        # 规则 2: 如果类名不在排除包中，过滤其超类列表
        filtered_superclasses = []
        removed_count_for_this_class = 0
        for superclass in superclasses:
            if not is_in_exclusion_packages(superclass, exclusion_packages):
                filtered_superclasses.append(superclass)
            else:
                # print(f"  > 移除超类 (在排除包): {class_name} -> {superclass}") # 调试用，可选
                removed_count_for_this_class += 1

        # 保留类条目，使用过滤后的超类列表
        filtered_class_graph[class_name] = filtered_superclasses
        removed_superclass_count += removed_count_for_this_class

    dep_graph.class_graph = filtered_class_graph
    print(f"类图过滤完成。原始类条目数: {original_class_count}, 移除的类条目数: {removed_class_entry_count}, 保留的类条目数: {len(dep_graph.class_graph)}.")
    print(f"从保留的类中移除了 {removed_superclass_count} 个超类/接口。")


    # --- 过滤 Method Graph ---
    print("\n阶段 2/2: 过滤方法图 (method_graph)...")
    original_method_count = len(dep_graph.method_graph)
    filtered_method_graph = {}
    removed_method_entry_count = 0
    removed_called_method_count = 0

    # 迭代原始图的副本
    for calling_method, called_methods in list(dep_graph.method_graph.items()):
        # 提取调用方类名
        calling_class_name = get_class_name_from_signature(calling_method)

        # 规则 1: 如果调用方法所在的类在排除包中，移除整个条目
        if is_in_exclusion_packages(calling_class_name, exclusion_packages):
            # print(f"  > 移除方法条目 (调用方类在排除包): {calling_method}") # 调试用，可选
            removed_method_entry_count += 1
            continue

        # 规则 2: 如果调用方法所在的类不在排除包中，过滤其被调方法列表
        filtered_called_methods = []
        removed_count_for_this_method = 0
        for called_method in called_methods:
            # 提取被调方类名
            called_class_name = get_class_name_from_signature(called_method)

            if not is_in_exclusion_packages(called_class_name, exclusion_packages):
                filtered_called_methods.append(called_method)
            else:
                # print(f"  > 移除被调方法 (被调方类在排除包): {calling_method} -> {called_method}") # 调试用，可选
                removed_count_for_this_method += 1

        # 保留方法条目，使用过滤后的被调方法列表
        filtered_method_graph[calling_method] = filtered_called_methods
        removed_called_method_count += removed_count_for_this_method


    dep_graph.method_graph = filtered_method_graph
    print(f"方法图过滤完成。原始方法条目数: {original_method_count}, 移除的方法条目数: {removed_method_entry_count}, 保留的方法条目数: {len(dep_graph.method_graph)}.")
    print(f"从保留的调用方法中移除了 {removed_called_method_count} 个被调方法。")

    print("\n--- 依赖图根据排除列表过滤完毕 ---")


import json
import config
from utils import general_utils # Assuming utils is the correct module name
import os
from dependency_graph import DependencyGraph # Assuming dependency_graph is the correct module name
import traceback # Added for detailed error reporting in __main__

# Assuming the following functions are already defined and present in your code:
# is_in_analysis_packages        # Used for external filtering (if config.filter_mode is True)
# is_in_exclusion_packages       # Used for external filtering (if config.filter_mode is True)
# get_class_name_from_signature  # Used for filtering class_method_map
# analyze_extend_relationship    # Your original version with internal package_name check
# analyze_method_relationship   # Your original version with internal package_name check
# analyze_file                   # Calls the two analysis functions above
# get_class_method_map           # Gets method map for ALL classes in target_project
# filter_dependency_graph_by_package   # Filters dep_graph based on inclusion list (if config.filter_mode is True)
# filter_dependency_graph_by_exclusion # Filters dep_graph based on exclusion list (if config.filter_mode is True)


# --- New Reachability Filtering Function ---
from collections import deque # Needed for BFS traversal


def is_activity_class(class_name: str, class_graph: dict) -> bool:
    """
    检查一个类是否通过继承链是 Activity (继承自 android.app.Activity 或 androidx.appcompat.app.AppCompatActivity)。

    Args:
        class_name: 要检查的类的完整名称。
        class_graph: 类继承关系字典 {class_name: [superclass1, ...], ...}。
                     这个字典应该反映了经过前期过滤后的图的继承关系。

    Returns:
        如果是 Activity 类则返回 True，否则返回 False。
    """
    # Basic checks for the base Activity classes themselves
    if class_name in {"android.app.Activity", "androidx.appcompat.app.AppCompatActivity"}:
        return True

    # Use BFS to traverse up the inheritance hierarchy defined in class_graph
    queue = deque([class_name])
    visited = {class_name} # Track visited classes to prevent infinite loops in case of cycles

    while queue:
        current_class = queue.popleft()

        # Get superclasses for the current class from the provided class_graph
        # Use .get() with default empty list, as a class might be in visited but not in class_graph keys (e.g., Object)
        superclasses = class_graph.get(current_class, [])

        for superclass in superclasses:
            # Check if the superclass is one of the target Activity base classes (using full names)
            if superclass in {"android.app.Activity", "androidx.appcompat.app.AppCompatActivity"}:
                return True # Found a base Activity class in the hierarchy

            # If the superclass is java.lang.Object, we can stop this specific inheritance branch,
            # as Activity does not inherit from Object in the way we're checking.
            if superclass == "java.lang.Object":
                continue # Do not add Object to the queue for further traversal UP

            # Add the superclass to the queue if not visited, to continue traversal
            if superclass not in visited:
                visited.add(superclass)
                queue.append(superclass)

    # If the queue is empty and we haven't found Activity, it's not an Activity class via this graph
    return False


def apply_activity_reachability_filter(dep_graph: DependencyGraph, full_class_method_map: dict, config_obj, full_inheritance_map: dict):
    """
    根据从 Activity 类方法开始的可达性过滤依赖图。
    使用完整的继承关系判断哪些类是 Activity。
    如果未找到起始 Activity，则不修改传入的依赖图。

    Args:
        dep_graph: 要过滤的 DependencyGraph 对象 (通常是加载后的 loaded_graph)。
                   其 class_graph 必须包含经过前期过滤的继承关系信息。
                   此对象将被就地修改。
        full_class_method_map: 完整的类-方法映射 (在过滤 class_method_map 之前获取的)。
        config_obj: 配置对象 (用于获取 target_package 或 analysis_packages)。
        full_inheritance_map: 完整的类继承关系字典 {full_class_name: [full_superclass_name, ...], ...}。
                              用于准确判断类是否为 Activity，不应受前期过滤影响。
    """
    print("\n--- 开始应用 Activity 可达性过滤 ---")

    # 步骤 1: 确定分析的起点 - 找到所有属于目标范围内的 Activity 类 (基于完整的继承关系)
    analysis_scopes = getattr(config_obj, 'analysis_packages', [])
    if not analysis_scopes and hasattr(config_obj, 'target_package'):
        analysis_scopes = [config_obj.target_package]

    start_activity_classes = set()
    # Iterate through classes that were already kept in the dependency graph's class_graph by previous filters (e.g., the 11 classes)
    # These are candidates for starting points.
    for class_name in dep_graph.class_graph.keys():
        # Check if this class is an Activity based on its *full* inheritance chain using the full_inheritance_map
        if is_activity_class(class_name, full_inheritance_map): # Use full_inheritance_map for the check
            # Further check if it falls within the configured analysis scopes (if any are defined)
            if not analysis_scopes or is_in_analysis_packages(class_name, analysis_scopes):
                 start_activity_classes.add(class_name)


    if not start_activity_classes:
        # >>>>> MODIFIED: Do NOT clear dep_graph here. Just print warning and return. <<<<<
        print("警告: 未找到符合条件的起始 Activity 类 (在现有依赖图中，通过完整继承判断)。跳过可达性过滤，保留原图状态。")
        return # Exit the function early, leaving dep_graph unchanged.
        # >>>>> END MODIFIED <<<<<

    print(f"找到 {len(start_activity_classes)} 个潜在的起始 Activity 类 (在现有依赖图中，通过完整继承判断).")

    # 步骤 2: 收集起点 Activity 类的所有方法签名，作为遍历的初始集合
    reachable_methods = set()
    method_queue = deque()

    for activity_class_name in start_activity_classes:
        methods_list = full_class_method_map.get(activity_class_name, {}).get('methods', [])

        for method_info_element in methods_list:
             method_signature = None
             if isinstance(method_info_element, dict):
                 method_name = method_info_element.get('name')
                 method_signature = method_info_element.get('signature', f"{activity_class_name}.{method_name}" if method_name else None)
             elif isinstance(method_info_element, str):
                 method_name = method_info_element # Treat string as method name
                 method_signature = f"{activity_class_name}.{method_name}" # Construct signature
             else:
                 print(f"Warning: Unexpected method info format for class {activity_class_name}: element type {type(method_info_element)} - {method_info_element}. Skipping.")
                 continue

             if method_signature:
                if method_signature not in reachable_methods:
                    reachable_methods.add(method_signature)
                    method_queue.append(method_signature)


    if not reachable_methods:
         # >>>>> MODIFIED: Do NOT clear dep_graph here. Just print warning and return. <<<<<
         print("警告: 起始 Activity 类中未找到任何方法可用于遍历 (检查 get_class_method_map 返回结构及方法命名)。跳过可达性过滤，保留原图状态。")
         return # Exit the function early, leaving dep_graph unchanged.
         # >>>>> END MODIFIED <<<<<


    print(f"从起始 Activity 类开始，找到 {len(reachable_methods)} 个初始方法用于遍历.")


    # 步骤 3: 从初始方法开始，在依赖图 (method_graph) 上进行 BFS 遍历
    # This part traverses the graph *as it is* after previous filters.
    print("正在通过方法调用图进行可达性遍历...")
    visited_methods = set(reachable_methods)

    while method_queue:
        current_method_signature = method_queue.popleft()
        # Look up called methods in the *current filtered* dep_graph
        called_methods_list = dep_graph.method_graph.get(current_method_signature, [])

        for called_method_signature in called_methods_list:
            if called_method_signature not in visited_methods:
                visited_methods.add(called_method_signature)
                reachable_methods.add(called_method_signature)
                method_queue.append(called_method_signature)

    print(f"可达性遍历完成。总计找到 {len(reachable_methods)} 个可达方法.")

    # 4. 根据可达方法，确定需要保留的类
    reachable_classes = set()
    for method_signature in reachable_methods:
        class_name = get_class_name_from_signature(method_signature)
        reachable_classes.add(class_name)

    print(f"总计找到 {len(reachable_classes)} 个包含可达方法的类.")


    # 5. 过滤依赖图 (dep_graph) - 保留可达的类和它们之间的可达依赖
    # This part modifies dep_graph based on the results of the traversal (reachable_methods/classes)
    print("正在根据可达性过滤依赖图结构...")

    # 过滤 class_graph - Keep only classes that are reachable AND were already in the graph
    original_class_graph_count = len(dep_graph.class_graph)
    new_class_graph = {}
    removed_class_graph_entries = 0
    # Iterate through classes that were in the graph *before* this filter
    for class_name, superclasses in list(dep_graph.class_graph.items()): # Iterate over a copy
        # Keep the class if it's in the set of reachable classes
        if class_name in reachable_classes:
            # Filter superclasses to keep only those that are also reachable classes AND were in original superclasses list
            # This ensures edges are only kept if both nodes are reachable and the edge existed pre-filter
            filtered_superclasses = [sc for sc in superclasses if sc in reachable_classes] # Removed 'and sc in dep_graph.class_graph' check here, it's redundant
            new_class_graph[class_name] = filtered_superclasses
        else:
            removed_class_graph_entries += 1

    dep_graph.class_graph = new_class_graph
    print(f"类图过滤完成。移除了 {removed_class_graph_entries} 个条目, 保留 {len(dep_graph.class_graph)} 个.")


    # 过滤 method_graph - Keep only methods/edges that are reachable
    original_method_graph_count = len(dep_graph.method_graph)
    new_method_graph = {}
    removed_method_graph_entries = 0
    removed_method_graph_edges = 0

    # Iterate through the original method_graph (before this filter)
    for calling_method_signature, called_methods_list in list(dep_graph.method_graph.items()): # Iterate over a copy
        # Only consider this calling method entry if the calling method itself is reachable
        if calling_method_signature in reachable_methods:
             filtered_called_methods = []
             removed_edges_for_this_method = 0
             for called_method_signature in called_methods_list:
                 # Only keep the edge if the called method is also reachable
                 if called_method_signature in reachable_methods:
                    filtered_called_methods.append(called_method_signature)
                 else:
                    removed_edges_for_this_method += 1

             # Keep the calling method entry if it was reachable.
             # We add it to new_method_graph even if the filtered_called_methods list is empty.
             new_method_graph[calling_method_signature] = filtered_called_methods
             removed_method_graph_edges += removed_edges_for_this_method
        else:
            removed_method_graph_entries += 1


    dep_graph.method_graph = new_method_graph
    print(f"方法图过滤完成。移除了 {removed_method_graph_entries} 个调用方法条目。移除了 {removed_method_graph_edges} 条方法调用边。保留 {len(dep_graph.method_graph)} 个调用方法条目.")

    print("\n--- Activity 可达性过滤应用完毕 ---")



def analyzer_app():
    """
    主分析函数，用于构建和处理应用程序的依赖图。
    包含文件扫描、依赖构建 (含分析函数内部过滤)、图的外部过滤 (如果config启用)、
    Activity可达性过滤 (基于完整继承信息)、方法映射获取和**基于最终图的过滤**，以及后续图处理步骤。
    """
    print("--- 开始执行 analyzer_app 函数 ---")
    print("阶段 1/5: 初始化和文件收集...")

    package_name = config.target_package
    dep_graph = DependencyGraph()
    print(f"目标包名设置为: {package_name}")
    print("初始化依赖图对象.")

    print(f"正在递归获取保存路径 '{config.save_path}' 下的所有文件夹...")
    java_analysis_dirs = general_utils.get_all_folders_recursively(config.save_path)
    print(f"成功获取到 {len(java_analysis_dirs)} 个潜在的目录/文件条目.")

    # >>>>> NEW: Get the full inheritance map from the analysis results early <<<<<<
    print("\n正在扫描分析结果以提取完整的类继承关系...")
    full_inheritance_map = scan_and_extract_class_info(config.save_path) # Assumes scan_and_extract_class_info returns {full_class_name: [full_superclass_name, ...]}
    print(f"完成扫描继承关系。总计 {len(full_inheritance_map)} 个类条目.")
    # >>>>> END NEW <<<<<<


    # --- 阶段 2: 逐个分析文件/目录以构建初始依赖图 (包含分析函数内部过滤) ---
    print("\n阶段 2/5: 逐个分析符合条件的目录并构建初始依赖图 (含分析函数内部过滤)...")
    processed_count = 0
    skipped_count = 0

    for i, file_path in enumerate(java_analysis_dirs):
        if (i + 1) % 100 == 0 or (i + 1) == len(java_analysis_dirs):
             print(f"  > 正在处理分析目录 {i + 1}/{len(java_analysis_dirs)}: {file_path}/")

        if not os.path.isdir(file_path) or 'class_info.json' not in os.listdir(file_path):
            skipped_count += 1
            continue

        analyze_file(file_path + '/', package_name, dep_graph) # analyze_file uses package_name for internal filtering
        processed_count += 1

    print(f"阶段 2 完成。成功分析了 {processed_count} 个目录，跳过了 {skipped_count} 个条目.")
    print(f"分析函数内部过滤后 - 初始依赖图构建完毕。类图条目数: {len(dep_graph.class_graph)}, 方法图条目数: {len(dep_graph.method_graph)}")


    # --- 阶段 3: 进一步过滤依赖图 (如果config启用) ---
    print("\n阶段 3/5: 进一步过滤依赖图 (外部包过滤)...")
    if hasattr(config, 'filter_mode') and config.filter_mode is True:
        print("config.filter_mode is True. Applying external dependency graph filters.")
        if hasattr(config, 'analysis_packages') and config.analysis_packages:
             print(f"分析包列表 (外部包含过滤): {config.analysis_packages}")
             filter_dependency_graph_by_package(dep_graph, config.analysis_packages)
             print(f"外部包含过滤后 - 类图条目数: {len(dep_graph.class_graph)}, 方法图条目数: {len(dep_graph.method_graph)}")
        else:
             print("Warning: config.analysis_packages is not set or empty. External inclusion filter skipped.")

        if hasattr(config, 'EXCLUSION_PACKAGES') and config.EXCLUSION_PACKAGES:
             filter_dependency_graph_by_exclusion(dep_graph, config.EXCLUSION_PACKAGES)
             print(f"外部排除过滤后 - 类图条目数: {len(dep_graph.class_graph)}, 方法图条目数: {len(dep_graph.method_graph)}")
        else:
             print("Warning: config.EXCLUSION_PACKAGES is not set or empty. External exclusion filter skipped.")
    else:
        print("config.filter_mode is False or not set. Skipping external dependency graph filtering.")

    # At this point, 'dep_graph' contains the dependencies that passed both internal and external filtering.

    # Save the current filtered dependency graph state before reachability filtering
    current_graph_state_filename = 'dependency_graph_current_filtered.json'
    print(f"正在保存当前过滤后的依赖图状态到 '{current_graph_state_filename}' 文件...")
    dep_graph.save_graph(current_graph_state_filename)
    print("当前过滤后的依赖图状态保存完毕.")

    # Load the graph back to operate on 'loaded_graph' as in your original flow
    print(f"正在从 '{current_graph_state_filename}' 文件加载当前过滤后的依赖图...")
    loaded_graph = DependencyGraph.load_graph(current_graph_state_filename)
    print("当前过滤后的依赖图加载完毕.")
    print(f"加载后 - 类图条目数: {len(loaded_graph.class_graph)}, 方法图条目数: {len(loaded_graph.method_graph)}")


    # Get the full class-method map from source files (needed for method lists of starting Activities)
    print("\n正在收集所有类的详细方法信息 (class_method_map) 从源文件...")
    full_class_method_map = get_class_method_map() # Renamed to avoid confusion
    print(f"原始类-方法映射获取完毕。总计 {len(full_class_method_map)} 个类条目.")


    # --- 阶段 4: 应用 Activity 可达性过滤 ---
    print("\n阶段 4/5: 应用 Activity 可达性过滤...")

    # Apply the reachability filter to the loaded graph, using the full inheritance map for the check
    # The function is modified to NOT clear the graph if no starting Activity is found.
    apply_activity_reachability_filter(loaded_graph, full_class_method_map, config, full_inheritance_map) # <-- **传入 full_inheritance_map**

    # Check if the graph is empty after reachability filtering (or because no starting points were found)
    if not loaded_graph.class_graph and not loaded_graph.method_graph:
         print("\n警告: 依赖图在 Activity 可达性过滤后为空。跳过后续的图处理和 LLM 调用阶段。")
         # Exit the function or return here if the rest of the process requires a non-empty graph
         # For now, we'll continue but the subsequent steps might do nothing or error out gracefully.
         # You might want to add a 'return' here depending on desired behavior.
         pass # Continue to next phase even if graph is empty

    print(f"Activity 可达性过滤后 - 类图条目数: {len(loaded_graph.class_graph)}, 方法图条目数: {len(loaded_graph.method_graph)}")


    # --- 阶段 5: 过滤类方法映射并进行后续处理 ---
    print("\n阶段 5/5: 过滤类方法映射并进行后续处理...")

    # Now filter the full_class_method_map based on the classes present in the *final* loaded_graph (after reachability filtering)
    print("正在根据最终过滤依赖图过滤类-方法映射...")

    # Identify all unique fully qualified class names that are present as nodes in the final loaded (filtered) graph.
    allowed_classes_in_graph = set()
    allowed_classes_in_graph.update(loaded_graph.class_graph.keys())
    allowed_classes_in_method_graph_keys = set(get_class_name_from_signature(method_sig) for method_sig in loaded_graph.method_graph.keys())
    allowed_classes_in_graph.update(allowed_classes_in_method_graph_keys)
    allowed_classes_in_method_graph_values = set()
    for called_methods_list in loaded_graph.method_graph.values():
        # Corrected nested loop syntax
        for method_sig in called_methods_list:
             allowed_classes_in_method_graph_values.add(get_class_name_from_signature(method_sig))
    allowed_classes_in_graph.update(allowed_classes_in_method_graph_values)


    print("可达性过滤后，保留在依赖图中的类:")
    print(allowed_classes_in_graph)

    filtered_class_method_map = {}
    removed_map_entries_count = 0

    for class_name, methods_list in full_class_method_map.items():
        if class_name in allowed_classes_in_graph:
             filtered_class_method_map[class_name] = methods_list
        else:
             removed_map_entries_count += 1

    loaded_graph.class_method_map = filtered_class_method_map
    print(f"类-方法映射过滤完毕。移除了 {removed_map_entries_count} 个类条目, 保留 {len(loaded_graph.class_method_map)} 个.")

    print("阶段 5 完成.")

    # --- 阶段 6: 图的进一步处理 and LLM调用 ---
    print("\n阶段 4/4 (处理): 图的进一步处理和LLM调用...")

    # Add a check here: only proceed with graph processing if the graph is not empty
    if not loaded_graph.class_graph and not loaded_graph.method_graph:
         print("依赖图为空，跳过基节点初始化、循环移除和并发方法图处理。")
    else:
        print("正在初始化依赖图的基节点...")
        loaded_graph.init_base_node()
        print("基节点初始化完毕.")

        print("正在移除依赖图中的循环...")
        loaded_graph.remove_cycle()
        print("循环移除完毕.")

        print("正在启动并发方法图处理 (可能涉及LLM调用、LLM可能会查询 loaded_graph.class_method_map)...")
        loaded_graph.process_method_graph_with_llm_concurrent()
        print("并发方法图处理完成.")

    print("阶段 4 (处理) 完成.")

    print("--- analyzer_app 函数执行完毕 ---")

if __name__ == '__main__':



    # java_analyzed_path = "./program_analysis_results/it/feio/android/omninotes/MainActivity/"
    # package_name = 'it.feio.android.omninotes'
    package_name = config.target_package
    dep_graph = DependencyGraph()
    # analyze_file(java_analyzed_path,package_name,dep_graph)
    java_files = general_utils.get_all_folders_recursively(config.save_path)
    for file in java_files:
        # Check if 'file' is a directory and contains 'class_info.json'
        if not os.path.isdir(file) or 'class_info.json' not in os.listdir(file):
            continue
        analyze_file(file + '/', package_name, dep_graph)
    class_method_map = get_class_method_map()
    # print(class_method_map)
    dep_graph.save_graph('dependency_graph.json')
    loaded_graph = DependencyGraph.load_graph("dependency_graph.json")
    # class_method_map = utils.get_class_method_map()
    class_method_map = general_utils.get_class_method_map()

    loaded_graph.class_method_map = class_method_map
    loaded_graph.init_base_node()
    loaded_graph.remove_cycle()
    # # 打印图内容
    # print("Class Graph:")
    # print(json.dumps(loaded_graph.class_graph, indent=4))

    # print("Method Graph:")
    # print(json.dumps(loaded_graph.method_graph, indent=4))

    # 并发处理 Class Graph
    # print("Processing Class Graph:")

    loaded_graph.process_method_graph_with_llm_concurrent()

