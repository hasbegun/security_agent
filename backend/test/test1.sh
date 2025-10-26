# # simple hellow
# curl -X POST "http://127.0.0.1:8000/api/chat" \
#      -H "Content-Type: application/json" \
#      -d '{"query": "hellow are you there listening", "user_id": "test_user"}'

# echo "\n=====\n\n"
# # # policy search
# curl -X POST "http://127.0.0.1:8000/api/chat" \
# -H "Content-Type: application/json" \
# -d '{"query": "How do I handle phishing?", "user_id": "test_user"}'


# # echo "\n=====\n\n"
# # # log query
# curl -X POST "http://127.0.0.1:8000/api/chat" \
#      -H "Content-Type: application/json" \
#      -d '{"query": "show me todays failed login attempts", "user_id": "test_user"}'

# echo "\n=====\n\n"
# # general questions
# curl -X POST "http://127.0.0.1:8000/api/chat" \
#      -H "Content-Type: application/json" \
#      -d '{"query": "what can you help me?", "user_id": "test_user"}'

# curl -X POST "http://127.0.0.1:8000/api/chat" \
# -H "Content-Type: application/json" \
# -d '{"query": "can you modify data for me", "user_id": "test_user"}'


# echo "\n=====\n\n"
# # bogus requests
curl -X POST "http://127.0.0.1:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "rere", "user_id": "test_user"}'

# curl -X GET "http://127.0.0.1:8000/api/audit-logs"