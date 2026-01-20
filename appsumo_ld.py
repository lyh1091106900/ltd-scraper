import httpx, bs4, pandas as pd
from datetime import datetime, date
import os

def scrape_appsumo():
    url = 'https://appsumo.com/lifetime-deals/'
    try:
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"请求失败: {e}")
        return []

    soup = bs4.BeautifulSoup(resp.text, 'lxml')
    rows = []
    
    # 选择器可能随页面变化，需定期更新
    for card in soup.select('.deal-card'):
        try:
            title = card.select_one('.deal-title').text.strip()
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
        except AttributeError:
            continue
    
    return rows

def main():
    # 创建 data 目录
    os.makedirs('data', exist_ok=True)
    
    # 抓取数据
    data = scrape_appsumo()
    
    if not data:
        print("未抓取到数据")
        return
    
    # 保存为带日期的 CSV
    today = date.today().isoformat()
    df = pd.DataFrame(data)
    df.to_csv(f'data/appsumo_{today}.csv', index=False, encoding='utf-8')
    
    # 同时更新最新汇总
    df.to_csv('data/appsumo_latest.csv', index=False, encoding='utf-8')
    
    print(f"抓取完成: {len(data)} 条数据")

if __name__ == '__main__':
    main()