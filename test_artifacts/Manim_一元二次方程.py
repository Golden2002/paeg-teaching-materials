from manim import *

class QuadraticEquation(Scene):
    def construct(self):
        # 1. Geometry before algebra: 先展示图形
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 5, 1],
            x_length=6,
            y_length=4,
            axis_config={"color": BLUE},
        )
        graph = axes.plot(
            lambda x: x**2 - 2*x + 0.5,
            x_range=[-1.5, 3.5],
            color=YELLOW,
        )
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        graph_label = MathTex("y = x^2 - 2x + 0.5").next_to(axes, UP, buff=0.3)

        self.play(Create(axes), Write(labels))
        self.play(Create(graph), Write(graph_label))
        self.wait(0.5)

        # 2. 标注顶点与零点(Annotations ON objects)
        vertex = axes.coords_to_point(1, -0.5)
        vertex_dot = Dot(vertex, color=RED)
        vertex_label = MathTex("(1, -0.5)").next_to(vertex_dot, DOWN, buff=0.2)
        roots = [axes.coords_to_point(0.293, 0), axes.coords_to_point(1.707, 0)]
        root_dots = VGroup(*[Dot(r, color=GREEN) for r in roots])
        root_labels = VGroup(
            MathTex("x_1 \\approx 0.293").next_to(roots[0], DOWN, buff=0.2),
            MathTex("x_2 \\approx 1.707").next_to(roots[1], DOWN, buff=0.2),
        )

        self.play(
            LaggedStart(
                FadeIn(vertex_dot), Write(vertex_label),
                LaggedStart(*[FadeIn(d) for d in root_dots], lag_ratio=0.3),
                Write(root_labels),
                lag_ratio=0.5
            )
        )
        self.wait(1)

        # 3. 渐进披露:从图形到代数(TransformMatchingTex)
        equation = MathTex("x^2 - 2x + 0.5 = 0")
        equation.move_to(ORIGIN).scale(1.2)
        self.play(
            ReplacementTransform(graph_label, equation),
            FadeOut(vertex_label),
            FadeOut(root_labels),
            FadeOut(vertex_dot),
            FadeOut(root_dots),
        )
        self.wait(0.5)

        # 4. 配方步骤(Progressive complexity)
        step1 = MathTex("x^2 - 2x = -0.5")
        step2 = MathTex("x^2 - 2x + 1 = -0.5 + 1")
        step3 = MathTex("(x - 1)^2 = 0.5")
        step4 = MathTex("x - 1 = \\pm \\sqrt{0.5}")
        step5 = MathTex("x = 1 \\pm \\sqrt{0.5}")

        steps = [step1, step2, step3, step4, step5]
        for i, step in enumerate(steps):
            step.move_to(ORIGIN).scale(0.9)
            self.play(TransformMatchingTex(equation if i == 0 else steps[i-1], step))
            self.wait(0.4)

        # 5. 数值验证(Concrete values)
        result = MathTex("x_1 \\approx 0.293, \\quad x_2 \\approx 1.707")
        result.move_to(ORIGIN).scale(1.1)
        self.play(TransformMatchingTex(step5, result))
        self.wait(1)

        # 6. 收尾:回到图形(Persistent context)
        self.play(FadeOut(result), FadeIn(axes), FadeIn(graph))
        self.wait(0.5)
        self.play(FadeOut(axes), FadeOut(graph), FadeOut(labels))
        self.wait(0.5)