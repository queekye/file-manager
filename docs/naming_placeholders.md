# 文件命名规则引擎 - 占位符参考

本文档提供文件命名规则引擎支持的所有占位符的详细说明和使用示例。

## 占位符列表

在配置文件的`naming_pattern`字段中，您可以使用以下占位符组合文件命名规则：

| 占位符 | 描述 | 示例值 |
|-------|------|-------|
| `{person}` | 人员目录名 | `zhangsan` |
| `{person_name}` | 人员姓名 | `张三` |
| `{person_id}` | 人员ID | `001` |
| `{type}` | 文件类型目录名 | `ID_Cards` |
| `{type_name}` | 文件类型名称 | `身份证` |
| `{type_id}` | 文件类型ID | `id_card` |
| `{original_filename}` | 原始文件名（不含扩展名） | `scan` |
| `{original_extension}` | 原始文件扩展名（含点号） | `.pdf` |
| `{original_name}` | 完整的原始文件名（含扩展名） | `scan.pdf` |
| `{date}` | 当前日期（格式：YYYY-MM-DD） | `2023-05-20` |
| `{time}` | 当前时间（格式：HHMMSS） | `142530` |
| `{datetime}` | 当前日期时间（格式：YYYYMMDD_HHMMSS） | `20230520_142530` |
| `{year}` | 当前年份 | `2023` |
| `{month}` | 当前月份 | `05` |
| `{day}` | 当前日 | `20` |
| `{hour}` | 当前小时 | `14` |
| `{minute}` | 当前分钟 | `25` |
| `{second}` | 当前秒 | `30` |

## 使用示例

以下是一些常用的命名模式示例：

### 基本示例
```
{person}_{type}_{original_filename}{original_extension}
```
生成结果：`zhangsan_ID_Cards_scan.pdf`

### 使用日期时间
```
{person}_{type}_{date}_{original_filename}{original_extension}
```
生成结果：`zhangsan_ID_Cards_2023-05-20_scan.pdf`

### 使用年月日文件夹结构
```
{year}/{month}/{day}/{person}_{type}_{original_filename}{original_extension}
```
生成结果：`2023/05/20/zhangsan_ID_Cards_scan.pdf`

### 使用自定义前缀
```
Doc_{person_id}_{type_id}_{datetime}{original_extension}
```
生成结果：`Doc_001_id_card_20230520_142530.pdf`

## 注意事项

1. 如果某个占位符对应的数据不可用（例如没有提供人员信息），该占位符将被替换为空字符串。
2. 生成的文件名会自动清理非法字符，例如Windows中的`< > : " / \ | ? *`将被替换为下划线。
3. 文件名长度如果超过240个字符，将被自动截断以确保符合Windows文件系统限制。
4. 前导和尾随的空格和点号将被自动移除。
5. 连续的点号将被合并为单个点号。
6. 如果生成的文件名为空，将使用默认名称`file_当前日期时间`。

## 配置示例

在配置文件（`config.yaml`）中，您可以设置全局命名模式：

```yaml
# 文件命名模式
naming_pattern: "{person}_{type}_{original_filename}{original_extension}"
```

您也可以在代码中直接使用NamingEngine类：

```python
from src.core.naming import NamingEngine

# 创建命名引擎
engine = NamingEngine("{person}_{type}_{date}_{original_filename}{original_extension}")

# 生成文件名
new_filename = engine.generate_name(
    original_filename="scan.pdf",
    person={"id": "001", "name": "张三", "directory": "zhangsan"},
    file_type={"id": "id_card", "name": "身份证", "directory": "ID_Cards"}
) 