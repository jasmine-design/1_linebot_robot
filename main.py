import urllib.request, csv, json
from ExampleData import department_table
from ExampleData import route_table
from requests import request
import re
import random
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

RegisteredData_path = './registered_data.json'

# Global variable
student_data = dict()

# 功能一：註冊、查詢帳號

def search_id(text, user_id):  # text => 接收到的訊息字串;   user_id => User的Line ID

    student_data = dict()  # 學生資料

    x = text[-9:-7]
    y = text[-4:-3]
    department = department_table.get(x)  # 學號對應的系所_拿到學號前兩碼
    route = route_table.get(y)  # 入學管道_倒數第四碼

    student_id = text[-9:]
    student_name = text[5:-13]
    student_data[student_id] = {'name': student_name, 'user_id': user_id}

    return ('您的系所是 ' + department + ' ，入學管道是 ' + route, student_data)

def register_id(text, user_id):  # text => 接收到的訊息字串(Ex. '姓名:王曉明/學號:A01234567');   user_id => User的Line系統ID

    url = 'https://playlab.computing.ncku.edu.tw:8000/student-list/1/csv'  # CTPS 2021 Spring 修課名單下載連結
    webpage = urllib.request.urlopen(url)
    data = csv.DictReader(webpage.read().decode('utf-8-sig').splitlines())  # 下載的修課名單

    # Todo:
    # 1. 判斷傳入訊息的姓名、學號是否存在於修課名單，不存在則回覆 '使用者資料錯誤，請重新輸入，謝謝！'
    # 2. 倘若該user_id已註冊，回覆 '您已經註冊過囉！'
    # 3. 將使用者的資訊依下列格式的 dictionary 存放至 registered_data.json，並回覆 '註冊成功！'
    # {
    #     user_id: {
    #         "Name": name,
    #         "Student_ID": student_id,
    #     }
    # }

    student_id = text[-9:]
    student_name = text[3:-13]
    flag = False

    for row in data:
        id = str(row["學號"])
        name = str(row["姓名"])
        if student_id in id and student_name in name:
            flag = True
            break

    if flag:
        with open(RegisteredData_path, 'r') as f:
            user = json.load(f)

        if user_id in user.keys():
            reply = '您已經註冊過囉！'

        else:
            user[user_id] = {"Name": student_name, "Student_ID": student_id}
            with open(RegisteredData_path, 'w', encoding='utf-8') as f2:
                json.dump(user, f2, ensure_ascii=False, indent=4)
            reply = '註冊成功！'

    else:
        reply = '使用者資料錯誤，請重新輸入，謝謝！'


    return reply

# 功能二：設定作業繳交提醒、查詢作業繳交情況

def hw_notify(text, user_id):
    with open(RegisteredData_path, 'r') as f:
        user = json.load(f)
    if user_id not in user.keys():
        return "請先註冊，謝謝！"

    weekday = text[4:5]
    weekday_list = ['ㄧ', '二', '三', '四', '五', '六', '日']
    time = text[6:8]
    time_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    if weekday not in weekday_list: return "星期輸入錯誤！"
    if text[6:7] not in ['0', '1', '2'] or text[7:8] not in time_list: return "時間輸入錯誤！"

    user[user_id]["Notify"] = {'Day': weekday, 'Hour': time}

    with open(RegisteredData_path, 'w', encoding='utf-8') as f2:
        json.dump(user, f2, ensure_ascii=False, indent=4)

    reply = '設定成功！將於星期{}的{}點提醒'.format(weekday, time)

    return reply

def hw_check(user_id):
    url = 'https://playlab.computing.ncku.edu.tw:8000/homework-record/1/json'  # 作業繳交紀錄 url
    homework_record = json.loads(request('GET', url).text)

    with open(RegisteredData_path, 'r') as f:
        user = json.load(f)
    if user_id not in user.keys(): return "請先註冊，謝謝！"

    target_id = user[user_id]["Student_ID"]
    hw_list = [record["HW"] for record in homework_record if record["Student_ID"] == target_id]
    if not hw_list:
        reply = "已繳交作業：無"
    else:
        reply = "已繳交作業：" + " ".join(hw_list)

    return reply

