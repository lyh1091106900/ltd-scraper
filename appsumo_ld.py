import httpx, bs4, pandas as pd
from datetime import datetime, date
import os, sys, traceback
from playwright.sync_api import sync_playwright

# ==================== 数据源配置 ====================
SOURCES = [
    {"name": "stacksocial", "func": "scrape_stacksocial", "type": "static"},  # 优先级最高
    {"name": "appsumo", "func": "scrape_appsumo", "type": "dynamic"},         # 备用
]

# ==================== StackSocial 实现 ====================

def scrape_stacksocial():
    """爬取 StackSocial（静态页面，成功率高）"""
    url = "https://stacksocial.com/sales"
    print(f"[StackSocial] 正在请求: {url}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = httpx.get(url, timeout=30, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(f"[StackSocial] 请求失败: {e}", file=sys.stderr)
        return []

    soup = bs4.BeautifulSoup(resp.text, 'lxml')
    rows = []
    
    # 更灵活的选择器（根据实际页面结构）
    for card in soup.select('.offer-card, [class*="offer"], .deal-card'):
        try:
            # 尝试多种标题选择器
            title_elem = (card.select_one('h3') or 
                         card.select_one('.title') or 
                         card.select_one('[class*="title"]'))
            
            # 尝试多种价格选择器
            price_elem = (card.select_one('.price') or 
                         card.select_one('.price-tag') or 
                         card.select_one('.offer-price'))
            
            # 尝试链接
            link_elem = card.select_one('a')
            
            title = title_elem.text.strip() if title_elem else 'N/A'
            price = price_elem.text.strip() if price_elem else 'N/A'
            link = link_elem['href'] if link_elem else ''
            
            # 过滤掉 N/A 过多的数据
            if title == 'N/A' and price == 'N/A':
                continue
                
            rows.append({
                'name': title,
                'price': price,
                'category': 'Software',  # StackSocial 分类不明显
                'link': f"https://stacksocial.com{link}" if link.startswith('/') else link,
                'scraped_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f"[StackSocial] 解析卡片失败: {e}", file=sys.stderr)
            continue
    
    print(f"[StackSocial] 成功抓取 {len(rows)} 条数据")
    return rows

# ==================== AppSumo 实现 ====================

def scrape_appsumo():
    """AppSumo（Playwright 动态渲染，备用）"""
    with sync_playwright() as p:
        print("[AppSumo] 正在启动浏览器...")
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()
        
        url = "https://appsumo.com/lifetime-deals/"
        print(f"[AppSumo] 正在访问: {url}")
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(8000)  # 等待 8 秒让 JS 充分加载
        except Exception as e:
            print(f"[AppSumo] 访问失败: {e}", file=sys.stderr)
            browser.close()
            return []

        # 尝试多种选择器
        selectors = [".deal-card", "[class*='deal']", "[class*='card']", "article"]
        cards = []
        
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=5000)
                cards = page.query_selector_all(selector)
                print(f"[AppSumo] 选择器 '{selector}' 找到 {len(cards)} 个元素")
                if cards:
                    break
            except:
                print(f"[AppSumo] 选择器 '{selector}' 超时")
                continue
        
        if not cards:
            print("[AppSumo] 所有选择器都未找到元素")
            # 截图诊断
            page.screenshot(path="appsumo_debug.png", full_page=True)
            print("📸 已保存诊断截图: appsumo_debug.png")
            browser.close()
            return []

        rows = []
        for i, card in enumerate(cards[:30]):  # 限制前30个
            try:
                # 尝试多种选择器组合
                title = card.query_selector("h3, .title, .deal-title, h2")
                price = card.query_selector(".price, .deal-price, [class*='price']")
                category = card.query_selector(".category, .deal-category, .tag")
                link = card.query_selector("a")
                
                title_text = title.inner_text().strip() if title else 'N/A'
                price_text = price.inner_text().strip() if price else 'N/A'
                category_text = category.inner_text().strip() if category else 'N/A'
                link_href = link.get_attribute("href") if link else ''
                
                # 过滤无效数据
                if title_text == 'N/A' and price_text == 'N/A':
                    continue
                
                rows.append({
                    'name': title_text,
                    'price': price_text,
                    'category': category_text,
                    'link': f"https://appsumo.com{link_href}" if link_href.startswith('/') else link_href,
                    'scraped_at': datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"[AppSumo] 解析第 {i} 个卡片失败: {e}", file=sys.stderr)
                continue
        
        browser.close()
        print(f"[AppSumo] 成功解析 {len(rows)} 条有效数据")
        return rows

def generate_mock_data():
    """保底模拟数据"""
    print("⚠️  使用模拟数据")
    return [
        {
            'name': f'Lifetime Deal Tool {i+1}',
            'price': f'${39 + i*20}',
            'category': 'Productivity',
            'link': f'https://example.com/tool-{i+1}',
            'scraped_at': datetime.utcnow().isoformat()
        }
        for i in range(5)
    ]

# ==================== 主调度 ====================

def main():
    print(f"\n=== 开始多源抓取（{date.today()}） ===\n")
    os.makedirs('data', exist_ok=True)
    
    all_data = []
    success_source = None
    
    for source in SOURCES:
        print(f"\n--- 尝试数据源: {source['name']} ---")
        try:
            func = globals()[source['func']]
            data = func()
            
            if data and len(data) > 0:
                # 过滤掉全是 N/A 的无效数据
                valid_data = [d for d in data if d.get('name') != 'N/A' or d.get('price') != 'N/A']
                if valid_data:
                    print(f"✅ {source['name']} 成功: {len(valid_data)} 条有效数据")
                    all_data = valid_data
                    success_source = source['name']
                    break
                else:
                    print(f"⚠️  {source['name']} 数据无效（全为 N/A）")
            else:
                print(f"⚠️  {source['name']} 返回空数据")
        except Exception as e:
            print(f"❌ {source['name']} 异常: {e}", file=sys.stderr)
            traceback.print_exc()
    
    if not all_data:
        print("\n--- 全部失败，使用模拟数据 ---")
        all_data = generate_mock_data()
        success_source = "mock"
    
    # 保存
    df = pd.DataFrame(all_data)
    today = date.today().isoformat()
    
    dated_path = f'data/appsumo_{today}.csv'
    latest_path = 'data/appsumo_latest.csv'
    
    df.to_csv(dated_path, index=False, encoding='utf-8')
    df.to_csv(latest_path, index=False, encoding='utf-8')
    
    print(f"\n=== 抓取完成 ===")
    print(f"数据源: {success_source}")
    print(f"数据条数: {len(df)}")
    print(f"有效列: {[col for col in df.columns if df[col].nunique() > 1]}")
    print(f"\n数据预览:\n{df.head()}")

if __name__ == '__main__':
    main()