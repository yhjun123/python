import os
import re
import json
import pandas as pd
from typing import Dict, Any, Union

class TextReplacer:
    """
    数据清洗模块：支持关键字/正则表达式文本替换功能
    提供批量处理、区分大小写选项、正则表达式匹配模式，以及替换前后差异对比和结果统计。
    """

    def __init__(self, target: str, replacement: str, case_sensitive: bool = False, use_regex: bool = False):
        """
        初始化文本替换器
        
        :param target: 目标关键字或正则表达式模式
        :param replacement: 替换后的关键字
        :param case_sensitive: 是否区分大小写 (默认 False)
        :param use_regex: 是否将目标关键字视为正则表达式 (默认 False)
        """
        if not target:
            raise ValueError("目标关键字(target)不能为空")

        self.target = target
        self.replacement = replacement
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex

        # 编译正则表达式以提高匹配速度
        flags = 0 if self.case_sensitive else re.IGNORECASE
        pattern_str = self.target if self.use_regex else re.escape(self.target)
        self.pattern = re.compile(pattern_str, flags)

    def _replace_text(self, text: Any) -> tuple:
        """
        处理单条文本，返回 (新文本, 替换次数)
        如果输入不是字符串，或者为空值，则直接返回原值和 0 次替换
        """
        if pd.isna(text) or text is None:
            return text, 0
        if not isinstance(text, str):
            return text, 0

        new_text, count = self.pattern.subn(self.replacement, text)
        return new_text, count

    def process_txt(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """按行处理 TXT 文件，支持大文件流式读取"""
        stats = {"total_rows": 0, "replacements": 0, "diff_samples": []}
        
        with open(input_path, 'r', encoding='utf-8') as fin, \
             open(output_path, 'w', encoding='utf-8') as fout:
            for line in fin:
                stats["total_rows"] += 1
                new_line, count = self._replace_text(line)
                
                if count > 0:
                    stats["replacements"] += count
                    # 保留前10个差异对比示例
                    if len(stats["diff_samples"]) < 10:
                        stats["diff_samples"].append({
                            "line": stats["total_rows"],
                            "before": line.strip(),
                            "after": new_line.strip()
                        })
                fout.write(new_line)
        return stats

    def process_csv(self, input_path: str, output_path: str, chunksize: int = 50000) -> Dict[str, Any]:
        """
        分块处理 CSV 文件，防止内存溢出。
        通过 pandas chunksize 分批读取和写入。
        """
        stats = {"total_rows": 0, "replacements": 0, "diff_samples": []}
        first_chunk = True

        for chunk in pd.read_csv(input_path, chunksize=chunksize, dtype=str):
            stats["total_rows"] += len(chunk)
            
            # 找到可能包含匹配项的字符串列进行处理，提高性能
            for col in chunk.columns:
                if pd.api.types.is_string_dtype(chunk[col]) or chunk[col].dtype == object:
                    # 使用 pandas str.contains 快速过滤出包含匹配项的行
                    # na=False 忽略 NaN 避免报错
                    mask = chunk[col].str.contains(self.pattern, na=False)
                    if mask.any():
                        matching_indices = chunk[mask].index
                        for idx in matching_indices:
                            val = chunk.at[idx, col]
                            new_val, count = self._replace_text(val)
                            
                            chunk.at[idx, col] = new_val
                            stats["replacements"] += count
                            
                            if len(stats["diff_samples"]) < 10:
                                stats["diff_samples"].append({
                                    "row_index": idx,
                                    "column": col,
                                    "before": str(val),
                                    "after": str(new_val)
                                })
            
            # 分块写入 CSV
            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            chunk.to_csv(output_path, mode=mode, header=header, index=False, encoding='utf-8')
            first_chunk = False

        return stats

    def process_json(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        处理 JSON 文件。尝试普通数组格式；如果文件过大，尝试 JSON Lines 格式。
        """
        stats = {"total_rows": 0, "replacements": 0, "diff_samples": []}
        
        # 首先尝试作为普通 JSON 数组读取
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("不支持的 JSON 格式，目前仅支持对象数组(List[Dict])。")

            stats["total_rows"] = len(data)
            new_data = []
            
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    new_data.append(item)
                    continue
                    
                new_item = {}
                for k, v in item.items():
                    new_v, count = self._replace_text(v)
                    new_item[k] = new_v
                    if count > 0:
                        stats["replacements"] += count
                        if len(stats["diff_samples"]) < 10:
                            stats["diff_samples"].append({
                                "row_index": idx,
                                "key": k,
                                "before": str(v),
                                "after": str(new_v)
                            })
                new_data.append(new_item)
                
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
                
        except json.JSONDecodeError:
            # 如果普通 JSON 解析失败，假设是 JSON Lines 并流式处理
            with open(input_path, 'r', encoding='utf-8') as fin, \
                 open(output_path, 'w', encoding='utf-8') as fout:
                for line in fin:
                    stats["total_rows"] += 1
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        fout.write(line + '\n')
                        continue

                    if not isinstance(item, dict):
                        fout.write(line + '\n')
                        continue

                    new_item = {}
                    for k, v in item.items():
                        new_v, count = self._replace_text(v)
                        new_item[k] = new_v
                        if count > 0:
                            stats["replacements"] += count
                            if len(stats["diff_samples"]) < 10:
                                stats["diff_samples"].append({
                                    "line": stats["total_rows"],
                                    "key": k,
                                    "before": str(v),
                                    "after": str(new_v)
                                })
                    fout.write(json.dumps(new_item, ensure_ascii=False) + '\n')

        return stats

    def process_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        入口方法：根据文件扩展名自动路由到相应的处理函数
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"找不到输入文件: {input_path}")
            
        ext = os.path.splitext(input_path)[1].lower()
        if ext == '.csv':
            return self.process_csv(input_path, output_path)
        elif ext in ['.json', '.jsonl']:
            return self.process_json(input_path, output_path)
        elif ext == '.txt':
            return self.process_txt(input_path, output_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}，当前仅支持 .csv, .json, .jsonl, .txt")

