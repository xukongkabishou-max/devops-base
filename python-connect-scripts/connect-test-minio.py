# pip install minio
from minio import Minio
from minio.error import S3Error
import io

# =============== 閰嶇疆淇℃伅 ===============
MINIO_ENDPOINT = "xxxxxx"
ACCESS_KEY = "xxxxxx"
SECRET_KEY = "xxxxxx"
BUCKET_NAME = "test-minio"
SECURE = False
# ======================================

client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=SECURE
)

test_object_name = "permission-test-object.txt"
test_content = b"Test content to verify MinIO read/write permission."

def test_minio_access():
    print(f"姝ｅ湪娴嬭瘯瀵?MinIO 妗?'{BUCKET_NAME}' 鐨勮鍐欐潈闄?..")
    print(f"Endpoint: http{'s' if SECURE else ''}://{MINIO_ENDPOINT}")

    try:
        found = client.bucket_exists(BUCKET_NAME)
        if not found:
            print(f"馃敂 妗?'{BUCKET_NAME}' 涓嶅瓨鍦紝姝ｅ湪鍒涘缓...")
            try:
                client.make_bucket(BUCKET_NAME)
                print(f"鉁?妗?'{BUCKET_NAME}' 宸插垱寤恒€?)
            except S3Error as e:
                if e.code == "BucketAlreadyOwnedByYou":
                    print(f"鉁?妗?'{BUCKET_NAME}' 宸插瓨鍦ㄣ€?)
                else:
                    print(f"鉂?鍒涘缓妗跺け璐? [{e.code}] {e.message}")
                    return False
        else:
            print(f"鉁?妗?'{BUCKET_NAME}' 瀛樺湪銆?)

        print(f"馃摑 姝ｅ湪娴嬭瘯鍐欐潈闄愶紙涓婁紶 {test_object_name}锛?..")
        client.put_object(
            BUCKET_NAME,
            test_object_name,
            io.BytesIO(test_content),
            length=len(test_content),
            content_type="text/plain"
        )
        print(f"鉁?鍐欐潈闄愭祴璇曢€氳繃銆?)

        print(f"馃摜 姝ｅ湪娴嬭瘯璇绘潈闄愶紙涓嬭浇 {test_object_name}锛?..")
        response = client.get_object(BUCKET_NAME, test_object_name)
        data = response.read()
        if data == test_content:
            print(f"鉁?璇绘潈闄愭祴璇曢€氳繃銆?)
        else:
            print(f"鉂?璇诲彇鍐呭涓嶄竴鑷达紒")
            return False
        response.close()
        response.release_conn()

        print(f"馃棏锔?姝ｅ湪娓呯悊娴嬭瘯瀵硅薄...")
        client.remove_object(BUCKET_NAME, test_object_name)
        print(f"鉁?娴嬭瘯瀵硅薄宸插垹闄ゃ€?)

        print(f"\n馃帀 鎵€鏈夋祴璇曢€氳繃锛佽璐﹀彿瀵规《 '{BUCKET_NAME}' 鍏锋湁瀹屾暣鐨勮鍐欐潈闄愩€?)
        return True

    except S3Error as e:
        if e.code == "AccessDenied":
            print(f"鉂?璁块棶琚嫆缁濓細鍙兘娌℃湁瀵硅妗剁殑璇诲啓鏉冮檺銆?)
        elif e.code == "NoSuchBucket":
            print(f"鉂?妗朵笉瀛樺湪涓旀棤娉曞垱寤恒€?)
        else:
            print(f"鉂?MinIO 閿欒 [{e.code}]: {e.message}")
        return False

    except Exception as e:
        print(f"鉂?杩炴帴澶辫触鎴栫綉缁滈敊璇? {e}")
        return False

if __name__ == "__main__":
    test_minio_access()