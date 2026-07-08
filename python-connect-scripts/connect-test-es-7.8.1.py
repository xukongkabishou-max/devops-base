# ================== 閰嶇疆淇℃伅 ==================
ES_HOST = "xxxxxx"
ES_PORT = 9200
USERNAME = "xxxxxx"
PASSWORD = "xxxxxx"
USE_SSL = False
VERIFY_CERTS = False
# =============================================

#涓嬭浇pip install elasticsearch==7.17.9

import sys
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import AuthenticationException, ConnectionError, AuthorizationException

def test_es_connection():
    scheme = "https" if USE_SSL else "http"
    es_url = f"{scheme}://{ES_HOST}:{ES_PORT}"

    try:
        # 鉁?ES 7.x 姝ｇ‘鍐欐硶
        client = Elasticsearch(
            [es_url],
            http_auth=(USERNAME, PASSWORD),
            verify_certs=VERIFY_CERTS
        )

        if client.ping():
            info = client.info()
            version = info.get("version", {}).get("number", "unknown")
            cluster_name = info.get("cluster_name", "unknown")
            print(f"鉁?鎴愬姛杩炴帴鍒?Elasticsearch [{cluster_name}]")
            print(f"馃搶 鐗堟湰: {version}")
        else:
            print("鈿狅笍 鏃犳硶 ping 閫?ES锛岃妫€鏌ラ厤缃?)

    except AuthenticationException:
        print("鉂?璁よ瘉澶辫触锛岃妫€鏌ョ敤鎴峰悕鎴栧瘑鐮?)
        sys.exit(1)
    except AuthorizationException:
        print("鉂?鎺堟潈澶辫触锛屽綋鍓嶇敤鎴锋病鏈夋潈闄?)
        sys.exit(1)
    except ConnectionError:
        print("鉂?鏃犳硶杩炴帴鍒?Elasticsearch锛岃妫€鏌ョ綉缁?绔彛/闃茬伀澧?)
        sys.exit(1)
    except Exception as e:
        print(f"鉂?鍙戠敓鏈煡閿欒: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_es_connection()
