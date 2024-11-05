import requests
import time
import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# 配置 WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

# 目标 URL
url = 'http://wc.wahlap.net/maidx/location/index.html'  # 替换为实际的 URL

# 打开页面
driver.get(url)

# 等待 class="store_list" 的 ul 元素加载完成
try:
    ul_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'store_list'))
    )
except Exception as e:
    print(f"Error waiting for store_list: {e}")
    driver.quit()
    exit()

# 获取页面内容
page_content = driver.page_source
driver.quit()

# 使用 BeautifulSoup 解析 HTML
soup = BeautifulSoup(page_content, 'html.parser')
store_list = soup.find('ul', class_='store_list')

# 数据库连接配置
db_config = {
    'host': 'maimap-mysql.mfnest.tech',
    'port': 3306,
    'user': 'root',
    'password': 'yelsjdhl',
    'database': 'maimap',
    'charset': 'utf8mb4'
}

# 连接到数据库
connection = pymysql.connect(**db_config)
cursor = connection.cursor()

# 获取arcades表的行数
cursor.execute("SELECT COUNT(*) FROM arcades")
row_count = cursor.fetchone()[0]

# 提取每个 li 元素中的 store_name 和 store_address
id = 1
for li in store_list.find_all('li'):
    store_name = li.find('span', class_='store_name').text.strip()
    store_address = li.find('span', class_='store_address').text.strip()
    store_type = "mai"

    if id > row_count:
        # 发送请求获取位置信息
        response = requests.get('https://apis.map.qq.com/ws/geocoder/v1/', params={
            'address': store_address,
            'key': "4BQBZ-6DJWA-MJDKJ-CEHME-I4AL7-IDBK7"
        })
        result = response.json()
        if result['status'] == 0:
            location = result['result']['location']
            store_lat = location['lat']
            store_lng = location['lng']
        else:
            store_lat = None
            store_lng = None
        print(store_name)
        print(store_address)
        print(store_lat, store_lng)
        time.sleep(0.2)  # 每0.2秒发送一次请求

        # 更新数据库
        cursor.execute("""
            INSERT INTO arcades (store_name, store_address, id, store_lat, store_lng, store_pos)
            VALUES (%s, %s, %s, %s, %s, ST_GeomFromText('POINT(%s %s)', %s))
        """, (store_name, store_address, id, store_lat, store_lng, store_lng, store_lat, store_type))
        connection.commit()

    id += 1

# 关闭数据库连接
cursor.close()
connection.close()