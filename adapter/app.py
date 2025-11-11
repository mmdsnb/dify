import os
import logging
import sys
from flask import Flask, jsonify, request
from werkzeug.exceptions import Unauthorized
from sqlalchemy import create_engine, text
from functools import wraps

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 数据库连接配置
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "difyai123456")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_DATABASE = os.getenv("DB_DATABASE", "dify")
ADAPTER_API_KEY = os.getenv("ADAPTER_API_KEY", "")

# 创建数据库引擎
DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def require_api_key(f):
    """API Key 鉴权装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise Unauthorized("Authorization header must be provided with Bearer token")

        token = auth_header.replace("Bearer ", "")

        if not ADAPTER_API_KEY:
            raise Unauthorized("ADAPTER_API_KEY not configured on server")

        if token != ADAPTER_API_KEY:
            raise Unauthorized("Invalid API key")

        return f(*args, **kwargs)

    return decorated_function


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "healthy"}), 200


@app.route("/apps/by-ids", methods=["GET", "POST"])
@require_api_key
def get_apps_by_ids():
    """
    根据 IDs 查询应用信息（无数量限制）

    GET 请求参数: ?ids=id1,id2,id3
    POST 请求体: {"ids": ["id1", "id2", "id3"]}

    返回格式:
    {
        "data": [
            {
                "id": "...",
                "code": "app-name",
                "name": "app-name",
                "description": "...",
                "api_key": "app-xxx...",
                "mode": "chat",
                "enable_api": true
            }
        ]
    }
    """
    try:
        # 获取 IDs 参数
        if request.method == "GET":
            ids_param = request.args.get("ids", "")
            if not ids_param:
                return jsonify({"error": "Bad Request", "message": "ids parameter is required"}), 400
            app_ids = [id.strip() for id in ids_param.split(",") if id.strip()]
        else:  # POST
            data = request.get_json()
            if not data or "ids" not in data:
                return jsonify({"error": "Bad Request", "message": "ids field is required in request body"}), 400
            app_ids = data.get("ids", [])

        if not app_ids:
            return jsonify({"error": "Bad Request", "message": "At least one id is required"}), 400

        with engine.connect() as conn:
            # 构建 IN 查询
            placeholders = ",".join([f":id{i}" for i in range(len(app_ids))])
            query = text(f"""
                SELECT
                    a.id,
                    a.name,
                    a.description,
                    a.mode,
                    a.enable_api,
                    at.token as api_key
                FROM apps a
                LEFT JOIN api_tokens at ON a.id = at.app_id AND at.type = 'app'
                WHERE a.id IN ({placeholders})
                  AND a.enable_api = true
                  AND a.status = 'normal'
                ORDER BY a.created_at DESC
            """)

            # 构建参数字典
            params = {f"id{i}": app_id for i, app_id in enumerate(app_ids)}
            result = conn.execute(query, params)
            rows = result.fetchall()

            apps = []
            for row in rows:
                apps.append({
                    "id": str(row.id),
                    "code": row.name,
                    "name": row.name,
                    "description": row.description or "",
                    "api_key": row.api_key or None,
                    "mode": row.mode,
                    "enable_api": row.enable_api
                })

            return jsonify({
                "data": apps
            }), 200

    except Exception as e:
        app.logger.error(f"Error fetching apps by ids: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/apps", methods=["GET"])
@require_api_key
def get_apps():
    """
    获取所有应用及其 API Key

    返回格式:
    {
        "data": [
            {
                "code": "app-name",
                "name": "app-name",
                "description": "app description",
                "api_key": "app-xxx...",
                "mode": "chat",
                "enable_api": true
            }
        ],
        "total": 1
    }
    """
    logger.info("开始获取应用列表")
    try:
        with engine.connect() as conn:
            logger.info("数据库连接成功")
            # 查询所有启用 API 的正常应用及其 API Token
            query = text("""
                SELECT
                    a.id,
                    a.name,
                    a.description,
                    a.mode,
                    a.enable_api,
                    at.token as api_key
                FROM apps a
                LEFT JOIN api_tokens at ON a.id = at.app_id AND at.type = 'app'
                WHERE a.enable_api = true AND a.status = 'normal'
                ORDER BY a.created_at DESC
            """)

            logger.info(f"执行查询: {query}")
            result = conn.execute(query)
            rows = result.fetchall()
            logger.info(f"查询结果行数: {len(rows)}")

            apps = []
            for i, row in enumerate(rows):
                logger.info(f"处理第 {i+1} 行数据: id={row.id}, name={row.name}, api_key={row.api_key}")
                app_data = {
                    "id": str(row.id),
                    "code": row.name,  # 使用 name 作为 code
                    "name": row.name,
                    "description": row.description or "",
                    "api_key": row.api_key or None,
                    "mode": row.mode,
                    "enable_api": row.enable_api
                }
                logger.info(f"构建的应用数据: {app_data}")
                apps.append(app_data)

            response_data = {
                "data": apps,
                "total": len(apps)
            }
            logger.info(f"返回响应数据: {response_data}")
            return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"获取应用列表时发生错误: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.errorhandler(Unauthorized)
def handle_unauthorized(e):
    """处理 401 错误"""
    return jsonify({"error": "Unauthorized", "message": str(e)}), 401


@app.errorhandler(404)
def handle_not_found(e):
    """处理 404 错误"""
    return jsonify({"error": "Not found", "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def handle_internal_error(e):
    """处理 500 错误"""
    return jsonify({"error": "Internal server error", "message": str(e)}), 500


if __name__ == "__main__":
    # 启动时检查必需的环境变量
    if not ADAPTER_API_KEY:
        logger.warning("ADAPTER_API_KEY is not set. API will reject all requests.")
    else:
        logger.info("ADAPTER_API_KEY is configured")

    logger.info(f"数据库连接配置: {DATABASE_URL}")
    logger.info("启动 Flask 应用...")
    
    # 启动 Flask 应用
    app.run(host="0.0.0.0", port=5003, debug=False)
    print("haha")
