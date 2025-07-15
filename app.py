from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, Tag, NavigableString


app = Flask(__name__)

# 用于存储每次搜索的结果
search_results = {}
lock = threading.Lock()

def get_quark_linksy03_retry(movie_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 1. 打开网站
        driver.get("https://chatbot-weixin-qq-com-u0rr7jzu0kscgu02d04dfb1bw-lpaoau04.heykafeijun.com/")
        time.sleep(2)

        # 2. 输入电影名并搜索
        search_box = driver.find_element(By.NAME, "keyword")
        search_box.send_keys(movie_name)
        search_box.submit()
        time.sleep(3)  # 等待结果加载

        # 3. 获取所有资源项
        results = []
        groups = driver.find_elements(By.CSS_SELECTOR, ".result-group")
        for group in groups:
            # 获取分组标题
            group_title = group.find_element(By.CSS_SELECTOR, ".result-title").text.strip()
            # 获取所有资源项
            items = group.find_elements(By.CSS_SELECTOR, ".resource-item")
            quark_links = []
            for item in items:
                # 有的 resource-item 可能没有下载按钮，要判断
                try:
                    download_btn = item.find_element(By.CSS_SELECTOR, ".download-button")
                    quark_link = download_btn.get_attribute("data-link")
                    if quark_link:
                        quark_links.append(quark_link)
                except:
                    continue
            # 只要有链接就加入结果
            if quark_links:
                results.append({
                    "title": group_title,
                    "links": quark_links
                })

        # 输出格式化
        for group in results:
            print(f"【{group['title']}】")
            for link in group['links']:
                print(link)
            print("-" * 30)

        return results

    finally:
        driver.quit()


def get_kuaikan_links_kuake5_retry(movie_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    print("开始获取夸克5链接")

    try:
        # 1. 构造和JS一致的URL
        # JS: 'search-' + xn.urlencode(keyword) + '-' + range
        search_url = f"https://kuake5.com/search-{quote(movie_name)}-0.htm"
        driver.set_page_load_timeout(15)
        try:
            driver.get(search_url)
            print("已跳转到搜索结果页")
        except TimeoutException:
            print("页面加载超时！")
        except Exception as e:
            print("页面加载出错：", e)

        # 2. 等待页面加载（可用WebDriverWait等条件）
        # 这里可以等待某个你确定会出现的元素，比如资源块
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(driver, 10).until(
            #EC.presence_of_element_located((By.CSS_SELECTOR, ".media.post"))
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.my-2"))
        )
        print("页面已加载资源块")

        # 3. 获取所有资源项
        results = []
        #print(driver.page_source)
        blocks = driver.find_elements(By.CSS_SELECTOR, ".media.post")
        blocks = driver.find_elements(By.CSS_SELECTOR, ".media")
        print("media数量：", len(blocks))
        # blocks2 = driver.find_elements(By.CSS_SELECTOR, ".post")
        # print("post数量：", len(blocks2))
        for block in blocks:
            print("找到资源块")
            p = driver.find_element(By.CSS_SELECTOR, "p.my-2")
            full_text = p.text.strip()
            match = re.search(r'(https?://[^\s]+)', full_text)
            if match:
                url = match.group(1)
                before_url = full_text.split(url)[0].strip()
                results.append({
                    "title": before_url,
                    "links": url
                })
                print("网址前内容：", before_url)
                print("网址：", url)
            else:
                print("没有找到网址")

        # 输出格式化
        # for group in results:
        #     print(f"【{group['title']}】")
        #     for link in group['links']:
        #         print(link)
        #     print("-" * 30)

        return results

    finally:
        driver.quit()

def extract_info_content(info_html):
    soup = BeautifulSoup(info_html, "html.parser")
    # 移除所有 ctrl-box 节点
    for ctrl in soup.select('.ctrl-box'):
        ctrl.decompose()

    result = []
    for elem in soup.recursiveChildGenerator():
        if isinstance(elem, Tag):
            if elem.name == "a":
                text = elem.get_text(strip=True)
                href = elem.get("href", "")
                result.append(f"{text} {href}")
            elif elem.name == "br":
                result.append("\n")
        elif isinstance(elem, NavigableString):
            if str(elem).strip():
                result.append(str(elem).strip())
    return "".join(result).replace("\n\n", "\n").strip()

def get_kuaikan_links_youzi_retry(movie_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    driver = webdriver.Chrome(options=chrome_options)
    print("开始获取夸克5链接")

    try:
        # 1. 打开网站
        driver.get("http://m.yzjfilm.cn/app/index.html?id=200616nc")
        time.sleep(2)
        print("页面已打开")

        # 2. 输入电影名并搜索
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='请输入搜索的影视名称']"))
        )
        print("找到搜索框")
        search_box.send_keys(movie_name)
        print("已输入电影名")
        search_btn = driver.find_element(By.ID, "submitSearch")
        search_btn.click()
        print("已提交搜索")

        results = []
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".access-box"))
        )
        access_boxes = driver.find_elements(By.CSS_SELECTOR, ".access-box")
        for box in access_boxes:
            print("找到资源块")
            try:
                info_elem = box.find_element(By.CSS_SELECTOR, ".info")
                info_html = info_elem.get_attribute("innerHTML")
                info_content = extract_info_content(info_html)
                print(info_content)
                print("-" * 30)
            except Exception as e:
                print("提取 info 内容失败：", e)


            # 3. 只保留包含 http 的内容
            # merged_content = info_content + "\n" + flex_content
            # if "http" in merged_content:
            #     results.append(merged_content.strip())
            # print(results)
            
        return results


    finally:
        driver.quit()


