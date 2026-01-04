# OCR资源管理

<cite>
**本文档中引用的文件**  
- [assets/MaaCommonAssets/OCR/README.md](file://assets/MaaCommonAssets/OCR/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v3/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v4/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v4/zh_cn/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v5/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v5/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/keys.txt)
- [assets/MaaCommonAssets/OCR/ppocr_v3/en_us/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v3/en_us/keys.txt)
- [assets/MaaCommonAssets/OCR/ppocr_v4/zh_cn/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v4/zh_cn/keys.txt)
- [assets/MaaCommonAssets/OCR/ppocr_v4/en_us/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v4/en_us/keys.txt)
- [assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn/keys.txt)
- [assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/keys.txt)
</cite>

## 目录
1. [OCR资源概述](#ocr资源概述)
2. [OCR版本技术差异与适用场景](#ocr版本技术差异与适用场景)
3. [语言目录结构与keys.txt作用](#语言目录结构与keys.txt作用)
4. [README.md配置说明](#readmemd配置说明)
5. [OCR模型安全替换指南](#ocr模型安全替换指南)
6. [MaaFramework资源加载机制](#maaframework资源加载机制)

## OCR资源概述

MaaDuDuL项目中的OCR资源基于PaddlePaddle框架构建，位于`assets/MaaCommonAssets/OCR/`目录下。该资源包提供了多语言文本识别能力，支持多种应用场景下的图像文字检测与识别。OCR资源采用版本化管理，当前包含ppocr_v3、ppocr_v4和ppocr_v5三个主要版本，每个版本针对不同的性能需求和语言支持进行了优化。

**Section sources**
- [assets/MaaCommonAssets/OCR/README.md](file://assets/MaaCommonAssets/OCR/README.md)

## OCR版本技术差异与适用场景

### ppocr_v3：多语言支持版本
ppocr_v3是功能最全面的多语言OCR版本，支持简体中文（zh_cn）、日语（ja_jp）、韩语（ko_kr）、繁体中文（zh_tw）和英语（en_us）五种语言。该版本适用于需要处理多语言混合文本的复杂环境，具备较强的通用性。

根据配置文件信息，ppocr_v3的中文和繁体中文版本使用`ch_PP-OCRv3_det`检测模型和`ch_PP-OCRv3_rec`识别模型，而英文版本使用`en_PP-OCRv3_det`和`en_PP-OCRv3_rec`模型。日语和韩语版本仅提供识别模型，建议使用中文检测模型进行文本定位。

**Section sources**
- [assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v3/en_us/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v3/en_us/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v3/ja_jp/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v3/ja_jp/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v3/ko_kr/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v3/ko_kr/README.md)

### ppocr_v4：轻量化版本
ppocr_v4是专为性能敏感场景设计的轻量化版本，仅支持简体中文（zh_cn）和英语（en_us）两种语言。该版本在保持较高识别精度的同时，显著降低了模型体积和计算资源消耗，适合在移动设备或嵌入式系统中部署。

ppocr_v4的中文版本使用`ch_PP-OCRv4_det`检测模型和`ch_PP-OCRv4_rec`识别模型，英文版本使用`en_PP-OCRv4_rec`识别模型。值得注意的是，该版本未提供独立的英文检测模型，建议使用中文检测模型或ppocr_v3的英文检测模型。

**Section sources**
- [assets/MaaCommonAssets/OCR/ppocr_v4/zh_cn/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v4/zh_cn/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v4/en_us/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v4/en_us/README.md)

### ppocr_v5：中文优化版本
ppocr_v5是专为中文识别优化的最新版本，包含`zh_cn`和`zh_cn-server`两个子版本。根据官方说明，ppocr_v5模型实际上支持简体中文、繁体中文、英文、日文和中文拼音等多种语言，但为保持兼容性，文件夹仍命名为zh_cn。

- **zh_cn**：通用中文优化版本，适用于大多数中文识别场景
- **zh_cn-server**：服务器端高精度版本，专为服务器环境设计，提供更高的识别精度和更强的复杂文本处理能力，适合对识别质量要求极高的应用场景

服务器端版本使用PP-OCRv5_server_det检测模型和PP-OCRv5_server_rec识别模型，能够高效精准地支持手写、竖版、生僻字等复杂文本场景的识别。

**Section sources**
- [assets/MaaCommonAssets/OCR/ppocr_v5/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v5/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/README.md)

## 语言目录结构与keys.txt作用

### 目录结构组织
OCR资源按照"版本→语言"的层级结构进行组织：
```
OCR/
├── ppocr_v3/
│   ├── zh_cn/
│   ├── en_us/
│   ├── ja_jp/
│   ├── ko_kr/
│   └── zh_tw/
├── ppocr_v4/
│   ├── zh_cn/
│   └── en_us/
└── ppocr_v5/
    ├── zh_cn/
    └── zh_cn-server/
```

这种组织方式便于用户根据具体需求选择合适的OCR版本和语言配置，同时也方便MaaFramework在运行时进行资源定位和加载。

### keys.txt文件作用
每个语言目录下的`keys.txt`文件定义了该语言模型的字符集（字符字典），即模型能够识别的所有字符列表。该文件对OCR识别的准确性和完整性至关重要：

- **字符集定义**：文件中每一行包含一个可识别的字符，包括字母、数字、标点符号和汉字等
- **识别范围限制**：OCR模型只能识别字符集中包含的字符，超出范围的字符将无法正确识别
- **版本差异**：不同版本和语言的keys.txt文件内容不同，反映了各模型的支持字符范围

例如，`ppocr_v3/zh_cn/keys.txt`包含6623个字符，涵盖了常用汉字、英文字符和各种符号，而`ppocr_v3/en_us/keys.txt`则主要包含英文字母、数字和基本符号。

**Section sources**
- [assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/keys.txt)
- [assets/MaaCommonAssets/OCR/ppocr_v3/en_us/keys.txt](file://assets/MaaCommonAssets/OCR/ppocr_v3/en_us/keys.txt)

## README.md配置说明

各版本OCR目录下的README.md文件提供了详细的模型配置信息，主要包括以下内容：

### 模型元数据
- **版本日期**：标识模型的发布时间，如ppocr_v3为2023年7月或8月，ppocr_v4为2023年9月
- **来源信息**：指明模型来自PaddleOCR官方仓库的哪个文档页面

### 检测模型（det model）配置
- **模型名称**：如`ch_PP-OCRv3_det`、`ch_PP-OCRv4_det`等
- **功能描述**：说明模型支持的文本检测能力，如"支持中英文、多语种文本检测"
- **下载链接**：提供模型文件的官方下载地址

### 识别模型（rec model）配置
- **模型名称**：如`ch_PP-OCRv3_rec`、`en_PP-OCRv4_rec`等
- **功能描述**：说明模型支持的文本识别能力，如"支持中英文、数字识别"
- **下载链接**：提供模型文件的官方下载地址

### 字符标签（rec label）配置
- **字典来源**：指明字符集文件的来源，通常指向PaddleOCR仓库中的字典文件

这些配置信息对于理解各OCR版本的能力边界、进行模型替换和故障排查具有重要参考价值。

**Section sources**
- [assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v4/zh_cn/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v4/zh_cn/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn-server/README.md)

## OCR模型安全替换指南

### 文件格式要求
- **检测模型文件**：必须为ONNX格式，文件名为`det.onnx`
- **识别模型文件**：必须为ONNX格式，文件名为`rec.onnx`
- **字符集文件**：必须为纯文本格式，文件名为`keys.txt`，每行一个字符
- **编码规范**：所有文本文件（包括keys.txt和README.md）必须使用UTF-8编码

### 替换步骤
1. **备份原文件**：在替换前备份原有模型文件，以便出现问题时可快速恢复
2. **验证文件完整性**：确保下载的模型文件完整无损，可通过校验和验证
3. **保持目录结构**：将新模型文件放入对应的版本和语言目录中，保持原有的目录层级
4. **更新配置文件**：根据需要更新README.md中的模型信息
5. **测试验证**：在实际环境中测试新模型的识别效果和性能表现

### 版本兼容性注意事项
- **API兼容性**：确保新模型的输入输出格式与MaaFramework的OCR接口兼容
- **字符集兼容性**：新keys.txt文件应包含原字符集的所有字符，避免出现无法识别的情况
- **性能影响**：大型模型可能增加内存占用和处理延迟，需评估对整体性能的影响
- **回滚计划**：准备旧版本模型的备份，以便在新模型出现问题时能够快速回滚

**Section sources**
- [assets/MaaCommonAssets/OCR/README.md](file://assets/MaaCommonAssets/OCR/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v3/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v3/zh_cn/README.md)

## MaaFramework资源加载机制

MaaFramework采用分层的资源加载策略，确保OCR资源能够被正确加载和使用：

### 加载优先级规则
1. **版本优先级**：系统优先加载更高版本的OCR模型，如ppocr_v5 > ppocr_v4 > ppocr_v3
2. **语言匹配**：根据应用的语言设置选择最匹配的OCR语言模型
3. **子版本选择**：对于ppocr_v5，系统会根据运行环境（客户端/服务器）选择`zh_cn`或`zh_cn-server`版本

### 路径映射规则
- **基础路径**：`assets/MaaCommonAssets/OCR/`
- **版本路径**：`{version}/`，如`ppocr_v3/`、`ppocr_v4/`
- **语言路径**：`{language}/`，如`zh_cn/`、`en_us/`
- **最终路径**：`assets/MaaCommonAssets/OCR/{version}/{language}/`

### 运行时加载流程
1. **环境检测**：系统检测当前运行环境和语言设置
2. **路径构建**：根据检测结果构建OCR资源的完整路径
3. **文件查找**：按优先级顺序查找可用的模型文件（det.onnx、rec.onnx）
4. **资源加载**：加载模型文件和字符集（keys.txt）
5. **初始化验证**：验证模型加载是否成功，必要时回退到备用版本

这种灵活的加载机制确保了系统能够在不同环境下自动选择最优的OCR配置，同时保持了良好的向后兼容性。

**Section sources**
- [assets/MaaCommonAssets/OCR/README.md](file://assets/MaaCommonAssets/OCR/README.md)
- [assets/MaaCommonAssets/OCR/ppocr_v5/README.md](file://assets/MaaCommonAssets/OCR/ppocr_v5/README.md)