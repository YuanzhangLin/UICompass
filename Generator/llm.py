from openai import OpenAI, BadRequestError
import config
import json
import time
import datetime
import threading
MODEL_PRICING = {
    "qwen-max": {"input": 2.4 / 1_000_000, "output": 9.6 / 1_000_000},
    "qwen-vl-max": {"input": 3 / 1_000_000, "output": 9 / 1_000_000},
    "deepseek-v3": {"input": 2 / 1_000_000, "output": 8 / 1_000_000},
}
# llm.py



class CostTracker:
    def __init__(self, pricing_table):
        self.pricing = pricing_table
        self.usage_data = {
            model: {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}
            for model in pricing_table
        }
        self.total_cost = 0.0
        self.lock = threading.Lock()

    def update_usage(self, model_name, prompt_tokens, completion_tokens):
        """
        线程安全地更新使用情况。
        此版本【已移除】内部的print语句，以避免在并发时造成阻塞。
        """
        with self.lock:
            if model_name not in self.pricing:
                if "qwen" in model_name:
                    model_name = "qwen-max"
                elif "deepseek" in model_name:
                    model_name = "deepseek-v3"
                else:
                    # 即使有警告，也只是静默返回，不打印
                    return

            # 所有计算和累加都在锁的保护下进行
            self.usage_data[model_name]["prompt_tokens"] += prompt_tokens
            self.usage_data[model_name]["completion_tokens"] += completion_tokens

            input_cost = prompt_tokens * self.pricing[model_name]["input"]
            output_cost = completion_tokens * self.pricing[model_name]["output"]
            call_cost = input_cost + output_cost

            self.usage_data[model_name]["cost"] += call_cost
            self.total_cost += call_cost

    def get_summary(self):
        """
        返回最终的成本摘要字符串。此方法在所有线程结束后由主线程调用。
        """
        with self.lock:
            summary = "\n" + "="*50 + "\n"
            summary += "LLM API Cost & Usage Summary\n"
            summary += "="*50 + "\n"
            for model, data in self.usage_data.items():
                if data['prompt_tokens'] > 0 or data['completion_tokens'] > 0:
                    summary += f"Model: {model}\n"
                    summary += f"  - Input Tokens:  {data['prompt_tokens']:,}\n"
                    summary += f"  - Output Tokens: {data['completion_tokens']:,}\n"
                    summary += f"  - Cost:          ${data['cost']:.6f}\n"
                    summary += "-"*20 + "\n"
            
            summary += f"Total Estimated Cost: ${self.total_cost:.6f}\n"
            summary += "="*50 + "\n"
            return summary

# 在 llm.py 的全局作用域创建一个实例
cost_tracker = CostTracker(MODEL_PRICING)


def quert_llm(prompt, role="You are a android source code analysis assistant"):
    # return quert_llm(prompt)
    # return query_deep_seek_huoshan(prompt)
    attempts = 0
    max_attempts = 2
    result = None

    while attempts < max_attempts:
        result = query_qwen_max_bailian(prompt)
        if result:
            break
        attempts += 1

    return result


def query_qwen_max_bailian(prompt, message=None, role="You are a android source code analysis agent"):
    client = OpenAI(
    api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message
    model_name_for_billing="qwen-max"

    completion = client.chat.completions.create(
        model="qwen-plus",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    # --- 核心修改在这里 ---
    # 1. 从返回对象中获取 token 使用情况
    usage = completion.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    # 2. 更新计费器
    cost_tracker.update_usage(model_name_for_billing, prompt_tokens, completion_tokens)
  
    return completion.choices[0].message.content



def query_qwen_vl_max_bailian(prompt, message=None, role="You are a android task agent"):
    client = OpenAI(
    api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message
    model_name_for_billing= "qwen-vl-max"

    completion = client.chat.completions.create(
        model="qwen-vl-max",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    # --- 核心修改在这里 ---
    # 1. 从返回对象中获取 token 使用情况
    usage = completion.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    # 2. 更新计费器
    cost_tracker.update_usage(model_name_for_billing, prompt_tokens, completion_tokens)
    return completion.choices[0].message.content


def query_llm_and_parse(prompt, role="You are a android source code analysis assistant"):
    attempts = 0
    max_attempts = 2
    result = None
    while attempts < max_attempts:
        result = quert_llm(prompt)
        if result:
            result = parse_json(result)
            if result:
                break
        attempts += 1

    return result

def check_braces(json_string):
   stack = []
   for char in json_string:
       if char == '{':
           stack.append(char)
       elif char == '}':
           if not stack:
               return False  # 找到闭合括号但没有对应的开启括号
           stack.pop()
   
   return len(stack) == 0  # 栈为空表示所有括号都匹配


def query_deep_seek_bailian(prompt, role="You are a android source code analysis assistant", retries=5, delay=60):
   client = OpenAI(
       api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
       base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
   )

   for attempt in range(retries):
       try:
            completion = client.chat.completions.create(
                model="deepseek-v3",
                messages=[
                    {'role': 'system', 'content': role},
                    {'role': 'user', 'content': prompt}
                ]
            )
            # 1. 从返回对象中获取 token 使用情况
            usage = completion.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            model_name_for_billing = "deepseek-v3"
            # 2. 更新计费器
            cost_tracker.update_usage(model_name_for_billing, prompt_tokens, completion_tokens)
            return completion.choices[0].message.content
       except BadRequestError as e:
            print(e)
            time.sleep(delay)
       except Exception as e:
           print(f"An unexpected error occurred: {e}")
           raise

   raise Exception("All retry attempts failed")



def query_deepseek(prompt, role="You are a android source code analysis assistant"):

    client = OpenAI(api_key=config.deep_seek_key, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

def parse_json(answer):
    """
    解析一个可能嵌入在更大文本块中的JSON字符串。
    此版本完全在内存中操作，使其对于并发使用是线程安全的。
    它不使用任何临时文件。
    """
    # 步骤 1: 将 answer 转换为字符串（确保它是字符串类型）
    answer = str(answer)
    
    # 步骤 2: 清理LLM可能添加的Markdown代码块标记 (```json ... ```)
    # 这种方法比简单的replace更健壮，能处理前后有额外文本的情况。
    if '```' in answer:
        start_index = answer.find('{')
        end_index = answer.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            answer = answer[start_index : end_index + 1]
        else:
            # 如果找不到大括号，回退到简单的替换逻辑
            answer = answer.replace("```json", "").replace("```", "").strip()

    # 步骤 3: 应用你自定义的括号不匹配修复逻辑
    # 注意：这些是你原来代码中的修复规则，我们予以保留。
    if not check_braces(answer):
        print('----警告：检测到括号不匹配，尝试进行简单修复。')
        if '{"{"' in answer:
            answer = answer.replace('{"{"', '{"')
        elif '{{' in answer:
            answer = answer.replace('{{', '{')
        else:
            # 这个修复规则比较激进，但遵从原逻辑
            answer = answer.replace('{', '', 1)

    # 步骤 4: 直接在内存中解析清理后的字符串
    try:
        data = json.loads(answer)
        return data
    except json.JSONDecodeError as e:
        # 当解析失败时，打印出导致问题的确切字符串，这对于调试至关重要。
        print("--- 错误：解析JSON字符串失败 ---")
        print(f"JSONDecodeError: {e}")
        print("--- 出问题的字符串内容如下: ---")
        print(answer)
        print("---------------------------------")
        # 在失败时返回 None
        return None

