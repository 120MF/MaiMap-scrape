import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson import ObjectId, Decimal128

# 配置 WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  #
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# 目标 URL
url = "http://wc.wahlap.net/maidx/location/index.html"  # 替换为实际的 URL

# 打开页面
driver.get(url)

# 等待 class="store_list" 的 ul 元素加载完成
# 等待 class="store_list" 的 ul 元素加载完成
try:
    ul_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "store_list"))
    )

    # 检查 ul_element 是否包含子元素
    while not ul_element.find_elements(By.TAG_NAME, "li"):
        time.sleep(1)  # 等待1秒后再检查
        ul_element = driver.find_element(By.CLASS_NAME, "store_list")

except Exception as e:
    print(f"Error waiting for store_list: {e}")
    driver.quit()
    exit()

# 获取页面内容
page_content = driver.page_source
driver.quit()

# 使用 BeautifulSoup 解析 HTML
soup = BeautifulSoup(page_content, "html.parser")
store_list = soup.find("ul", class_="store_list")


# 连接到数据库
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["maimap"]
arcades_collection = db.arcades

max_store_id_document = arcades_collection.find_one(sort=[("store_id", -1)])
max_store_id = max_store_id_document["store_id"] if max_store_id_document else 0

print(f"Max store_id: {max_store_id}")

# 提取每个 li 元素中的 store_name 和 store_address
id = 1
for li in store_list.find_all("li"):
    store_name = li.find("span", class_="store_name").text.strip()
    store_address = li.find("span", class_="store_address").text.strip()
    store_type = "mai"

    if id > max_store_id:
        # 发送请求获取位置信息
        response = requests.get(
            "https://apis.map.qq.com/ws/geocoder/v1/",
            params={
                "address": store_address,
                "key": "4BQBZ-6DJWA-MJDKJ-CEHME-I4AL7-IDBK7",
            },
        )
        result = response.json()
        if result["status"] == 0:
            location = result["result"]["location"]
            store_lat = location["lat"]
            store_lng = location["lng"]
        else:
            store_lat = None
            store_lng = None
        print(store_name)
        print(store_address)
        print(store_lat, store_lng)
        time.sleep(0.2)  # 每0.2秒发送一次请求

        arcade_document = {
            "store_name": store_name,
            "store_address": store_address,
            "store_id": id,
            "store_lat": Decimal128(str(store_lat)) if store_lat is not None else None,
            "store_lng": Decimal128(str(store_lng)) if store_lng is not None else None,
            "store_type": store_type,
            "arcade_dead": False,
            "store_pos": {
                "type": "Point",
                "coordinates": (
                    [store_lng, store_lat]
                    if store_lat is not None and store_lng is not None
                    else []
                ),
            },
        }
        arcades_collection.insert_one(arcade_document)

    id += 1

# 关闭数据库连接
client.close()
