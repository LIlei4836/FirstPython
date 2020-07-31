# 请使用3.6以上版本
import threading
from userAgents import get_html_bytes, get_html
import json
import time
import datetime
import pymysql
import contextlib
from multiprocessing import Pool
import requests
import logging



fmt = '%(asctime)s , %(levelname)s , %(filename)s %(funcName)s line %(lineno)s , %(message)s'
datefmt = '%Y-%m-%d %H:%M:%S %a'
logging.basicConfig(level=logging.INFO,
format=fmt,
datefmt=datefmt,
filename="log.txt")


@contextlib.contextmanager
# def mysql(host='127.0.0.1', port=3306, user='root', passwd='', db='tkq1',charset='utf8'):
def mysql(host='103.80.18.238', port=3306, user='hhjc', passwd='ZjMxMGUzODE4Y2UyZWEyM2M1MmQyNzJh',
          db='hhjc', charset='utf8'):
# def mysql(host='localhost', port=3306, user='root', passwd='123456',
#           db='lll', charset='utf8'):
    conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)  # 生成游标对象
    try:
        yield cursor
    finally:
        conn.commit()
        cursor.close()
        conn.close()


def create_database():
    with mysql() as cursor:
        sql = """CREATE TABLE IF NOT EXISTS qm_huihuangtest(
            id INT AUTO_INCREMENT PRIMARY KEY comment '主键',
            expect VARCHAR(20) comment '期望值',
            code VARCHAR(20) comment '彩种',
            openCode VARCHAR(20) comment '中奖号码',
            openTimeStamp int comment '中奖时间戳',
            nextExpect VARCHAR(20) comment '下一期期号',
            nextTimeStamp int comment '下期开奖时间戳')
            ENGINE = MyISAM DEFAULT CHARSET=utf8;"""
        cursor.execute(sql)
        cursor.execute("ALTER TABLE qm_huihuangtest ADD UNIQUE KEY(expect, code)")
        cursor.execute("ALTER TABLE qm_huihuangtest ADD UNIQUE KEY(nextExpect, nextTimeStamp, code)")
        print('数据库创建成功！')


