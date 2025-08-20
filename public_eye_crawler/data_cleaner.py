import os
import pandas as pd
from datetime import datetime, timedelta

def remove_special_sign(tar_data, debug):
    """去除特殊符号"""
    special_sign = " ！@#￥%……&*（）【】|、：；“”‘’《》，。…？~·.!.\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~\n"
    for the_sign in special_sign:
            tar_data = tar_data.str.replace(the_sign,'')
    if debug:
        print("---" * 50)
        print("removed special signs in contents")
    return tar_data


def data_cleaning(data, start_time, end_time, debug=False, output_as_file=False):
    """数据清洗"""
    # 去除特殊符号，填充空值，去重
    data.info()
    data['content'] = data['content'].fillna(value=data['title'])
    data['content'] = remove_special_sign(data['content'], debug) # 去除特殊符号
    data['author'] = data['author'].fillna(value=data['source'])
    data['like_count'] = data['like_count'].fillna(value=0)
    data['share_count'] = data['share_count'].fillna(value=0)
    data['comment_count'] = data['comment_count'].fillna(value=0)
    data['read_count'] = data['read_count'].fillna(value=0)

    data = data.drop_duplicates(subset=['title'])  # 去重
    # 筛选发布时间在昨天的news
    if start_time is not None and end_time is not None:
        data.loc[:, 'publish_time'] = pd.to_datetime(data['publish_time'])
        data = data[(data['publish_time'] >= start_time) & (data['publish_time'] <= end_time)]

    if debug:
        print("---" * 50)
        print("filled NA/NAN value")
        data.info()
    if output_as_file:
         # 将整合后的数据存入'./data/all_info.csv'
        file_dir = './data'
        file_path = file_dir + os.sep + 'all_info.csv'
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)
        data.to_csv(file_path, encoding="utf_8_sig", index_label='event_id') 
        print("---" * 50)
        print("succeeded in renewing all the info in './data/all_info.csv'")
        print("---" * 50)
    return data

# TODO: this is just a demo
if __name__ == "__main__":
    cctv_data = pd.read_csv("./cctv_crawler/crawler_result.csv", index_col='event_id')
    sina_data = pd.read_csv("./sina_crawler/crawler_result.csv", index_col='event_id')
    tengxun_data = pd.read_csv("./tengxun_crawler/crawler_result.csv", index_col='event_id')
    south_weekend_data = pd.read_csv("./south_weekend_crawler/crawler_result.csv", index_col='event_id')
    data = pd.concat(objs=[cctv_data, sina_data, tengxun_data, south_weekend_data], axis=0, join='outer', ignore_index=True)

    # 获取昨天的日期
    yesterday = datetime.now() - timedelta(days=2)
    start_time = pd.Timestamp(yesterday.strftime('%Y-%m-%d 00:00:00'))
    end_time = pd.Timestamp(yesterday.strftime('%Y-%m-%d 23:59:59'))

    data_cleaning(data, start_time, end_time, True, True)