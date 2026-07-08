# pip install redis
# ================== 閰嶇疆淇℃伅 ==================
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
REDIS_HOST = "xxxxxx"
REDIS_PORT = 6379
REDIS_PASSWORD = "xxxxxx"  # 娌″瘑鐮佸氨鐣欑┖ ""
# =============================================

import redis

def test_redis_connection():
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD or None,
            socket_connect_timeout=5
        )
        # 娴嬭瘯 ping
        if r.ping():
            logging.info(
                "姝ｅ湪杩炴帴Redis 杩炴帴鍦板潃涓?IP锛歨ost=%s port锛歱ort=%s",
                REDIS_HOST,
                REDIS_PORT
            )
            print(f"鉁?鎴愬姛杩炴帴 Redis: {REDIS_HOST}:{REDIS_PORT}")
        else:
            print(f"鉂?鏃犳硶 ping Redis: {REDIS_HOST}:{REDIS_PORT}")

    except Exception as e:
        print(f"鉂?Redis 杩炴帴澶辫触: {e}")

if __name__ == "__main__":
    test_redis_connection()