def getData(variety):
    url = f'http://api.caipiaokong.com/lottery/?name={variety}&format=json&uid=1382037&token=8b5b9e77f58db225e6ba37dd1f19a5c8f34b4bfb&num=1'
    # url = f'http://ho.apiplus.net/daily.do?token=tb986ae9a96e6052ak&code={variety}&format=json&date=2020-01-21'
    while 1:
        try:
            datas = get_html(url)
            if not datas:
                continue
            datas = json.loads(datas, encoding='utf-8')

            for key,expect in enumerate(datas):

                openCode = datas[expect]['number']
                openTime = datas[expect]['dateline']
                timeArray = time.strptime(openTime, "%Y-%m-%d %H:%M:%S")
                openTimeStamp = int(time.mktime(timeArray))
                nextExpect = 0
                nextTimeStamp = 0


                periodDict = {'shks': 41, 'shsyxw': 45,'fjks':42,'fjsyxw':45,'hubks':39,'hbsyxw':40,'jxks':42,'jxsyxw':42,'zjsyxw':42}
                openTimeDict = {'shks': '08:38:00','shsyxw': '09:00:00','fjks':'08:30:00','fjsyxw':'08:10:00',
                                'hubks':'09:00:00','hbsyxw':'08:35:00','jxks':'08:15:00','jxsyxw':'09:10:00','zjsyxw':'08:30:00'}

                areaDict = {'shsyxw': 'shanghai', 'fjsyxw': 'fujian', 'hbsyxw': 'hubei', 'jxsyxw': 'jiangxi','zjsyxw': 'zhejiang'}
                codeDict = {'shks': 'shk3', 'shsyxw': 'sh11x5', 'fjks': 'fjk3', 'fjsyxw': 'fj11x5', 'hubks': 'hubk3',
                            'hbsyxw': 'hub11x5', 'jxks': 'jxk3', 'jxsyxw': 'jx11x5', 'zjsyxw': 'zj11x5'}

                if variety in periodDict and int(expect[-2:]) < periodDict[variety]:
                    nextExpect = int(expect) + 1

                    # 得到下一期开奖时间
                    tm_year, tm_mon, tm_mday, tm_hour, tmr_min = getDetailDate()

                    if int(tm_mon) < 10:
                        tm_mon = ('0' + str(tm_mon))[-2:]
                    if int(tm_mday) < 10:
                        tm_mday = ('0' + str(tm_mday))[-2:]

                    firstTime = str(tm_year) + '-' + str(tm_mon) + '-' + str(tm_mday) + ' ' + str(openTimeDict[variety])
                    timeArray = time.strptime(firstTime, "%Y-%m-%d %H:%M:%S")
                    now_time_stamp = time.mktime(timeArray)
                    nextTimeStamp = now_time_stamp + (int(expect[-2:])) * 1200 + 1200
                    # print(variety,nextExpect,nextTimeStamp)
                    # print(int(nextTimeStamp)-int(time.time()))
                    # 延迟开奖
                    if int(int(nextTimeStamp) - int(time.time())) < 0:
                        # print('下一期倒计时开始1:', variety, int(int(nextTimeStamp) - int(time.time())), nextExpect + 1, nextTimeStamp + 1200)
                        if int(str(nextExpect + 1)[-2:]) <= periodDict[variety]:
                            # 不让上海十一选五最后一期延迟开奖后插入下一期数据，
                            if variety == 'shsyxw' and int((str(nextExpect + 1))[-2:]) == 45:

                                # 重新拼接期号
                                expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                                currYear = expect[0:4]
                                currMonth = expect[4:6]
                                currDay = expect[6:8]

                                if int(currMonth) < 10:
                                    currMonth = ('0' + str(currMonth))[-2:]
                                if int(currDay) == 0:
                                    currDay = ('0' + str(currDay))[-2:]

                                currRiqi = str(currYear) + '-' + str(currMonth) + '-' + str(currDay)
                                date_time = datetime.datetime.strptime(currRiqi, '%Y-%m-%d')
                                date_time = date_time + datetime.timedelta(days=1)
                                nextTimeStamp = time.mktime(date_time.timetuple()) - 1200

                            # 重新拼接期号
                            expect,nextExpect = spliceExpect(variety,expect, nextExpect)

                            insertData(codeDict[variety], nextExpect + 1, nextTimeStamp + 1200)

                elif variety in periodDict and int(expect[-2:]) == periodDict[variety]:

                    # 上海11x5开奖
                    # 最后一期是凌晨12点之后开奖
                    if variety == 'shsyxw':

                        # 获取最后一期的开奖日期
                        openTimeArray = datetime.datetime.fromtimestamp(openTimeStamp)

                        year = openTimeArray.year
                        month = openTimeArray.month
                        day = openTimeArray.day

                        if int(month) < 10:
                            month = ('0' + str(month))[-2:]
                        if int(day) < 10:
                            day = ('0' + str(day))[-2:]

                        nextExpect = str(year) + str(month) + str(day) + '01'

                        # 12点之后开奖
                        if int(openTimeArray.hour) < 1:

                            currRiqi = str(year) + '-' + str(month) + '-' + str(day) + ' ' + str(openTimeDict[variety])

                            timeArray = time.strptime(currRiqi, "%Y-%m-%d %H:%M:%S")
                            nextTimeStamp = int(time.mktime(timeArray)) + 1200

                            # 重新拼接期号
                            expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                            insertData(codeDict[variety], nextExpect, int(nextTimeStamp))
                        else:

                            # 重新拼接期号
                            expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                            # 最后一期在12点之前开奖
                            currYear = expect[0:4]
                            currMonth = expect[4:6]
                            currDay = expect[6:8]
                            currRiqi = str(currYear) + '-' + str(currMonth) + '-' + str(currDay)
                            date_time = datetime.datetime.strptime(currRiqi, '%Y-%m-%d')
                            date_time = date_time + datetime.timedelta(days=1)
                            year = date_time.year
                            month = date_time.month
                            day = date_time.day
                            if int(month) < 10:
                                month = ('0' + str(month))[-2:]
                            if int(day) < 10:
                                day = ('0' + str(day))[-2:]

                            nextqi = str(year) + str(month) + str(day)

                            nextRiqi = str(year) + '-' + str(month) + '-' + str(day)

                            # 获取每天第一期的期数
                            nextExpect = int(nextqi + '01')

                            # 获取明天第一期的时间戳
                            strTime = str(nextRiqi) + " " + str(openTimeDict[variety])
                            timeArray = time.strptime(strTime, "%Y-%m-%d %H:%M:%S")
                            nextTimeStamp = int(time.mktime(timeArray)) + 1200

                            # 重新拼接期号
                            expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                            insertData(codeDict[variety], nextExpect, int(nextTimeStamp))

                    else:
                        # today = datetime.date.today()
                        # tomorrow = today + datetime.timedelta(days=1)

                        # 重新拼接期号
                        expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                        currYear = expect[0:4]
                        currMonth = expect[4:6]
                        currDay = expect[6:8]
                        currRiqi = str(currYear) + '-' + str(currMonth) + '-' + str(currDay)
                        date_time = datetime.datetime.strptime(currRiqi, '%Y-%m-%d')
                        date_time = date_time + datetime.timedelta(days=1)
                        year = date_time.year
                        month = date_time.month
                        day = date_time.day

                        if int(month) < 10:
                            month = ('0' + str(month))[-2:]
                        if int(day) < 10:
                            day = ('0' + str(day))[-2:]

                        nextqi = str(year) + str(month) + str(day)

                        nextRiqi = str(year)+'-'+str(month)+'-'+str(day)

                        # 获取每天第一期的期数
                        if 'ks' in variety:
                            nextExpect = int(nextqi + '001')
                        elif 'syxw' in variety:
                            nextExpect = int(nextqi + '01')
                        print(nextExpect)
                        # 获取明天第一期的时间戳
                        strTime = str(nextRiqi) + " " + str(openTimeDict[variety])
                        timeArray = time.strptime(strTime, "%Y-%m-%d %H:%M:%S")
                        nextTimeStamp = int(time.mktime(timeArray)) + 1200

                        # 重新拼接期号
                        expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                        insertData(codeDict[variety], nextExpect, int(nextTimeStamp))

                    # 当第一期延迟开奖
                    # 获取当天日期
                    curr_year, curr_mon, curr_mday, curr_hour, curr_min = getDetailDate()

                    if int(curr_hour) < 10:
                        curr_hour = ('0' + str(curr_hour))[-2:]
                    if int(curr_min) == 0 or curr_min == '00':
                        curr_min = ('0' + str(curr_min))[-2:]

                    currentTime = str(curr_hour) + ':' + str(curr_min)

                    secondTimeDict = {'fjks': '08:50:00', 'shks': '08:58:00', 'jxks': '08:35:00','hubks': '09:20:00','shsyxw': '09:20:00',
                                      'hbsyxw': '08:55:00', 'zjsyxw': '08:50:00', 'fjsyxw': '08:30:00','jxsyxw': '09:30:00'}

                    # 达到第一期开奖时时间
                    if currentTime == secondTimeDict[variety][0:5]:
                        # 得到第一期期号
                        if int(curr_mon) < 10:
                            curr_mon = ('0' + str(curr_mon))[-2:]
                        if int(curr_mday) < 10:
                            curr_mday = ('0' + str(curr_mday))[-2:]
                        if 'ks' in variety:
                            nextExpect = str(curr_year) + str(curr_mon) + str(curr_mday) + '002'
                        elif 'syxw' in variety:
                            nextExpect = str(curr_year) + str(curr_mon) + str(curr_mday) + '02'

                        firstTime = str(curr_year) + '-' + str(curr_mon) + '-' + str(curr_mday) + ' ' + str(secondTimeDict[variety])
                        currTimeArray = time.strptime(firstTime, "%Y-%m-%d %H:%M:%S")
                        nextTimeStamp = time.mktime(currTimeArray)

                        # 重新拼接期号
                        expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                        # 每天第一期提前倒计时
                        insertData(codeDict[variety], nextExpect, int(nextTimeStamp) + 1200)

                # 重新拼接期号
                expect, nextExpect = spliceExpect(variety, expect, nextExpect)

                # print(expect, openCode, openTimeStamp, nextExpect, nextTimeStamp, codeDict[variety])
                with mysql() as cursor:
                    insertsql = "insert into qm_huihuangtest(expect,code,openCode,openTimeStamp,nextExpect,nextTimeStamp)" \
                    "values('%s','%s','%s','%d','%s','%d')" % (
                    expect, codeDict[variety], openCode, openTimeStamp, nextExpect, nextTimeStamp)

                    updatesql = "update qm_huihuangtest set expect='%s',openCode='%s',openTimeStamp='%d' where " \
                          "nextExpect='%s'AND nextTimeStamp='%s' AND code='%s'" % (
                          expect, openCode, openTimeStamp, nextExpect, nextTimeStamp, codeDict[variety])

                    try:
                        num = 0
                        num1 = 0

                        try:
                            num = cursor.execute(updatesql)
                        except Exception as e:
                            print(e)

                        if num == 0:
                            try:
                                num1 = cursor.execute(insertsql)
                            except Exception as e:
                                time.sleep(1)
                                # print(e)


                        if num == 1:
                            print('更新成功！', variety, expect, num)
                        elif num1 == 1:
                            print('插入成功！', variety, expect, num1)

                        if num == 1 or num1 == 1:
                            if 'syxw' in variety:
                                area = areaDict[variety]
                                url_11x5 = ['http://whjc.h148777.com/api/index/epf/', 'expect/', str(expect), '/area/',
                                            area]
                                url_11x5 = ''.join(url_11x5)
                                try:
                                    html11x5 = requests.get(url_11x5,timeout=5)
                                    result = json.loads(html11x5.text)
                                    code = result['code']
                                    logging.info(variety + ',' + str(code) + ',' + url_11x5)
                                except Exception as e:
                                    logging.info(html11x5 + ',' + url_11x5)
                                print(url_11x5)
                            elif 'ks' in variety:

                                url_k3 = ['http://whjc.h148777.com/api/ft/open/', 'code/', codeDict[variety], '/outSn/',
                                          expect, '/nums/', openCode]
                                url_k3 = ''.join(url_k3)
                                try:
                                    htmlk3 = requests.get(url_k3, timeout=5)
                                    result = json.loads(htmlk3.text)
                                    code = result['code']
                                    logging.info(variety + ',' + str(code) + ',' + url_k3)
                                except Exception as e:
                                    logging.info(htmlk3+','+url_k3)
                                print(url_k3)
                    except Exception as e:
                        print(e)
                        time.sleep(1)

        except Exception as e:
            # print(e)
            time.sleep(3)

        time.sleep(6)

