import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode
import time

# 定义年份阈值（跳过2022年及之前的论文）
YEAR_THRESHOLD = 2022


def fetch_webpage(url, max_retries=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

    for retry in range(max_retries):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                allow_redirects=True,
                verify=True
            )
            if 400 <= response.status_code < 500:
                response.raise_for_status()
            elif 500 <= response.status_code < 600:
                print(f"服务器返回500错误，第{retry + 1}次重试...")
                time.sleep(2 ** retry)
                continue
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"请求失败（重试{retry + 1}/{max_retries}）：{e}")
            if retry < max_retries - 1:
                time.sleep(2 ** retry)
            else:
                raise
    return ""


def check_comments_year(comments_text):
    """检查Comments字段中的年份，若包含<= YEAR_THRESHOLD的年份返回True（需要跳过），否则返回False"""
    if not comments_text:
        return False

    # 提取所有4位数字的年份
    year_matches = re.findall(r'\b20\d{2}\b', comments_text)
    if not year_matches:
        return False

    # 检查是否有年份<=阈值
    for year_str in year_matches:
        year = int(year_str)
        if year <= YEAR_THRESHOLD:
            print(f"  检测到Comments中包含{year}年（≤{YEAR_THRESHOLD}），跳过该论文")
            return True
    return False


def parse_arxiv_results(html_content, page_num):
    """解析arxiv搜索结果页面，提取符合条件的论文信息（跳过2022年及更早的论文）"""
    soup = BeautifulSoup(html_content, 'html.parser')
    papers = []
    paper_index = 0

    for result in soup.find_all('li', class_='arxiv-result'):
        paper_index += 1
        paper_info = {}

        # 1. 提取论文题目
        title_elem = result.find('p', class_='title is-5 mathjax')
        title = title_elem.get_text(strip=True) if title_elem else "无标题"
        paper_info['title'] = title

        # 2. 提取论文网页链接（abs链接）
        web_link = ""
        web_a_elem = result.find('a', href=re.compile(r'/abs/\d+\.\d+'))
        if web_a_elem:
            web_href = web_a_elem.get('href', '')
            if web_href.startswith('/'):
                web_link = f"https://arxiv.org{web_href}"
            else:
                web_link = web_href
        paper_info['web_link'] = web_link

        # 3. 提取PDF链接
        pdf_link = ""
        pdf_a_elem = result.find('a', href=re.compile(r'/pdf/\d+\.\d+'))
        if pdf_a_elem:
            pdf_href = pdf_a_elem.get('href', '')
            if pdf_href.startswith('/'):
                pdf_link = f"https://arxiv.org{pdf_href}"
            else:
                pdf_link = pdf_href
        paper_info['pdf_link'] = pdf_link

        # 4. 提取作者
        authors_elem = result.find('p', class_='authors')
        if authors_elem:
            author_links = authors_elem.find_all('a')
            authors = [a.get_text(strip=True) for a in author_links]
            paper_info['authors'] = ', '.join(authors)
        else:
            paper_info['authors'] = ""

        # 5. 提取完整摘要
        abstract_full = result.find('span', class_='abstract-full')
        abstract_short = result.find('span', class_='abstract-short')
        if abstract_full:
            abstract_text = abstract_full.get_text(strip=True).replace('⊖ Less', '').strip()
        elif abstract_short:
            abstract_text = abstract_short.get_text(strip=True).replace('⊕ More', '').strip()
        else:
            abstract_text = ""
        paper_info['abstract'] = abstract_text.replace("△ Less", "")

        # 6. 提取提交时间
        submitted_elem = result.find('p', class_='is-size-7')
        if submitted_elem:
            submitted_text = submitted_elem.get_text(strip=True)
            paper_info['submitted'] = submitted_text
        else:
            paper_info['submitted'] = ""

        # 7. 提取Comments字段并检查年份
        comments_elem = result.find('p', class_='comments is-size-7')
        comments_text = ""
        if comments_elem:
            comments_text_elem = comments_elem.find('span', class_='has-text-grey-dark mathjax')
            comments_text = comments_text_elem.get_text(strip=True) if comments_text_elem else ""
        paper_info['comments'] = comments_text

        # 打印当前论文信息
        print(f"  第{page_num}页 - 论文{paper_index}：{title}")
        if web_link:
            print(f"     网页链接：{web_link}")
        if pdf_link:
            print(f"     PDF链接：{pdf_link}")

        # 检查Comments中的年份，若需要跳过则不添加到列表中
        if check_comments_year(comments_text):
            continue  # 跳过当前论文，处理下一篇

        papers.append(paper_info)

    return papers


