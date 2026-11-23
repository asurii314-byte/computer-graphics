import math
import tkinter as tk
from tkinter import ttk, messagebox


def bernstein(i, n, t):
    return math.comb(n, i) * (t ** i) * ((1.0 - t) ** (n - i))


def de_casteljau_levels(points, t):
    levels = [list(points)]
    current = list(points)
    while len(current) > 1:
        nxt = [
            ((1.0 - t) * current[i][0] + t * current[i + 1][0],
             (1.0 - t) * current[i][1] + t * current[i + 1][1])
            for i in range(len(current) - 1)
        ]
        levels.append(nxt)
        current = nxt
    return levels


def build_cubic_bezier(points, steps, t_param):
    curve = []
    first_seg_levels = []
    idx = 0
    while idx + 3 < len(points):
        seg = points[idx:idx + 4]
        if not first_seg_levels:
            first_seg_levels = de_casteljau_levels(seg, t_param)
        for s in range(steps + 1):
            u = s / steps
            curve.append(de_casteljau_levels(seg, u)[-1][0])
        idx += 3
    return curve, first_seg_levels


def build_chaikin(points, iterations):
    pts = list(points)
    for _ in range(iterations):
        if len(pts) < 2:
            break
        nxt = [pts[0]]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            nxt.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1))
            nxt.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
        nxt.append(pts[-1])
        pts = nxt
    return pts


def build_bezier_surface(grid, steps):
    n = len(grid) - 1
    m = len(grid[0]) - 1
    surf = []
    for iu in range(steps + 1):
        u = iu / steps
        row = []
        for iv in range(steps + 1):
            v = iv / steps
            sx = sy = sz = 0.0
            for i in range(n + 1):
                bi = bernstein(i, n, u)
                for j in range(m + 1):
                    w = bi * bernstein(j, m, v)
                    px, py, pz = grid[i][j]
                    sx += px * w
                    sy += py * w
                    sz += pz * w
            row.append((sx, sy, sz))
        surf.append(row)
    return surf


class SimpleCurvesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Кривые и поверхности")
        self.root.geometry("1120x720")
        self.build_ui()
        self.load_demo()

    def build_ui(self):
        root_frame = ttk.Frame(self.root, padding=10)
        root_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            root_frame,
            text="Кривые и поверхности",
            font=("Times New Roman", 16, "bold")
        ).pack(anchor="w", pady=(0, 8))

        content = ttk.Frame(root_frame)
        content.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(content, width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        self.algo_var = tk.StringVar(value="Кубическая Безье")
        algo_cb = ttk.Combobox(
            left,
            textvariable=self.algo_var,
            values=["Кубическая Безье", "Кривая Чайкина", "Поверхность Безье"],
            state="readonly"
        )
        algo_cb.pack(fill=tk.X, pady=(0, 6))
        algo_cb.bind("<<ComboboxSelected>>", lambda e: self.load_demo())

        ttk.Label(
            left,
            text="Точки по строкам. Поверхность:\nx y z; x y z; ...",
            justify=tk.LEFT
        ).pack(anchor="w")

        self.pts_text = tk.Text(left, height=12, font=("Consolas", 10))
        self.pts_text.pack(fill=tk.X, pady=(2, 8))

        self.steps_entry = self._add_field(left, "Деления / итерации Чайкина", "20")
        self.t_entry = self._add_field(left, "Параметр t первого сегмента", "0.5")
        self.level_entry = self._add_field(left, "Уровень де Кастельжо (0–3)", "3")
        self.angle_entry = self._add_field(left, "Поворот поверхности, °", "35")

        self.show_orig_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left, text="Исходные вершины",
            variable=self.show_orig_var, command=self.draw
        ).pack(anchor="w", pady=(4, 0))

        self.show_refined_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left, text="Уточнённые вершины",
            variable=self.show_refined_var, command=self.draw
        ).pack(anchor="w", pady=(2, 8))

        ttk.Button(left, text="Построить", command=self.draw).pack(fill=tk.X, pady=(0, 5))


        right = ttk.Frame(content)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right, bg="white", highlightthickness=1, highlightbackground="#cccccc")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw())

        self.log_text = tk.Text(right, height=5, font=("Consolas", 9))
        self.log_text.pack(fill=tk.X, pady=(6, 0))

    def _add_field(self, parent, label, default):
        ttk.Label(parent, text=label).pack(anchor="w")
        entry = ttk.Entry(parent)
        entry.insert(0, default)
        entry.pack(fill=tk.X, pady=(1, 6))
        return entry

    def load_demo(self):
        algo = self.algo_var.get()
        self.pts_text.delete("1.0", tk.END)

        if algo == "Кубическая Безье":
            self.pts_text.insert("1.0", "0 0\n1 4\n4 4\n5 0\n6 -3\n8 -3\n9 1")
            self._set_entry(self.steps_entry, "20")
            self._set_entry(self.t_entry, "0.5")
            self._set_entry(self.level_entry, "3")
        elif algo == "Кривая Чайкина":
            self.pts_text.insert("1.0", "0 0\n1 4\n4 4\n5 0\n8 -2")
            self._set_entry(self.steps_entry, "3")
        else:
            self.pts_text.insert(
                "1.0",
                "-2 -2 0; -0.7 -2 1.5; 0.7 -2 1.5; 2 -2 0\n"
                "-2 -0.7 1.5; -0.7 -0.7 3; 0.7 -0.7 3; 2 -0.7 1.5\n"
                "-2 0.7 1.5; -0.7 0.7 3; 0.7 0.7 3; 2 0.7 1.5\n"
                "-2 2 0; -0.7 2 1.5; 0.7 2 1.5; 2 2 0"
            )
            self._set_entry(self.steps_entry, "12")
            self._set_entry(self.angle_entry, "35")

        self.draw()

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def parse_2d(self):
        pts = []
        for line in self.pts_text.get("1.0", tk.END).splitlines():
            line = line.strip().replace(",", ".")
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError("Для кривой введите по 2 координаты: x y")
            pts.append((float(parts[0]), float(parts[1])))
        return pts

    def parse_3d(self):
        grid = []
        for line in self.pts_text.get("1.0", tk.END).splitlines():
            line = line.strip().replace(",", ".")
            if not line:
                continue
            row = []
            for item in line.split(";"):
                item = item.strip()
                if not item:
                    continue
                parts = item.split()
                if len(parts) != 3:
                    raise ValueError("Для поверхности введите 3 координаты: x y z")
                row.append((float(parts[0]), float(parts[1]), float(parts[2])))
            if row:
                grid.append(row)
        if len(grid) < 2 or len(grid[0]) < 2:
            raise ValueError("Сетка поверхности должна быть минимум 2x2")
        return grid

    def project(self, x, y, z, angle_deg):
        rad = math.radians(angle_deg)
        xr = x * math.cos(rad) - y * math.sin(rad)
        yr = x * math.sin(rad) + y * math.cos(rad)
        return xr + 0.5 * z, yr + 0.5 * z

    def make_transformer(self, points_2d):
        w = max(self.canvas.winfo_width(), 100)
        h = max(self.canvas.winfo_height(), 100)
        pad = 50
        xs = [p[0] for p in points_2d]
        ys = [p[1] for p in points_2d]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        dx = max(max_x - min_x, 1e-6)
        dy = max(max_y - min_y, 1e-6)
        scale = min((w - 2 * pad) / dx, (h - 2 * pad) / dy)
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        return lambda pt: (w / 2 + (pt[0] - cx) * scale, h / 2 - (pt[1] - cy) * scale)

    def draw_line(self, pts, color, width=2, dash=None):
        if len(pts) >= 2:
            coords = [c for p in pts for c in p]
            self.canvas.create_line(*coords, fill=color, width=width, dash=dash)

    def draw_dots(self, pts, color, r=3.5, prefix=None):
        for i, (x, y) in enumerate(pts):
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="")
            if prefix is not None:
                self.canvas.create_text(x + 7, y - 7, text=f"{prefix}{i}", font=("Segoe UI", 8), fill="#333333")

    def log(self, text):
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert("1.0", text)

    def draw(self):
        self.canvas.delete("all")
        algo = self.algo_var.get()

        try:
            steps = int(self.steps_entry.get())
            if steps < 1:
                raise ValueError("Число делений / итераций должно быть >= 1")

            if algo == "Кубическая Безье":
                pts = self.parse_2d()
                if len(pts) < 4:
                    raise ValueError("Для кубической Безье нужно минимум 4 точки")
                t_val = float(self.t_entry.get().replace(",", "."))
                max_lvl = int(self.level_entry.get())
                curve, levels = build_cubic_bezier(pts, steps, t_val)

                to_px = self.make_transformer(pts + curve)
                if self.show_orig_var.get():
                    self.draw_line([to_px(p) for p in pts], "#8aa2be", width=1.2)
                    self.draw_dots([to_px(p) for p in pts], "#1d4ed8", r=3.5, prefix="P")

                self.draw_line([to_px(p) for p in curve], "#15803d", width=2.5)
                if self.show_refined_var.get():
                    self.draw_dots([to_px(p) for p in curve], "#15803d", r=2.5)
                    for lvl_idx in range(1, min(max_lvl, len(levels) - 1) + 1):
                        lvl_pts = [to_px(p) for p in levels[lvl_idx]]
                        self.draw_line(lvl_pts, "#d97706", width=1.5)
                        self.draw_dots(lvl_pts, "#d97706", r=3.5)

                lines_out = [
                    f"Уровень {i}: {[(round(x, 2), round(y, 2)) for x, y in lvl]}"
                    for i, lvl in enumerate(levels[:max_lvl + 1])
                ]
                self.log("\n".join(lines_out))

            elif algo == "Кривая Чайкина":
                pts = self.parse_2d()
                if len(pts) < 2:
                    raise ValueError("Для кривой Чайкина нужно минимум 2 точки")
                refined = build_chaikin(pts, min(steps, 10))
                to_px = self.make_transformer(pts + refined)

                if self.show_orig_var.get():
                    self.draw_line([to_px(p) for p in pts], "#8aa2be", width=1.2, dash=(4, 3))
                    self.draw_dots([to_px(p) for p in pts], "#1d4ed8", r=3.5, prefix="P")

                self.draw_line([to_px(p) for p in refined], "#15803d", width=2.5)
                if self.show_refined_var.get():
                    self.draw_dots([to_px(p) for p in refined], "#d97706", r=3)

                self.log(f"Итераций: {min(steps, 10)}  Исходных точек: {len(pts)}  Уточнённых точек: {len(refined)}")

            else:
                grid = self.parse_3d()
                angle = float(self.angle_entry.get().replace(",", "."))
                surf = build_bezier_surface(grid, steps)

                proj_grid = [[self.project(*p, angle) for p in row] for row in grid]
                proj_surf = [[self.project(*p, angle) for p in row] for row in surf]
                all_2d = [p for r in proj_grid for p in r] + [p for r in proj_surf for p in r]
                to_px = self.make_transformer(all_2d)

                s_grid = [[to_px(p) for p in row] for row in proj_grid]
                s_surf = [[to_px(p) for p in row] for row in proj_surf]

                if self.show_orig_var.get():
                    for r in s_grid:
                        self.draw_line(r, "#8aa2be", width=1, dash=(3, 3))
                    for c in range(len(s_grid[0])):
                        self.draw_line([s_grid[r][c] for r in range(len(s_grid))], "#8aa2be", width=1, dash=(3, 3))
                    for r in s_grid:
                        self.draw_dots(r, "#1d4ed8", r=3.5)

                for r in s_surf:
                    self.draw_line(r, "#15803d", width=1.5)
                for c in range(len(s_surf[0])):
                    self.draw_line([s_surf[r][c] for r in range(len(s_surf))], "#15803d", width=1.5)

                if self.show_refined_var.get():
                    for r in s_surf:
                        self.draw_dots(r, "#d97706", r=2)

                self.log(f"Поверхность Безье {len(grid)-1}x{len(grid[0])-1}  Сетка разбиений: {steps}x{steps}  Поворот: {angle}°")

        except ValueError as err:
            messagebox.showerror("Ошибка", str(err))


if __name__ == "__main__":
    root = tk.Tk()
    SimpleCurvesApp(root)
    root.mainloop()