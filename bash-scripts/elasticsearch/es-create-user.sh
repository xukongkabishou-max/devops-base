curl -X PUT "https://localhost:9200/_security/user/newadmin" \
  -u admin:"$ADMIN_PW" \
  -H "Content-Type: application/json" \
  -k \
  -d '{
    "password": "xxxxxx",
    "roles": ["superuser"],
    "full_name": "New Super Admin",
    "email": "newadmin@example.com",
    "enabled": true
  }'