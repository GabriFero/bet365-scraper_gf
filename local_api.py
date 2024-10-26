import time
from flask_cors import CORS
from flask import Flask, request, jsonify
app = Flask(__name__)


# cn: 中文版365
language = "cn"

# en: 英文版365
# language = "en"



# Choose different DATA structures and key SUFFIX based on the version
# 根据版本选择不同的 DATA 结构 和 key 后缀
if language == "cn":
    DATA = {
        "C1A_10_0": [],
        "C18A_10_0": []
    }
    SUFFIX = "_10_0"
else:
    DATA = {
        "C1A_1_3": [],
        "C18A_1_3": []
    }
    SUFFIX = "_1_3"


def to_dit(txt):
    """
    Parse text data into dict format.
    将文本数据解析为字典格式。
    """
    dit = {}
    try:
        data = txt[:-1].split(';')
        for item in data:
            arr = item.split('=')
            if len(arr) > 1:
                dit[arr[0]] = arr[1]
    except Exception as e:
        print(f"Error in to_dit: {txt}")
    return dit

def handle_insert(it, data_obj, category_key):
    """
    插入数据到相应的 category_key。
    """
    if it not in DATA[category_key]:
        DATA[category_key].append(it)
        print(f"insert {it}")
        if it not in DATA:
            DATA[it] = data_obj

def update_data(target_key, txt):
    """
    This function parses the data, supporting U (Update), I (Insert), and D (Delete) operations, as well as the initialization of data.
    更新数据，处理 更新, 插入, 删除 操作。
    """
    action_name, action_data = txt.split('|', 1)

    if action_name == "U":
        # update event data
        # 更新比赛信息
        dit = to_dit(action_data)
        if DATA.get(target_key) and target_key.endswith(SUFFIX):
            DATA[target_key].update(dit)

    elif action_name == "I" and action_data[:2] == "EV":
        # insert event
        # 插入新的比赛
        dit = to_dit(action_data[3:])
        it = dit.get('IT')
        if not it:
            return

        if it.endswith(f"C1A{SUFFIX}"):
            handle_insert(it, dit, f"C1A{SUFFIX}")
        elif it.endswith(f"C18A{SUFFIX}"):
            handle_insert(it, dit, f"C18A{SUFFIX}")

    elif action_name == "D":
        # remove event
        # 删除比赛
        it = target_key.split("/")[-1]
        for key in [f"C1A{SUFFIX}", f"C18A{SUFFIX}"]:
            if it in DATA[key]:
                DATA[key].remove(it)
                del DATA[it]

def init_data(txt):
    """
    Parse the initial full data.
    解析初始的全量数据.
    """
    lst = txt.split("|")[1:]

    for item in lst:
        data_type = item[:2]
        data_obj = to_dit(item[3:])
        it = data_obj.get("IT")
        if not it:
            continue

        if data_type == "EV":
            if it.endswith(f"C1A{SUFFIX}"):
                handle_insert(it, data_obj, f"C1A{SUFFIX}")
            elif it.endswith(f"C18A{SUFFIX}"):
                handle_insert(it, data_obj, f"C18A{SUFFIX}")

def data_parse(txt):
    """
    parses the data
    解析数据
    """
    if txt.startswith(('\x15', '\x14')):
        item_arr = txt.split('|\x08')
        for item in item_arr:
            item = item.strip()
            action_item = item[1:].split('\x01')
            action_key = action_item[0]
            action_val = action_item[1]

            if item.startswith('\x14OVInPlay_'):
                global DATA
                DATA = {
                    f"C1A{SUFFIX}": [],
                    f"C18A{SUFFIX}": []
                }
                init_data(action_val)
            elif item.startswith('\x15'):
                update_data(action_key, action_val)


