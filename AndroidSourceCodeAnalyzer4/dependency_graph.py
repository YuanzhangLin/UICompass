import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import llm
from utils import general_utils
import prompt
import config
import os

class DependencyGraph:
    def __init__(self):
        self.class_graph = {}
        self.method_graph = {}
        self.marked_class_nodes = set()  # 用于标记已经标注的节点
        self.marked_method_nodes = set()  # 用于标记已经标注的节点
        self.class_method_map = {} # 保存了每个class以及它所拥有的method。
        self.base_class_nodes = set()
        self.base_method_nodes = set()
        self.unreferenced_classes = set()
        self.unreferenced_methods = set()

    def add_class_dependency(self, class_name, extends_class):
        if extends_class is None:
            return
        if class_name not in self.class_graph:
            self.class_graph[class_name] = []
        # Avoid duplicates by checking if the class already depends on the extends_class
        if extends_class not in self.class_graph[class_name]:
            self.class_graph[class_name].append(extends_class)

    def add_method_dependency(self, method_name, called_method):
        if called_method is None:
            return
        if method_name not in self.method_graph:
            self.method_graph[method_name] = []
        # Avoid duplicates by checking if the method already calls the called_method
        if called_method not in self.method_graph[method_name]:
            self.method_graph[method_name].append(called_method)

    def save_graph(self, file_path):
        graph = {
            "class_graph": self.class_graph,
            "method_graph": self.method_graph
        }
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(graph, file, indent=4, ensure_ascii=False)

    # 模拟调用 LLM 的函数
    def call_llm(self, node):
        """
        模拟处理节点的函数
        :param node: 当前处理的节点
        """

        print(f"Processing node: {node}")
        prom = prompt.make_prompt(node, self.method_graph)
        answer = llm.quert_llm(prom)
        print(prom)
        print('---------------answer by llm -------------')
        print(answer)
        general_utils.save_string_as_json(general_utils.extract_json_from_answer(answer), config.save_path + node.replace('.','/') + '.json')

    def init_base_node(self):
        self.init_class_base_node()
        self.init_method_base_node()

    def init_class_base_node(self):
        self.base_class_nodes = set()
        # for node, dependencies in self.class_graph.items():
        #     self.base_class_nodes.add(node)
        #     for dep in dependencies:
        #         self.base_class_nodes.add(dep)

        for _class in self.class_method_map:
            self.base_class_nodes.add(_class)
        # 遍历 class_graph 中的所有节点，移除不在 base_class_nodes 中的节点
        nodes_to_remove = [node for node in self.class_graph if node not in self.base_class_nodes]
        
        for node in nodes_to_remove:
            del self.class_graph[node]
        # 删除所有依赖于这些被删除节点的边，并清理空的依赖关系
        for node, dependencies in list(self.class_graph.items()):
            self.class_graph[node] = [dep for dep in dependencies if dep in self.base_class_nodes]
            
        # 清理掉所有没有依赖关系的节点
        self.class_graph = {node: deps for node, deps in self.class_graph.items() if deps}

    def init_method_base_node(self):
        self.base_method_nodes = set()
        # for node, dependencies in self.method_graph.items():
        #     self.base_method_nodes.add(node)
        #     for dep in dependencies:
                # self.base_method_nodes.add(dep)
        for _class in self.class_method_map:
            for _method in self.class_method_map[_class]['methods']:
                self.base_method_nodes.add(_class + '.' + _method)
        # 遍历 method_graph 中的所有方法节点，移除不在 base_method_nodes 中的节点
        methods_to_remove = [node for node in self.method_graph if node not in self.base_method_nodes]
        for method in methods_to_remove:
            del self.method_graph[method]        

        # 删除所有依赖这些被删除节点的边    
        for method, dependencies in list(self.method_graph.items()):
            # 过滤掉依赖于已删除方法节点的边
            self.method_graph[method] = [dep for dep in dependencies if dep in self.base_method_nodes]
            
        # 清理掉没有依赖关系的节点（空的依赖关系）
        self.method_graph = {method: deps for method, deps in self.method_graph.items() if deps}

    def update_unreferenced_classes(self):
        referenced_nodes = set()
        for node, dependencies in self.class_graph.items():
            no_depend = True
            for dep in dependencies:
                if dep not in self.marked_class_nodes:
                    no_depend = False
            if not no_depend:
                self.unreferenced_classes.add(node)  # 记录所有被依赖的节点
        # 返回那些没有被依赖的节点，且不在已标注节点中的节点
        temp_list = [node for node in self.base_class_nodes if node not in referenced_nodes and  node not in self.marked_class_nodes]  
        self.unreferenced_classes = set()

        for item in temp_list:
            self.unreferenced_classes.add(item)
        return  self.unreferenced_classes


    # 获取没有被依赖的method
    def update_unreferenced_methods(self):
        # 初始化所有节点的被依赖计数（入度）为 0
        referenced_nodes = set() 
        # 遍历图，统计每个节点是否被其他节点依赖
        for node, dependencies in self.method_graph.items():
            no_depend = True
            for dep in dependencies:
                if dep not in self.marked_method_nodes:
                    no_depend = False
            if  not no_depend:
                referenced_nodes.add(node)  # 记录所有被依赖的节点
        # 返回那些没有被依赖的节点，且不在已标注节点中的节点
        temp_list = [node for node in self.base_method_nodes if node not in referenced_nodes and  node not in self.marked_method_nodes]
        # 去掉class还没有准备好的method。
        self.unreferenced_methods = set()
        for node in temp_list:
            if node.rsplit('.',1)[0] in self.unreferenced_classes:
                self.unreferenced_methods.add(node)
        for method in self.base_method_nodes:
            if method not in self.method_graph and method not in self.marked_method_nodes:
                self.unreferenced_methods.add(method)
        return self.unreferenced_methods


    # 标注节点，使其在获取没有被依赖的节点时不被考虑
    def mark_class_node(self, node):
        """
        标注节点，确保在后续查询没有被依赖的节点时排除此节点
        :param node: 要标注的节点
        """
        self.marked_class_nodes.add(node)

    def mark_method_node(self, node):
        self.marked_method_nodes.add(node)

    def mark_class_node_auto(self):
        # 如果一个class的所有method都被处理了，那就释放它。
        for _class in self.base_class_nodes:
            if _class in self.marked_class_nodes:
                continue
            else:
                unlabel = False
                for method in  self.class_method_map[_class]["methods"]:
                    method_name = _class + '.' + method
                    if method_name not in self.marked_class_nodes:
                        unlabel = True
                if not unlabel:
                    self.marked_class_nodes.add(_class)

    def remove_cycle(self):
        has_cycle = True
        while(has_cycle):
            has_cycle = self.has_cycle(self.method_graph)
        has_cycle = True
        while(has_cycle):
            has_cycle = self.has_cycle(self.class_graph)

    def has_cycle(self, graph):
        """
        判断图是否有环，并打印环的路径
        :param graph: 字典类型的图, 键为节点，值为该节点的邻居节点列表
        :return: 如果图中有环，返回 True；否则返回 False
        """
        visited = {}  # 存储节点是否访问过
        recursion_stack = {}  # 存储节点是否在当前递归栈中
        path_stack = []  # 记录当前递归路径上的节点，用来构建环
        parent_map = {}  # 用于记录每个节点的父节点，帮助删除环中的边

        # 初始化所有节点为未访问
        for node in graph:
            visited[node] = False
            recursion_stack[node] = False
            for n in graph[node]:
                visited[n] = False
                recursion_stack[n] = False
                parent_map[node] = None  # 初始化父节点为 None

        def dfs(node):
            # 如果当前节点已经在递归栈中，说明有环
            if recursion_stack[node]:
                # 找到环后，构建环路径并打印
                cycle = []
                cycle_start = path_stack.index(node)
                cycle.extend(path_stack[cycle_start:])
                # 删除环中的一条边
                # 这里选择删除路径栈中的第一个节点与其父节点之间的边
                cycle_edge_start = path_stack[cycle_start]
                cycle_edge_end = parent_map[cycle_edge_start]  # 获取父节点
                if cycle_edge_end in graph[cycle_edge_start]:
                    graph[cycle_edge_start].remove(cycle_edge_end)  # 删除边
                    # print(f"Edge ({cycle_edge_start}, {cycle_edge_end}) has been removed.")  # 打印删除的边
                elif len(cycle) == 1:
                    # 自环
                    graph[cycle_edge_start].remove(cycle_edge_start)
                    # print(f"Edge ({cycle_edge_start}, {cycle_edge_start}) has been removed.")  # 打印删除的边
                else: 
                    # 环在cycle数组的开头- 删除最后一个的边。
                    graph[cycle[-1]].remove(cycle_edge_start)
                return True
            if visited[node]:
                return False

            # 将当前节点标记为已访问并加入递归栈
            visited[node] = True
            recursion_stack[node] = True
            path_stack.append(node)  # 将当前节点添加到递归路径栈中

            # 递归遍历邻居节点
            if node in graph:
                for neighbor in graph[node]:
                    if dfs(neighbor):
                        return True

            # 回溯时将节点从递归栈中移除，并从路径栈中移除
            recursion_stack[node] = False
            path_stack.pop()  # 从路径栈中移除当前节点
            return False

        # 对图中的每个节点进行 DFS 遍历
        for node in graph:
            if not visited[node]:
                if dfs(node):
                    return True

        return False




    def process_method_graph_with_llm_concurrent(self, max_workers=10):
        # 初始化未处理的method集合
        unprocessed_method_node = self.base_method_nodes
        print('-------------------unprocessed_method_node')
        print(unprocessed_method_node)
        print(len(unprocessed_method_node))
        processed_method_node = set()

        continue_generate = True
        # 定义一个方法用于处理每个method
        def process_method(method):
            self.call_llm(method)  # 调用LLM
            self.mark_method_node(method)  # 标记方法节点
        remain_size = len(unprocessed_method_node)
        # 创建一个线程池执行器
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while unprocessed_method_node:
                print(len(unprocessed_method_node))
                self.mark_class_node_auto()  # 更新class的标注
                self.update_unreferenced_classes()  # 更新可以处理的class的列表
                self.update_unreferenced_methods()  # 更新可以处理的method的列表
                # 将方法分配到线程池中并发执行
                futures = []
                #
                if not self.unreferenced_methods and unprocessed_method_node:
                    # 如果沒有unferenced_method並且有unprocess_method，可能是有循環或者別的原因，強行破圈：
                    unprocessed_method_node_list = list(unprocessed_method_node)
                    first_element = unprocessed_method_node_list[0]  # 访问第一个元素
                    self.unreferenced_methods.add(first_element)
                for method in self.unreferenced_methods:
                    if continue_generate:
                        path = config.save_path + method.replace(".", "/") + ".json"
                        # 检查路径是否存在
                        # if 'refreshMenus' not in path: #os.path.exists(path) or 
                        # print('===================')
                        # if 'MainActivity' in path:
                        #     print(path)

                        if os.path.exists(path) :#or 'onRestoreInstanceState' in path or 'processDataIfReady' in path
                            try:
                                unprocessed_method_node.remove(method)
                                processed_method_node.add(method)
                                self.mark_method_node(method)
                            except Exception as e:
                                print(e)
                            continue
                        else:
                            print(path)
                        # 如果路径存在，跳过当前循环
    
                    futures.append(executor.submit(process_method, method))  # 提交任务到线程池
                    # break
                # 等待所有任务完成并处理结果
                for future in as_completed(futures):
                    method = future.result()  # 获取返回值，如果有的话
                    # return
                    # 当任务完成后，从unprocessed_method_node中移除该method
                    try:
                        unprocessed_method_node.remove(method)
                        processed_method_node.add(method)
                        print('remove method........', method)
                    except Exception as e :
                        print(e)
                # if continue_generate:
                #     for method in processed_method_node:
                #         if 'refreshMenus' in processed_method_node:
                #             return
                # 如果需要的话，可以在每轮循环结束后更新class标注等
                self.mark_class_node_auto()  # 更新class的标注
                print(len(unprocessed_method_node))

                # if remain_size != len(unprocessed_method_node):
                #     remain_size = len(unprocessed_method_node)
                # else:
                #     print('return from here')
                #     return

    @staticmethod
    def load_graph(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            graph = json.load(file)
        dep_graph = DependencyGraph()
        dep_graph.class_graph = graph.get("class_graph", {})
        dep_graph.method_graph = graph.get("method_graph", {})
        return dep_graph
    

if __name__ == '__main__':
    print('------------------')
    # 创建图对象
    dep_graph = DependencyGraph()

    # 添加类依赖关系
    dep_graph.add_class_dependency("MainActivity", "SomeCustomClass")

    # 添加方法调用关系
    dep_graph.add_method_dependency("MainActivity.onCreate", "MainActivity.initViews")
    dep_graph.add_method_dependency("MainActivity.initViews", "BaseActivity.loadData")

    # # **添加孤立节点**
    # dep_graph.class_graph["NewClass1"] = []  # 添加孤立节点到 class_graph
    # dep_graph.class_graph["NewClass2"] = []  # 添加孤立节点到 class_graph
    # dep_graph.method_graph["NewMethod1"] = []  # 添加孤立节点到 method_graph
    # dep_graph.method_graph["NewMethod2"] = []  # 添加孤立节点到 method_graph

    # # 标注某些节点
    # dep_graph.mark_node("NewClass1")
    # dep_graph.mark_node("NewMethod2")

    # 获取没有被依赖的节点，排除被标注的节点
    # unreferenced_classes = dep_graph.get_unreferenced_nodes(dep_graph.class_graph)
    # unreferenced_methods = dep_graph.get_unreferenced_nodes(dep_graph.method_graph)

    # print("Unreferenced Classes:", unreferenced_classes)
    # print("Unreferenced Methods:", unreferenced_methods)

    # 保存图到文件
    dep_graph.save_graph("./output/dependency_graph.json")
    loaded_graph = DependencyGraph.load_graph("./output/dependency_graph.json")

    # class_method_map模拟

    class_method_map = {
        "MainActivity": ["MainActivity.onCreate", "MainActivity.initViews"],
        "BaseActivity": ["BaseActivity.BaseMethod"],  # 确保每个类都对应有方法列表
        "SomeCustomClass": ["SomeCustomClass.loadData"],
        "TestActivity": ["TestActivity.testMethod"]
    }


    # 打印图内容
    print("Class Graph:")
    print(json.dumps(loaded_graph.class_graph, indent=4))
    print("Method Graph:")
    print(json.dumps(loaded_graph.method_graph, indent=4))
    print(loaded_graph.class_method_map)
    loaded_graph.class_method_map =class_method_map
    loaded_graph.init_base_node()

    loaded_graph.process_method_graph_with_llm_concurrent()