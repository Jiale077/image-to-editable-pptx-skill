# 来源及改动

上游为 [Sleepy-Avacado/FigGenie-paper-diagram-skill](https://github.com/Sleepy-Avacado/FigGenie-paper-diagram-skill)，选用 [c136a6a](https://github.com/Sleepy-Avacado/FigGenie-paper-diagram-skill/tree/c136a6aeefc6f6fe11fc615a5199cca57be3322a) 中的 PPTX 导出器及配套工具。

上游代码版权归 Sleepy Avacado，原始 [MIT 许可](LICENSE) 保留。Jiale077 对本仓库新增代码与文档同样采用 MIT 许可。

- `vendor/figgenie/` 收录上游 SVG 导出器、检查工具、SVG/公式/文字工具和字体名称映射。转换器构造函数加入共享演示文稿和位置偏移参数，支持将多份 SVG 写入同一个 PPTX。
- `scripts/export_pptx.py` 新增统一画布、输入兼容检查、按页对象统计与输出保护。
- `SKILL.md` 和教程新增位图重建流程。示例为本次制作的原创 AI 生成图、按图重建的 SVG 和实测 PPTX。

上游论文图、图形语料、字体文件、MathJax 安装与 WorkBuddy 本机配置未打包。依赖由使用者通过各项目的发布渠道安装。
