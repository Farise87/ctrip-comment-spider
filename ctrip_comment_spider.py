# -*- coding: utf-8 -*-
"""
携程景点评论爬虫
功能：爬取携程景点网页的全部用户评论数据
参考：https://blog.csdn.net/weixin_73817187/article/details/157257605

使用方法：
    python ctrip_comment_spider.py                    # 使用默认URL
    python ctrip_comment_spider.py --url https://you.ctrip.com/sight/longnan2424/4383341.html
    python ctrip_comment_spider.py --poi_id 49958175  # 直接指定poi_id（跳过页面解析）
"""

import requests
import pandas as pd
import time
import random
import logging
import os
import re
import argparse
import json
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spider.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CtripCommentSpider:
    """携程景点评论爬虫类"""
    
    def __init__(self, poi_id: str, output_file: str = None):
        """
        初始化爬虫
        
        Args:
            poi_id: 景点POI ID，从景点页面HTML中获取
            output_file: 输出CSV文件路径，默认为 comments_{poi_id}_{timestamp}.csv
        """
        self.poi_id = str(poi_id)
        self.base_url = "https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList"
        self.output_file = output_file or f"comments_{self.poi_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.comments_data: List[Dict] = []
        self.total_count_from_api = 0
        self.session = requests.Session()
        self._setup_headers()
        
    def _setup_headers(self):
        """设置请求头，模拟浏览器访问"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://you.ctrip.com',
            'Referer': f'https://you.ctrip.com/sight/0/{self.poi_id}.html',
            'Connection': 'keep-alive',
        }
        
    def _build_request_data(self, page: int, page_size: int = 10) -> Dict:
        """
        构建请求数据
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量，默认10
            
        Returns:
            请求体字典
        """
        return {
            'arg': {
                'channelType': 2,
                'collapseType': 0,
                'commentTagId': 0,
                'pageIndex': page,
                'pageSize': page_size,
                'poiId': int(self.poi_id),
                'sourceType': 3,
                'sortType': 1,
                'starType': 0,
            },
            'head': {
                'cid': '09031025312449459187',
                'ctok': '',
                'cver': '1.0',
                'lang': '01',
                'sid': '8888',
                'syscode': '09',
                'auth': '',
                'xsid': '',
                'extension': [],
            },
        }
    
    def _parse_comment(self, item: Dict) -> Optional[Dict]:
        """
        解析单条评论数据
        
        Args:
            item: API返回的单条评论数据
            
        Returns:
            解析后的评论字典，解析失败返回None
        """
        try:
            comment = {}
            
            try:
                user_info = item.get("userInfo", {})
                comment['用户名'] = user_info.get("userNick", "匿名") if user_info else "匿名"
            except Exception:
                comment['用户名'] = "匿名"
            
            try:
                publish_tag = item.get("publishTypeTag", "")
                comment['评论时间'] = publish_tag.split(' ')[0] if publish_tag else ""
            except Exception:
                comment['评论时间'] = ""
            
            comment['评论内容'] = item.get("content", "")
            
            comment['IP属地'] = item.get("ipLocatedName", "")
            
            comment['评分'] = item.get("score", "")
            
            recommend_items = item.get("recommendItems", [])
            comment['推荐标签'] = ",".join(recommend_items) if recommend_items else ""
            
            comment['点赞数'] = item.get("usefulCount", 0)
            
            comment['评论ID'] = item.get("commentId", "")
            
            comment['图片数量'] = len(item.get("images", [])) if item.get("images") else 0
            
            comment['回复数'] = item.get("replyCount", 0)
            
            try:
                user_info = item.get("userInfo", {})
                comment['用户身份'] = user_info.get("identitiesName", "") if user_info else ""
            except Exception:
                comment['用户身份'] = ""
            
            return comment
            
        except Exception as e:
            logger.warning(f"解析评论数据失败: {e}")
            return None
    
    def fetch_comments(self, max_pages: int = None, delay_range: tuple = (1.5, 3)) -> int:
        """
        获取所有评论数据
        
        Args:
            max_pages: 最大爬取页数，None表示爬取全部
            delay_range: 请求间隔时间范围(秒)，默认1.5-3秒随机
            
        Returns:
            成功获取的评论数量
        """
        logger.info(f"开始爬取景点POI ID: {self.poi_id} 的评论数据...")
        
        page = 1
        total_count = 0
        consecutive_empty = 0
        max_consecutive_empty = 3
        
        while True:
            if max_pages and page > max_pages:
                logger.info(f"已达到最大页数限制: {max_pages}")
                break
            
            try:
                json_data = self._build_request_data(page)
                
                logger.info(f"正在爬取第 {page} 页...")
                
                response = self.session.post(
                    self.base_url,
                    headers=self.headers,
                    json=json_data,
                    timeout=30
                )
                
                if response.status_code != 200:
                    logger.error(f"请求失败，状态码: {response.status_code}")
                    consecutive_empty += 1
                    if consecutive_empty >= max_consecutive_empty:
                        logger.error("连续多次请求失败，停止爬取")
                        break
                    page += 1
                    time.sleep(3)
                    continue
                
                result = response.json()
                
                if 'result' not in result:
                    logger.warning(f"响应数据格式异常")
                    logger.debug(f"响应内容: {result}")
                    break
                
                result_data = result.get('result', {})
                items = result_data.get('items', [])
                self.total_count_from_api = result_data.get('totalCount', 0)
                
                if page == 1:
                    logger.info(f"API返回总评论数: {self.total_count_from_api}")
                    if self.total_count_from_api == 0:
                        logger.warning("该景点暂无评论数据！")
                        return 0
                
                if not items:
                    logger.info(f"第 {page} 页无数据，爬取完成")
                    break
                
                page_count = 0
                for item in items:
                    comment = self._parse_comment(item)
                    if comment:
                        self.comments_data.append(comment)
                        page_count += 1
                        total_count += 1
                
                logger.info(f"第 {page} 页获取 {page_count} 条评论，累计 {total_count} 条")
                
                consecutive_empty = 0
                page += 1
                
                delay = random.uniform(delay_range[0], delay_range[1])
                logger.debug(f"等待 {delay:.2f} 秒...")
                time.sleep(delay)
                
            except requests.exceptions.Timeout:
                logger.error(f"第 {page} 页请求超时，稍后重试...")
                time.sleep(5)
                continue
                
            except requests.exceptions.ConnectionError as e:
                logger.error(f"网络连接错误: {e}")
                logger.info("等待10秒后重试...")
                time.sleep(10)
                continue
                
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {e}")
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    logger.error("连续多次请求异常，停止爬取")
                    break
                time.sleep(5)
                continue
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                logger.debug(f"响应内容: {response.text[:500]}")
                break
                
            except Exception as e:
                logger.error(f"未知错误: {e}")
                break
        
        logger.info(f"爬取完成，共获取 {total_count} 条评论")
        return total_count
    
    def save_to_csv(self) -> str:
        """
        将评论数据保存为CSV文件
        
        Returns:
            保存的文件路径
        """
        if not self.comments_data:
            logger.warning("没有数据可保存")
            return ""
        
        try:
            df = pd.DataFrame(self.comments_data)
            
            columns_order = [
                '用户名', '评论时间', '评分', '评论内容', 
                'IP属地', '推荐标签', '点赞数', '回复数', 
                '图片数量', '用户身份', '评论ID'
            ]
            
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]
            
            df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
            
            logger.info(f"数据已保存到: {os.path.abspath(self.output_file)}")
            logger.info(f"共保存 {len(df)} 条评论")
            
            return self.output_file
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return ""
    
    def get_statistics(self) -> Dict:
        """
        获取评论统计信息
        
        Returns:
            统计信息字典
        """
        if not self.comments_data:
            return {}
        
        df = pd.DataFrame(self.comments_data)
        
        stats = {
            '总评论数': len(df),
            'API显示总数': self.total_count_from_api,
        }
        
        if '评分' in df.columns:
            scores = pd.to_numeric(df['评分'], errors='coerce')
            stats['平均评分'] = scores.mean()
            stats['最高评分'] = scores.max()
            stats['最低评分'] = scores.min()
        
        if '点赞数' in df.columns:
            stats['总点赞数'] = df['点赞数'].sum()
            stats['平均点赞数'] = df['点赞数'].mean()
        
        return stats


def fetch_poi_id_from_page(page_url: str) -> Optional[str]:
    """
    从携程景点页面HTML中提取真实的poiId
    
    根据参考文档说明：需要访问景点页面，从页面HTML中提取poiId字段
    URL中的数字只是页面ID，不是评论API需要的poiId
    
    Args:
        page_url: 携程景点页面URL
        
    Returns:
        poiId，提取失败返回None
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        logger.info(f"正在从页面获取poiId: {page_url}")
        response = requests.get(page_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"页面请求失败，状态码: {response.status_code}")
            return None
        
        html = response.text
        
        pattern = r'"poiId"\s*:\s*(\d+)'
        match = re.search(pattern, html)
        
        if match:
            poi_id = match.group(1)
            logger.info(f"成功从页面提取poiId: {poi_id}")
            return poi_id
        else:
            logger.error("未能从页面中找到poiId")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"页面请求异常: {e}")
        return None
    except Exception as e:
        logger.error(f"解析页面失败: {e}")
        return None


