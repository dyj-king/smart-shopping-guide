from fastapi import APIRouter
from db import (
    db_add_goods,
    db_get_all_goods,
    db_get_goods_by_id,
    db_update_goods,
    db_delete_goods,
    db_query_goods,
    db_add_category,
    db_get_all_category
)
from common import success

# 创建商品路由实例
# prefix: 给该组所有接口统一加上 /goods 前缀
# tags: 在接口文档里分组显示，方便查看
router = APIRouter(prefix="/goods", tags=["商品管理"])

# 新增商品
@router.post("/add")
def add_goods(name: str, price: float, stock: int, description: str = "", category_id: int = None):
    goods_id = db_add_goods(name, price, stock, description, category_id)
    return success(data={"id": goods_id})

# 查询全部商品
@router.get("/all")
def get_all_goods():
    goods_list = db_get_all_goods()
    return success(data=goods_list)

# 分页+多条件查询商品
@router.get("/list")
def goods_list(
    keyword: str = None,
    min_price: float = None,
    max_price: float = None,
    category_id: int = None,
    order_by: str = "price",
    order: str = "asc",
    page: int = 1,
    page_size: int = 10
):
    result = db_query_goods(
        keyword=keyword,
        min_price=min_price,
        max_price=max_price,
        category_id=category_id,
        order_by=order_by,
        order=order,
        page=page,
        page_size=page_size
    )
    return success(data=result)

# 根据ID查询商品详情
@router.get("/detail")
def get_goods_detail(goods_id: int):
    goods = db_get_goods_by_id(goods_id)
    return success(data=goods)

# 更新商品
@router.post("/update")
def update_goods(goods_id: int, name: str = None, price: float = None, stock: int = None, description: str = None, category_id: int = None):
    db_update_goods(goods_id, name, price, stock, description, category_id)
    return success(data={"msg": "更新成功"})

# 删除商品
@router.post("/delete")
def delete_goods(goods_id: int):
    db_delete_goods(goods_id)
    return success(data={"msg": "删除成功"})


# ========== 分类管理路由 ==========
router_category = APIRouter(prefix="/category", tags=["分类管理"])

@router_category.post("/add")
def add_category(name: str):
    category_id = db_add_category(name)
    return success(data={"id": category_id})

@router_category.get("/list")
def get_category_list():
    category_list = db_get_all_category()
    return success(data=category_list)