def save_to_csv(papers, filename='arxiv_eccv_papers.csv'):
    """将论文信息保存为CSV文件（包含网页链接+PDF链接）"""
    df = pd.DataFrame(papers)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"成功保存{len(papers)}篇论文信息到 {filename}（含网页链接+PDF链接字段）")


def extract_total_results(html_content):
    """从arxiv搜索页面提取总结果数（如3,543 → 3543）"""
    soup = BeautifulSoup(html_content, 'html.parser')
    h1_elem = soup.find('h1', class_='title is-clearfix')

    if not h1_elem:
        return 0

    text = h1_elem.get_text(strip=True)
    match = re.search(r'of ([\d,]+)', text)
    if match:
        total = int(match.group(1).replace(',', ''))
        return total
    return 0


def spider_target(target):
    """针对单个顶会关键词爬取arxiv论文，跳过Comments中包含2022年及更早年份的论文"""
    if not target:
        print("跳过空的顶会关键词")
        return

    print(f"\n========== 开始爬取 {target} 相关论文（跳过{YEAR_THRESHOLD}年及更早） ==========")
    page_size = 200
    all_papers = []

    # init_params = {
    #     'advanced': '',
    #     'terms-0-operator': 'AND',
    #     'terms-0-term': target,
    #     'terms-0-field': 'comments',
    #     'classification-physics_archives': 'all',
    #     'classification-include_cross_list': 'include',
    #     'date-filter_by': 'all_dates',
    #     'date-year': '',
    #     'date-from_date': '',
    #     'date-to_date': '',
    #     'date-date_type': 'submitted_date',
    #     'abstracts': 'show',
    #     'size': page_size,
    #     'order': '-announced_date_first',
    #     'start': '0'
    # }
    init_params={
        "query": target,
        "searchtype":"comments",
        "abstracts" : "show",
        "size" : "200",
        "order" : "-announced_date_first",
        "date-date_type" : "submitted_date",
        "start" :"0",
    }
    init_url = "https://arxiv.org/search/?" + urlencode(init_params)

    try:
        init_content = fetch_webpage(init_url)
        if not init_content:
            print(f"{target} - 初始化请求失败，无法获取总结果数")
            return

        total_results = extract_total_results(init_content)
        print(f"{target} - 搜索结果总数：{total_results}")

        if total_results == 0:
            print(f"{target} - 未找到任何论文结果")
            return

        total_pages = (total_results + page_size - 1) // page_size
        print(f"{target} - 开始分页爬取，共{total_pages}页...")

        for page_num in range(total_pages):
            start = page_num * page_size
            current_page_num = page_num + 1
            print(f"\n{target} - 爬取第{current_page_num}页（start={start}）")

            params = init_params.copy()
            params['start'] = str(start)
            # https://arxiv.org/search/?searchtype=comments&query=IJCAI&abstracts=show&size=200&order=-announced_date_first&date-date_type=submitted_date&start=200
            current_url = "https://arxiv.org/search/?" + urlencode(params)
            content = fetch_webpage(current_url)

            if not content:
                print(f"{target} - 第{current_page_num}页请求失败，跳过")
                continue

            # 解析当前页（不再传入停止标志）
            page_papers = parse_arxiv_results(content, current_page_num)
            print(f"{target} - 第{current_page_num}页解析到 {len(page_papers)} 篇符合条件的论文")
            all_papers.extend(page_papers)

            time.sleep(1 + page_num * 0.1)

        # 保存已爬取的论文
        if all_papers:
            filename = f"arxiv_{target}_papers_after_{YEAR_THRESHOLD}.csv"
            save_to_csv(all_papers, filename=filename)
            print(f"\n{target} - 爬取完成，总计保存 {len(all_papers)} 篇{YEAR_THRESHOLD + 1}年及以后的论文")
        else:
            print(f"\n{target} - 未爬取到{YEAR_THRESHOLD + 1}年及以后的论文")

    except Exception as e:
        print(f"{target} - 爬取过程中出现错误：{e}")
        if all_papers:
            filename = f"arxiv_{target}_partial_papers_after_{YEAR_THRESHOLD}.csv"
            save_to_csv(all_papers, filename=filename)
            print(f"{target} - 已保存部分爬取的 {len(all_papers)} 篇论文到 {filename}")


def main():
    # 计算机视觉顶会列表
    targets = [
        "CVPR",
        "ACM",
        # "ICCV",
        # "ECCV",
        # "ICLR",
        # "NeurIPS",
        # "ICML",
        # "AAAI",
        # "IJCAI",
        # "WACV",
        # "BMVC",
        # "ACCV"
    ]

    # 循环爬取每个顶会
    for target in targets:
        spider_target(target)
        time.sleep(10)


if __name__ == "__main__":
    main()