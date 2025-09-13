import base64
import requests
import time
import random
import html2text
import trafilatura

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs




class SearchEngine(ABC):
    
    """搜索引擎抽象基类"""
    
    def __init__(self, user_agent=None, delay=1.0, timeout=10):
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    

    def search(self, query, num_results=10, lang="en"):
        results = []
        page = 0
        
        while len(results) < num_results:
            page_results = self._fetch_search_page(query, page, lang)
            if not page_results:
                break
                
            results.extend(page_results)
            page += 1
            time.sleep(self.delay * random.uniform(0.5, 1.5))
        
        return results[:num_results]
    
    @abstractmethod
    def _fetch_search_page(self, query, page, lang):
        pass
    
    @abstractmethod
    def _parse_results(self, soup: BeautifulSoup):
        pass
    
    def set_proxy(self, proxy):
        """设置代理服务器"""
        self.session.proxies = {
            'http': proxy,
            'https': proxy
        }


class BingSearchEngine(SearchEngine):
    """Bing搜索引擎实现"""
    
    def __init__(self, user_agent=None, delay=1.0, timeout=10):
        super().__init__(user_agent, delay, timeout)
        self.url = "https://www.bing.com/search"
        self.param = "q"
        self.result_selector = "li.b_algo"
        self.title_selector = "h2"
        self.link_selector = "a"
        self.snippet_selector = "div.b_caption p"
        self.next_page_selector = "a.sb_pagN"
    
    def _fetch_search_page(self, query, page, lang):
        params = {self.param: query}
        
        if page > 0:
            params["first"] = page * 10 + 1
        
        try:
            response = self.session.get(self.url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_results(soup)
            
        except requests.RequestException as e:
            print(f"Bing请求出错: {e}")
            return []
        except Exception as e:
            print(f"Bing解析出错: {e}")
            return []
    
    def _parse_results(self, soup: BeautifulSoup):
        results = []
        search_results = soup.select(self.result_selector)
        
        for result in search_results:
            try:
                title_elem = result.select_one(self.title_selector)
                title = title_elem.get_text().strip() if title_elem else "无标题"
                
                link_elem = result.select_one(self.link_selector)
                if not link_elem or not link_elem.get('href'):
                    continue
                    
                link = link_elem['href']
                
                if "ck/a" in link:
                    query = urlparse(link).query
                    params = parse_qs(query)
                    if 'u' in params:
                        encoded_url = params['u'][0]

                        # move "a1"
                        if encoded_url.startswith('a1'):
                            encoded_url = encoded_url[2:]
                        
                        # base64 padding
                        missing_padding = len(encoded_url) % 4
                        if missing_padding:
                            encoded_url += '=' * (4 - missing_padding)

                        link = base64.b64decode(encoded_url).decode('utf-8')

                
                snippet_elem = result.select_one(self.snippet_selector)
                snippet = snippet_elem.get_text().strip() if snippet_elem else "无摘要"
                
                results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet
                })
                
            except Exception as e:
                print(f"Bing解析单个结果时出错: {e}")
                continue
        
        return results


class BaiduSearchEngine(SearchEngine):
    """百度搜索引擎实现"""
    
    def __init__(self, user_agent=None, delay=1.0, timeout=10):
        super().__init__(user_agent, delay, timeout)
        self.url = "https://www.baidu.com/s"
        self.param = "wd"
        self.result_selector = "div.result"
        self.title_selector = "h3 a"
        self.link_selector = "a"
        self.snippet_selector = "div.c-abstract"
        self.next_page_selector = "a.n"
    
    def _fetch_search_page(self, query, page, lang):
        params = {self.param: query}
        
        if page > 0:
            params["pn"] = page * 10
        
        try:
            response = self.session.get(self.url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_results(soup)
            
        except requests.RequestException as e:
            print(f"百度请求出错: {e}")
            return []
        except Exception as e:
            print(f"百度解析出错: {e}")
            return []
    
    def _parse_results(self, soup: BeautifulSoup):
        results = []
        search_results = soup.select(self.result_selector)
        
        for result in search_results:
            try:
                title_elem = result.select_one(self.title_selector)
                title = title_elem.get_text().strip() if title_elem else "无标题"
                
                link_elem = result.select_one(self.link_selector)
                if not link_elem or not link_elem.get('href'):
                    continue
                    
                link = link_elem['href']
                
                if link.startswith('/'):
                    base_url = urlparse(self.url).netloc
                    link = f"https://{base_url}{link}"
                
                snippet_elem = result.select_one(self.snippet_selector)
                snippet = snippet_elem.get_text().strip() if snippet_elem else "无摘要"
                
                results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet
                })
                
            except Exception as e:
                print(f"百度解析单个结果时出错: {e}")
                continue
        
        return results


