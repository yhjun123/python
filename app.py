import streamlit as st  # 导入 Streamlit 库，用于构建 Web 应用
import requests  # 导入 requests 库，用于发送 HTTP 请求
import pandas as pd  # 导入 pandas 库，用于数据处理和分析
import io  # 导入 io 库，用于处理输入输出流

# 设置页面配置
st.set_page_config(  # 调用 set_page_config 方法设置页面属性
    page_title="B站排行榜数据可视化",  # 设置浏览器标签页标题为“B站排行榜数据可视化”
    page_icon="📺",  # 设置浏览器标签页图标为小电视 emoji
    layout="wide"  # 设置页面布局模式为宽屏，充分利用屏幕宽度
)  # 结束 set_page_config 方法调用

# 页面标题
st.title("📺 B站全站排行榜可视化")  # 在页面主区域显示带 emoji 的主标题
st.markdown("通过请求后端 FastAPI 接口获取数据，并进行动态展示。")  # 显示一段 Markdown 格式的说明文字

# 侧边栏：选择功能模块
st.sidebar.header("功能选择")  # 在左侧侧边栏添加一个“功能选择”的头部标题
module_choice = st.sidebar.radio("选择查看的数据", ["🚀 全站排行榜", "🔍 关键词搜索"])  # 在侧边栏创建一个单选框，用于在两个模块间切换

