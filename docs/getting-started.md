# 使用教程

## 安装依赖

需要 Python 3.10+。在终端获取项目并为项目单独安装依赖。

```sh
git clone https://github.com/Jiale077/image-to-editable-pptx-skill.git
cd image-to-editable-pptx-skill
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Windows PowerShell 的虚拟环境激活命令为 `.venv\Scripts\Activate.ps1`，可用 `python` 替代 `python3`。

可直接让视觉助手读取仓库根目录的 `SKILL.md`。想在 WorkBuddy 中作为技能使用，可以在本机将仓库安装到 `~/.workbuddy/skills/image-to-editable-pptx-skill`，再让助手读取该目录的 `SKILL.md` 并使用已安装依赖的 Python。Codex 可将目录放到 `~/.agents/skills/`，Claude Code 可放到 `~/.claude/skills/`。安装目录名为 `image-to-editable-pptx-skill`。

## 从图片开始

把普通 JPG、PNG、PPT 截图，或 Image 2.5、Nano Banana 等工具生成的图交给助手。助手需要能看图、创建文件和执行导出命令。

1. **看图。** 确认每页标题、文字、形状、连接关系、复杂图像及层级。原图文字模糊时请补充高清图或原文。
2. **重建。** 每页写一份结构化 SVG。用 `text` 记录实际文字，用几何形状记录版式，将照片等复杂图像作为独立图片。
3. **导出。** 将 SVG 按顺序交给导出器。它会生成统一画布的 PPTX。
4. **验收。** 查看渲染结果。在 PowerPoint 打开选择窗格，展开对象组，检查标题、卡片和箭头能否选中和编辑。

项目附带一次实际转换的各阶段文件。 [AI 生成的原图](../examples/source-ai.png) · [重建用 SVG](../examples/01-rebuilt.svg) · [实际 PPTX](../examples/editable-demo.pptx)

## 跑通示例

```sh
python3 scripts/export_pptx.py examples/01-rebuilt.svg examples/02-mixed.svg -o runs/demo.pptx
```

第一页重建「企业知识助手架构」的分层版式、六张模块卡片、矢量图标和连接线。第二页演示原图与独立文本、形状混排。视觉助手根据 AI 生成的 PNG 重建了第一页。

| 参数 | 用途 |
| --- | --- |
| `-o runs/demo.pptx` | 指定输出位置 |
| `--size 960x540` | 以 pt 指定统一画布。不同长宽比的图居中等比缩放 |
| `--latin Arial --cjk "Microsoft YaHei"` | 选择目标设备上安装的西文字体和中文字体 |
| `--allow-partial` | 输出可以转换的部分并列出警告 |
| `--force` | 允许替换指定的 PPTX。已在 PowerPoint 改过的文件建议另存 |

## SVG 兼容写法

| 元素 | 推荐写法 |
| --- | --- |
| 画布 | `xmlns="http://www.w3.org/2000/svg"` 与 `viewBox="0 0 960 540"` |
| 文字 | 每行一个 `text`，字体和坐标用属性表示。保留中文原文 |
| 图形 | `rect`、`circle`、`ellipse`、`path`、`polygon`、`polyline`、`line` |
| 连接线 | `line` 配 `marker-end`，或使用独立箭头图形 |
| 图片 | `image` 指向同目录或下级目录的 PNG/JPEG，或嵌入对应 data URI |
| 分组 | 用带 `id` 的顶层 `g` 将同一张卡片的形状与文字放在一起 |
| 复杂效果 | 将相应区域单独保留为 PNG/JPEG。CSS 类样式、遮罩、裁切和渐变需要先处理 |

输出的字体由打开文件的设备决定。代码中的 SVG 坐标按画布等比映射，清晰可读的截图适合重建文字和基础形状。图表原始数据、动画、图层语义和文字识别的准确率取决于可获得的源材料。批量入口将带有排版度量的公式作为文字写入。

## 本次验证

- 实际生成并检查两页 PPTX。第一页的模块文字、卡片、线条和矢量图标可逐项编辑，第二页的原图是可独立替换的图片对象。
- 对第一页的标题和模块文字做了修改、保存和重新读取，核对了 PPTX 中的独立对象。预览来自 macOS Quick Look。
- 图片重建示例使用原创 AI 生成 PNG。Image 2.5 和 Nano Banana 是可提供图片的来源，运行流程接收的是它们导出的图像文件。

[回到项目首页](../README.md)
