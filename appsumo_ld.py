import pandas as pd
from datetime import datetime, date
import os, sys, traceback
from playwright.sync_api import sync_playwright

def scrape_appsumo():
    with sync_playwright() as p:
        print("正在启动浏览器...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 设置请求头
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        url = "https://appsumo.com/lifetime-deals/"
        print(f"正在访问: {url}")
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            print("页面加载完成")
        except Exception as e:
            print(f"页面加载失败: {e}", file=sys.stderr)
            browser.close()
            return []
        
        # 等待 deal cards 出现
        try:
            page.wait_for_selector(".deal-card", timeout=30000)
            print("deal-card 元素已找到")
        except Exception as e:
            print(f"等待 deal-card 超时: {e}", file=sys.stderr)
            browser.close()
            return []
        
        # 获取所有 deal cards
        cards = page.query_selector_all(".deal-card")
        print(f"找到 {len(cards)} 个 deal-card 元素")
        
        rows = []
        for i, card in enumerate(cards):
            try:
                title_elem = card.query_selector(".deal-title")
                price_elem = card.query_selector(".deal-price")
                category_elem = card.query_selector(".deal-category")
                link_elem = card.query_selector("a")
                
                title = title_elem.inner_text().strip() if title_elem else "N/A"
                price = price_elem.inner_text().strip() if price_elem else "N/A"
                category = category_elem.inner_text().strip() if category_elem else "N/A"
                link = link_elem.get_attribute("href") if link_elem else ""
                
                rows.append({
                    'name': title,
                    'price': price,
                    'category': category,
                    'link': f"https://appsumo.com{link}",
                    'scraped_at': datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"解析第 {i} 个卡片失败: {e}", file=sys.stderr)
                traceback.print_exc()
                continue
        
        browser.close()
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
    
    # 强制保存文件
    today = date.today().isoformat()
    dated_path = f'data/appsumo_{today}.csv'
    latest_path = 'data/appsumo_latest.csv'
    
    df.to_csv(dated_path, index=False, encoding='utf-8')
    df.to_csv(latest_path, index=False, encoding='utf-8')
    
    print(f"文件已强制生成:")
    print(f"  - {dated_path} ({os.path.getsize(dated_path)} 字节)")
    print(f"  - {latest_path} ({os.path.getsize(latest_path)} 字节)")
    
    # 打印 data 目录内容
    print("\ndata 目录内容:")
    for f in os.listdir('data'):
        print(f"  - {f} ({os.path.getsize(f'data/{f}')} 字节)")

if __name__ == '__main__':
    main()