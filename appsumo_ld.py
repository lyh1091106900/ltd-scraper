import httpx, pandas as pd
from datetime import datetime, date
import os, sys

def scrape_appsumo_api():
    # 直接调用 API 接口
    url = "https://appsumo.com/api/v1/products"
    params = {
        "type": "lifetime_deal",
        "limit": 100,
        "offset": 0
    }
    
    try:
        resp = httpx.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"API 返回数据条数: {len(data.get('results', []))}")
    except Exception as e:
        print(f"API 请求失败: {e}", file=sys.stderr)
        return []

    rows = []
    for item in data.get('results', []):
        rows.append({
            'name': item.get('name', 'N/A'),
            'price': f"${item.get('pricing', {}).get('price', 0)}",
            'category': item.get('category', 'N/A'),
            'link': f"https://appsumo.com/products/{item.get('slug', '')}",
            'scraped_at': datetime.utcnow().isoformat()
        })
    
    return rows

def main():
    os.makedirs('data', exist_ok=True)
    data = scrape_appsumo_api()
    
    df = pd.DataFrame(data)
    today = date.today().isoformat()
    
    df.to_csv(f'data/appsumo_{today}.csv', index=False, encoding='utf-8')
    df.to_csv('data/appsumo_latest.csv', index=False, encoding='utf-8')
    
    print(f"抓取完成: {len(data)} 条数据")
    print(f"DataFrame 列名: {list(df.columns)}")
    print(f"数据预览:\n{df.head()}")

if __name__ == '__main__':
    main()