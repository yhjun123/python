import streamlit as st
import pandas as pd
import io
from text_replacer import TextReplacer

# 设置页面标题
st.set_page_config(page_title="自动化数据清洗工具", layout="wide")
st.title("🧼 自动化数据清洗工作台")
st.write("上传你的数据集，一键完成去重、填补缺失值、格式转换和文本脱敏。")

# 1. 文件上传
uploaded_file = st.file_uploader("选择一个 CSV 或 Excel 文件", type=["csv", "xlsx"])

if uploaded_file:
    # 根据后缀名读取数据
    if uploaded_file.name.endswith('.csv'):
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='gbk')
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📊 原始数据预览")
    st.dataframe(df.head(10))

    # 侧边栏：清洗选项
    st.sidebar.header("清洗设置")
    
    # 选项：去重
    do_drop_duplicates = st.sidebar.checkbox("去除重复行", value=True)
    
    # 选项：填补缺失值
    fill_missing = st.sidebar.selectbox(
        "如何处理缺失值？",
        ["不处理", "用 0 填充", "用平均值填充(仅数值列)", "用众数填充"]
    )

    # 选项：日期转换
    date_column = st.sidebar.selectbox("选择需要转换成日期格式的列 (可选)", ["无"] + list(df.columns))

    # 选项：文本替换与脱敏
    st.sidebar.markdown("---")
    st.sidebar.subheader("文本替换与脱敏")
    enable_replace = st.sidebar.checkbox("开启文本替换/脱敏", value=False)
    
    if enable_replace:
        target_text = st.sidebar.text_input("目标关键字或正则表达式", value=r"\d{17}[\dXx]")
        replace_text = st.sidebar.text_input("替换为", value="******************")
        use_regex = st.sidebar.checkbox("使用正则表达式", value=True)
        case_sensitive = st.sidebar.checkbox("区分大小写", value=False)
    else:
        target_text = ""
        replace_text = ""
        use_regex = False
        case_sensitive = False

    # --- 执行清洗逻辑 ---
    clean_df = df.copy()

    if do_drop_duplicates:
        before_count = len(clean_df)
        clean_df = clean_df.drop_duplicates()
        st.sidebar.info(f"已删除 {before_count - len(clean_df)} 条重复记录")

    if fill_missing == "用 0 填充":
        clean_df = clean_df.fillna(0)
    elif fill_missing == "用平均值填充(仅数值列)":
        num_cols = clean_df.select_dtypes(include=['number']).columns
        clean_df[num_cols] = clean_df[num_cols].fillna(clean_df[num_cols].mean())
    elif fill_missing == "用众数填充":
        clean_df = clean_df.fillna(clean_df.mode().iloc[0])

    if date_column != "无":
        try:
            clean_df[date_column] = pd.to_datetime(clean_df[date_column])
            st.sidebar.success(f"列 '{date_column}' 已转为日期格式")
        except Exception as e:
            st.sidebar.error(f"日期转换失败: {e}")

    # 执行文本替换逻辑
    if enable_replace and target_text:
        try:
            replacer = TextReplacer(
                target=target_text,
                replacement=replace_text,
                case_sensitive=case_sensitive,
                use_regex=use_regex
            )
            
            replace_count = 0
            diffs = []
            
            for col in clean_df.columns:
                if pd.api.types.is_string_dtype(clean_df[col]) or clean_df[col].dtype == object:
                    # 使用 apply 进行替换
                    def replace_val(val):
                        if pd.isna(val) or not isinstance(val, str):
                            return val, 0
                        new_val, count = replacer.pattern.subn(replacer.replacement, val)
                        return new_val, count
                    
                    results = clean_df[col].apply(replace_val)
                    clean_df[col] = results.apply(lambda x: x[0])
                    col_counts = results.apply(lambda x: x[1])
                    replace_count += col_counts.sum()
                    
            if replace_count > 0:
                st.sidebar.success(f"成功替换了 {replace_count} 处文本")
            else:
                st.sidebar.info("未找到匹配的文本")
        except Exception as e:
            st.sidebar.error(f"文本替换出错: {e}")

    # --- 展示清洗后的结果 ---
    st.subheader("✨ 清洗后的数据预览")
    st.dataframe(clean_df.head(10))

    # 数据统计对比
    col1, col2 = st.columns(2)
    with col1:
        st.write("原始数据行列数:", df.shape)
    with col2:
        st.write("清洗后行列数:", clean_df.shape)

    # --- 下载按钮 ---
    # 将 DataFrame 转为 CSV 字节流，使用 utf-8-sig 编码以防止 Excel 打开时中文乱码
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8-sig')

    csv_data = convert_df(clean_df)
    
    st.download_button(
        label="📥 下载清洗后的 CSV 文件",
        data=csv_data,
        file_name='cleaned_data.csv',
        mime='text/csv',
    )
else:
    st.info("💡 请先在上方上传文件以开始清洗。")