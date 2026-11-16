# # ⭐️ 接口层：项目入口，只负责路由和业务流程组装
# # 原则：不写具体的数据库操作、大模型调用，只调用下层模块的函数
# from fastapi import FastAPI
# from pydantic import BaseModel
# from db import init_db
# from contextlib import asynccontextmanager

# # 导入下层模块的函数
# from llm import call_llm, format_goods_to_text, extract_filter_conditions
# from db import init_db, db_add_goods, db_get_all_goods, db_get_goods_by_id, db_update_goods, db_delete_goods, filter_goods, db_get_session, db_save_session, db_query_goods, db_add_category, db_get_all_category
# # 1. 创建FastAPI实例
# #app = FastAPI()

# # 2. 项目启动时自动初始化数据库
# # ⭐️ 服务生命周期管理器：替代已弃用的 on_event
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # ===== 服务启动前执行（等价于原来的 startup） =====
#     init_db()  # 自动初始化数据库表
#     yield
#     # ===== 服务关闭前执行（等价于原来的 shutdown） =====
#     # 后续需要释放资源（如关闭数据库连接）可以写在这里，目前留空即可
# # 创建应用实例，绑定生命周期
# app = FastAPI(lifespan=lifespan)





# # ========== 请求体模型 ==========
# class ChatRequest(BaseModel):
#     session_id: str
#     question: str
#     temperature: float = 0.7

# # class GoodsUpdateRequest(BaseModel):
# #     name: str | None = None
# #     price: float | None = None
# #     stock: int | None = None
# #     description: str | None = None

# class GoodsUpdateRequest(BaseModel):
#     name: str | None = None
#     price: float | None = None
#     stock: int | None = None
#     description: str | None = None
#     category_id: int | None = None

# class GoodsAddRequest(BaseModel):
#     name: str
#     price: float
#     stock: int = 0
#     description: str | None = None
#     category_id: int | None = None

# # class GoodsAddRequest(BaseModel):
# #     name: str
# #     price: float
# #     stock: int = 0
# #     description: str | None = None




# # ========== 统一返回工具函数 ==========
# def success(data=None, msg="成功"):
#     return {"code": 0, "msg": msg, "data": data}

# def error(code=500, msg="失败", data=None):
#     return {"code": code, "msg": msg, "data": data}

# session_history = {}
# # ========== 聊天接口（多轮对话） ==========
# @app.post("/chat")
# def chat(req: ChatRequest):
#     if req.session_id not in session_history:
#         session_history[req.session_id] = []
    
#     session_history[req.session_id].append({"role": "user", "content": req.question})

#     reply = call_llm(session_history[req.session_id], req.temperature)

#     session_history[req.session_id].append({"role": "assistant", "content": reply})
    
#     return success(data={"reply": reply})


# # ========== 商品CRUD接口 ==========
# # 新增商品
# # @app.post("/goods/add")
# # def add_goods(req: GoodsAddRequest):
# #     goods_id = db_add_goods(req.name, req.price, req.stock, req.description)
# #     return success(data={"id": goods_id})
# # 新增商品
# @app.post("/goods/add")
# def add_goods(req: GoodsAddRequest):
#     goods_id = db_add_goods(req.name, req.price, req.stock, req.description, req.category_id)
#     return success(data={"id": goods_id})

# # 查询全部商品
# @app.get("/goods/list")
# def get_goods_list():
#     goods_list = db_get_all_goods()
#     return success(data=goods_list)

# # 查询单个商品
# @app.get("/goods/detail")
# def get_goods_detail(goods_id: int):
#     goods = db_get_goods_by_id(goods_id)
#     if not goods:
#         return error(msg="商品不存在")
#     return success(data=goods)

# # 修改商品
# @app.put("/goods/update")
# def update_goods(goods_id: int, req: GoodsUpdateRequest):
#     result = db_update_goods(goods_id, req.name, req.price, req.stock, req.description)
#     if not result:
#         return error(msg="修改失败，商品不存在")
#     return success(msg="修改成功")

# # 删除商品
# @app.delete("/goods/delete")
# def delete_goods(goods_id: int):
#     result = db_delete_goods(goods_id)
#     if not result:
#         return error(msg="删除失败，商品不存在")
#     return success(msg="删除成功")

# # ========== 分类管理接口 ==========
# # 新增分类
# @app.post("/category/add")
# def add_category(name: str):
#     category_id = db_add_category(name)
#     return success(data={"id": category_id})

# # 查询全部分类
# @app.get("/category/list")
# def get_category_list():
#     category_list = db_get_all_category()
#     return success(data=category_list)


# # ========== 智能导购接口 ==========
# # ⭐️ 智能导购接口（动态筛选优化版）
# # 完整流程：提取条件 → 代码精准筛选商品 → 拼接Prompt → 生成推荐话术
# # @app.post("/goods/ask")
# # def goods_ask(req: ChatRequest):
# #     # 第一步：从数据库读取全量商品数据
# #     goods_list = db_get_all_goods()

# #     # 第二步：从用户自然语言问题中，提取结构化筛选条件
# #     conditions = extract_filter_conditions(req.question, req.temperature)
# #     max_price = conditions.get("max_price")
# #     category = conditions.get("category")

# #     # 第三步：用代码100%精准过滤商品
# #     valid_goods = filter_goods(goods_list, max_price, category)

