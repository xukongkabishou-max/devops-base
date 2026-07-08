# pip install confluent-kafka -i https://pypi.tuna.tsinghua.edu.cn/simple
from confluent_kafka import Producer, Consumer, KafkaException

# **娉ㄦ剰: 妫€鏌ヨ繖閲岀殑 IP 鍦板潃鏄惁姝ｇ‘**
BOOTSTRAP_SERVERS = "xxxxxx"
TOPIC = "test-topic"

def test_producer():
    """娴嬭瘯鐢熶骇鑰?""
    conf = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        # 鏂板: 蹇€熷け璐ヨ缃紝閬垮厤闀挎椂闂撮樆濉?
        "socket.timeout.ms": 2000,
        "reconnect.backoff.max.ms": 5000, # 閲嶈繛鏈€澶х瓑寰呮椂闂?
    }
    producer = Producer(conf)

    try:
        producer.produce(TOPIC, key="key1", value="hello kafka")

        # 鏄惧紡璋冪敤 poll() 鏉ヨЕ鍙戦敊璇鐞嗗拰鍥炶皟
        producer.poll(0)

        # flush() 浼氱瓑寰呮墍鏈夋湭鍐虫秷鎭鍙戦€侊紝濡傛灉杩炴帴澶辫触锛屽畠浼氱瓑寰呰秴鏃?
        # 榛樿 flush() 鏄棤闄愮瓑寰咃紝浣嗙敱浜庢垜浠缃簡 socket.timeout.ms锛屽畠浼氬皾璇曞湪杩欎釜鏃堕棿鍐呭畬鎴?
        result = producer.flush(timeout=10) # 璁剧疆涓€涓槑纭殑 flush 瓒呮椂鏃堕棿

        if result == 0:
             print("鉁?鐢熶骇鑰呮秷鎭彂閫佹垚鍔?宸插鐞嗗畬鎴?)
        else:
             print(f"鈿狅笍 鐢熶骇鑰呮秷鎭鐞嗚秴鏃舵垨澶辫触 (鏈彂閫佹暟閲? {result})")

    except KafkaException as e:
        print("鉂?鐢熶骇鑰呭嚭閿?", e)

def test_consumer():
    """娴嬭瘯娑堣垂鑰?""
    conf = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": "test-group",
        "auto.offset.reset": "earliest",
        # 鏂板: 蹇€熷け璐ヨ缃?
        "socket.timeout.ms": 2000,
        "reconnect.backoff.max.ms": 5000,
    }
    # ... (娑堣垂鑰呬唬鐮佷繚鎸佷笉鍙?
    consumer = Consumer(conf)
    consumer.subscribe([TOPIC])

    try:
        msg = consumer.poll(5.0)  # 绛夊緟 5 绉?
        if msg is None:
            print("鈿狅笍 娌℃湁鏀跺埌娑堟伅")
        elif msg.error():
            # 杩欓噷鐨勯敊璇€氬父灏辨槸杩炴帴澶辫触
            print("鉂?娑堣垂鑰呭嚭閿?", msg.error())
        else:
            print(f"鉁?鏀跺埌娑堟伅: key={msg.key()}, value={msg.value().decode()}")
    finally:
        # 纭繚 close() 琚皟鐢ㄤ互閲婃斁璧勬簮
        consumer.close()

if __name__ == "__main__":
    test_producer()
    test_consumer()




