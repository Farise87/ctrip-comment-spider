# 携程景点评论爬虫

一个用于爬取携程景点用户评论的Python爬虫工具，支持自动获取景点POI ID并批量下载评论数据。

## 功能特性

- **自动POI ID获取** - 自动从景点页面HTML中提取真实的poiId，无需手动查找
- **全量评论爬取** - 支持爬取景点的全部用户评论数据
- **多字段提取** - 提取用户名、评论时间、评分、评论内容、IP属地、点赞数等完整信息
- **CSV数据导出** - 将评论数据保存为结构化的CSV文件，便于后续分析
- **请求间隔控制** - 可配置的随机请求间隔，避免对目标服务器造成压力
- **完善异常处理** - 网络超时、连接错误等异常的自动重试机制
- **命令行接口** - 支持多种命令行参数，灵活配置爬取任务

## 环境要求

- Python 3.7+
- Windows / macOS / Linux

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/Farise87/ctrip-comment-spider.git
cd ctrip-comment-spider
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
# 使用默认URL爬取（上海市动物园）
python ctrip_comment_spider.py

# 指定景点页面URL
python ctrip_comment_spider.py --url https://you.ctrip.com/sight/shanghai2/25506.html

# 直接指定poiId（跳过页面解析）
python ctrip_comment_spider.py --poi_id 81728
```

### 高级选项

```bash
# 限制最大爬取页数
python ctrip_comment_spider.py --max_pages 10

# 自定义请求间隔（秒）
python ctrip_comment_spider.py --min_delay 2 --max_delay 5

# 指定输出文件路径
python ctrip_comment_spider.py --output my_comments.csv

# 组合使用多个参数
python ctrip_comment_spider.py \
    --url https://you.ctrip.com/sight/shanghai2/25506.html \
    --max_pages 20 \
    --min_delay 2 \
    --max_delay 4 \
    --output shanghai_zoo_comments.csv
```

### 命令行参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--url` | str | 上海市动物园URL | 携程景点页面URL，程序自动提取poiId |
| `--poi_id` | str | None | 直接指定poiId，跳过页面解析 |
| `--max_pages` | int | None | 最大爬取页数，不指定则爬取全部 |
| `--output` | str | 自动生成 | 输出CSV文件路径 |
| `--min_delay` | float | 1.5 | 最小请求间隔（秒） |
| `--max_delay` | float | 3.0 | 最大请求间隔（秒） |

## 输出数据

### CSV文件字段

| 字段名 | 说明 |
|--------|------|
| 用户名 | 评论用户的昵称 |
| 评论时间 | 评论发布的日期 |
| 评分 | 用户评分（1-5分） |
| 评论内容 | 评论的完整文本内容 |
| IP属地 | 评论者的IP地理位置 |
| 推荐标签 | 用户选择的推荐标签 |
| 点赞数 | 评论获得的点赞数量 |
| 回复数 | 评论的回复数量 |
| 图片数量 | 评论包含的图片数量 |
| 用户身份 | 用户身份标识（如签约旅行家） |
| 评论ID | 评论的唯一标识符 |

### 输出示例

```
用户名,评论时间,评分,评论内容,IP属地,推荐标签,点赞数,回复数,图片数量,用户身份,评论ID
七牛行路,2021-12-14,4.0,来丽江，肯定听说过"三朵神"...,,1,0,4,签约旅行家,168737323
```

## 技术原理

### POI ID获取

携程景点URL中的数字（如 `4383341`）只是页面ID，评论API需要使用真实的 `poiId`。本程序通过以下步骤获取：

1. 访问景点页面
2. 解析页面HTML
3. 使用正则表达式提取 `"poiId": xxx` 字段
4. 使用提取的poiId调用评论API

### API接口

评论数据通过携程移动端API获取：

```
POST https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList
```

## 项目结构

```
ctrip-comment-spider/
├── ctrip_comment_spider.py    # 主程序
├── requirements.txt           # 依赖列表
├── README.md                  # 项目说明
├── spider.log                 # 运行日志（自动生成）
└── comments_*.csv             # 爬取结果（自动生成）
```

## 注意事项

1. **请求频率** - 默认请求间隔为1.5-3秒，请勿设置过小以免对服务器造成压力
2. **数据限制** - 网页版API最多可获取约3000条评论
3. **网络环境** - 确保网络连接稳定，程序会自动重试失败的请求
4. **合法使用** - 请遵守网站服务条款，仅用于学习研究目的

## 常见问题

### Q: 为什么显示"该景点暂无评论数据"？

A: 可能原因：
- 该景点确实没有用户评论
- 网络连接问题导致无法获取页面
- 景点URL格式不正确

### Q: 如何获取其他景点的poiId？

A: 程序会自动从URL中提取，只需提供正确的景点页面URL即可。

### Q: 爬取速度可以更快吗？

A: 可以通过 `--min_delay` 和 `--max_delay` 参数调整，但建议保持合理的请求间隔。

## 许可证

本项目仅供学习交流使用，请勿用于商业用途。使用本程序爬取数据时，请遵守相关法律法规和网站服务条款。

## 参考

- [携程景点评论爬虫教程](https://blog.csdn.net/weixin_73817187/article/details/157257605)
