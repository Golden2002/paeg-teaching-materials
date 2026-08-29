# -*- coding: utf-8 -*-
"""细胞呼吸 · 教学动画（ManimCE v0.19.0）

配合 `视频分镜_细胞呼吸.json` 的 8 镜分镜与 `讲稿_细胞呼吸.md` 的旁白
（旁白已由 edge-tts 合成 `旁白_细胞呼吸.mp3`，本动画为纯视觉分镜）。
中文标签使用系统字体 Microsoft YaHei（避免默认字体缺字产生豆腐块）。
"""
from manim import *

ZH_FONT = "Microsoft YaHei"


def zh(s, **kw):
    """中文 Text，统一指定 CJK 字体。"""
    kw.setdefault("font", ZH_FONT)
    return Text(s, **kw)


def stage_box(label, sub, color, width=3.4, height=1.7):
    """一个「车间」卡片：圆角矩形 + 中文标题 + 副标题。"""
    box = RoundedRectangle(
        corner_radius=0.2, width=width, height=height,
        fill_color=color, fill_opacity=0.16,
        stroke_color=color, stroke_width=2.5,
    )
    t = zh(label, font_size=30, color=color)
    s = zh(sub, font_size=18, color=GREY)
    txt = VGroup(t, s).arrange(DOWN, buff=0.18).move_to(box)
    return VGroup(box, txt)


