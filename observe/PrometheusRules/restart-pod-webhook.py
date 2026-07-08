from flask import Flask, request
import subprocess
import logging
import jsonpath
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/restart-pod', methods=['POST'])
def restart_pod():
    logging.basicConfig(filename='restart-pod.log', level=logging.INFO)
    data = request.json
    pods_name = jsonpath.jsonpath(data, '$.alerts[*].labels.pod')
    logger.info(pods_name)
    # TODO: 闈炴硶JSON瑙ｆ瀽涓篵ool?
    if isinstance(pods_name, bool):
        logger.info("ignored")
        return "ignored", 200
    namespace = "test-ecmas" # 鎸夐渶淇敼
    for pod_name in pods_name:
        subprocess.run(["kubectl", "delete", "pod", pod_name, "-n", namespace])
        logger.info("kubectl delete pod:%s", pod_name)
        return "Pod restarted", 200

if __name__ == "__main__":
    app.run(host="xxxxxx", port=5000) # 鎸夐渶淇敼