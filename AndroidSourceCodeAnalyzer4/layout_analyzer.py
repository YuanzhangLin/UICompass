import os
import xml.etree.ElementTree as ET
import json
import re
from CodeMap import Layout, Element

class LayoutMenuAnalyzer:
    def __init__(self, layout_dir, menu_dir, strings_dir=None, xml_dir=None):
        self.layout_dir = layout_dir
        self.menu_dir = menu_dir
        self.strings_dir = strings_dir
        self.xml_dir = xml_dir
        self.layout_files = []  # 存储解析的布局文件数据
        self.menu_files = []    # 存储解析的菜单文件数据
        self.layout_dependencies = {}  # 布局文件依赖关系
        self.strings_files = []  # 存储解析的字符串文件数据
        self.xml_files = []  # 存储解析的其他 XML 文件数据

    def init(self):
        self.parse_layout_files()
        self.parse_menu_files()
        self.parse_strings_files()
        self.parse_xml_files()


    def parse_strings_files(self):
        """
        解析 strings 文件夹中的所有字符串 XML 文件，提取字符串资源。
        """
        for root, _, files in os.walk(self.strings_dir):
            for file in files:
                if file.endswith(".xml"):
                    strings_file_path = os.path.join(root, file)
                    self.strings_files.append(self.parse_strings_file(strings_file_path))

    def parse_xml_files(self):
        """
        解析 xml 文件夹中的所有 XML 文件，提取元素和它们的属性。
        """
        for root, _, files in os.walk(self.xml_dir):
            for file in files:
                if file.endswith(".xml"):
                    xml_file_path = os.path.join(root, file)
                    self.xml_files.append(self.parse_xml_file(xml_file_path))


    def parse_strings_file(self, strings_file_path):
            """
            解析单个 strings 文件，递归提取所有 <string> 元素的字符串资源。
            """
            def _recursive_parse(current_node, strings_data):
                """
                递归遍历 XML 树，找到所有 <string> 标签并提取数据。
                """
                # 如果当前节点是 <string> 标签，提取数据
                if current_node.tag == "string":
                    string_data = {
                        "name": current_node.get("name"),
                        "value": current_node.text.strip() if current_node.text else ""
                    }
                    strings_data["strings"].append(string_data)
                
                # 遍历当前节点的所有子节点
                for child in current_node:
                    _recursive_parse(child, strings_data)
            tree = ET.parse(strings_file_path)
            root = tree.getroot()
            strings_data = {
                "file_name": os.path.basename(strings_file_path),
                "strings": []
            }
            
            # 递归调用的方式
            _recursive_parse(root, strings_data)
            return strings_data




    def parse_xml_file(self, xml_file_path):
        """
        解析单个 XML 文件，提取元素和它们的属性。
        """
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        xml_data = {
            "file_name": os.path.basename(xml_file_path),
            "elements": []
        }

        # 遍历 XML 文件的所有元素
        for elem in root.iter():
            element_data = {
                "tag": elem.tag,
                "attributes": {
                    re.sub(r'\{[^}]*\}', '', key): value  # 正则替换掉所有的命名空间部分
                    for key, value in elem.attrib.items()
                }
            }
            xml_data["elements"].append(element_data)

        return xml_data

    def parse_layout_files(self):
        """
        解析布局文件夹中的所有布局文件，提取元素和它们的属性。
        """
        for root, _, files in os.walk(self.layout_dir):
            for file in files:
                if file.endswith(".xml"):
                    layout_file_path = os.path.join(root, file)
                    try:
                        self.layout_files.append(self.parse_layout_file(layout_file_path))
                    except Exception as e:
                        print(e)
    def parse_menu_files(self):
        """
        解析菜单文件夹中的所有菜单文件，提取菜单项和它们的属性。
        """
        for root, _, files in os.walk(self.menu_dir):
            for file in files:
                if file.endswith(".xml"):
                    menu_file_path = os.path.join(root, file)
                    self.menu_files.append(self.parse_menu_file(menu_file_path))

    def parse_layout_file(self, layout_file_path):
        """
        解析单个布局文件，提取元素的结构、内容和属性。
        """
        tree = ET.parse(layout_file_path)
        root = tree.getroot()
        layout_data = {
            "file_name": os.path.basename(layout_file_path),
            "elements": [],
            "dependencies": []  # 用于存储该布局文件依赖的其他布局文件（通过 <include>）
        }

        # 遍历布局文件的所有元素
        for elem in root.iter():
            element_data = {
                "tag": elem.tag,
                "attributes": {
                    re.sub(r'\{[^}]*\}', '', key): value  # 正则替换掉所有的命名空间部分
                    for key, value in elem.attrib.items()
                }            
            }
            layout_data["elements"].append(element_data)

            # 检查布局文件是否通过 <include> 标签依赖其他布局
            if elem.tag == "include" and "layout" in elem.attrib:
                included_layout = elem.attrib["layout"]
                # layout_data["dependencies"].append(included_layout)
                layout_data["dependencies"].append(included_layout)
                if layout_data['file_name'] not in self.layout_dependencies:
                    # 如果不存在，则初始化为空列表
                    self.layout_dependencies[layout_data['file_name']] = []
                self.layout_dependencies[layout_data['file_name']].append(included_layout)

        return layout_data

    def parse_menu_file(self, menu_file_path):
        """
        解析单个菜单文件，提取菜单项的结构和属性。
        """
        tree = ET.parse(menu_file_path)
        root = tree.getroot()
        menu_data = {
            "file_name": os.path.basename(menu_file_path),
            "items": []
        }

        # 遍历菜单文件的所有 item 元素
        for item in root.iter("item"):
            item_data = {
                "id": item.get("{http://schemas.android.com/apk/res/android}id"),
                "title": item.get("{http://schemas.android.com/apk/res/android}title"),
                "icon": item.get("{http://schemas.android.com/apk/res/android}icon"),
                "enabled": item.get("{http://schemas.android.com/apk/res/android}enabled"),
            }

            # 在添加每个属性之前做替换，避免 None 值导致错误
            for key in item_data:
                if item_data[key]:  # 只有当值不为 None 时才调用 replace()
                    item_data[key] = item_data[key].replace('{http://schemas.android.com/apk/res-auto}', '')

            # 将处理后的 item_data 添加到 menu_data 中
            menu_data["items"].append(item_data)

        # 输出处理后的 menu_data
        return menu_data


    # def analyze_dependencies(self):
    #     """
    #     分析布局文件之间的依赖关系，构建一个依赖关系图。
    #     """
    #     for layout_data in self.layout_files:
    #         layout_name = layout_data["file_name"]
    #         for dependency in layout_data["dependencies"]:
    #             if dependency not in self.layout_dependencies:
    #                 self.layout_dependencies[dependency] = []
    #             # self.layout_dependencies[layout_name].append(layout_name)
    #             self.layout_dependencies[layout_name].append(layout_name)


    def save_to_json(self, output_path):
        """
        将布局和菜单解析结果保存为 JSON 格式。
        """
        result = {
            "layouts": self.layout_files,
            "menus": self.menu_files,
            "strings": self.strings_files,
            "xml_files": self.xml_files,
            "layout_dependencies": self.layout_dependencies
        }
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(result, json_file, indent=4, ensure_ascii=False)
        print(f"Data has been saved to {output_path}")



    def  get_dep_layout_file(self, file_name):
        # '@layout/widget_layout_toolbar 
        if file_name.startswith('@layout'):
            file_name = file_name.rsplit('/',1)[1]
            for layout in self.layout_files:
                if layout["file_name"] == file_name + '.xml':
                    return layout
        elif file_name.startswith('@menu'):
            file_name = file_name.rsplit('/',1)[1]
            for layout in self.menu_files:
                if layout["file_name"] == file_name + '.xml':
                    return layout


    def get_layout_prompt(self, file_name):
        ori_file_name = file_name
        file_type = file_name.split('.', 2)[1]
        file_name = file_name.split('.', 2)[2]
        exclude_keys = [
            'layout_width', 'layout_height', 'layout_weight', 
            'background', 'gravity', 'padding', 'src', 'layout_marginTop',
            'layout_gravity', 'paddingBottom', 'paddingTop',' paddingLeft','paddingStart', 'paddingRight','paddingEnd'
        ]
        layout_prompt = "The elements in the layout " + ori_file_name + ": \n"
        if file_type == 'layout':
            for layout in self.layout_files:
                if layout.get('file_name').rsplit('.',1)[0] == file_name:
                    ele_index = 0
                    for element in layout["elements"]:
                            element_prompt = "element index: " + str(ele_index) +':  '
                            element_prompt += '{Tag:' + element.get("tag") + ' },'
                            filtered_attributes = {key: value for key, value in element.get("attributes").items() if key not in exclude_keys}
                            # print(filtered_attributes)
                            for key in filtered_attributes:
                                element_prompt += "{ " + key + ":" + filtered_attributes[key] + " }"
                            layout_prompt += element_prompt + "\n"
        elif file_type == 'menu':
            for layout in self.menu_files:
                if layout.get('file_name').rsplit('.',1)[0] == file_name:
                    ele_index = 0
                    for element in layout["items"]:
                            element_prompt = "item index: " + str(ele_index) +':  '
                            filtered_attributes = {key: value for key, value in element.items() if key not in exclude_keys}
                            for key in filtered_attributes:
                                if filtered_attributes[key]:
                                    element_prompt += "{ " + key + ":" + self.change_to_normal_string(filtered_attributes[key]) + " }"
                            layout_prompt += element_prompt + "\n"


        for  dep in  self.layout_dependencies:
            if dep.rsplit('.',1)[0] == file_name :
                for dep_layout in self.layout_dependencies[dep]:
                        temp_layout_prompt = ""
                        temp_layout_prompt += "The layout include <" + dep_layout + '>\n'
                        temp_layout_prompt += "The element of <" + dep_layout + '> is here: \n'
                        dep_layout = self.get_dep_layout_file(dep_layout)
                        if dep_layout:
                            ele_index = 0
                            for element in dep_layout["elements"]:
                                element_prompt = "element index: " + str(ele_index) +': '
                                element_prompt += '{Tag:' + element.get("tag") + ' },'
                                filtered_attributes = {key: value for key, value in element.get("attributes").items() if key not in exclude_keys}
                                # print(filtered_attributes)
                                for key in filtered_attributes:
                                    element_prompt += "{ " + key + ":" + self.change_to_normal_string(filtered_attributes[key]) + " }"
                                temp_layout_prompt += element_prompt + "\n"
                            layout_prompt += temp_layout_prompt
                break

        return layout_prompt
    


    def get_layout(self, file_name):
        ori_file_name = file_name
        file_type = file_name.split('.', 2)[1]
        file_name = file_name.split('.', 2)[2]
        exclude_keys = [
            'layout_width', 'layout_height', 'layout_weight', 
            'background', 'gravity', 'padding', 'src', 'layout_marginTop',
            'layout_gravity', 'paddingBottom', 'paddingTop',' paddingLeft','paddingStart', 'paddingRight','paddingEnd'
        ]
        layout_result = Layout()
        layout_result.name = file_name
        if file_type == 'layout':
            layout_result.set_type('layout')
            for layout in self.layout_files:
                if layout.get('file_name').rsplit('.',1)[0] == file_name:
                    ele_index = 0
                    for element in layout["elements"]:
                            element_struct = Element()
                            element_struct.set_name(str(ele_index))
                            element_struct.add_static_property("tag", element.get("tag"))
                            filtered_attributes = {key: value for key, value in element.get("attributes").items() if key not in exclude_keys}
                            # print(filtered_attributes)
                            for key in filtered_attributes:
                                element_struct.add_static_property(key, self.change_to_normal_string(filtered_attributes[key]))
                            layout_result.add_element(element_struct)
        elif file_type == 'menu':
            layout_result.set_type('menu')
            for layout in self.menu_files:
                if layout.get('file_name').rsplit('.',1)[0] == file_name:
                    ele_index = 0
                    for element in layout["items"]:
                            element_struct = Element()
                            element_struct.set_name(str(ele_index))
                            element_struct.add_static_property("tag", element.get("tag"))
                            filtered_attributes = {key: value for key, value in element.items() if key not in exclude_keys}
                            for key in filtered_attributes:
                                if filtered_attributes[key]:
                                    element_struct.add_static_property(key, self.change_to_normal_string(filtered_attributes[key]))
                            layout_result.add_element(element_struct)

        for  dep in  self.layout_dependencies:
            if dep.rsplit('.',1)[0] == file_name :
                for dep_layout in self.layout_dependencies[dep]:
                        temp_layout = Layout()
                        temp_layout.set_type('dependency')
                        dep_layout = self.get_dep_layout_file(dep_layout)
                        if dep_layout:
                            ele_index = 0
                            for element in dep_layout["elements"]:
                                element_struct = Element()
                                element_struct.set_name(str(ele_index))
                                element_struct.add_static_property("tag", element.get("tag"))
                                filtered_attributes = {key: value for key, value in element.get("attributes").items() if key not in exclude_keys}
                                for key in filtered_attributes:
                                    element_struct.add_static_property(key, self.change_to_normal_string(filtered_attributes[key]))
                                temp_layout.add_element(element_struct)
                            layout_result.add_dependency(temp_layout)
                break

        return layout_result

    def get_string_value(self, string_ref):
        """
        根据给定的 R.string.xxx 字符串资源引用，返回对应的字符串值。
        """
        # 提取 R.string.xxx 中的 'xxx' 部分
        if string_ref.startswith('R.string.'):
            string_name = string_ref.split('.')[-1]
        elif string_ref.startswith('@string'):
            string_name = string_ref.replace('@string/', '')
        # 遍历所有的 strings 文件，查找对应的 string 名称
        for strings_data in self.strings_files:
            for string in strings_data["strings"]:
                if string["name"] == string_name:
                    return string["value"]
        
        # 如果找不到对应的 string，返回 None 或者一个合适的默认值
        return None
    
    def get_xml_file_content(self, file_name):
        """
        根据给定的文件名返回对应 XML 文件的内容（元素及属性）。
        如果找不到该文件，返回 None。
        """
        # 遍历 xml_files 列表，查找匹配的文件名
        for xml_file in self.xml_files:
            if xml_file["file_name"] == file_name:
                return xml_file["elements"]  # 返回该文件的所有元素
        # 如果未找到匹配的文件，返回 None
        return None

    def extract_linked_files_from_elements(self, elements):
        """
        从给定的元素列表中提取链接到的布局文件和 XML 配置文件（例如 settings_data.xml）
        
        :param elements: XML 元素列表，包含每个 XML 文件的元素和它们的属性
        :return: 返回链接到的布局文件和 XML 配置文件路径的列表
        """
        linked_files = []

        for element in elements:
            # 遍历元素的属性，特别关注布局文件（@layout/）和 XML 文件（key）
            for attr_name, attr_value in element['attributes'].items():
                # 处理布局文件，通常以 '@layout/' 开头
                if attr_value.startswith('@layout/'):
                    linked_files.append(attr_value)
                
                # 处理 XML 配置文件引用，通常是通过 'key' 属性引用的
                elif attr_name == 'key':
                    linked_files.append(attr_value + ".xml")  # 假设这些 'key' 对应的文件名以 .xml 结尾
                
                # 处理 fragment 或其他类相关引用
                elif attr_name == 'fragment' or attr_name == 'targetClass':
                    linked_files.append(attr_value)

        return linked_files

    def analyze_xml_files(self):
        """
        解析给定的多个 XML 文件，提取其中所有链接到的资源或文件。
        
        :param xml_files: 包含 XML 文件信息的字典列表
        :return: 返回所有链接的资源或文件路径的集合
        """
        all_linked_files = set()
        for xml_file in self.xml_files:
            file_name = xml_file['file_name']
            elements = xml_file['elements']
            linked_files = self.extract_linked_files_from_elements(elements)
            
            for file in linked_files:
                if '.xml' in file:
                    content = self.get_xml_file_content(file)
                    if content:
                        print(content)
                elif '@layout' in file:
                    content = self.get_layout_prompt('R.layout.' + file.replace('@layout/', ''))
                    if content:
                        print(content)
            
            # 将提取的文件路径添加到结果集合中（去重）
            all_linked_files.update(linked_files)

        return list(all_linked_files)


    def get_xml_file_prompt(self, file):
        """
        解析给定的多个 XML 文件，提取其中所有链接到的资源或文件。
        
        :param xml_files: 包含 XML 文件信息的字典列表
        :return: 返回所有链接的资源或文件路径的集合
        """
        all_linked_files = set()
        prompt = "Here is the linked files of <" + file +">:\n"
        if 'R.xml.' in file:
            file = file.replace('R.xml.','') + '.xml'

        for xml_file in self.xml_files:
            if file == xml_file['file_name']:
                file_name = xml_file['file_name']
                elements = xml_file['elements']
                linked_files = self.extract_linked_files_from_elements(elements)
                for file in linked_files:
                    temp_prompt = ""
                    if '.xml' in file:
                        content = self.get_xml_file_content(file)
                        if content:
                            temp_prompt += self.convert_to_natural_language(content)
                    elif '@layout' in file:
                        content = self.get_layout_prompt('R.layout.' + file.replace('@layout/', ''))
                        if content:
                            temp_prompt += content
                    if temp_prompt:
                        prompt += "The linked file <" + file + ">:\n"
                        prompt += temp_prompt
                
                # 将提取的文件路径添加到结果集合中（去重）
                all_linked_files.update(linked_files)

        return prompt
    

    def get_xml_file(self, file):
        """
        解析给定的多个 XML 文件，提取其中所有链接到的资源或文件。
        
        :param xml_files: 包含 XML 文件信息的字典列表
        :return: 返回所有链接的资源或文件路径的集合
        """
        all_linked_files = set()
        prompt = "Here is the linked files of <" + file +">:\n"
        if 'R.xml.' in file:
            file = file.replace('R.xml.','') + '.xml'

        for xml_file in self.xml_files:
            if file == xml_file['file_name']:
                file_name = xml_file['file_name']
                elements = xml_file['elements']
                linked_files = self.extract_linked_files_from_elements(elements)
                for file in linked_files:
                    temp_prompt = ""
                    if '.xml' in file:
                        content = self.get_xml_file_content(file)
                        if content:
                            temp_prompt += self.convert_to_natural_language(content)
                    elif '@layout' in file:
                        content = self.get_layout_prompt('R.layout.' + file.replace('@layout/', ''))
                        if content:
                            temp_prompt += content
                    if temp_prompt:
                        prompt += "The linked file <" + file + ">:\n"
                        prompt += temp_prompt
                
                # 将提取的文件路径添加到结果集合中（去重）
                all_linked_files.update(linked_files)

        return prompt

    def change_to_normal_string(self, input_string):
        if input_string.startswith('R.string.') or input_string.startswith('@string/'):
            if self.get_string_value(input_string):
                return self.get_string_value(input_string)
        return input_string
    
    def convert_to_natural_language(self, content):

        """
        将 XML 配置内容转换为自然语言描述（英语）。
        
        :param content: XML 配置元素列表
        :return: 返回转换后的自然语言描述
        """
        descriptions = []
        
        for element in content:
            tag = element['tag']
            attributes = element['attributes']
            
            if tag == 'PreferenceScreen':
                # 描述 PreferenceScreen
                descriptions.append("A preference screen with specific settings.<")
            
            elif tag == 'SwitchPreference':
                # 获取必要的属性：key、title、summary
                key = self.change_to_normal_string(attributes.get('key', ''))
                title = self.change_to_normal_string(attributes.get('title', ''))
                summary = self.change_to_normal_string(attributes.get('summary', ''))
                summary_off = self.change_to_normal_string(attributes.get('summaryOff', ''))
                summary_on = self.change_to_normal_string(attributes.get('summaryOn', ''))
                
                # 基于属性生成描述
                if key:
                    descriptions.append(f"A switch preference with key '{key}'")
                if title:
                    descriptions.append(f"titled '{title}'.")
                if summary_off and summary_on:
                    descriptions.append( f"Summary when off: '{summary_off}', Summary when on: '{summary_on}'.")
        descriptions.append(">\n")
        # 返回完整的自然语言描述
        return " ".join(descriptions)




