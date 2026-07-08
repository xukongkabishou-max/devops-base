#!/bin/bash
# ES 绱㈠紩杩佺Щ鑴氭湰
# 婧怑S鍜岀洰鏍嘐S璐﹀彿瀵嗙爜闇€瑕佽嚜宸变慨鏀?
# 妫€鏌ユ槸鍚﹀畨瑁?elasticdump锛屽鏋滄病鏈夊垯瀹夎
if ! command -v elasticdump &> /dev/null
then
    echo "elasticdump 鏈畨瑁咃紝寮€濮嬪畨瑁?.."
    # 瀹夎 Node.js 鍜?npm锛堝鏋滄病鏈夌殑璇濓級
    if ! command -v npm &> /dev/null
    then
        echo "璇峰厛瀹夎 Node.js 鍜?npm"
        exit 1
    fi
    npm install -g elasticdump
    echo "elasticdump 瀹夎瀹屾垚"
fi

# 婧怑S鍜岀洰鏍嘐S淇℃伅
SRC_ES="http://xxxxxx:xxxxxx@xxxxxx:9200"
DST_ES="http://xxxxxx:xxxxxx@xxxxxx:9200"

# 瑕佽縼绉荤殑绱㈠紩鍒楄〃
INDEX_LIST=("recommends" "posts" "com.zzxy.chunk" "com.smart.chunk_v0")

# 寰幆杩佺Щ姣忎釜绱㈠紩
for my_index in "${INDEX_LIST[@]}"
do
    echo "===================="
    echo "寮€濮嬭縼绉荤储寮? $my_index"

    # 杩佺Щ settings
    elasticdump \
        --input="$SRC_ES/$my_index" \
        --output="$DST_ES/$my_index" \
        --type=settings

    # 杩佺Щ analyzer
    elasticdump \
        --input="$SRC_ES/$my_index" \
        --output="$DST_ES/$my_index" \
        --type=analyzer

    # 杩佺Щ mapping
    elasticdump \
        --input="$SRC_ES/$my_index" \
        --output="$DST_ES/$my_index" \
        --type=mapping

    # 杩佺Щ data
    elasticdump \
        --input="$SRC_ES/$my_index" \
        --output="$DST_ES/$my_index" \
        --type=data

    echo "绱㈠紩 $my_index 杩佺Щ瀹屾垚"
done

echo "鎵€鏈夌储寮曡縼绉诲畬鎴?
