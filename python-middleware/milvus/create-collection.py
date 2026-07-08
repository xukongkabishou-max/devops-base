import logging
from typing import Any, Dict, List

from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema

# =========================================================
# 閰嶇疆淇℃伅
# =========================================================
SRC_URI = "http://xxxxxx:19530"
SRC_TOKEN = "xxxxxx"
SRC_DB = "alg_service_forecast"

DST_URI = "http://xxxxxx:5272"
DST_TOKEN = "xxxxxx"
DST_DB = "test"




INCLUDE_COLLECTIONS: List[str] = ["histories"]  # 濉叆浣犺鍚屾鐨?Collection 鍚嶇О锛屼负绌哄垯鍚屾鍏ㄩ儴
RECREATE_IF_EXISTS = True  # 寤鸿璁句负 True 浠ユ竻鐞嗕箣鍓嶅け璐ョ殑娈嬬暀缁撴瀯
FORCE_DYNAMIC = True  # 寮哄埗寮€鍚洰鏍囩鐨勫姩鎬?Schema
DEFAULT_VECTOR_INDEX_TYPE = "HNSW"
DEFAULT_METRIC_TYPE = "IP"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def build_collection_schema(desc: Dict[str, Any]) -> CollectionSchema:
    """
    閽堝 Array, JSON, VarChar 浼樺寲鐨?Schema 鏋勫缓鍣?
    瑙ｅ喅浜?'element data type None is not valid' 绛夊厓鏁版嵁涓㈠け闂
    """
    fields: List[FieldSchema] = []

    for f in desc["fields"]:
        # 1. 杩囨护绯荤粺瀛楁
        if f.get("name") == "$meta":
            continue

        field_name = f["name"]
        # 杞崲鏁版嵁绫诲瀷涓烘灇涓?
        field_type = f["type"] if isinstance(f["type"], (int, DataType)) else DataType[f["type"]]

        # 鑾峰彇婧愮鍙傛暟瀛楀吀
        params = f.get("params") or {}
        if isinstance(params, str): params = {}

        # 2. 鏋勯€?FieldSchema 鐨勫熀纭€鍙傛暟
        field_kwargs = {
            "name": field_name,
            "dtype": field_type,
            "is_primary": f.get("is_primary", False),
            "description": f.get("description", ""),
            "is_partition_key": f.get("is_partition_key", False),
            "auto_id": f.get("auto_id", False),
        }

        # 3. 閽堝鎬ф彁鍙栫壒瀹氱被鍨嬬殑灞炴€э紙瑙ｅ喅鎶ラ敊鐨勫叧閿級

        # --- 澶勭悊 VarChar ---
        if field_type == DataType.VARCHAR:
            max_len = f.get("max_length") or params.get("max_length")
            if max_len:
                field_kwargs["max_length"] = int(max_len)

        # --- 澶勭悊 Array (閽堝浣犵殑 tags 瀛楁) ---
        elif field_type == DataType.ARRAY:
            # 鎻愬彇鍏冪礌绫诲瀷
            e_type = f.get("element_type") or params.get("element_type")
            if e_type:
                field_kwargs["element_type"] = e_type if isinstance(e_type, (int, DataType)) else DataType[e_type]

            # 鎻愬彇鏁扮粍鏈€澶у閲?
            max_cap = f.get("max_capacity") or params.get("max_capacity")
            if max_cap:
                field_kwargs["max_capacity"] = int(max_cap)

            # 濡傛灉鏁扮粍鍏冪礌鏄?VarChar锛岃繕闇€瑕佹寚瀹氬厓绱犵殑鏈€澶ч暱搴?
            if field_kwargs.get("element_type") == DataType.VARCHAR:
                e_max_len = f.get("max_length") or params.get("max_length")
                if e_max_len:
                    field_kwargs["max_length"] = int(e_max_len)

        # --- 澶勭悊 Vector ---
        elif field_type in [DataType.FLOAT_VECTOR, DataType.BINARY_VECTOR, DataType.FLOAT16_VECTOR,
                            DataType.BFLOAT16_VECTOR]:
            dim = f.get("dim") or params.get("dim")
            if dim:
                field_kwargs["dim"] = int(dim)

        # --- 澶勭悊 JSON ---
        # JSON 绫诲瀷鍦?Milvus 涓€氬父涓嶉渶瑕侀澶栧弬鏁?

        # 娓呯悊 params 涓凡鍖呭惈鍦?field_kwargs 閲岀殑閲嶅閿紝闃叉浼犲弬鍐茬獊
        for k in list(params.keys()):
            if k in field_kwargs:
                params.pop(k)

        # 鍚堝苟鍓╀綑鍙傛暟骞跺垱寤哄瓧娈?
        field_kwargs.update(params)
        fields.append(FieldSchema(**field_kwargs))

    # 4. 鏋勫缓骞惰繑鍥炲畬鏁?Schema
    schema = CollectionSchema(
        fields=fields,
        description=desc.get("description", ""),
        enable_dynamic_field=FORCE_DYNAMIC if FORCE_DYNAMIC else desc.get("enable_dynamic_field", False)
    )
    return schema


