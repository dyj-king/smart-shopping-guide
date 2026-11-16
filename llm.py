# ⭐️ AI层：封装所有大模型交互逻辑
# 职责：大模型调用、数据格式化、Prompt模板，只提供AI能力给上层调用
import requests
# 从配置层导入大模型相关配置

from config import API_KEY, BASE_URL, MODEL


# ⭐️ 通用大模型调用函数
def call_llm(messages, temperature=0.7):
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]


# ⭐️ 商品数据格式化：转成大模型易读的文本格式
def format_goods_to_text(goods_list):
    if not goods_list:
        return "暂无商品数据"
    
    text_lines = []
    for idx, goods in enumerate(goods_list, 1):
        line = f"{idx}. {goods['name']} | 价格:{goods['price']}元 | 库存:{goods['stock']}件"
        if goods.get("description"):
            line += f" | 描述:{goods['description']}"
        text_lines.append(line)
    
    return "\n".join(text_lines)






###
# ⭐️ 必须掌握：从用户问题中提取结构化筛选条件（优化稳定版）
# 作用：让大模型输出标准JSON，供后端代码做精准过滤
def extract_filter_conditions(question, temperature=0.1):
    # 超强约束Prompt：禁止任何多余内容，只输出纯JSON
    prompt = f"""任务：从用户问题中提取商品筛选条件，只输出纯JSON，绝对不能输出任何解释、说明、markdown代码块、多余文字。
严格遵守以下规则：
1. 只能输出一个JSON对象，不要有任何其他内容
2. 可提取字段：
   - max_price: 数字类型，用户要求的最高价格（单位：元），用户没提预算则为 null
   - category: 字符串类型，用户指定的商品品类/产品类型关键词，用户没提品类则为 null
3. 价格必须是纯数字，不能带单位、汉字
4. 提取不到的字段必须写 null，不能省略字段
5. 必须准确识别商品品类名称，比如“键盘”“鼠标”“充电宝”都属于品类关键词

用户问题：{question}

正确输出示例：
{{"max_price": 100, "category": "键盘"}}
"""

    messages = [{"role": "user", "content": prompt}]
    # 温度设极低，最大程度保证输出稳定
    result_text = call_llm(messages, temperature)
    
    import json
    try:
        # 多层清洗：去除所有可能的多余内容
        result_text = result_text.strip()
        # 去除markdown代码块标记
        if "```" in result_text:
            start = result_text.find("```") + 3
            end = result_text.rfind("```")
            result_text = result_text[start:end].strip()
            if result_text.startswith("json"):
                result_text = result_text[4:].strip()
        # 找到第一个{和最后一个}，只保留JSON本体
        json_start = result_text.find("{")
        json_end = result_text.rfind("}")
        if json_start != -1 and json_end != -1:
            result_text = result_text[json_start:json_end+1]
        
        conditions = json.loads(result_text)
        # 兜底校验：确保两个字段都存在
        if "max_price" not in conditions:
            conditions["max_price"] = None
        if "category" not in conditions:
            conditions["category"] = None
    except Exception:
        # 解析完全失败，返回空条件，保证接口不报错
        conditions = {"max_price": None, "category": None}
    
    return conditions