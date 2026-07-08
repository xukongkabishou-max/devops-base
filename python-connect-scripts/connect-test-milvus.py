from pymilvus import connections, utility

try:
    # 寤虹珛杩炴帴
    connections.connect(
        alias="default",
        host="xxxxxx",
        port="5272",   # 寤鸿鍐欐垚瀛楃涓?
        user="xxxxxx"
        password="xxxxxx"
    )

    # 楠岃瘉杩炴帴鏄惁鎴愬姛
    if utility.has_collection("_default"):  # _default 鏄?Milvus 鑷甫鐨勯泦鍚?
        print("鉁?Connected to Milvus successfully")
    else:
        print("鈿狅笍 Connected but no collections found")

except Exception as e:
    print(f"鉂?Failed to connect to Milvus: {e}")
