import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


class SearchEngineCrawler:
    def __init__(self, user_agent=None, delay=1.0, timeout=10):
        """
        初始化搜索引擎爬虫
        
        Args:
            user_agent: 使用的User-Agent字符串
            delay: 请求之间的延迟时间（秒），避免被封IP
            timeout: 请求超时时间（秒）
        """
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        # 搜索引擎配置
        self.search_engines = {
            "google": {
                "url": "https://www.google.com/search",
                "param": "q",
                "result_selector": "div.g",
                "title_selector": "h3",
                "link_selector": "a",
                "snippet_selector": "div.VwiC3b",
                "next_page_selector": "#pnnext"
            },
            "bing": {
                "url": "https://www.bing.com/search",
                "param": "q",
                "result_selector": "li.b_algo",
                "title_selector": "h2",
                "link_selector": "a",
                "snippet_selector": "div.b_caption p",
                "next_page_selector": "a.sb_pagN"
            },
            "baidu": {
                "url": "https://www.baidu.com/s",
                "param": "wd",
                "result_selector": "div.result",
                "title_selector": "h3 a",
                "link_selector": "a",
                "snippet_selector": "div.c-abstract",
                "next_page_selector": "a.n"
            },
            "duckduckgo": {
                "url": "https://html.duckduckgo.com/html/",
                "param": "q",
                "result_selector": "div.result",
                "title_selector": "a.result__a",
                "link_selector": "a.result__a",
                "snippet_selector": "a.result__snippet",
                "method": "POST",
                "next_page_selector": "div.nav-link form"
            }
        }
    
    def search(self, query, engine="google", num_results=10, lang="en"):
        """
        执行搜索并返回结果
        
        Args:
            query: 搜索关键词
            engine: 搜索引擎名称 (google, bing, baidu, duckduckgo)
            num_results: 需要返回的结果数量
            lang: 搜索语言
            
        Returns:
            list: 包含搜索结果的字典列表
        """
        if engine not in self.search_engines:
            raise ValueError(f"不支持的搜索引擎: {engine}。支持的引擎: {list(self.search_engines.keys())}")
        
        config = self.search_engines[engine]
        results = []
        page = 0
        
        while len(results) < num_results:
            # 获取当前页面的搜索结果
            page_results = self._fetch_search_page(query, config, page, lang)
            
            if not page_results:
                break  # 没有更多结果了
            
            results.extend(page_results)
            page += 1
            
            # 避免请求过于频繁
            time.sleep(self.delay * random.uniform(0.5, 1.5))
        
        return results[:num_results]
    
    def _fetch_search_page(self, query, config, page, lang):
        """获取单页搜索结果"""
        params = {config["param"]: query}
        
        # 添加分页参数
        if page > 0:
            if config["url"] == "https://www.google.com/search":
                params["start"] = page * 10
            elif config["url"] == "https://www.bing.com/search":
                params["first"] = page * 10 + 1
            elif config["url"] == "https://www.baidu.com/s":
                params["pn"] = page * 10
        
        # 添加语言参数
        if lang and config["url"] == "https://www.google.com/search":
            params["hl"] = lang
        
        try:
            # 发送请求
            if config.get("method") == "POST":
                response = self.session.post(config["url"], data=params, timeout=self.timeout)
            else:
                response = self.session.get(config["url"], params=params, timeout=self.timeout)
            
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取搜索结果
            return self._parse_results(soup, config)
            
        except requests.RequestException as e:
            print(f"请求出错: {e}")
            return []
        except Exception as e:
            print(f"解析出错: {e}")
            return []
    
    def _parse_results(self, soup, config):
        """解析搜索结果页面"""
        results = []
        search_results = soup.select(config["result_selector"])
        
        for result in search_results:
            try:
                # 提取标题
                title_elem = result.select_one(config["title_selector"])
                title = title_elem.get_text().strip() if title_elem else "无标题"
                
                # 提取链接
                link_elem = result.select_one(config["link_selector"])
                if not link_elem or not link_elem.get('href'):
                    continue
                    
                link = link_elem['href']
                
                # 处理相对链接和Google/Baidu的跳转链接
                if link.startswith('/'):
                    base_url = urlparse(config["url"]).netloc
                    link = f"https://{base_url}{link}"
                elif link.startswith('/url?q='):  # Google的跳转链接
                    link = parse_qs(urlparse(link).query)['q'][0]
                
                # 提取摘要
                snippet_elem = result.select_one(config["snippet_selector"])
                snippet = snippet_elem.get_text().strip() if snippet_elem else "无摘要"
                
                results.append({
                    'title': title,
                    'link': link,
                    'snippet': snippet
                })
                
            except Exception as e:
                print(f"解析单个结果时出错: {e}")
                continue
        
        return results
    
    def add_custom_engine(self, name, config):
        """
        添加自定义搜索引擎配置
        
        Args:
            name: 引擎名称
            config: 配置字典，包含以下键:
                - url: 搜索URL
                - param: 查询参数名
                - result_selector: 结果容器选择器
                - title_selector: 标题选择器
                - link_selector: 链接选择器
                - snippet_selector: 摘要选择器
                - method: 请求方法 (可选，默认为GET)
        """
        required_keys = ['url', 'param', 'result_selector', 'title_selector', 
                         'link_selector', 'snippet_selector']
        
        if not all(key in config for key in required_keys):
            raise ValueError("配置必须包含所有必需的键")
        
        self.search_engines[name] = config
    
    def set_proxy(self, proxy):
        """设置代理服务器"""
        self.session.proxies = {
            'http': proxy,
            'https': proxy
        }
        

class PageCrawler:
    pass


if __name__ == "__main__":
    crawler = SearchEngineCrawler(delay=1.5)
    try:
        results = crawler.search("Python编程教程", engine="bing", num_results=5, lang="zh")
        
        print(f"找到 {len(results)} 条结果:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   链接: {result['link']}")
            print(f"   摘要: {result['snippet'][:100]}...")
            
    except Exception as e:
        print(f"搜索出错: {e}")
    