if module_choice == "🚀 全站排行榜":  # 如果用户选择了“全站排行榜”模块
    st.sidebar.header("请求参数配置")  # 在侧边栏添加“请求参数配置”的头部标题
    limit = st.sidebar.slider("获取前 N 名数据", min_value=10, max_value=100, value=200, step=10)  # 创建一个滑块，用于选择获取的数据条数（10-100，默认20）

    # 获取数据的按钮
    if st.sidebar.button("获取最新数据"):  # 在侧边栏创建一个按钮，点击后执行下方逻辑
        with st.spinner("正在从接口获取数据..."):  # 显示一个加载动画，提示用户正在请求数据
            try:  # 开始 try 块，捕获可能出现的异常
                # 这里的接口地址应与 FastAPI 运行地址一致
                api_url = f"http://localhost:8000/api/bilibili/rank?limit={limit}"  # 构造后端 API 请求 URL，包含 limit 参数
                response = requests.get(api_url, timeout=10)  # 发送 GET 请求到后端接口，设置超时时间为 10 秒
                
                # 解析 JSON
                if response.status_code == 200:  # 如果 HTTP 响应状态码为 200（成功）
                    res_data = response.json()  # 将响应内容解析为 JSON 字典
                    if res_data.get("status") == "success":  # 如果后端返回的 status 字段值为 success
                        video_data = res_data.get("data", [])  # 获取 data 字段中的视频列表，默认为空列表
                        if video_data:  # 如果视频列表不为空
                            # 转换为 Pandas DataFrame 方便展示与可视化
                            df = pd.DataFrame(video_data)  # 将视频列表数据转换为 Pandas DataFrame 格式
                            
                            # 1. 成功提示卡片
                            st.success(f"成功获取 {len(df)} 条排行榜数据！")  # 在页面顶部显示绿色的成功提示，包含获取的数据条数
                            
                            # 2. 布局：分成两列
                            col1, col2 = st.columns([2, 1])  # 将页面布局划分为左右两列，宽度比例为 2:1
                            
                            with col1:  # 在左侧列（较宽）中执行
                                st.subheader("📊 播放量柱状图 (前10名)")  # 添加子标题，提示下方是柱状图
                                # 提取前10名用于画图
                                top10_df = df.head(10).copy()  # 提取 DataFrame 的前 10 行并复制
                                # 为了图表显示更直观，将标题设为索引
                                top10_df.set_index('title', inplace=True)  # 将视频标题列设置为索引，用作 X 轴标签
                                st.bar_chart(top10_df['play_count_raw'])  # 绘制柱状图，展示原始播放量数据
                                
                            with col2:  # 在右侧列（较窄）中执行
                                st.subheader("💡 播放量折线趋势")  # 添加子标题，提示下方是折线图
                                st.line_chart(df['play_count_raw'])  # 绘制折线图，展示所有获取视频的播放量趋势
                                
                            # 3. 详细数据表格
                            st.subheader("📋 详细排名数据表")  # 添加子标题，提示下方是详细数据表
                            st.dataframe(  # 渲染一个交互式数据表格
                                df,  # 传入包含所有视频数据的 DataFrame
                                column_config={  # 配置表格各列的显示方式
                                    "rank": st.column_config.NumberColumn("排名", format="%d"),  # 将 rank 列配置为数字类型，标题为“排名”，格式为整数
                                    "title": "视频标题",  # 将 title 列标题修改为“视频标题”
                                    "author": "UP主",  # 将 author 列标题修改为“UP主”
                                    "date": "发布日期",  # 将 date 列标题修改为“发布日期”
                                    "play_count": "播放量",  # 将 play_count 列标题修改为“播放量”
                                    "play_count_raw": None # 隐藏原始数据列，不向用户展示纯数字的播放量列
                                },  # 结束列配置字典
                                use_container_width=True,  # 开启宽度自适应，使表格填满容器宽度
                                hide_index=True  # 隐藏 DataFrame 自带的数字索引列
                            )  # 结束 st.dataframe 方法调用
                        else:  # 如果获取到的视频列表为空
                            st.warning("接口返回数据为空！")  # 显示黄色的警告提示框
                    else:  # 如果后端返回的 status 不是 success
                        st.error(f"接口返回错误: {res_data.get('message')}")  # 显示红色的错误提示框，包含后端错误信息
                else:  # 如果 HTTP 请求状态码不是 200
                    st.error(f"请求失败，状态码: {response.status_code}")  # 显示红色的错误提示框，包含 HTTP 状态码
                    
            except requests.exceptions.ConnectionError:  # 捕获请求连接错误（通常是后端服务未启动）
                st.error("无法连接到后端接口！请确保 `server.py` 已经通过 `uvicorn src.python.server:app --reload` 启动在 8000 端口。")  # 显示提示用户启动后端的错误信息
            except Exception as e:  # 捕获其他所有未预料的异常
                st.error(f"发生未知错误: {str(e)}")  # 显示包含具体异常信息的错误提示框

    else:  # 如果用户还没有点击“获取最新数据”按钮
        st.info("👈 请在左侧侧边栏点击【获取最新数据】开始加载！")  # 显示蓝色的信息提示，引导用户操作

