
# ========== 错误码定义 ==========
CODE_SUCCESS = 0          # 成功
CODE_PARAM_ERROR = 1001   # 参数校验错误
CODE_BUSINESS_ERROR = 2001 # 业务逻辑异常
CODE_SYSTEM_ERROR = 5000  # 系统内部错误

# 统一成功返回
def success(data=None, msg="成功"):
    return {
        "code": CODE_SUCCESS,
        "msg": msg,
        "data": data
    }

# 统一失败返回
def error(code=CODE_SYSTEM_ERROR, msg="请求失败"):
    return {
        "code": code,
        "msg": msg,
        "data": None
    }


import logging
import os
from datetime import datetime

# ========== 日志系统配置 ==========
# 自动创建日志文件夹
if not os.path.exists("logs"):
    os.makedirs("logs")

# 配置日志：控制台 + 文件双输出
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler(
            f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
            encoding="utf-8"
        )  # 输出到日志文件，按天生成
    ]
)

# 全局日志实例，所有文件都可以导入使用
logger = logging.getLogger(__name__)


