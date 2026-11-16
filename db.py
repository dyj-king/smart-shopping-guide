
# ⭐️ 数据层：封装所有数据库操作
# 职责：只负责和数据库交互，提供增删改查函数给上层调用
import pymysql
import os
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 数据库连接配置
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "root"),
    "database": os.getenv("MYSQL_DB", "smart_shop"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor  # 查询结果直接返回字典，和sqlite3.Row效果对齐
}

# print("MYSQL_USER =", os.getenv("MYSQL_USER"))
# print("MYSQL_PASSWORD =", os.getenv("MYSQL_PASSWORD"))
# print("MYSQL_DB =", os.getenv("MYSQL_DB"))


# 统一数据库连接
def get_conn():
    conn = pymysql.connect(**MYSQL_CONFIG)
    return conn


# 初始化数据库：创建表结构（升级版：3张核心表）
def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    # 1. 商品分类表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS category (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(50) NOT NULL UNIQUE,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 2. 商品表（新增分类ID关联字段）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goods (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        stock INT NOT NULL DEFAULT 0,
        description TEXT,
        category_id INT,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES category(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 3. 会话记录表：持久化存储筛选条件
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_session (
        session_id VARCHAR(64) PRIMARY KEY,
        max_price DECIMAL(10,2),
        category VARCHAR(100),
        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 给常用查询字段加索引，提升查询速度
    import pymysql.err
    index_sqls = [
        "CREATE INDEX idx_goods_price ON goods(price)",
        "CREATE INDEX idx_goods_category ON goods(category_id)",
        "CREATE INDEX idx_goods_name ON goods(name)"
    ]
    for sql in index_sqls:
        try:
            cursor.execute(sql)
        except pymysql.err.OperationalError as e:
            if e.args[0] == 1061:
                print("索引已存在，跳过：", sql)
            else:
                raise
    conn.commit()

    conn.close()


# ⭐️ 新增商品（支持关联分类）
def db_add_goods(name, price, stock=0, description=None, category_id=None):
    conn = get_conn()
    cursor = conn.cursor()
    sql = """
        INSERT INTO goods(name, price, stock, description, category_id)
        VALUES(%s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (name, price, stock, description, category_id))
    conn.commit()
    goods_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return goods_id


# ⭐️ 查询全部商品
def db_get_all_goods():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock, description, category_id FROM goods")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# 根据ID查询单个商品
def db_get_goods_by_id(goods_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, price, stock, description, category_id FROM goods WHERE id = %s",
        (goods_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


# 修改商品信息
def db_update_goods(goods_id, name=None, price=None, stock=None, description=None, category_id=None):
    conn = get_conn()
    cursor = conn.cursor()
    update_fields = []
    params = []
    if name is not None:
        update_fields.append("name = %s")
        params.append(name)
    if price is not None:
        update_fields.append("price = %s")
        params.append(price)
    if stock is not None:
        update_fields.append("stock = %s")
        params.append(stock)
    if description is not None:
        update_fields.append("description = %s")
        params.append(description)
    if category_id is not None:
        update_fields.append("category_id = %s")
        params.append(category_id)

    if not update_fields:
        conn.close()
        return False

    sql = f"UPDATE goods SET {', '.join(update_fields)} WHERE id = %s"
    params.append(goods_id)
    cursor.execute(sql, params)
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected > 0


# 删除商品
def db_delete_goods(goods_id):
    goods = db_get_goods_by_id(goods_id)
    if not goods:
        return False

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goods WHERE id = %s", (goods_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True


# ⭐️ 必须掌握：根据动态条件筛选商品
# 作用：用代码做100%精准过滤，替代大模型不靠谱的筛选
def filter_goods(goods_list, max_price=None, category=None):
    result = goods_list

    # 筛选规则1：只保留有库存的商品（固定规则）
    result = [goods for goods in result if goods["stock"] > 0]

    # 筛选规则2：按最高预算过滤
    if max_price is not None:
        result = [goods for goods in result if goods["price"] <= max_price]

    # 筛选规则3：按品类关键词过滤（商品名包含关键词即匹配）
    if category is not None and category.strip():
        keyword = category.strip()
        result = [goods for goods in result if keyword in goods["name"]]

    return result


# ===================== 分类表操作 =====================
# 新增分类
def db_add_category(name):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO category (name) VALUES (%s)", (name,))
        conn.commit()
        return cursor.lastrowid
    except pymysql.err.IntegrityError:
        # 分类名唯一，重复则返回已存在的ID
        cursor.execute("SELECT id FROM category WHERE name = %s", (name,))
        res = cursor.fetchone()
        return res["id"] if res else None
    finally:
        cursor.close()
        conn.close()


# 查询全部分类
def db_get_all_category():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM category")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


# ===================== 会话表操作 =====================
# 查询会话的历史筛选条件
def db_get_session(session_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_session WHERE session_id = %s", (session_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


# 保存/更新会话筛选条件（MySQL版本，替代sqlite的ON CONFLICT）
def db_save_session(session_id, max_price, category):
    conn = get_conn()
    cursor = conn.cursor()
    sql = """
    INSERT INTO chat_session (session_id, max_price, category)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
        max_price = %s,
        category = %s,
        update_time = CURRENT_TIMESTAMP
    """
    cursor.execute(sql, (session_id, max_price, category, max_price, category))
    conn.commit()
    cursor.close()
    conn.close()


# ===================== 进阶商品查询 =====================
# 分页+多条件查询商品
def db_query_goods(keyword=None, min_price=None, max_price=None, category_id=None, order_by="price", order="asc", page=1, page_size=10):
    conn = get_conn()
    cursor = conn.cursor()

    # 动态拼接查询条件
    sql = "SELECT * FROM goods WHERE 1=1"
    params = []

    if keyword:
        sql += " AND name LIKE %s"
        params.append(f"%{keyword}%")
    if min_price is not None:
        sql += " AND price >= %s"
        params.append(min_price)
    if max_price is not None:
        sql += " AND price <= %s"
        params.append(max_price)
    if category_id is not None:
        sql += " AND category_id = %s"
        params.append(category_id)

    # 排序
    sql += f" ORDER BY {order_by} {order}"

    # 分页：计算偏移量
    offset = (page - 1) * page_size
    sql += " LIMIT %s OFFSET %s"
    params.extend([page_size, offset])

    cursor.execute(sql, params)
    result = cursor.fetchall()

    # 同时查询总条数
    count_sql = "SELECT COUNT(*) as total FROM goods WHERE 1=1"
    count_params = params[:-2]  # 去掉分页参数
    cursor.execute(count_sql, count_params)
    total = cursor.fetchone()["total"]

    cursor.close()
    conn.close()
    return {
        "list": result,
        "total": total,
        "page": page,
        "page_size": page_size
    }