def soccer_data():
    live_lst = []
    ev_lst = DATA.get(f"C1A{SUFFIX}")
    for ev_it in ev_lst:
        info = DATA.get(ev_it)
        if info:
            try:
                TU = info['TU']
                TT = int(info['TT'])
                TS = int(info['TS'])
                TM = int(info['TM'])
                MD = info['MD']
                league = info["CT"]

                begin_ts = time.mktime(time.strptime(TU, '%Y%m%d%H%M%S'))
                now_ts = time.time() - 7 * 60 * 60 + TS
                if TM == 0 and TT == 0:
                    rel_time_set = '00:00'
                else:
                    if TT == 1:
                        rel_time_set = str(int((now_ts - begin_ts) / 60.0) + TM) + \
                                       ':' + str(int((now_ts - begin_ts) % 60.0)).zfill(2)
                    else:
                        rel_time_set = str(TM) + ":" + str(TS).zfill(2)
                if "Esoccer" in league and "mins play" in league:
                    total_mins = int(league.split(" - ")[1].split(" ")[0])
                else:
                    total_mins = 90
                if TM == total_mins / 2 and TS == 0 and TT == 0 and MD == "1":
                    period = "HalfTime"
                elif TM == total_mins and TS == 0 and TT == 0 and MD == "1":
                    period = "FullTime"
                elif TM == 0 and TS == 0 and TT == 0 and MD == "0":
                    period = "ToStart"
                else:
                    period = "FirstHalf" if MD == "0" else "SecondHalf"
                event = {
                    "id": info["C2"],
                    "event": info["NA"],
                    "league": league,
                    "time": rel_time_set,
                    "score": info["SS"],
                    "period": period
                }
                live_lst.append(event)
            except Exception as e:
                print(f"Error parsing {ev_it} : {e}")
    return live_lst

def basketball_data():
    live_lst = []
    ev_lst = DATA.get(f"C18A{SUFFIX}")
    for ev_it in ev_lst:
        info = DATA.get(ev_it)
        if info:
            try:
                TU = info['TU']
                TT = int(info['TT'])
                TS = int(info['TS'])
                TM = int(info['TM'])
                score = info["SS"]
                period = info["CP"]

                try:
                    begin_ts = int(time.mktime(time.strptime(TU, '%Y%m%d%H%M%S')))
                    now_ts = int(time.time()) - 7 * 60 * 60

                    if TT == 1:
                        if now_ts - begin_ts >= TS:
                            rel_time_set = str(TM - 1).zfill(2) + \
                                           ':' + str((60 + TS + begin_ts - now_ts)).zfill(2)
                        else:
                            rel_time_set = str(TM).zfill(2) + \
                                           ':' + str((TS + begin_ts - now_ts)).zfill(2)
                    else:
                        rel_time_set = str(TM).zfill(2) + ":" + str(TS).zfill(2)
                except:
                    rel_time_set = str(TM).zfill(2) + ":" + str(TS).zfill(2)

                event = {
                    "id": info["C2"],
                    "event": info["NA"],
                    "league": info["CT"],
                    "time": rel_time_set,
                    "score": score,
                    "period": period
                }
                live_lst.append(event)
            except Exception as e:
                print(f"Error parsing {ev_it} : {e}")
    return live_lst


@app.route('/data', methods=['GET', 'POST'])
def handle_data():
    """
    Native data requests, including receiving POST data parsing and returning GET requests.
    原生数据请求，包括接收 POST 数据解析和返回 GET 请求。
    """
    if request.method == 'POST':
        data = request.json
        try:
            data_parse(data.get("data", ""))
        except Exception as e:
            print(f"Error parsing data: {e}")
        return "1"
    elif request.method == 'GET':
        return jsonify(DATA), 200





@app.route('/live', methods=['GET'])
def live_event():
    """
    Visual and readable live data.
    可视易读的实时比赛列表数据.
    """
    sport = request.args.get("sport")
    if sport == "1":
        live_lst = soccer_data()
    elif sport == "18":
        live_lst = basketball_data()
    else:
        live_lst = []
    return jsonify(live_lst), 200

if __name__ == '__main__':
    CORS(app)
    app.run(host='0.0.0.0', port=8485, threaded=True, debug=False)