class DuckDuckGoSearchEngine(SearchEngine):
    """DuckDuckGo搜索引擎实现"""
    
    def __init__(self, user_agent=None, delay=1.0, timeout=10):
        super().__init__(user_agent, delay, timeout)
        self.url = "https://html.duckduckgo.com/html/"
        self.param = "q"
        self.result_selector = "div.result"
        self.title_selector = "a.result__a"
        self.link_selector = "a.result__a"
        self.snippet_selector = "a.result__snippet"
        self.next_page_selector = "div.nav-link form"
        self.method = "POST"
    
    
    def _fetch_search_page(self, query, page, lang):
        params = {self.param: query}
        
        try:
            if self.method == "POST":
                response = self.session.post(self.url, data=params, timeout=self.timeout)
            else:
                response = self.session.get(self.url, params=params, timeout=self.timeout)
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_results(soup)
            
        except requests.RequestException as e:
            print(f"DuckDuckGo请求出错: {e}")
            return []
        except Exception as e:
            print(f"DuckDuckGo解析出错: {e}")
            return []
    
    def _parse_results(self, soup: BeautifulSoup):
        results = []
        search_results = soup.select(self.result_selector)
        
        for result in search_results:
            try:
                title_elem = result.select_one(self.title_selector)
                title = title_elem.get_text().strip() if title_elem else "无标题"
                
                link_elem = result.select_one(self.link_selector)
                if not link_elem or not link_elem.get('href'):
                    continue
                    
                link = link_elem['href']
                
                snippet_elem = result.select_one(self.snippet_selector)
                snippet = snippet_elem.get_text().strip() if snippet_elem else "无摘要"
                
                results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet
                })
                
            except Exception as e:
                print(f"DuckDuckGo解析单个结果时出错: {e}")
                continue
        
        return results


class SearchEngineFactory:
    """搜索引擎工厂类"""
    
    @staticmethod
    def create_engine(engine_type, user_agent=None, delay=1.0, timeout=10) -> SearchEngine:
        engines = {
            "bing": BingSearchEngine,
            "baidu": BaiduSearchEngine,
            "duckduckgo": DuckDuckGoSearchEngine
        }
        
        if engine_type not in engines:
            raise ValueError(f"不支持的搜索引擎: {engine_type}。支持的引擎: {list(engines.keys())}")
        
        return engines[engine_type](user_agent, delay, timeout)


class SearchEngineCrawler:
    """搜索引擎爬虫主类（外观模式）"""
    
    def __init__(self, user_agent=None, delay=1.0, timeout=10):
        self.user_agent = user_agent
        self.delay = delay
        self.timeout = timeout
    
    def search(self, query, engine="google", num_results=10, lang="en"):
        """执行搜索并返回结果"""
        search_engine = SearchEngineFactory.create_engine(
            engine, self.user_agent, self.delay, self.timeout
        )
        return search_engine.search(query, num_results, lang)
        

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

    def fetch_page_content(self, url, selectors=None):
        """
        抓取指定网页内容并转换为Markdown格式
        
        Args:
            url: 目标网页URL
            selectors: 自定义内容选择器字典，例如：
                {
                    "title": "h1",
                    "content": "div.article-content",
                    "author": "span.author"
                }
                若未提供，则使用智能正文提取逻辑。
        
        Returns:
            dict: 包含提取内容的字典，包含Markdown格式的正文
        """
        try:
            time.sleep(self.delay * random.uniform(0.5, 1.5))  # 避免请求过快
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding  # 自动识别编码
            
            if selectors:
                # 使用自定义选择器
                return self._extract_with_selectors(response.text, selectors)
            else:
                # 使用智能正文提取
                return self._extract_main_content(response.text)
                
        except Exception as e:
            print(f"抓取页面 {url} 出错: {e}")
            return {"error": str(e)}

    def _extract_with_selectors(self, html_content, selectors):
        """
        使用提供的选择器提取内容并转换为Markdown
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted = {}
        
        for key, selector in selectors.items():
            elements = soup.select(selector)
            if key == "content":
                # 对正文内容进行Markdown转换
                content_html = "".join(str(e) for e in elements)
                extracted[key] = self.html_converter.handle(content_html).strip()
            else:
                # 对其他字段提取文本
                extracted[key] = "\n".join([e.get_text().strip() for e in elements if e.get_text().strip()])
        
        return extracted

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
            print(f"智能提取失败 {e}")


if __name__ == "__main__":
    search_crawler = SearchEngineCrawler(delay=0.5)
    page_crawler = PageCrawler(delay=0.5)
    
    try:
        results = search_crawler.search("Python编程教程", engine="baidu", num_results=3, lang="zh")
        
        print(f"找到 {len(results)} 条结果:")
        for i, result in enumerate(results, 1):
            print(f"\n{'='*80}")
            print(f"{i}. 标题: {result['title']}")
            print(f"   链接: {result['link']}")
            print(f"   摘要: {result['snippet'][:100]}...")
            
            # 抓取该页面的正文内容
            print(f"   正在抓取页面内容...")
            page_content = page_crawler.fetch_page_content(result['link'])
            
            if "error" not in page_content:
                print(f"   页面标题: {page_content.get('title', '无')}")
                print(f"   正文长度: {page_content.get('word_count', 0)} 词")
                print(f"   正文预览: \n{page_content.get('content', '')[:300]}...")
            else:
                print(f"   页面抓取失败: {page_content['error']}")
                
    except Exception as e:
        print(f"搜索出错: {e}")
    