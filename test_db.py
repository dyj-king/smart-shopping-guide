from db import init_db, db_get_all_goods
try:
    init_db()
    print("✅ init_db 执行成功，数据库连通")
    res = db_get_all_goods()
    print("✅ 查询商品成功：", res)
except Exception as e:
    print("❌ 数据库报错！", type(e), str(e))
