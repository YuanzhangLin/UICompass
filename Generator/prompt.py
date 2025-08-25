
from utils import general_utils

def make_prompt(node, method_graph):
    package, class_name, method_name = general_utils.split_method_node(node)
    # 获取方法体
    method_body = general_utils.get_method_body_by_method_name(package, class_name, method_name)
    # 获取全局变量描述
    global_variable_description = general_utils.get_global_variables_in_methods(package, class_name, method_name)
    global_assignment = general_utils.get_all_global_assignment(package, class_name, method_name)
    # 构造提示词时检查 global_variable_description 是否为空
    prompt = f"""
    You are an Android analyst. I will give you a method from the class {class_name}.
    Here is the method from the given Android source code:
    {method_body}
    """

    # 只有在 global_variable_description 不为空时，才加入这一部分内容
    if global_variable_description:
        prompt += f"""
        Here is the global variable in the class file:
        {global_variable_description}
        """

    if global_assignment:
        prompt += f"""
        Here is the global variable assignment in the class file:
        {global_assignment}
        """

    # 增加已有方法的描述
    if node in method_graph:
        depend_methods = method_graph[node]
        if len(depend_methods) > 0:
            for depend_method in depend_methods:
                try:
                    method_info = general_utils.get_method_info(depend_method)
                    prompt += f"""
                    Here is the explanation of the method named {depend_method} that is called within the given method:
                    {method_info['functionality']}
                    """
                except Exception as e :
                    print(e)

    prompt += """
    Please analyze the method above and identify any activity migration relationships that exist.
    Specifically, look for `startActivity` calls and their associated `Intent` objects. 
    """
    prompt += """
    You need to analyze the functionality of the source code. If there are any actionable elements, provide a description of the element's response.
    Additionally, identify all **UI elements** involved in the method. An **element** should be one of the following:
    - A view component such as `Button`, `TextView`, `ImageView`, etc.
    - An interaction-triggering element, like a button that starts an activity or any clickable UI component.
    Do **not** include things like `Build.VERSION.SDK_INT`, constants, or non-UI variables.
    """

    prompt += """
    In addition to activity migrations, please also check for:
    1. Any **fragment** and **activity** dependencies or relationships in the code. Specifically, identify if a fragment is associated with an activity (e.g., using `getActivity()`, `FragmentTransaction`, or similar methods).
    2. Any **migration relationships** between fragments and activities. This could include cases where a fragment starts an activity, or an activity dynamically replaces a fragment, or any other relationships indicating a transition between a fragment and an activity.
    3. Any relationship between **XML files (R.layout，or R.menu)** and **activities** or **fragments**. Look for references to XML layouts that are inflated in an activity or fragment (e.g., using `setContentView()`, `LayoutInflater`, `FragmentTransaction.replace()`, etc.). **You only need to output layout files that start with R.layout and R.menu.**
    4. **element_list**: Please list all the elements (normal element or menu item) present in the method. Tell me the type and ID of each element. Additionally, describe the conditions under which the element is executed and the effects it will have. For example, the condition could be that the login button can only be clicked after entering the account password, and the effect could be a transition to MainActivity.
    The output should be in JSON format, for example:
    {
        "functionality": "description of the method functionality",
        "element_list": [
            {
                "type": "element type",
                "element_id": "R.id.xx",
                "action": "description of the action triggered by the element"
            }
        ],
        "activity_migrations": [
            {
                "from_activity_or_fragment": "sourceActivityOrFragmentName",
                "to_activity_or_fragment": "targetActivityOrFragmentName",
                "description": "A brief description of how the migration happens."
            }
        ],
        "fragment_activity_relationships": [
            {
                "fragment": "fragmentName",
                "activity": "activityName",
                "relationship": "Fragment is attached to Activity using FragmentTransaction methods like add(), replace(), or show()."
            }
        ],
        "xml_relationships": [
            {
                "xml_file": "R.layout.xx.xml",
                "associated_with": "activity_or_fragment"
            }
        ]
    }

    Note that: **Do not output anything except the json format answer.**
    """

    # 输出提示词
    # print(prompt)
    return prompt