class CellularRespiration(Scene):
    def _section_title(self, text, color):
        # 先清掉上一节的标题，再显示本节标题
        if hasattr(self, "_title_mobj") and self._title_mobj is not None:
            self.play(FadeOut(self._title_mobj))
        t = zh(text, font_size=34, color=color).to_edge(UP)
        self._title_mobj = t
        self.play(FadeIn(t))
        self.wait(0.4)
        return t

    def construct(self):
        self._title_mobj = None

        # ── 1. 标题 ──
        title = zh("细胞呼吸", font_size=66, color=BLUE)
        sub = zh("把有机物中的化学能释放出来，供生命活动使用", font_size=28, color=GREY)
        header = VGroup(title, sub).arrange(DOWN, buff=0.25).to_edge(UP)
        self.play(Write(title), FadeIn(sub))
        self.wait(1.0)

        # ── 2. 总反应式 ──
        eq = MathTex(
            r"C_6H_{12}O_6 + 6O_2 \rightarrow 6CO_2 + 6H_2O + \text{ATP}",
            font_size=46,
        ).next_to(header, DOWN, buff=0.8)
        eq_note = zh("葡萄糖 + 氧气 → 二氧化碳 + 水 + 能量（ATP）",
                     font_size=26, color=YELLOW).next_to(eq, DOWN, buff=0.5)
        self.play(FadeOut(title), FadeOut(sub))
        self.play(Write(eq), FadeIn(eq_note))
        self.wait(1.4)
        self.play(FadeOut(eq_note))

        # ── 3. 三阶段总览流水线 ──
        g = stage_box("糖酵解", "细胞质基质 · 无需氧气", GREEN)
        k = stage_box("柠檬酸循环", "线粒体基质", ORANGE)
        e = stage_box("电子传递链", "线粒体内膜 · 产能主力", RED)
        flow = VGroup(g, k, e).arrange(RIGHT, buff=1.1)
        flow.next_to(eq, DOWN, buff=1.1)
        flow_arrows = VGroup(
            Arrow(g.get_right(), k.get_left(), buff=0.22, color=WHITE),
            Arrow(k.get_right(), e.get_left(), buff=0.22, color=WHITE),
        )
        self.play(FadeIn(flow), FadeIn(flow_arrows))
        self.wait(1.3)
        self.play(FadeOut(flow), FadeOut(flow_arrows), FadeOut(eq))

        # ── 4. 糖酵解 ──
        self._section_title("第一阶段 · 糖酵解（细胞质基质）", GREEN)
        glu = MathTex(r"\text{Glucose}", font_size=36).shift(LEFT * 4.2)
        glu_label = zh("1× 六碳葡萄糖", font_size=24, color=BLUE).next_to(glu, DOWN)
        pyr = MathTex(r"2 \times \text{Pyruvate}", font_size=36).shift(RIGHT * 3.6)
        pyr_label = zh("2× 三碳丙酮酸", font_size=24, color=GREEN).next_to(pyr, DOWN)
        yield_note = zh("少量 ATP + NADH（不需氧气）", font_size=26, color=YELLOW) \
            .shift(DOWN * 2.4)
        g_arrow = Arrow(glu.get_right(), pyr.get_left(), buff=0.3, color=WHITE)
        self.play(FadeIn(glu), FadeIn(glu_label))
        self.play(FadeIn(pyr), FadeIn(pyr_label))
        self.play(Create(g_arrow), FadeIn(yield_note))
        self.wait(1.3)
        self.play(FadeOut(VGroup(glu, glu_label, pyr, pyr_label, yield_note, g_arrow)))

        # ── 5. 柠檬酸循环 ──
        self._section_title("第二阶段 · 柠檬酸循环（线粒体基质）", ORANGE)
        cycle = Circle(radius=1.6, color=ORANGE, stroke_width=3).move_to(ORIGIN)
        co2 = MathTex(r"\text{CO}_2", font_size=34, color=GREY)
        co2.next_to(cycle, RIGHT, buff=1.6)
        carriers = zh("NADH + FADH₂ 带走氢与电子", font_size=26, color=YELLOW) \
            .next_to(cycle, DOWN, buff=1.6)
        acetyl = zh("乙酰辅酶 A 进入循环", font_size=24, color=ORANGE) \
            .next_to(cycle, LEFT, buff=1.8)
        self.play(Create(cycle), FadeIn(acetyl))
        self.play(
            FadeIn(co2), FadeIn(carriers),
            Rotate(co2, angle=2 * PI, about_point=cycle.get_center(), run_time=2.2),
        )
        self.wait(1.0)
        self.play(FadeOut(VGroup(cycle, co2, carriers, acetyl)))

        # ── 6. 电子传递链（瀑布 + 梯度 + ATP 合酶）──
        self._section_title("第三阶段 · 电子传递链（产能主力）", RED)
        steps = VGroup(*[
            Rectangle(width=1.0, height=0.55, color=BLUE, fill_opacity=0.3)
            for _ in range(5)
        ]).arrange(DOWN, buff=0.28).to_edge(LEFT, buff=2.2)
        e_dot = Dot(color=YELLOW).move_to(steps[0].get_top() + UP * 0.4)
        atp = zh("大量 ATP", font_size=30, color=GOLD).to_edge(RIGHT, buff=1.9)
        h2o = zh("O₂ + 电子 → H₂O", font_size=24, color=GREY).next_to(atp, DOWN, buff=0.6)
        self.play(FadeIn(steps), FadeIn(e_dot))
        for i in range(5):
            self.play(e_dot.animate.move_to(steps[i].get_center()), run_time=0.3)
        self.play(FadeIn(atp), FadeIn(h2o))
        self.wait(1.2)
        self.play(FadeOut(VGroup(steps, e_dot, atp, h2o)))

        # ── 7. ATP 账本 + 无氧呼吸 ──
        self._section_title("能量账本 · 有氧 ≈ 32 ATP vs 无氧 = 2 ATP", GOLD)
        aerobic = zh("有氧呼吸 ≈ 32 ATP", font_size=34, color=GOLD)
        anaerobic = zh("无氧呼吸 = 2 ATP（乳酸 / 酒精）", font_size=30, color=GREY)
        tally = VGroup(aerobic, anaerobic).arrange(DOWN, buff=0.5).move_to(ORIGIN)
        self.play(Write(tally))
        self.wait(1.6)
        self.play(FadeOut(tally))

        # ── 8. 收尾 ──
        closing = zh("细胞呼吸：生命得以延续的引擎", font_size=40, color=BLUE).to_edge(UP)
        self.play(FadeOut(self._title_mobj), Write(closing))
        self.wait(1.4)
        self.play(FadeOut(closing))
