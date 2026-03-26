# TextReplacer 文本清洗模块 API 文档

`TextReplacer` 是一个高效、灵活的数据清洗模块，专注于通过关键字或正则表达式在不同格式的文本数据中执行批量替换操作。

支持的文件格式包括：
- `.csv`（自动分块读取，防止大文件内存溢出）
- `.json`（支持标准对象数组）
- `.jsonl`（JSON Lines，流式读取大文件）
- `.txt`（按行流式读取）

---

## 快速开始

```python
from text_replacer import TextReplacer

# 初始化：将所有的 "apple" 替换为 "[苹果]"，不区分大小写
replacer = TextReplacer(target="apple", replacement="[苹果]", case_sensitive=False)

# 执行文件处理
stats = replacer.process_file("input.csv", "output.csv")

# 打印统计和差异信息
print(f"处理行数: {stats['total_rows']}")
print(f"替换次数: {stats['replacements']}")
print(f"前10条差异对比: {stats['diff_samples']}")
```

---

## 核心类：`TextReplacer`

### 1. 初始化方法 `__init__`

```python
def __init__(self, target: str, replacement: str, case_sensitive: bool = False, use_regex: bool = False)
```

**参数列表：**
- `target` (str): 目标关键字或正则表达式模式。**必须提供**。
- `replacement` (str): 替换后的目标字符串。
- `case_sensitive` (bool): 是否区分大小写，默认为 `False`。
- `use_regex` (bool): 是否将 `target` 解析为正则表达式，默认为 `False`。

**异常：**
- `ValueError`: 如果 `target` 关键字为空时抛出。

---

### 2. 文件处理入口 `process_file`

```python
def process_file(self, input_path: str, output_path: str) -> dict
```

**描述：** 
自动根据 `input_path` 的扩展名调用相应的格式处理方法。

**参数：**
- `input_path` (str): 输入文件的绝对路径或相对路径。
- `output_path` (str): 输出清洗后文件的路径。

**返回值 (Dict[str, Any])：** 
返回一个统计字典，包含替换的概览信息和前10条差异对比：
```json
{
  "total_rows": 1000, 
  "replacements": 45, 
  "diff_samples": [
    {
      "row_index": 12,
      "column": "description",
      "before": "I like apple.",
      "after": "I like [苹果]."
    }
  ]
}
```

**异常：**
- `FileNotFoundError`: 输入文件不存在时。
- `ValueError`: 文件扩展名不受支持时。

---

### 3. CSV 专有方法 `process_csv`

```python
def process_csv(self, input_path: str, output_path: str, chunksize: int = 50000) -> dict
```

**描述：** 
采用 Pandas 分块读取模式 (`chunksize`) 来处理超大 CSV 文件。支持对所有的对象/字符串列进行匹配过滤（基于 `str.contains` 优化），跳过无需处理的数据，处理速度极快且内存消耗低。处理过程会忽略空值 (`NaN`)。

---

### 4. JSON 专有方法 `process_json`

```python
def process_json(self, input_path: str, output_path: str) -> dict
```

**描述：** 
处理 JSON 格式数据。程序首先会尝试解析完整的 JSON 文件（仅支持包含对象的数组 `List[Dict]`）。如果文件格式不合法或是过大触发解析失败，程序将自动退化为 **JSON Lines** (`.jsonl`) 模式进行流式逐行解析与写入，极大地提高了对大数据日志类文件的兼容性。

---

### 5. TXT 专有方法 `process_txt`

```python
def process_txt(self, input_path: str, output_path: str) -> dict
```

**描述：** 
流式逐行读取并写入 TXT 文本，内存安全。差异记录中将附带行号(`line`)信息。

---

## 示例应用场景

### 1. 电话号码脱敏 (正则表达式)
```python
replacer = TextReplacer(
    target=r"\d{3}-\d{3}-\d{4}", 
    replacement="***-***-****", 
    use_regex=True
)
stats = replacer.process_file("users.json", "users_safe.json")
```

### 2. 特定品牌名称统一化 (区分大小写)
```python
replacer = TextReplacer(
    target="macbook", 
    replacement="MacBook", 
    case_sensitive=True
)
stats = replacer.process_file("products.csv", "products_cleaned.csv")
```