---
name: figgenie-editable-pptx
description: Rebuild slide screenshots, JPG/PNG images and AI-generated designs as editable PowerPoint, or export structured SVGs to a multi-slide PPTX. Use when the user wants editable text, diagram shapes and image objects.
---

# 图片重建为可编辑 PPT

定位本文件所在的项目根目录。导出入口是 `scripts/export_pptx.py`。运行环境和示例见 [教程](docs/getting-started.md)。

## 1. 从原图确定可重建对象

逐张打开用户的 PNG、JPG 或截图。按页记录画布比例、原文、位置、层级和颜色。标题、正文、数字与标注保留为文本。卡片、线条、箭头和简单轮廓用形状表示。照片与复杂纹理按区域保留为 PNG/JPEG。无法辨认的文字或数据标为待核对。已有结构化 SVG 时直接检查它的元素和外部图片路径。

完成条件是能对应原图指出哪些是文本、形状或图片，以及哪些信息有待用户核对。

## 2. 写结构化 SVG

每张输入生成一份 SVG。使用标准 SVG 命名空间和带四个数字的 `viewBox`。用单独的 `text` 元素写每行文字，使用 `x`、`y`、`font-size`、`font-weight` 与 `fill` 表达版式。用带 `id` 的顶层 `g` 组织卡片。按从背景到前景的顺序绘制。图片引用使用相对于 SVG 目录的路径或 PNG/JPEG data URI。查看 [兼容写法](docs/getting-started.md#svg-兼容写法)。

完成条件是每页 SVG 包含预期的独立对象，图片资源能够读取，文字可追溯到原图。

## 3. 导出 PPTX 并核对

```sh
python3 scripts/export_pptx.py /path/to/page-01.svg /path/to/page-02.svg -o /path/to/result.pptx
```

读取命令输出的对象计数。有兼容错误时修正 SVG 或将复杂部分保留为图片后重新导出。需要保留未完整转换的结果时用 `--allow-partial`，并说明相应的差异。

使用可用的 PPT 渲染器查看输出。与原图对照版面、文字、图片和箭头。核对 PPTX 对象结构，确认要求可编辑的文字与几何确实是独立对象。交付 PPTX、SVG 和引用资源，说明视觉保留的图片区域及待确认内容。
