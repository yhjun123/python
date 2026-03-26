from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

app = FastAPI()

# 允许你的 Vue 项目访问 (跨域配置)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 开发环境允许所有源，生产环境建议指定端口
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/predict")
async def predict():
    # 模拟一个 AI 模型的计算过程
    # 生成 5 个随机的预测概率
    raw_data = np.random.rand(5).tolist() 
    
    return {
        "status": "success",
        "model": "SimplePerceptron_v1",
        "predictions": raw_data
    }

# 启动命令提示：在终端运行 uvicorn server:app --reload
import requests
import aiohttp
import asyncio
import random
from typing import List, Dict, Any
from datetime import datetime

# UA 池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]

def format_play_count(count: int) -> str:
    """将播放量格式化为百、千、万形式"""
    if count < 100:
        return str(count)
    elif count < 1000:
        return f"{count/100:.1f}百".rstrip('0').rstrip('.') if count % 100 != 0 else f"{count//100}百"
    elif count < 10000:
        return f"{count/1000:.1f}千".rstrip('0').rstrip('.') if count % 1000 != 0 else f"{count//1000}千"
    else:
        return f"{count/10000:.1f}万".rstrip('0').rstrip('.') if count % 10000 != 0 else f"{count//10000}万"

async def bili_rank_search_videos(keyword: str, max_retries: int = 3, limit: int = 100) -> List[Dict[str, Any]]:
    """
    异步调用B站搜索接口，带重试、UA池和随机延时。
    通过循环获取多页数据，直到达到 limit 限制。
    """
    url = "https://api.bilibili.com/x/web-interface/wbi/search/type"
    
    all_results = []
    page = 1
    
    while len(all_results) < limit:
        params = {
            "search_type": "video",
            "keyword": keyword,
            "page": page,
            "order": "click"
        }
        
        for attempt in range(max_retries):
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://search.bilibili.com/"
            }
            
            try:
                if attempt > 0:
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        response.raise_for_status()
                        data = await response.json()
                        
                        if data.get("code") != 0:
                            raise ValueError(f"API Error: {data.get('message')}")
                            
                        items = data.get("data", {}).get("result", [])
                        if not items: # 如果某一页没有数据了，说明已经搜索完毕
                            break
                            
                        for item in items:
                            title = item.get("title", "").replace('<em class="keyword">', '').replace('</em>', '')
                            play_count = item.get("play", 0)
                            # B站返回的 pubdate 是时间戳
                            pubdate = item.get("pubdate", 0)
                            date_str = datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d') if pubdate else "未知"
                            
                            all_results.append({
                                "title": title,
                                "author": item.get("author", ""),
                                "play_count_raw": play_count,
                                "play_count": format_play_count(play_count),
                                "date": date_str,
                                "bvid": item.get("bvid", ""),
                                "url": item.get("arcurl", "")
                            })
                            if len(all_results) >= limit:
                                break
                        break # 当前页成功获取，跳出重试循环
                        
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
                if attempt == max_retries - 1:
                    print(f"第 {page} 页请求失败(重试{max_retries}次): {str(e)}")
                    break # 跳出当前页的重试，但不影响整体返回已收集的数据
                continue
                
        if len(items) == 0: # 如果该页本来就没有数据，或者重试失败被 break 出循环但 items 为空(或者未定义，取决于异常发生位置)
            break
            
        page += 1
        await asyncio.sleep(random.uniform(0.5, 1.5)) # 分页请求之间增加延时，防止被反爬
        
    all_results.sort(key=lambda x: x["play_count_raw"], reverse=True)
    return all_results[:limit]

@app.get("/api/bilibili/search")
async def bili_rank_search_api(keyword: str, limit: int = 100):
    """
    提供给前端的搜索接口
    """
    if not keyword.strip():
        return {
            "status": "error",
            "message": "关键词不能为空",
            "data": []
        }
        
    try:
        results = await bili_rank_search_videos(keyword, limit=limit)
        return {
            "status": "success",
            "message": f"成功获取搜索结果，共 {len(results)} 条",
            "data": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@app.get("/api/bilibili/rank")
async def get_bilibili_rank_api(limit: int = 100):
    url = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        video_list = data.get('data', {}).get('list', [])
        
        result = []
        # 使用动态传入的 limit 参数限制返回数量
        for i, video in enumerate(video_list[:limit], 1):
            play_count = video.get('stat', {}).get('view', 0)
            pubdate = video.get("pubdate", 0)
            date_str = datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d') if pubdate else "未知"
            
            result.append({
                "rank": i,
                "title": video.get('title'),
                "author": video.get('owner', {}).get('name'),
                "play_count_raw": play_count,
                "play_count": format_play_count(play_count),
                "date": date_str
            })
            
        return {
            "status": "success",
            "message": f"获取 B 站排行榜前 {limit} 名成功",
            "data": result
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"爬取失败: {str(e)}",
            "data": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)