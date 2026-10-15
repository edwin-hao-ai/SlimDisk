"""深色模式「跟随系统」策略的静态门禁。

背景（真实拒审）：App Store Guideline 2.1(a) —— 深色模式下输入框文字不可见。
根因不是某条颜色写错，而是**深色机制分裂**：

- `styles.css` 里用 `@media (prefers-color-scheme: dark)` 切换 CSS 变量与
  `.card` / `.btn-ghost` / `.sidebar-item` 等组件色 —— 这套照常生效；
- 但只要样式里再写一句 `@custom-variant dark (&:where(.dark, .dark *))`，
  Tailwind 的 `dark:` 变体就被改成**只认 `.dark` class**。而全工程从不给任何
  元素加 `.dark`（本文件第二个用例兜底），于是全部 `dark:*` 工具类失效。

两边一打架，深色下就出现「背景变深、文字还停在浅色档」：最严重的是输入框
（`bg-white dark:bg-zinc-800`）—— `dark:` 失效后仍是白底，文字却继承近白的
`--text-primary`，白底白字完全看不见。

所以只有一条铁律：**深色跟随系统（`prefers-color-scheme`），不得把 `dark:`
变体改成 class 驱动**。要做手动切换，必须同时引入 `.dark` 切换器 + 迁移本文件
所有 media query，两边统一 —— 不能只改一半。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLES = ROOT / "src" / "styles.css"
SRC = ROOT / "src"

#: 任何形式的 class 驱动 dark 变体声明（含注释被剥掉后仍要能抓到）。
CLASS_GATED_DARK = re.compile(r"@custom-variant\s+dark\b")

#: 源码里「给元素加/删 .dark」的动作。出现即意味着另一套 class 机制被引入。
DARK_CLASS_TOGGLER = re.compile(
    r"""classList\.(?:add|remove|toggle)\(\s*["']dark["']"""
    r"""|setAttribute\(\s*["']class["']\s*,\s*["'][^"']*\bdark\b"""
)


def _strip_css_comments(text: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/", "", text)


class DarkModeStrategyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.styles_raw = STYLES.read_text(encoding="utf-8")
        self.styles = _strip_css_comments(self.styles_raw)

    def test_dark_variant_is_not_class_gated(self) -> None:
        """核心回归点：不能让 dark: 变体变成 class 驱动。"""
        match = CLASS_GATED_DARK.search(self.styles)
        self.assertIsNone(
            match,
            msg=(
                "styles.css 出现了 class 驱动的 dark 变体声明"
                "（@custom-variant dark ...）。全工程不加 .dark，"
                "这会让所有 dark: 工具类失效、深色下白底白字（App Store 2.1a）。"
                "深色必须由 prefers-color-scheme 驱动。"
            ),
        )

    def test_dark_styling_is_media_query_driven(self) -> None:
        """反向确认深色确实还有实现（删过头会连带把深色机制删没）。"""
        self.assertIn("prefers-color-scheme: dark", self.styles)
        # :root 深色变量块必须还在
        self.assertRegex(self.styles, r"prefers-color-scheme:\s*dark[\s\S]*--text-primary")

    def test_no_dark_class_toggler_is_introduced(self) -> None:
        """兜底：没人给 .dark 加类，才证明 media-query 策略是自洽的。

        若将来真要做手动主题切换，必须同时改本测试与 styles.css —— 只加切换器
        而不迁移 media query，会回到「两套机制打架」的老 bug。
        """
        offenders: list[str] = []
        for path in sorted(SRC.rglob("*")):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            if DARK_CLASS_TOGGLER.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(
            offenders,
            [],
            msg=(
                "发现给元素添加/切换 .dark class 的代码："
                f"{offenders}。深色目前是 prefers-color-scheme 驱动，"
                "混入 class 切换会再次造成两套机制不一致。"
            ),
        )


if __name__ == "__main__":
    unittest.main()
