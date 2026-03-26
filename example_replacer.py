import os
import json
import pandas as pd
from text_replacer import TextReplacer

def create_sample_files():
    """生成用于测试的样例文件"""
    print("正在生成测试样例文件...")
    
    # 1. 创建示例 CSV
    csv_data = pd.DataFrame({
        "id": [1, 2, 3],
        "content": ["这是一个关于 Apple 的介绍。", "I like APPLE very much.", "apple is a fruit."],
        "date": ["2023-01-01", "2023-02-01", "2023-03-01"]
    })
    csv_data.to_csv("sample.csv", index=False)

    # 2. 创建示例 JSON
    json_data = [
        {"id": 1, "text": "Contact us at 123-456-7890."},
        {"id": 2, "text": "My phone is 987-654-3210 please call."},
        {"id": 3, "text": "No phone number here."}
    ]
    with open("sample.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 3. 创建示例 TXT
    txt_data = "Hello World!\nHELLO universe.\nhello everyone."
    with open("sample.txt", "w", encoding="utf-8") as f:
        f.write(txt_data)

def test_csv_replacement():
    """测试 CSV 文件的普通关键字替换 (不区分大小写)"""
    print("\n--- 测试 1: CSV 关键字替换 (忽略大小写) ---")
    replacer = TextReplacer(target="apple", replacement="[苹果]", case_sensitive=False)
    
    stats = replacer.process_file("sample.csv", "cleaned_sample.csv")
    print(f"处理完成！总行数: {stats['total_rows']}, 替换总次数: {stats['replacements']}")
    print("差异示例 (最多展示10条):")
    for diff in stats["diff_samples"]:
        print(f"  行索引 {diff['row_index']}, 列 '{diff['column']}':")
        print(f"    前: {diff['before']}")
        print(f"    后: {diff['after']}")

def test_json_regex():
    """测试 JSON 文件的正则表达式替换 (匹配电话号码)"""
    print("\n--- 测试 2: JSON 正则表达式替换 (脱敏电话号码) ---")
    # 正则表达式匹配形如 123-456-7890 的电话号码
    phone_regex = r"\d{3}-\d{3}-\d{4}"
    replacer = TextReplacer(target=phone_regex, replacement="***-***-****", use_regex=True)
    
    stats = replacer.process_file("sample.json", "cleaned_sample.json")
    print(f"处理完成！总行数: {stats['total_rows']}, 替换总次数: {stats['replacements']}")
    print("差异示例:")
    for diff in stats["diff_samples"]:
        print(f"  索引 {diff['row_index']}, 键 '{diff['key']}':")
        print(f"    前: {diff['before']}")
        print(f"    后: {diff['after']}")

def test_txt_case_sensitive():
    """测试 TXT 文件的区分大小写替换"""
    print("\n--- 测试 3: TXT 关键字替换 (区分大小写) ---")
    # 只替换完全大写的 HELLO
    replacer = TextReplacer(target="HELLO", replacement="[你好]", case_sensitive=True)
    
    stats = replacer.process_file("sample.txt", "cleaned_sample.txt")
    print(f"处理完成！总行数: {stats['total_rows']}, 替换总次数: {stats['replacements']}")
    print("差异示例:")
    for diff in stats["diff_samples"]:
        print(f"  第 {diff['line']} 行:")
        print(f"    前: {diff['before']}")
        print(f"    后: {diff['after']}")

if __name__ == "__main__":
    # 准备测试数据
    create_sample_files()
    
    # 运行测试示例
    test_csv_replacement()
    test_json_regex()
    test_txt_case_sensitive()
    
    print("\n测试完成。生成的清洗文件为: cleaned_sample.csv, cleaned_sample.json, cleaned_sample.txt")
