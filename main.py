from venv import logger
import requests
from datetime import datetime
import sys
import json
import yaml
# 默认配置
DEFAULT_CONFIG = {
    'CORPID': '',
    'CORPSECRET': '',
    'AGENTID': '',
    'START_ADDRESS': '',
    'ARRIVAl_ADDRESS': '',
    'START_DATE': '',
    'END_DATE': '',
}


def load_config():
    try:
        systemencoding = sys.getfilesystemencoding()
        logger.info(f"Load_Config_Nomal:{systemencoding}")
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        # Generate a new key pair
        systemencoding = sys.getfilesystemencoding()
        logger.info(f"Load_Config_Exception:{systemencoding}")
        logger.error(e)
        config = DEFAULT_CONFIG
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(DEFAULT_CONFIG, file)

    return config

# 加载配置
try:
    CONFIG = load_config()
    # 企业微信配置
    CORPID = CONFIG['CORPID']
    CORPSECRET = CONFIG['CORPSECRET']
    AGENTID = CONFIG['AGENTID']
    START_ADDRESS = CONFIG['START_ADDRESS']
    ARRIVAl_ADDRESS = CONFIG['ARRIVAl_ADDRESS']
    START_DATE = CONFIG['START_DATE']
    END_DATE = CONFIG['END_DATE']
except KeyError as e:
    logger.error(f"Config '{e}'Not Found")
    sys.exit(1)



class WeChatPush:
    def __init__(self, corpid, corpsecret, agentid):
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid
        self.access_token = self.get_access_token()

    def send_text_message(self, message):
        send_text_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(self.access_token)
        data = {
            "touser": "@all",
            "msgtype": "text",
            "agentid": self.agentid,
            "text": {
                "content": message
            },
            "safe": 0,
        }
        text_message_res = requests.post(url=send_text_url, data=json.dumps(data)).json()
        return text_message_res

    def get_media_id(self, filetype, path):
        upload_file_url = "https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={}&type={}".format(
            self.access_token, filetype)
        files = {filetype: open(path, 'rb')}
        file_upload_result = requests.post(upload_file_url, files=files).json()
        return file_upload_result["media_id"]

    def send_picture_message(self, media_id):
        send_picture_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(self.access_token)
        data = {
            "touser": "@all",
            "msgtype": "image",
            "agentid": self.agentid,
            "image": {
                "media_id": media_id
            },
            "safe": 0,
        }
        picture_message_res = requests.post(url=send_picture_url, data=json.dumps(data)).json()
        return picture_message_res

    def get_access_token(self):
        get_act_url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}".format(
            self.corpid, self.corpsecret)
        act_res = requests.get(url=get_act_url).json()
        access_token = act_res["access_token"]
        return access_token
try:
    wechat_push = WeChatPush(CORPID, CORPSECRET, AGENTID)
except KeyError:
    logger.error("企业微信配置错误，请检查企业微信相关配置")
    sys.exit(0)
except NameError:
    logger.error("企业微信配置错误，请检查企业微信相关配置")
    sys.exit(0)

