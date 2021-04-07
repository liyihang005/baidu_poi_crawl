# coding: utf-8
import requests
import json
import time
import os
import pandas as pd
import argparse
# from tool import transCoordinateSystem
import math

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


def gcj02_to_bd09(lng, lat):
    """
    火星坐标系(GCJ-02)转百度坐标系(BD-09)
    谷歌、高德——>百度
    :param lng:火星坐标经度
    :param lat:火星坐标纬度
    :return:
    """
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return [bd_lng, bd_lat]


def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>谷歌、高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return [gg_lng, gg_lat]


def wgs84_to_gcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    if out_of_china(lng, lat):  # 判断是否在国内
        return lng, lat
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [mglng, mglat]


def gcj02_to_wgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return lng, lat
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def bd09_to_wgs84(bd_lon, bd_lat):
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)


def wgs84_to_bd09(lon, lat):
    lon, lat = wgs84_to_gcj02(lon, lat)
    return gcj02_to_bd09(lon, lat)


def _transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)

# keywords =['房地产','购物','教育培训','医疗','政府机构','公司企业','美食','出入口','休闲娱乐','交通设施','生活服务','酒店','丽人','运动健身','文化传媒','汽车服务','自然地物','金融','旅游景点']

parser = argparse.ArgumentParser(description="manual to this script")
parser.add_argument('--type', type=str, default='交通设施')
parser.add_argument('--ak', type=str, default='BV4mRLXbRN9ovtsySZLH1ToTsI1uGBER')

parser.add_argument('--leftx', type=float, default=113.14956108672817)
parser.add_argument('--lefty', type=float, default=22.880584526656673)
parser.add_argument('--rightx', type=float, default=113.55498931429548)
parser.add_argument('--righty', type=float, default=23.441036057995387)
# parser.add_argument('--leftx', type=float, default=113.28234269022006)
# # parser.add_argument('--lefty', type=float, default=23.33239570905962)
# # parser.add_argument('--rightx', type=float, default=114.07361387488976)
# # parser.add_argument('--righty', type=float, default=23.937747436286248)

# Portol
# parser.add_argument('--leftx', type=float, default=-8.6510)
# parser.add_argument('--lefty', type=float, default=41.1351)
# parser.add_argument('--rightx', type=float, default=-8.5807)
# parser.add_argument('--righty', type=float, default=41.1754)

parser.add_argument('--x', type=int, default=10)
parser.add_argument('--y', type=int, default=2)
args = parser.parse_args()
# TODO 1 查询关键字，只支持单个
KeyWord = args.type

# TODO 2 apk关键词，只支持单个
baiduAk = args.ak

[args.leftx, args.lefty] = wgs84_to_bd09(args.leftx, args.lefty)
[args.rightx, args.righty] = wgs84_to_bd09(args.rightx, args.righty)

# TODO 3 爬取区域的左下角和右上角百度地图坐标(经纬度）
BigRect = {
    'left': {
        'x': args.leftx,
        'y': args.lefty
    },
    'right': {
        'x': args.rightx,
        'y': args.righty
    }
}

# TODO 4 划分细分窗口的数量，默认2，横向X * 纵向Y
WindowSize = {
    'xNum': args.x,
    'yNum': args.y
}