# 获取当天日期信息
def getDetailDate():
    currDate = time.localtime()
    curr_year = currDate.tm_year
    curr_mon = currDate.tm_mon
    curr_mday = currDate.tm_mday
    curr_hour = currDate.tm_hour
    curr_min = currDate.tm_min
    return curr_year, curr_mon, curr_mday, curr_hour, curr_min

# 插入数据库关于下一期
def insertData( variety, nextExpect,nextTimeStamp):
    with mysql() as cursor:
        sql = "insert into qm_huihuangtest(code, nextExpect,nextTimeStamp) values('%s','%s','%d')" % (variety, nextExpect, nextTimeStamp)
        try:
            cursor.execute(sql)
        except Exception as e:
            # print(e)
            pass

def spliceExpect(variety, expect, nextExpect):
    # 重新拼接开奖号
    if 'ks' in variety and len(expect) == 9:
        if variety in ['fjks', 'shks', 'jxks']:
            expect = '20' + expect
            if len(str(nextExpect)) == 9:
                nextExpect = int('20' + str(nextExpect))
    if 'syxw' in variety and len(expect) == 8:
        if variety in ['fjsyxw', 'hbsyxw', 'zjsyxw']:
            expect = '20' + expect
            if len(str(nextExpect)) == 8:
                nextExpect = int('20' + str(nextExpect))
    return expect, nextExpect

if __name__ == '__main__':
    # create_database()
    varietys = ['shks', 'shsyxw','fjks','fjsyxw','hubks','hbsyxw','jxks','jxsyxw','zjsyxw']
    # varietys = [ 'zjsyxw']
    for variety in varietys:
        t1 = threading.Thread(target=getData, args=(variety,))
        t1.start()
    t1.join()