# 功能三：班級成績等第查詢

def score_ranking(text, user_id):
    score_table = '/Users/jasmine/PycharmProjects/HW2/score_table.json'
    ranking = text[11:-3]

    flag = False
    with open(RegisteredData_path, 'r') as f:
        user = json.load(f)
    if user_id in user.keys():
        flag = True
    score_range = {"excellent": [85, 100],
                   "good": [70, 84],
                   "notbad": [50, 69],
                   "bad": [35, 49],
                   "unbelievable": [0, 34]}
    if flag and ranking in ["excellent", "good", "notbad", "bad", "unbelievable"]:
        with open(score_table, 'r') as f:
            student_score = json.load(f)
        num = len(
            [score for score in student_score.values() if score_range[ranking][0] <= score <= score_range[ranking][1]])
        reply = "共有{}位同學".format(num)
    elif not flag:
        reply = '請先註冊，謝謝！'
    else:
        reply = "沒有這個等第！"

    return reply

# 功能四：查詢口罩剩餘數目

def get_data():
    url = 'https://data.nhi.gov.tw/resource/mask/maskdata.csv'  # 衛服部口罩存量即時資料下載連結
    # 自 url 位址下載口罩存量即時資料，解讀為csv並放入data
    webpage = urllib.request.urlopen(url)
    mask_data = csv.reader(webpage.read().decode('utf-8-sig').splitlines())
    data = list()
    for row in mask_data:
        data.append(row)
    return data

def mask_shop(text, maskdata):
    # text => 接收到的訊息字串(Ex. '機構:臺南市東區衛生所剩下多少成人口罩');    maskdata => 已下載的口罩存量資料

    # Todo:
    # 1. 若類型輸入錯誤，回覆 '口罩類型輸入錯誤！'
    # 2. 若機構名稱不存在，回覆 '醫事機構不存在！'
    # 3. 若該機構仍存有口罩，回覆 '還有XX個'
    # 4. 若該機構已無口罩，回覆 '已經銷售一空了！'

    global reply
    mask_type = text[-4:-2]
    organization = text[3:-8]
    pos_adult = mask_type.find('成人')
    pos_child = mask_type.find('兒童')
    flag = False
    for row in maskdata:
        if organization in row:
            flag = True
            break
    if flag:
        for row in maskdata:
            if organization in row:
                if pos_adult != -1:
                    if row[-3] == 0:
                        reply = '已經銷售一空了！'
                    else:
                        reply = "還有{}個".format(row[-3])
                elif pos_child != -1:
                    if row[-2] == 0:
                        reply = '已經銷售一空了！'
                    else:
                        reply = "還有{}個".format(row[-2])
                elif pos_adult == -1 and pos_child == -1:
                    reply = '口罩類型輸入錯誤！'
    elif not flag:
        reply = '醫事機構不存在！'

    return reply

def mask_city(text, maskdata):

    # text => 接收到的訊息字串(Ex. '地區:臺南市剩下多少兒童口罩');  maskdata => 已下載的口罩存量資料

    # Todo:
    # 1. 若類型輸入錯誤，回覆 '口罩類型輸入錯誤！'
    # 2. 若地區名稱不存在，回覆 '醫事機構不存在！'
    # 3. 若該地區仍存有口罩，回覆 '還有XX個'
    # 4. 若該地區已無口罩，回覆 '已經銷售一空了！'

    global reply
    mask_type = text[-4:-2]
    city = text[3:-8]
    pos_adult = mask_type.find('成人')
    pos_child = mask_type.find('兒童')
    flag = False

    for row in maskdata:
        if any(city in s for s in row):
            flag = True
            break

    if flag:
        adult_num = 0
        child_num = 0
        for row in maskdata:
            if any(city in s for s in row):
                if pos_adult != -1:
                    adult_num += int(row[-3])
                elif pos_child != -1:
                    child_num += int(row[-2])
                elif pos_adult == -1 and pos_child == -1:
                    reply = '口罩類型輸入錯誤！'
        if pos_adult != -1:
            reply = '還有{}個'.format(adult_num)
        if pos_child != -1:
            reply = '還有{}個'.format(child_num)

    else:
        reply = '醫事機構不存在！'

    return reply