def getSmallRect(bigRect, windowSize, windowIndex):
    """
    获取小矩形的左上角和右下角坐标字符串（百度坐标系）
    :param bigRect: 关注区域坐标信息
    :param windowSize:  细分窗口数量信息
    :param windowIndex:  Z型扫描的小矩形索引号
    :return: lat,lng,lat,lng
    """
    offset_x = (bigRect['right']['x'] - bigRect['left']['x']) / windowSize['xNum']
    offset_y = (bigRect['right']['y'] - bigRect['left']['y']) / windowSize['yNum']
    left_x = bigRect['left']['x'] + offset_x * (windowIndex % windowSize['xNum'])
    left_y = bigRect['left']['y'] + offset_y * (windowIndex // windowSize['xNum'])
    right_x = (left_x + offset_x)
    right_y = (left_y + offset_y)
    print(windowIndex)
    print("___")
    print(windowIndex % windowSize['xNum'])
    print(windowIndex // windowSize['yNum'])
    print(offset_x)
    print(offset_y)
    print(left_x)
    print(left_y)
    print(right_x)
    print(right_y)
    return str(left_y) + ',' + str(left_x) + ',' + str(right_y) + ',' + str(right_x)


def requestBaiduApi(keyWords, smallRect, baiduAk):
    pageNum = 0
    # file = open(os.getcwd() + os.sep + "data/result.txt", 'a+', encoding='utf-8')
    file = open(os.path.join("D:\\2021-spring\\时空智能\\出租车数据", "poi_test.txt"), 'a+', encoding='utf-8')
    pois = []
    while True:
        URL = "http://api.map.baidu.com/place/v2/search?query=" + keyWords + \
              "&bounds=" + smallRect + \
              "&output=json" + \
              "&ak=" + baiduAk + \
              "&scope=2" + \
              "&page_size=20" + \
              "&page_num=" + str(pageNum)
        # print("\t第" + str(pageNum) + "页")
        # print(URL)
        resp = requests.get(URL)
        res = json.loads(resp.text)
        # print(resp.text.strip())
        if len(res['results']) == 0:
            print('返回结果为0')
            break
        else:
            for r in res['results']:
                pois.append(r)
                file.writelines(str(r).strip() + '\n')
        pageNum += 1
        '''
        try:
            URL = "http://api.map.baidu.com/place/v2/search?query=" + keyWords + \
                  "&bounds=" + smallRect + \
                  "&output=json" + \
                  "&ak=" + baiduAk + \
                  "&scope=2" + \
                  "&page_size=20" + \
                  "&page_num=" + str(pageNum)
            #print("\t第" + str(pageNum) + "页")
            #print(URL)
            resp = requests.get(URL)
            res = json.loads(resp.text)
            # print(resp.text.strip())
            if len(res['results']) == 0:
                #print('返回结果为0')
                break
            else:
                for r in res['results']:
                    pois.append(r)
                    file.writelines(str(r).strip() + '\n')
            pageNum += 1
        except:
            print("except")
            break
        '''
    return pois


def main():
    all_pois = []
    for index in range(int(WindowSize['xNum'] * WindowSize['yNum'])):
        smallRect = getSmallRect(BigRect, WindowSize, index)
        print(smallRect)
        #print("第" + str(index + 1) + "块搜索区域，共" + str(int(WindowSize['xNum'] * WindowSize['yNum'])) + "块")
        pois = requestBaiduApi(keyWords=KeyWord, smallRect=smallRect, baiduAk=baiduAk)
        all_pois.extend(pois)

    data_csv = {}
    uids, names, provinces, citys, areas, addresses, lngs, lats, lng_WGS84s, lat_WGS84s, tag1s, tag2s, types = [], [], [], [], [], [], [], [], [], [], [], [], []
    for poi in all_pois:
        if poi == None:
            continue
        # print(poi)
        uids.append(poi.get('uid'))
        names.append(poi.get('name', '————'))
        provinces.append(poi.get('province', '————'))
        citys.append(poi.get('city', '————'))
        areas.append(poi.get('area', '————'))
        addresses.append(poi.get('address', '————'))

        location = poi.get('location', '————')
        if (location is not '————'):
            lng = location['lng']
            lat = location['lat']
            lng_WGS84, lat_WGS84 = bd09_to_wgs84(lng, lat)
            lng_WGS84s.append(lng_WGS84)
            lat_WGS84s.append(lat_WGS84)
        else:
            lng_WGS84s.append('————')
            lat_WGS84s.append('————')

        detail_info = poi.get('detail_info', '————')
        if (detail_info is not '————'):
            if ('tag' in detail_info.keys()):
                tag = detail_info['tag'].split(';')
                if (len(tag) == 1):
                    tag1 = detail_info['tag'].split(';')[0]
                    tag2 = '————'
                elif (len(tag) == 2):
                    tag1 = detail_info['tag'].split(';')[0]
                    tag2 = detail_info['tag'].split(';')[1]
            else:
                tag1 = '————'
                tag2 = '————'
            tag1s.append(tag1)
            tag2s.append(tag2)

            if ('type' in detail_info.keys()):
                type = detail_info['type']
            else:
                type = '————'
            types.append(type)
        else:
            tag1s.append('————')
            tag2s.append('————')
            types.append('————')

    data_csv['uid'] = uids
    data_csv['name'] = names
    data_csv['tag1'] = tag1s
    data_csv['tag2'] = tag2s
    data_csv['type'] = types
    data_csv['province'] = provinces
    data_csv['city'] = citys
    data_csv['area'] = areas
    data_csv['address'] = addresses
    data_csv['lng_WGS84'] = lng_WGS84s
    data_csv['lat_WGS84'] = lat_WGS84s

    df = pd.DataFrame(data_csv)
    data_path = "D:\\2021-spring\\时空智能\\出租车数据\\"
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    df.to_csv(data_path + "bmap-poi-shenzhen-new-" + args.type + '.csv', index=False, encoding='utf_8_sig')
    print("类别[" + args.type + "]已检索完毕！")


if __name__ == '__main__':
    main()