def extract_page_id_from_url(url: str) -> Optional[str]:
    """
    从携程景点URL中提取页面ID
    
    Args:
        url: 携程景点URL，如 https://you.ctrip.com/sight/longnan2424/4383341.html
        
    Returns:
        页面ID，提取失败返回None
    """
    pattern = r'/(\d+)\.html'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='携程景点评论爬虫')
    parser.add_argument('--url', type=str, 
                        default='https://you.ctrip.com/sight/shanghai2/25506.html',
                        help='携程景点页面URL，程序将自动从中提取poiId')
    parser.add_argument('--poi_id', type=str, default=None,
                        help='直接指定poiId（跳过页面解析，用于已知poiId的情况）')
    parser.add_argument('--max_pages', type=int, default=None,
                        help='最大爬取页数，不指定则爬取全部')
    parser.add_argument('--output', type=str, default=None,
                        help='输出CSV文件路径')
    parser.add_argument('--min_delay', type=float, default=1.5,
                        help='最小请求间隔(秒)，默认1.5')
    parser.add_argument('--max_delay', type=float, default=3.0,
                        help='最大请求间隔(秒)，默认3.0')
    
    args = parser.parse_args()
    
    if args.poi_id:
        poi_id = args.poi_id
        logger.info(f"使用指定的poiId: {poi_id}")
    else:
        poi_id = fetch_poi_id_from_page(args.url)
        if not poi_id:
            logger.error("无法获取poiId，请检查URL或使用 --poi_id 参数直接指定")
            return
    
    logger.info("=" * 60)
    logger.info("携程景点评论爬虫启动")
    logger.info(f"景点页面URL: {args.url}")
    logger.info(f"POI ID: {poi_id}")
    logger.info(f"请求间隔: {args.min_delay}-{args.max_delay}秒")
    if args.max_pages:
        logger.info(f"最大页数: {args.max_pages}")
    logger.info("=" * 60)
    
    spider = CtripCommentSpider(poi_id=poi_id, output_file=args.output)
    
    total = spider.fetch_comments(
        max_pages=args.max_pages, 
        delay_range=(args.min_delay, args.max_delay)
    )
    
    if total > 0:
        output_file = spider.save_to_csv()
        
        stats = spider.get_statistics()
        if stats:
            logger.info("=" * 60)
            logger.info("评论统计信息:")
            for key, value in stats.items():
                if isinstance(value, float):
                    logger.info(f"  {key}: {value:.2f}")
                else:
                    logger.info(f"  {key}: {value}")
            logger.info("=" * 60)
    else:
        logger.warning("=" * 60)
        logger.warning("未获取到任何评论数据")
        logger.warning("可能原因：")
        logger.warning("  1. 该景点暂无评论")
        logger.warning("  2. poiId不正确")
        logger.warning("  3. 网络连接问题")
        logger.warning("=" * 60)


if __name__ == "__main__":
    main()