def sync_indexes(src: MilvusClient, dst: MilvusClient, col_name: str):
    """鎻愬彇婧愮储寮曞苟鍦ㄧ洰鏍囧垱寤?""
    try:
        indexes = src.list_indexes(col_name)
        if not indexes:
            logging.warning(f"Collection {col_name} 鏃犲師濮嬬储寮?)
            return False

        for idx_name in indexes:
            idx_info = src.describe_index(col_name, idx_name)
            if isinstance(idx_info, list): idx_info = idx_info[0]

            field_name = idx_info.get("field_name")
            index_params = MilvusClient.prepare_index_params()

            m_type = idx_info.get("metric_type") or DEFAULT_METRIC_TYPE
            i_type = idx_info.get("index_type") or DEFAULT_VECTOR_INDEX_TYPE
            extra_params = idx_info.get("params") or {}
            if not isinstance(extra_params, dict): extra_params = {}

            index_params.add_index(
                field_name=field_name,
                index_name=idx_name,
                index_type=i_type,
                metric_type=m_type,
                params=extra_params
            )

            logging.info(f"姝ｅ湪鐩爣鍒涘缓绱㈠紩: {col_name} -> {field_name} ({i_type})")
            dst.create_index(collection_name=col_name, index_params=index_params)
        return True
    except Exception as e:
        logging.error(f"绱㈠紩鍚屾澶辫触 {col_name}: {e}")
        return False


def clone_collection(src: MilvusClient, dst: MilvusClient, name: str):
    """鎵ц Collection 缁撴瀯鐨勫鍒?""
    # 1. 澶勭悊鍐茬獊
    if dst.has_collection(name):
        if RECREATE_IF_EXISTS:
            logging.info(f"鐩爣宸插瓨鍦紝姝ｅ湪閲嶅缓: {name}")
            dst.drop_collection(name)
        else:
            logging.info(f"鐩爣宸插瓨鍦紝璺宠繃鍒涘缓: {name}")
            sync_indexes(src, dst, name)
            dst.load_collection(name)
            return

    # 2. 杞崲 Schema
    logging.info(f"姝ｅ湪鍚屾缁撴瀯: {name} ...")
    desc = src.describe_collection(name)
    schema = build_collection_schema(desc)

    # 3. 鍒涘缓 Collection
    dst.create_collection(
        collection_name=name,
        schema=schema
    )
    logging.info(f"鎴愬姛鍒涘缓 Collection: {name}")

    # 4. 鍚屾绱㈠紩
    index_success = sync_indexes(src, dst, name)

    # 5. 鍔犺浇
    if index_success:
        dst.load_collection(name)
        logging.info(f"宸叉垚鍔熷姞杞?Collection: {name}")


def main():
    # 鍒濆鍖栧鎴风
    src = MilvusClient(uri=SRC_URI, token=SRC_TOKEN, db_name=SRC_DB)
    dst = MilvusClient(uri=DST_URI, token=DST_TOKEN, db_name=DST_DB)

    # 纭繚鐩爣鏁版嵁搴撳瓨鍦?
    dbs = dst.list_databases()
    if DST_DB not in dbs:
        logging.info(f"姝ｅ湪鍒涘缓鐩爣鏁版嵁搴? {DST_DB}")
        dst.create_database(DST_DB)

    # 鑾峰彇寰呭悓姝ュ垪琛?
    all_cols = src.list_collections()
    target_cols = INCLUDE_COLLECTIONS if INCLUDE_COLLECTIONS else all_cols

    for col in target_cols:
        try:
            clone_collection(src, dst, col)
        except Exception as e:
            logging.error(f"鍚屾 {col} 澶辫触: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()