def get_week(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return "星期" + "日一二三四五六"[date_obj.weekday()]

def get_str(date, start_address, arrival_address, price):
    year, month, day = date[:4], date[4:6], date[6:]
    date_str = f"{year}-{month}-{day}"
    return f"{date_str} {get_week(date_str)}\n    {start_address} —— {arrival_address} 机票最低价格是 {price} 元\n"

def fetch_ticket_prices(start_code, end_code):
    url = f"https://flights.ctrip.com/itinerary/api/12808/lowestPrice?flightWay=Oneway&dcity={start_code}&acity={end_code}&direct=true&army=false"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('data', {}).get('oneWayPrice', [{}])[0]
    else:
        raise Exception(f"Failed to get data, status code: {response.status_code}")

def main_handler(start_address, arrival_address, start_date=None, end_date=None):
    txt = {
        '北京':'BJS', '上海':'SHA', '广州':'CAN', '深圳':'SZX', '成都':'CTU', '杭州':'HGH', '武汉':'WUH', '西安':'SIA', '重庆':'CKG', '青岛':'TAO', '长沙':'CSX', '南京':'NKG', '厦门':'XMN', '昆明':'KMG', '大连':'DLC', '天津':'TSN', '郑州':'CGO', '三亚':'SYX', '济南':'TNA', '福州':'FOC', '阿勒泰':'AAT', '阿克苏':'AKU', '鞍山':'AOG', '安庆':'AQG', '安顺':'AVA', '阿拉善左旗':'AXF', '中国澳门':'MFM', '阿里':'NGQ', '阿拉善右旗':'RHT', '阿尔山':'YIE', '巴中':'BZX', '百色':'AEB', '包头':'BAV', '毕节':'BFJ', '北海':'BHY', '北京(大兴国际机场)':'BJS,PKX', '北京(首都国际机场)':'BJS,PEK', '博乐':'BPL', '保山':'BSD', '白城':'DBC', '布尔津':'KJI', '白山':'NBS', '巴彦淖尔':'RLK', '昌都':'BPX', '承德':'CDE', '常德':'CGD', '长春':'CGQ', '朝阳':'CHG', '赤峰':'CIF', '长治':'CIH', '沧源':'CWJ', '常州':'CZX', '池州':'JUH', '大同':'DAT', '达州':'DAX', '稻城':'DCY', '丹东':'DDG', '迪庆':'DIG', '大理':'DLU', '敦煌':'DNH', '东营':'DOY', '大庆':'DQA', '德令哈':'HXD', '鄂尔多斯':'DSN', '额济纳旗':'EJN', '恩施':'ENH', '二连浩特':'ERL', '阜阳':'FUG', '抚远':'FYJ', '富蕴':'FYN', '果洛':'GMQ', '格尔木':'GOQ', '广元':'GYS', '固原':'GYU', '中国高雄':'KHH', '赣州':'KOW', '贵阳':'KWE', '桂林':'KWL', '红原':'AHJ', '海口':'HAK', '河池':'HCJ', '邯郸':'HDG', '黑河':'HEK', '呼和浩特':'HET', '合肥':'HFE', '淮安':'HIA', '怀化':'HJJ', '海拉尔':'HLD', '哈密':'HMI', '衡阳':'HNY', '哈尔滨':'HRB', '和田':'HTN', '花土沟':'HTT', '中国花莲':'HUN', '霍林郭勒':'HUO', '惠州':'HUZ', '汉中':'HZG', '黄山':'TXN', '呼伦贝尔':'XRQ', '中国嘉义':'CYI', '景德镇':'JDZ', '加格达奇':'JGD', '嘉峪关':'JGN', '井冈山':'JGS', '金昌':'JIC', '九江':'JIU', '荆门':'JM1', '佳木斯':'JMU', '济宁':'JNG', '锦州':'JNZ', '建三江':'JSJ', '鸡西':'JXA', '九寨沟':'JZH', '中国金门':'KNH', '揭阳':'SWA', '库车':'KCA', '康定':'KGT', '喀什':'KHG', '凯里':'KJH', '库尔勒':'KRL', '克拉玛依':'KRY', '黎平':'HZH', '澜沧':'JMJ', '龙岩':'LCX', '临汾':'LFQ', '兰州':'LHW', '丽江':'LJG', '荔波':'LLB', '吕梁':'LLV', '临沧':'LNJ', '陇南':'LNL', '六盘水':'LPF', '拉萨':'LXA', '洛阳':'LYA', '连云港':'LYG', '临沂':'LYI', '柳州':'LZH', '泸州':'LZO', '林芝':'LZY', '芒市':'LUM', '牡丹江':'MDG', '中国马祖':'MFK', '绵阳':'MIG', '梅州':'MXZ', '中国马公':'MZG', '满洲里':'NZH', '漠河':'OHE', '南昌':'KHN', '中国南竿':'LZN', '南充':'NAO', '宁波':'NGB', '宁蒗':'NLH', '南宁':'NNG', '南阳':'NNY', '南通':'NTG', '攀枝花':'PZI', '普洱':'SYM', '琼海':'BAR', '秦皇岛':'BPE', '祁连':'HBQ', '且末':'IQM', '庆阳':'IQN', '黔江':'JIQ', '泉州':'JJN', '衢州':'JUZ', '齐齐哈尔':'NDG', '日照':'RIZ', '日喀则':'RKZ', '若羌':'RQA', '神农架':'HPG', '莎车':'QSZ', '沈阳':'SHE', '石河子':'SHF', '石家庄':'SJW', '上饶':'SQD', '三明':'SQJ', '十堰':'WDS', '邵阳':'WGN', '松原':'YSQ', '台州':'HYN', '中国台中':'RMQ', '塔城':'TCG', '腾冲':'TCZ', '铜仁':'TEN', '通辽':'TGO', '天水':'THQ', '吐鲁番':'TLQ', '通化':'TNH', '中国台南':'TNN', '中国台北':'TPE', '中国台东':'TTT', '唐山':'TVS', '太原':'TYN', '五大连池':'DTU', '乌兰浩特':'HLH', '乌兰察布':'UCB', '乌鲁木齐':'URC', '潍坊':'WEF', '威海':'WEH', '文山':'WNH', '温州':'WNZ', '乌海':'WUA', '武夷山':'WUS', '无锡':'WUX', '梧州':'WUZ', '万州':'WXN', '乌拉特中旗':'WZQ', '巫山':'WSK', '兴义':'ACX', '夏河':'GXH', '中国香港':'HKG', '西双版纳':'JHG', '新源':'NLT', '忻州':'WUT', '信阳':'XAI', '襄阳':'XFN', '西昌':'XIC', '锡林浩特':'XIL', '西宁':'XNN', '徐州':'XUZ', '延安':'ENY', '银川':'INC', '伊春':'LDS', '永州':'LLF', '榆林':'UYN', '宜宾':'YBP', '运城':'YCU', '宜春':'YIC', '宜昌':'YIH', '伊宁':'YIN', '义乌':'YIW', '营口':'YKH', '延吉':'YNJ', '烟台':'YNT', '盐城':'YNZ', '扬州':'YTY', '玉树':'YUS', '岳阳':'YYA', '张家界':'DYG', '舟山':'HSN', '扎兰屯':'NZL', '张掖':'YZY', '昭通':'ZAT', '湛江':'ZHA', '中卫':'ZHY', '张家口':'ZQZ', '珠海':'ZUH', '遵义':'ZYI'
        # 确保添加了所有需要的城市和机场代码
    }
    start_code = txt.get(start_address)
    end_code = txt.get(arrival_address)

    if not start_code or not end_code:
        return '请确定输入的起始地是否正确'

    try:
        # 获取去程价格信息
        outbound_data = fetch_ticket_prices(start_code, end_code)
        # 获取返程价格信息
        return_data = fetch_ticket_prices(end_code, start_code)

        str_result = "去程票价信息:\n"
        lowest_outbound_price = float('inf')
        lowest_outbound_date = ''

        # 筛选日期范围内的数据
        def filter_dates(data, start_date, end_date):
            if not start_date and not end_date:
                return data
            filtered_data = {}
            for date, price in data.items():
                if start_date <= date <= end_date:
                    filtered_data[date] = price
            return filtered_data

        # 处理去程数据
        filtered_outbound_data = filter_dates(outbound_data, start_date, end_date)
        for date, price in filtered_outbound_data.items():
            str_result += get_str(date, start_address, arrival_address, price)
            if price < lowest_outbound_price:
                lowest_outbound_price = price
                lowest_outbound_date = date

        str_result += "返程票价信息:\n"
        lowest_return_price = float('inf')
        lowest_return_date = ''

        # 处理返程数据
        filtered_return_data = filter_dates(return_data, start_date, end_date)
        for date, price in filtered_return_data.items():
            str_result += get_str(date, arrival_address, start_address, price)
            if price < lowest_return_price:
                lowest_return_price = price
                lowest_return_date = date

        # 添加最低价格的特别说明
        if lowest_outbound_date:
            str_result += "\ntips：去程中最低的机票价格为 {} 元，日期为 {}。\n".format(lowest_outbound_price, lowest_outbound_date)
        if lowest_return_date:
            str_result += "tips：返程中最低的机票价格为 {} 元，日期为 {}。\n".format(lowest_return_price, lowest_return_date)

        # 发送到微信
        wechat_push.send_text_message(str_result)
        return str_result
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {}

# 使用示例
if __name__ == "__main__":
    response = main_handler(START_ADDRESS, ARRIVAl_ADDRESS, START_DATE, END_DATE)
    print(response)
