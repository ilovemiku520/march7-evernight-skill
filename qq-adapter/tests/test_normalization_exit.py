"""Role exit removes decoration while retaining literal and structured symbols."""
import importlib.util
from pathlib import Path
import sys
import unittest


ENGINE_PATH = Path(__file__).resolve().parents[1] / "plugin" / "engine.py"
SPEC = importlib.util.spec_from_file_location("exit_normalization_engine", ENGINE_PATH)
engine = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = engine
SPEC.loader.exec_module(engine)


class ExitNormalizationTests(unittest.TestCase):
    def decision(self, *, active=False, paused=True, strict=None):
        return engine.Decision("E", "长夜月", "长夜月", "", strict,
                               {"active": active, "paused": paused})

    def test_ooc_prose_removes_final_and_paragraph_decoration(self):
        for text, expected in (
            ("好的，已退出角色。♭", "好的，已退出角色。"),
            ("第一段普通说明。♭\n\n第二段。♭♭", "第一段普通说明。\n\n第二段。"),
            ("这是普通说明。 ♭  \r\n另一句。♭", "这是普通说明。\r\n另一句。"),
        ):
            self.assertEqual(engine.normalize_reply(text, self.decision()), expected)

    def test_paused_flag_alone_cannot_append_or_retain_role_decoration(self):
        decision = self.decision(active=True, paused=True)
        self.assertEqual(engine.normalize_reply("普通说明。♭", decision), "普通说明。")
        self.assertEqual(engine.normalize_reply("普通说明。", decision), "普通说明。")

    def test_strict_ooc_payload_is_unchanged(self):
        for kind in ("json", "code", "url", "quote"):
            text = "严格载荷中的原始♭"
            self.assertEqual(engine.normalize_reply(text, self.decision(strict=kind)), text)

    def test_structured_ooc_json_code_url_and_quotes_are_preserved(self):
        for text in (
            '{"symbol":"♭"}', '["♭"]', '```python\nsymbol = "♭"\n```',
            'https://example.invalid/music/♭', '[音乐](https://example.invalid/♭)',
            '> 原样引用♭', '“原样引用♭”', '「原样引用♭」',
        ):
            self.assertEqual(engine.normalize_reply(text, self.decision()), text)

    def test_mixed_ooc_content_preserves_protected_symbols_but_removes_decoration(self):
        text = '说明。♭\n```text\n保留♭\n```\n> 引文♭\n音乐是 E♭\n普通收句。♭'
        expected = '说明。\n```text\n保留♭\n```\n> 引文♭\n音乐是 E♭\n普通收句。'
        self.assertEqual(engine.normalize_reply(text, self.decision()), expected)

    def test_literal_music_and_flat_symbol_meaning_are_preserved(self):
        for text in ("这个降号是♭", "音乐记号：♭", "音高：E♭", "请保留 ♭", "符号♭出现在句中。"):
            self.assertEqual(engine.normalize_reply(text, self.decision()), text)

    def test_active_role_marker_behavior_is_unchanged(self):
        decision = self.decision(active=True, paused=False)
        self.assertEqual(engine.normalize_reply("我在。♭♭", decision), "我在。♭")


if __name__ == "__main__":
    unittest.main()
