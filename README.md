## 1_linebot_robot:

此為「運算思維與問題解決」之課堂作業，用python建置line bot機器人，而機器人共有六大功能：

### main.py

    1. 註冊、查詢帳號
       search_id(text, user_id), register_id(text, user_id)
    2. 設定作業繳交提醒、查詢作業繳交情況
       hw_notify(text, user_id), hw_check(user_id)
    3. 班級成績等第查詢
       score_ranking(text, user_id)
    4. 查詢口罩剩餘數目
       get_data(), mask_shop(text, maskdata), mask_city(text, maskdata)
    5. 簡易計算機
       calculator(text)
    6. 報告順序抽籤器
       random_order(text)
       
### linebot_server.py
    Python串接Linebot