def retry_call(func, args=(), kwargs=None, max_retries=3):
    """通用重试函数，func为要调用的函数，max_retries为最大重试次数"""
    if kwargs is None:
        kwargs = {}
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"第{attempt}次尝试失败，错误信息：{e}")
            if attempt == max_retries:
                print("已达到最大重试次数，放弃。")
                return None

# 假设这是你的三个资源检索函数（用sleep模拟耗时，实际用你的实现替换）
def get_quark_linksy03(keyword):
    links = retry_call(get_quark_linksy03_retry, args=(keyword,), max_retries=3)
    return links

def get_kuaikan_links_kuake5(keyword):
    links = retry_call(get_kuaikan_links_kuake5_retry, args=(keyword,), max_retries=3)
    return links

def get_kuaikan_links_youzi(keyword):
    links = retry_call(get_kuaikan_links_youzi_retry, args=(keyword,), max_retries=3)
    return links

def run_search(keyword, search_id):
    funcs = [
        ('links', get_quark_linksy03),
        ('links1', get_kuaikan_links_kuake5),
        ('links2', get_kuaikan_links_youzi)
    ]
    with ThreadPoolExecutor() as executor:
        future_to_key = {executor.submit(func, keyword): key for key, func in funcs}
        for future in future_to_key:
            key = future_to_key[future]
            def callback(fut, key=key):
                try:
                    result = fut.result()
                except Exception as e:
                    result = [f"出错: {e}"]
                with lock:
                    search_results[search_id][key] = result
            future.add_done_callback(callback)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    search_id = str(time.time()).replace('.', '')  # 简单唯一ID
    with lock:
        search_results[search_id] = {'links': None, 'links1': None, 'links2': None}
    threading.Thread(target=run_search, args=(keyword, search_id), daemon=True).start()
    return jsonify({'search_id': search_id})

@app.route('/progress/<search_id>')
def progress(search_id):
    with lock:
        result = search_results.get(search_id)
    all_links = []
    seen = set()
    if result:
        for key in ['links', 'links1', 'links2']:
            if result[key]:
                for item in result[key]:
                    # 转成字符串做唯一性判断
                    s = str(item)
                    if s not in seen:
                        all_links.append(item)
                        seen.add(s)
    return jsonify({'all_links': all_links})

if __name__ == '__main__':
    app.run(debug=True) 