elif module_choice == "🔍 关键词搜索":  # 如果用户选择了“关键词搜索”模块
    st.sidebar.header("搜索参数配置")  # 在侧边栏添加“搜索参数配置”的头部标题
    keyword = st.sidebar.text_input("输入关键词", value="Python 爬虫")  # 创建一个文本输入框，默认值为“Python 爬虫”
    
    if st.sidebar.button("开始搜索"):  # 在侧边栏创建一个按钮，点击后执行下方逻辑
        if not keyword.strip():  # 如果输入的关键词为空或只包含空格
            st.sidebar.warning("请输入有效的关键词！")  # 在侧边栏显示警告提示框
        else:  # 如果输入的关键词有效
            with st.spinner(f"正在全网搜索「{keyword}」的视频..."):  # 显示加载动画，包含正在搜索的关键词
                try:  # 开始 try 块，捕获可能出现的异常
                    api_url = f"http://localhost:8000/api/bilibili/search?keyword={keyword}&limit=100"  # 构造后端搜索 API 请求 URL，包含关键词和100条限制参数
                    response = requests.get(api_url, timeout=10)  # 发送 GET 请求到后端接口，设置超时时间为 10 秒
                    
                    if response.status_code == 200:  # 如果 HTTP 响应状态码为 200（成功）
                        res_data = response.json()  # 将响应内容解析为 JSON 字典
                        if res_data.get("status") == "success":  # 如果后端返回的 status 字段值为 success
                            video_data = res_data.get("data", [])  # 获取 data 字段中的视频列表，默认为空列表
                            if video_data:  # 如果视频列表不为空
                                df = pd.DataFrame(video_data)  # 将视频列表数据转换为 Pandas DataFrame 格式
                                # 确保前端展示数据严格按播放量降序排序
                                df = df.sort_values(by="play_count_raw", ascending=False).reset_index(drop=True)  # 根据原始播放量降序排序，并重置索引
                                
                                st.success(f"搜索完成！共找到 {len(df)} 个相关视频。")  # 在页面显示绿色的成功提示，包含找到的视频数量
                                
                                # 布局
                                col1, col2 = st.columns([2, 1])  # 将页面布局划分为左右两列，宽度比例为 2:1
                                
                                with col1:  # 在左侧列中执行
                                    st.subheader("📈 搜索结果播放量排行 (Top 10)")  # 添加子标题，提示下方是柱状图
                                    top10_df = df.head(100).copy()  # 提取 DataFrame 的前 100 行并复制
                                    top10_df.set_index('title', inplace=True)  # 将视频标题列设置为索引
                                    st.bar_chart(top10_df['play_count_raw'])  # 绘制柱状图展示播放量
                                    
                                with col2:  # 在右侧列中执行
                                    st.subheader("💡 播放量分布折线")  # 添加子标题，提示下方是折线图
                                    st.line_chart(df['play_count_raw'])  # 绘制折线图，展示搜索结果的播放量分布
                                    
                                st.subheader("📋 详细搜索结果 (按播放量降序)")  # 添加子标题，提示下方是详细数据表
                                st.dataframe(  # 渲染交互式数据表格
                                    df,  # 传入包含所有搜索结果视频数据的 DataFrame
                                    column_config={  # 配置表格各列的显示方式
                                        "title": "视频标题",  # 将 title 列标题修改为“视频标题”
                                        "author": "UP主",  # 将 author 列标题修改为“UP主”
                                        "date": "发布日期",  # 将 date 列标题修改为“发布日期”
                                        "play_count": "播放量",  # 将 play_count 列标题修改为“播放量”
                                        "play_count_raw": None, # 隐藏原始数据列，不向用户展示纯数字播放量
                                        "bvid": "BV号",  # 将 bvid 列标题修改为“BV号”
                                        "url": st.column_config.LinkColumn("视频链接", display_text="点击观看")  # 将 url 列配置为可点击的链接，显示文字为“点击观看”
                                    },  # 结束列配置字典
                                    use_container_width=True,  # 开启宽度自适应，使表格填满容器宽度
                                    hide_index=True  # 隐藏 DataFrame 自带的数字索引列
                                )  # 结束 st.dataframe 方法调用
                            else:  # 如果获取到的视频列表为空
                                st.warning("未搜索到相关视频或接口受限。")  # 显示黄色的警告提示框
                        else:  # 如果后端返回的 status 不是 success
                            st.error(f"接口返回错误: {res_data.get('message')}")  # 显示红色的错误提示框，包含后端错误信息
                    else:  # 如果 HTTP 请求状态码不是 200
                        st.error(f"请求失败，状态码: {response.status_code}")  # 显示红色的错误提示框，包含 HTTP 状态码
                        
                except requests.exceptions.ConnectionError:  # 捕获请求连接错误
                    st.error("无法连接到后端接口！请确保 `server.py` 已经启动。")  # 显示提示后端未启动的错误信息
                except Exception as e:  # 捕获其他所有未预料的异常
                    st.error(f"发生未知错误: {str(e)}")  # 显示包含具体异常信息的错误提示框
    else:  # 如果用户还没有点击“开始搜索”按钮
        st.info("👈 请在左侧输入关键词并点击【开始搜索】！")  # 显示蓝色的信息提示，引导用户操作

        