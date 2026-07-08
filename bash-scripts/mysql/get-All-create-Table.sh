#!/bin/bash
DB=prod_ecmas
HOST=xxxxxx
PORT=3306
USER=xxxxxx
PWD=xxxxxx

mysql -h${HOST} -P${PORT} -u${USER} -p${PWD} -N -e "SHOW TABLES FROM \`${DB}\`" \
| while read table; do
    # 璺宠繃绌鸿
    [ -z "$table" ] && continue

    echo "---- ${table} ----" >&2

    # 鍏堣緭鍑?DROP 璇彞
    echo "DROP TABLE IF EXISTS \`${table}\`;"

    # 鍐嶈緭鍑?CREATE 璇彞锛堜繚鎸佸師鏈夐€昏緫锛?    mysql -h${HOST} -P${PORT} -u${USER} -p${PWD} -e "SHOW CREATE TABLE \`${DB}\`.\`${table}\` \\G" \
    | awk 'BEGIN{f=0} /Create Table: /{f=1; sub(/^Create Table: /,""); print; next} f{print}'
    echo -e ";\n"
done > all_create_tables.sql