# 功能五：簡易計算機

def mul(processor):
    a = re.search(r"(\d+)?[.]?(\d+)[\*]", processor).group()[:-1]
    b = re.search(r"[\*]\d+[.]?(\d+)?", processor).group()[1:]
    ans = float(a) * float(b)
    ans = str(ans)
    processor_past = re.sub(r"\d+[.]?(\d+)?[*]\d+[.]?(\d+)?", ans, processor, count=1)

    return processor_past

def div(processor):
    a = re.search(r"(\d+)?[.]?(\d+)[/]", processor).group()[:-1]
    b = re.search(r"[/]\d+[.]?(\d+)?", processor).group()[1:]
    ans = float(a) / float(b)
    ans = str(ans)
    processor_past = re.sub(r"\d+[.]?(\d+)?[/]\d+[.]?(\d+)?", ans, processor, count=1)
    return processor_past

def add(processor):
    a = re.search("(\d+)?[.]?(\d+)[+]", processor).group()[:-1]
    b = re.search("[+]\d+[.]?(\d+)?", processor).group()[1:]
    ans = float(a) + float(b)
    ans = str(ans)
    processor_past = re.sub(r"\d+[.]?(\d+)?[+]\d+[.]?(\d+)?", ans, processor, count=1)
    return processor_past

def sub(processor):
    a = re.search("\d+[.]?(\d+)?[-]", processor).group()[:-1]
    b = re.search("[-]\d+[.]?(\d+)?", processor).group()[1:]
    ans = float(a) - float(b)
    ans = str(ans)
    processor_past = re.sub(r"\d+[.]?(\d+)?[-]\d+[.]?(\d+)?", ans, processor, count=1)
    return processor_past

def calculator(text):
    if re.search("[\*,/]", text):
        a = re.search("[\*,/]", text).group()
        if a == '*':
            text = mul(text)
        if a == '/':
            text = div(text)

        return HW6_1(text)
    else:
        for cul in text:
            if re.search("[+]", cul):
                text = add(text)
        for cul in text:
            if re.search("[-]", cul):
                text = sub(text)

        return round(float(text), 2)

# 功能六：報告順序抽籤器

def random_order(text):
    num = text[3:-8]
    num_list = [i for i in range(1, int(num) + 1)]
    random.shuffle(num_list)
    if int(num) <= 0:
        return "組別不能少於1組喔"
    reply = "報告順序：第{}組".format(num_list[0])
    for i in range(1, int(num)):
        reply += "→第{}組".format(num_list[i])

    return reply


if __name__ == '__main__':
    # print(search_id("查詢姓名:林玟其/學號:F34086074", "U9f1523bf3ce0f0faeb481d617b865633"))
    # print(register_id("姓名:林玟其/學號:F34086074", "U9f1523bf3ce0f0faeb481d617b865633"))
    # print(hw_notify(text='請在每週五的12時提醒我作業進度', user_id='U9f1523bf3ce0f0faeb481d617b865633'))
    # print(hw_check(user_id='U9f1523bf3ce0f0faeb481d617b865633'))

    # print(score_ranking(text='請問全班有幾位同學拿到bad的成績', user_id = "U9f1523bf3ce0f0faeb481d617b865633"))

    # print(get_data())
    # print(mask_shop('機構：保康藥局剩下多少兒童口罩', get_data()))
    # print(mask_city('地區：嘉義市剩下多少兒童口罩', get_data()))

    # print(calculator(text="計算3.6+10.5-8.2等於多少"[2:-4]))

    print(random_order(text="請排出10個小組的報告順序"))
