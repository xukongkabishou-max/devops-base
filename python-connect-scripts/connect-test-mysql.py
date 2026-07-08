# pip install pymysql


import pymysql
# ================== 閰嶇疆淇℃伅 ==================
MYSQL_HOST = "xxxxxx"
MYSQL_PORT = 9030
USERNAME = "xxxxxx"
PASSWORD = "xxxxxx"
# =============================================

def test_mysql_login():
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=USERNAME,
            password=PASSWORD,
            connect_timeout=5
        )
        print(f"鉁?鎴愬姛杩炴帴 MySQL: {MYSQL_HOST}:{MYSQL_PORT}锛岃处鍙? {USERNAME}")
    except pymysql.err.OperationalError as e:
        print(f"鉂?鐧诲綍澶辫触: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    test_mysql_login()

