import random
import time
import html2text
import requests
import trafilatura


class PageCrawler:
    def __init__(self, user_agent=None, delay=1.0, timeout=10):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True         # 忽略超链接
        self.html_converter.ignore_images = False       # 保留图片
        self.html_converter.ignore_emphasis = False     # 保留强调格式
        self.html_converter.body_width = 0              # 不换行

    def fetch_page_content(self, url):
        """抓取指定网页内容并转换为Markdown格式"""
        try:
            time.sleep(self.delay * random.uniform(0.5, 1.5))
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding 

            return self._extract_main_content(response.text)
                
        except Exception as e:
            print(f"抓取页面 {url} 出错: {e}")
            return {"error": str(e)}

    def _extract_main_content(self, html_content):
        """使用trafilatura智能提取正文内容并转换为Markdown格式"""
        try:
            extracted = trafilatura.extract(
                html_content,
                include_links=False,  # 不包含链接
                include_tables=True,  # 包含表格
                output_format="markdown"  # 直接输出markdown
            )
            
            title = trafilatura.extract_metadata(html_content).as_dict()["title"]
            
            return {
                "title": title,
                "content": extracted,
                "word_count": len(extracted.split())
            }
    
        except Exception as e:
            print(f"trafilatura提取失败 {e}")    