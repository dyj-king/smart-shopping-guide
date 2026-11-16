from fastapi import APIRouter
from pydantic import BaseModel
from llm import call_llm, extract_filter_conditions, format_goods_to_text
from db import db_get_all_goods, filter_goods, db_get_session, db_save_session
from common import success

# 创建聊天路由实例
router = APIRouter(prefix="/chat", tags=["AI聊天"])

# 请求参数模型
class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"
    temperature: float = 0.7


# 基础单轮聊天接口
@router.post("/simple")
def simple_chat(req: ChatRequest):
    reply = call_llm([{"role": "user", "content": req.question}], req.temperature)
    return success(data={"reply": reply})


# 智能导购接口（数据库持久化多轮版）
@router.post("/goods/ask")
def goods_ask(req: ChatRequest):
    # 1. 读取全量商品
    goods_list = db_get_all_goods()

    # 2. 提取本轮筛选条件
    conditions = extract_filter_conditions(req.question, req.temperature)
    new_max_price = conditions.get("max_price")
    new_category = conditions.get("category")

    # 3. 从数据库读取历史条件，做合并
    history = db_get_session(req.session_id)
    if not history:
        history = {"max_price": None, "category": None}
    
    final_max_price = new_max_price if new_max_price is not None else history.get("max_price")
    final_category = new_category if new_category is not None else history.get("category")

    # 4. 把最新条件存回数据库
    db_save_session(req.session_id, final_max_price, final_category)

    # 5. 兜底逻辑
    if final_max_price is None and final_category is None:
        reply = "我是智能商品导购助手，可以帮您推荐各类数码好物。您可以告诉我预算范围或者想要的商品品类，我来为您精准推荐~"
        return success(data={"reply": reply})

    # 6. 用最终条件过滤商品
    valid_goods = filter_goods(goods_list, final_max_price, final_category)
    if not valid_goods:
        reply = "抱歉，当前没有找到符合您需求的商品。您可以调整预算范围，或者告诉我其他品类需求~"
        return success(data={"reply": reply})

    # 7. 生成推荐话术
    goods_text = format_goods_to_text(valid_goods)
    prompt = f"""你是一名专业友好的商品导购员，请根据下方的商品列表，回答用户的问题。
要求：
1. 只使用给出的商品信息进行推荐，不要编造不存在的商品
2. 分点介绍每个推荐商品，说明价格、核心卖点和推荐理由
3. 语气自然亲切，符合电商导购的表达习惯

【商品列表】
{goods_text}

【用户问题】
{req.question}
"""
    reply = call_llm([{"role": "user", "content": prompt}], req.temperature)
    return success(data={"reply": reply})