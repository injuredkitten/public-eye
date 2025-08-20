import os
import json
import time
import random
import execjs

import requests
import pandas as pd
from datetime import datetime

class ZanaoMarketCrawler:
    def __init__(self, debug = False, output_as_file=False):
        """对象初始化"""
        # 从本地文件读取配置信息
        config_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'config.json'
        self.config_path = config_path
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 从本地文件读取爬取信息（上次爬取的时间和帖子id）
        last_info_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'last_info.json'
        self.last_info_path = last_info_path
        with open(last_info_path, "r", encoding="utf-8") as f:
            last_info = json.load(f)

        # 从本地文件读取JavaScript代码
        zanao_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'zanao.js'
        self.zanao_path = zanao_path
        with open(zanao_path, "r", encoding="utf-8") as f:
            self.js = f.read()

        # 存储用户认证信息的cookies
        self.cookies = {
            'user_token': config['headers']['x-sc-od']
        }

        self.headers = config["headers"]
        self.cate_ids = config["cate_ids"]
        self.last_info = last_info
        self.threads = []
        self.threads_count = 0
        self.debug = debug
        self.output_as_file = output_as_file


    def get_JS_result(self):
        """
        执行JavaScript代码并获取结果。

        使用execjs库编译并执行在 'zanao.js' 文件中的JavaScript代码，
        并调用 'get_result' 函数获取结果。

        返回:
            dict: 包含多个由JavaScript代码生成的键值对。
        """
        result = execjs.compile(self.js).call("get_result")
        return result


    def get_headers(self):
        result = self.get_JS_result()
        headers = {
            'Accept': 'application/json, text/plain, */*',
            "X-Sc-Nd": result["X-Sc-Nd"],
            "X-Sc-Od": result["X-Sc-Od"],
            "X-Sc-Ah": result["X-Sc-Ah"],
            "X-Sc-Td": str(result["X-Sc-Td"]),
            'X-Sc-Alias': result["X-Sc-Alias"],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090819) XWEB/8519 Flue'
        }
        return headers


    def crawl_data(self):
        url = "https://api.x.zanao.com/thread/v2/list"
        for cate_name, cate_id in self.cate_ids.items():
            if self.debug:
                print("crawling category: ", cate_name)
            last_visit_p_time = self.last_info[cate_name]['p_time']
            last_thread_id = self.last_info[cate_name]['last_thread_id']
            renew_flag = False
            break_flag = False
            for page in range(1, 5):
                # 睡一会，防止被封
                if break_flag:
                    # 如果break_flag为True，则说明上一页已经爬取到上次爬取的位置，退出循环
                    break
                print("page:", page)
                sleep_time = random.randint(1, 3)
                print(f"sleep {sleep_time} seconds......")
                time.sleep(sleep_time)
                params = {
                    "cate_id": cate_id,
                    "cur_page": page
                }
                headers = self.get_headers()
                response = requests.get(url, headers=headers, params=params)
                data = response.json()['data']
                for item in data['list']:
                    # print(item)
                    t={}
                    try:
                        # 获取帖子信息
                        t["cate_id"] = item['cate_id']
                        t["cate_name"] = item['cate_name']
                        t["thread_id"] = item['thread_id']
                        p_time = int(item['p_time'])
                        new_time = datetime.fromtimestamp(p_time)
                        t["publsh_time"] = datetime.strftime(new_time, "%Y-%m-%d %H:%M:%S")
                        t["title"] = item['title']
                        t["content"] = item['content'].replace('\n','').replace('\r','')
                        t["author"] = item['nickname']
                        t['read_count'] = item['view_count']
                        t['like_count'] = item['l_count']
                        t["comment_count"] = item['c_count']
                    except:
                        if self.debug:
                            print("get info err")
                    if self.debug:
                        print("p_time:", p_time)
                        print("last_visit_p_time:", last_visit_p_time)
                    if p_time < last_visit_p_time or (p_time == last_visit_p_time and t["thread_id"] == last_thread_id):
                        # 如果当前帖子的id和时间与上次爬取的相同，则说明已经爬取到上次爬取的位置，停止爬取
                        break_flag = True
                        break
                    if renew_flag==False:
                        # renew_flag为False时，说明是第一次爬取该板块，更新的帖子id和时间
                        renew_flag = True
                        self.last_info[cate_name]["p_time"] = p_time
                        self.last_info[cate_name]["last_thread_id"] = t["thread_id"]
                        self.last_info[cate_name]["last_visit_time"] = t["publsh_time"]
                    self.threads.append(t)
                    self.threads_count += 1
                    if self.debug:
                        print(t)
                        print("Succeeded in crawling one thread!\n")

        if self.debug:
            print('---'*30)
            print("The latest data crawling is completed!\n")
        return self.deal_info()


    def deal_info(self):
        """处理信息"""
        result_headers = [
            "cate_id",
            "cate_name",
            "thread_id",
            "publsh_time",
            "title",
            "content",
            "author",
            "read_count",
            "like_count",
            "comment_count"
        ] # 要写入结果文件的表头

        # 将数据转换为DataFrame格式
        result_data = [t.values() for t in self.threads]
        df = pd.DataFrame(data=result_data, columns=result_headers) 
            
        # 将最新的时间和帖子id写入last_info文件，盖掉原来的信息
        with open(self.last_info_path,'w',encoding='utf-8') as f:
            json.dump(self.last_info, f, indent=1, ensure_ascii=False) 

        if self.output_as_file:
            file_path =  os.path.split(os.path.realpath(__file__))[0] + os.sep + 'crawler_result.csv'
            df.to_csv(file_path, encoding="utf_8_sig")
        if self.debug:
            df.info()
        return df



if __name__ == "__main__":

    a = ZanaoMarketCrawler(True, True)
    a.crawl_data()