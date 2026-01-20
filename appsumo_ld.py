import httpx, bs4, pandas as pd
from datetime import datetime, date
import os, sys, traceback

# 确保在脚本所在目录执行
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"工作目录已切换到: {os.getcwd()}")

def scrape_appsumo():
    url = 'https://appsumo.com/lifetime-deals/'
    print(f"正在请求: {url}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = httpx.get(url, timeout=30, headers=headers)
        resp.raise_for_status()
        print(f"请求成功，状态码: {resp.status_code}")
    except Exception as e:
        print(f"请求失败: {e}\n{traceback.format_exc()}", file=sys.stderr)
        return []

    soup = bs4.BeautifulSoup(resp.text, 'lxml')
    cards = soup.select('.deal-card')
    print(f"找到 {len(cards)} 个 deal-card 元素")
    
    rows = []
    for i, card in enumerate(cards):
        try:
            title = card.select_one('.deal-title').text.strip() if card.select_one('.deal-title') else 'N/A'
            price = card.select_one('.deal-price').text.strip() if card.select_one('.deal-price') else 'N/A'
            category = card.select_one('.deal-category').text.strip() if card.select_one('.deal-category') else 'N/A'
            link = card.select_one('a')['href'] if card.select_one('a') else ''
            
            rows.append({
                'name': title,
                'price': price,
                'category': category,
                'link': f"https://appsumo.com{link}",
                'scraped_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f"解析第 {i} 个卡片失败: {e}", file=sys.stderr)
            continue
    
    print(f"成功解析 {len(rows)} 条数据")
    return rows

def main():
    # 强制创建 data 目录
    os.makedirs('data', exist_ok=True)
    print(f"data 目录已确认: {os.path.abspath('data')}")
    
    # 抓取数据
    data = scrape_appsumo()
    
    # 强制创建 DataFrame（即使数据为空）
    df = pd.DataFrame(data)
    print(f"DataFrame 形状: {df.shape}")
    
    # 强制保存文件（无论是否抓到数据）
    today = date.today().isoformat()
    dated_path = f'data/appsumo_{today}.csv'
    latest_path = 'data/appsumo_latest.csv'
    
    df.to_csv(dated_path, index=False, encoding='utf-8')  # 这里修复了语法错误
    df.to_csv(latest_path, index=False, encoding='utf-8') # 这里修复了语法错误
    
    print(f"文件已强制生成:")
    print(f"  - {dated_path} ({os.path.getsize(dated_path)} 字节)")
    print(f"  - {latest_path} ({os.path.getsize(latest_path)} 字节)")
    
    # 打印 data 目录内容
    print("\ndata 目录内容:")
    for f in os.listdir('data'):
        print(f"  - {f} ({os.path.getsize(f'data/{f}')} 字节)")

if __name__ == '__main__':
    main()