# #     # 兜底：无符合条件的商品，直接告知用户，无需调用大模型
# #     if not valid_goods:
# #         return success(data={"reply": "抱歉，没有找到符合您需求的商品，您可以调整预算或品类后再试试~"})

# #     # 第四步：将筛选后的商品，格式化为大模型易读的文本格式
# #     goods_text = format_goods_to_text(valid_goods)

# #     # 第五步：拼接推荐话术Prompt（大模型只负责写推荐理由，不做筛选）
# #     prompt = f"""你是一名专业友好的商品导购员，请根据下方的商品列表，回答用户的问题。
# # 要求：
# # 1. 只使用给出的商品信息进行推荐，不要编造不存在的商品
# # 2. 分点介绍每个推荐商品，说明价格、核心卖点和推荐理由
# # 3. 语气自然亲切，符合电商导购的表达习惯

# # 【商品列表】
# # {goods_text}

# # 【用户问题】
# # {req.question}
# # """

# #     # 第六步：调用大模型生成最终推荐回复
# #     reply = call_llm([{"role": "user", "content": prompt}], req.temperature)

# #     # 第七步：封装统一格式返回
# #     return success(data={"reply": reply})




# # ⭐️ 智能导购接口（数据库持久化多轮版）
# @app.post("/goods/ask")
# def goods_ask(req: ChatRequest):
#     # 1. 读取全量商品
#     goods_list = db_get_all_goods()

#     # 2. 提取本轮筛选条件
#     conditions = extract_filter_conditions(req.question, req.temperature)
#     new_max_price = conditions.get("max_price")
#     new_category = conditions.get("category")

#     # 3. 从数据库读取历史条件，做合并
#     history = db_get_session(req.session_id)
#     if not history:
#         history = {"max_price": None, "category": None}
    
#     final_max_price = new_max_price if new_max_price is not None else history.get("max_price")
#     final_category = new_category if new_category is not None else history.get("category")

#     # 4. 把最新条件存回数据库
#     db_save_session(req.session_id, final_max_price, final_category)

#     # 5. 用最终条件过滤商品
#     valid_goods = filter_goods(goods_list, final_max_price, final_category)

#     # 6. 兜底逻辑
#     if final_max_price is None and final_category is None:
#         reply = "我是智能商品导购助手，可以帮您推荐各类数码好物。您可以告诉我预算范围或者想要的商品品类，我来为您精准推荐~"
#         return success(data={"reply": reply})

#     if not valid_goods:
#         reply = "抱歉，当前没有找到符合您需求的商品。您可以调整预算范围，或者告诉我其他品类需求~"
#         return success(data={"reply": reply})

#     # 7. 生成推荐话术
#     goods_text = format_goods_to_text(valid_goods)
#     prompt = f"""你是一名专业友好的商品导购员，请严格根据下方给出的商品列表回答用户的问题，绝对不可以编造商品信息、价格、库存。
# 要求：
# 1. 只能使用给出的商品信息进行推荐，商品名称、价格、描述必须和列表完全一致，禁止自行修改
# 2. 分点介绍每个推荐商品，说明价格、核心卖点和推荐理由
# 3. 语气自然亲切，符合电商导购的表达习惯

# 【商品列表】
# {goods_text}

# 【用户问题】
# {req.question}

# """

#     reply = call_llm([{"role": "user", "content": prompt}], req.temperature)
#     return success(data={"reply": reply})







# # 商品分页+多条件查询接口
# @app.get("/goods/list")
# def goods_list(
#     keyword: str = None,
#     min_price: float = None,
#     max_price: float = None,
#     category_id: int = None,
#     order_by: str = "price",
#     order: str = "asc",
#     page: int = 1,
#     page_size: int = 10
# ):
#     result = db_query_goods(
#         keyword=keyword,
#         min_price=min_price,
#         max_price=max_price,
#         category_id=category_id,
#         order_by=order_by,
#         order=order,
#         page=page,
#         page_size=page_size
#     )
#     return success(data=result)


from fastapi import FastAPI
from routers.goods import router as goods_router, router_category as category_router
from routers.chat import router as chat_router
from db import init_db
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from common import error, CODE_PARAM_ERROR, CODE_SYSTEM_ERROR, logger
# 项目启动时自动初始化数据库表
init_db()

# 创建 FastAPI 应用实例
app = FastAPI(
    title="智能商品导购系统",
    description="基于 RAG 架构的智能商品导购后端项目"

)




# 1. 捕获参数校验异常：用户传参格式错误时触发
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 记录错误日志
    logger.warning(f"参数校验失败 | 路径：{request.url.path} | 错误：{exc.errors()}")
    # 返回友好的统一格式
    return JSONResponse(
        status_code=200,
        content=error(code=CODE_PARAM_ERROR, msg="参数格式错误，请检查输入")
    )
# 2. 全局兜底异常：捕获所有未处理的报错
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    # 记录完整错误日志，方便排查问题
    logger.error(f"系统异常 | 路径：{request.url.path}", exc_info=True)
    # 对外只返回友好提示，不暴露内部报错细节
    return JSONResponse(
        status_code=200,
        content=error(code=CODE_SYSTEM_ERROR, msg="系统内部错误，请稍后重试")
    )













# 注册所有业务路由
app.include_router(goods_router)
app.include_router(category_router)
app.include_router(chat_router)











if __name__ == "__main__":
    import uvicorn
    from config import APP_PORT
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)

