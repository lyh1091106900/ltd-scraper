import httpx, bs4, pandas as pd
from datetime import datetime, date
import os, sys

# 确保在脚本所在目录执行
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"工作目录已切换到: {os.getcwd()}")

def scrape_appsumo():
    # ❌ 错误：URL 末尾有空格
    # url = 'https://appsumo.com/lifetime-deals/ '
    
    # ✅ 正确：URL 干净无空格
    url = 'https://appsumo.com/lifetime-deals/'
    print(f"正在请求: {url}")
    
    try:
        # 增加 headers 模拟浏览器，防止被 Cloudflare 拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = httpx.get(url, timeout=30, headers=headers)
        resp.raise_for_status()
        print(f"请求成功，状态码: {resp.status_code}")
    except Exception as e:
        print(f"请求失败: {e}", file=sys.stderr)
        return []

    soup = bs4.BeautifulSoup(resp.text, 'lxml')
    rows = []
    
    # 打印页面标题，确认访问正常
    print(f"页面标题: {soup.title.string if soup.title else '无标题'}")
    
    # 检查选择器是否能匹配到元素
    cards = soup.select('.deal-card')
    print(f"找到 {len(cards)} 个 deal-card 元素")
    
    for i, card in enumerate(cards):
        try:
            title = card.select_one('.deal-title').text.strip() if card.select_one('.deal-title') else 'N/A'
            price = card.select_one('.deal-price').text.strip() if card.select_one('.deal-price') else 'N/A'
            category = card.select_one('.deal-category').text.strip() if card.select_one('.deal-category') else 'N/A'
            link = card.select_one('a')['href'] if card.select_one('a') else ''
            
            # ❌ 错误：链接拼接有空格
            # 'link': f"https://appsumo.com {link}",
            
            # ✅ 正确：链接干净无空格
            rows.append({
                'name': title,
                'price': price,
                'category': category,
                'link': f"https://appsumo.com{link}",
                'scraped_at': datetime.utcnow().isoformat()
            })
        except AttributeError as e:
            print(f"解析第 {i} 个卡片失败: {e}", file=sys.stderr)
            continue
    
    print(f"成功解析 {len(rows)} 条数据")
    return rows

def main():
    # 创建 data 目录
    os.makedirs('data', exist_ok=True)
    print(f"data 目录已确认: {os.path.abspath('data')}")
    
    # 抓取数据
    data = scrape_appsumo()
    
    if not data:
        print("警告: 未抓取到任何数据", file=sys.stderr)
        return
    
    # 保存为带日期的 CSV
    today = date.today().isoformat()
    df = pd.DataFrame(data)
    
    dated_path = f'data/appsumo_{today}.csv'
    df.to_csv(dated_path, index=False, encoding='utf-8')
    print(f"数据已保存到: {dated_path} ({os.path.getsize(dated_path)} 字节)")
    
    # 同时更新最新汇总
    latest_path = 'data/appsumo_latest.csv'
    df.to_csv(latest_path, index=False, encoding='utf-8')
    print(f"最新汇总已保存到: {latest_path} ({os.path.getsize(latest_path)} 字节)")
    