if __name__ == "__main__":
    # 输入布局和菜单文件夹路径
    layout_dir = "D:\code\AndroidSourceCodeAnalyzer/app_project/Omni-Notes/omniNotes/src/main/res/layout"
    menu_dir = "D:\code\AndroidSourceCodeAnalyzer/app_project/Omni-Notes/omniNotes/src/main/res/menu"
    xml_dir = "D:\code\AndroidSourceCodeAnalyzer/app_project/Omni-Notes/omniNotes/src/main/res/xml"
    string_dir = "D:\code\AndroidSourceCodeAnalyzer/app_project/Omni-Notes/omniNotes/src/main/res/values"

    # 创建分析器对象
    analyzer = LayoutMenuAnalyzer(layout_dir, menu_dir, string_dir, xml_dir)

    # 解析布局文件和菜单文件
    analyzer.init()

    # 分析布局文件之间的依赖关系
    # analyzer.analyze_dependencies()
    # 不需要显示的属性
    exclude_keys = [
        'layout_width', 'layout_height', 'layout_weight', 
        'background', 'gravity', 'padding', 'src', 'layout_marginTop',
        'layout_gravity'
    ]

    # layout_prompt = analyzer.get_layout('R.layout.fragment_list')
    layout_prompt = analyzer.get_layout_prompt('R.layout.fragment_navigation_drawer')
    print('---------------layout_prompt----------------')
    print(layout_prompt)