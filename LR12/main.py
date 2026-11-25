import math
import tkinter as tk
from tkinter import ttk, messagebox


def bernstein(i, n, t):
    return math.comb(n, i) * (t ** i) * ((1.0 - t) ** (n - i))


def build_bezier_surface(grid, steps):
    n = len(grid) - 1
    m = len(grid[0]) - 1
    surface = []
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
        surface.append(row)
    return surface


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_scale(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def doo_sabin_step(vertices, faces):
    new_vertices = []
    face_point_indices = []
    edge_map = {}
    vertex_incident = {}

    for f_idx, face in enumerate(faces):
        m = len(face)
        center = (0.0, 0.0, 0.0)
        for v_idx in face:
            center = vec_add(center, vertices[v_idx])
        center = vec_scale(center, 1.0 / m)

        local_new_indices = []
        for k in range(m):
            v_curr = face[k]
            v_prev = face[(k - 1) % m]
            v_next = face[(k + 1) % m]

            mid_prev = vec_scale(vec_add(vertices[v_curr], vertices[v_prev]), 0.5)
            mid_next = vec_scale(vec_add(vertices[v_curr], vertices[v_next]), 0.5)

            fp = vec_scale(
                vec_add(vec_add(vertices[v_curr], center), vec_add(mid_prev, mid_next)),
                0.25
            )
            new_idx = len(new_vertices)
            new_vertices.append(fp)
            local_new_indices.append(new_idx)

            vertex_incident.setdefault(v_curr, []).append((f_idx, k))

            e_key = (min(v_curr, v_next), max(v_curr, v_next))
            edge_map.setdefault(e_key, []).append((f_idx, k, (k + 1) % m))

        face_point_indices.append(local_new_indices)

    new_faces = []

    for local_indices in face_point_indices:
        if len(local_indices) >= 3:
            new_faces.append(list(local_indices))

    for (u, v), inc in edge_map.items():
        if len(inc) == 2:
            (f1, a1, b1), (f2, a2, b2) = inc
            p1_a = face_point_indices[f1][a1]
            p1_b = face_point_indices[f1][b1]
            p2_a = face_point_indices[f2][a2]
            p2_b = face_point_indices[f2][b2]
            if faces[f1][a1] == faces[f2][a2]:
                new_faces.append([p1_a, p1_b, p2_b, p2_a])
            else:
                new_faces.append([p1_a, p1_b, p2_a, p2_b])

    for v_idx, inc_list in vertex_incident.items():
        if len(inc_list) < 3:
            continue
        adj = {item: [] for item in inc_list}
        for i in range(len(inc_list)):
            f1, k1 = inc_list[i]
            face1 = faces[f1]
            m1 = len(face1)
            neighbors1 = {face1[(k1 - 1) % m1], face1[(k1 + 1) % m1]}
            for j in range(i + 1, len(inc_list)):
                f2, k2 = inc_list[j]
                face2 = faces[f2]
                m2 = len(face2)
                neighbors2 = {face2[(k2 - 1) % m2], face2[(k2 + 1) % m2]}
                if neighbors1 & neighbors2:
                    adj[(f1, k1)].append((f2, k2))
                    adj[(f2, k2)].append((f1, k1))

        if all(len(nb) == 2 for nb in adj.values()):
            start = inc_list[0]
            ordered = [start]
            prev = None
            curr = start
            while True:
                nxts = [x for x in adj[curr] if x != prev]
                if not nxts or nxts[0] == start:
                    break
                prev = curr
                curr = nxts[0]
                ordered.append(curr)
            if len(ordered) == len(inc_list):
                new_faces.append([face_point_indices[f][k] for f, k in ordered])

    return new_vertices, new_faces


def build_doo_sabin(vertices, faces, iterations):
    history = [(list(vertices), [list(f) for f in faces])]
    curr_v = list(vertices)
    curr_f = [list(f) for f in faces]
    for _ in range(iterations):
        curr_v, curr_f = doo_sabin_step(curr_v, curr_f)
        history.append((curr_v, curr_f))
    return history


class SurfacesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Построение поверхностей (Безье и Ду-Сабин)")
        self.root.geometry("1160x740")
        self.root.minsize(920, 620)

        self.build_ui()
        self.load_preset()

    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Построение поверхностей: метод Безье и метод Ду-Сабина",
            font=("Times New Roman", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        content = ttk.Frame(main_frame)
        content.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(content, width=300)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        ttk.Label(left, text="Метод построения поверхности:").pack(anchor="w")
        self.algo_var = tk.StringVar(value="Поверхность Безье")
        algo_cb = ttk.Combobox(
            left,
            textvariable=self.algo_var,
            values=["Поверхность Безье", "Поверхность Ду-Сабина"],
            state="readonly"
        )
        algo_cb.pack(fill=tk.X, pady=(2, 8))
        algo_cb.bind("<<ComboboxSelected>>", lambda e: self.load_preset())

        self.input_hint = ttk.Label(left, text="", justify=tk.LEFT)
        self.input_hint.pack(anchor="w")

        self.data_text = tk.Text(left, height=13, font=("Consolas", 9))
        self.data_text.pack(fill=tk.X, pady=(2, 8))

        self.steps_entry = self._add_field(left, "Количество разбиений / итераций:", "12")
        self.yaw_entry = self._add_field(left, "Поворот вокруг Z (°):", "35")
        self.pitch_entry = self._add_field(left, "Наклон по X (°):", "25")

        self.show_orig_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left,
            text="Точки и сетка исходного полигона",
            variable=self.show_orig_var,
            command=self.draw
        ).pack(anchor="w", pady=(4, 0))

        self.show_refined_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left,
            text="Вершины уточнённого полигона",
            variable=self.show_refined_var,
            command=self.draw
        ).pack(anchor="w", pady=(2, 8))

        ttk.Button(left, text="Построить", command=self.draw).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left, text="Загрузить пример сетки", command=self.load_preset).pack(fill=tk.X)

        right = ttk.Frame(content)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            right,
            bg="white",
            highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw())

        self.log_text = tk.Text(right, height=6, font=("Consolas", 9))
        self.log_text.pack(fill=tk.X, pady=(6, 0))

    def _add_field(self, parent, label, default):
        ttk.Label(parent, text=label).pack(anchor="w")
        entry = ttk.Entry(parent)
        entry.insert(0, default)
        entry.pack(fill=tk.X, pady=(1, 6))
        return entry

    def load_preset(self):
        algo = self.algo_var.get()
        self.data_text.delete("1.0", tk.END)

        if algo == "Поверхность Безье":
            self.input_hint.config(
                text="Сетка вершин : x y z):"
            )
            self.data_text.insert(
                "1.0",
                "-2 -2 0; -0.7 -2 1.5; 0.7 -2 1.5; 2 -2 0\n"
                "-2 -0.7 1.5; -0.7 -0.7 3.0; 0.7 -0.7 3.0; 2 -0.7 1.5\n"
                "-2 0.7 1.5; -0.7 0.7 3.0; 0.7 0.7 3.0; 2 0.7 1.5\n"
                "-2 2 0; -0.7 2 1.5; 0.7 2 1.5; 2 2 0"
            )
            self._set_entry(self.steps_entry, "12")
        else:
            self.input_hint.config(
                text="Вершины (x y z) и грани :"
            )
            self.data_text.insert(
                "1.0",
                "-1 -1 -1\n"
                "1 -1 -1\n"
                "1 1 -1\n"
                "-1 1 -1\n"
                "-1 -1 1\n"
                "1 -1 1\n"
                "1 1 1\n"
                "-1 1 1\n"
                "ГРАНИ:\n"
                "0 3 2 1\n"
                "4 5 6 7\n"
                "0 1 5 4\n"
                "2 3 7 6\n"
                "1 2 6 5\n"
                "3 0 4 7"
            )
            self._set_entry(self.steps_entry, "2")

        self.draw()

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def parse_bezier_grid(self):
        grid = []
        for line in self.data_text.get("1.0", tk.END).splitlines():
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
                    raise ValueError("Каждая вершина поверхности Безье должна иметь 3 координаты: x y z")
                row.append((float(parts[0]), float(parts[1]), float(parts[2])))
            if row:
                grid.append(row)

        if len(grid) < 2 or len(grid[0]) < 2:
            raise ValueError("Задайте сетку минимум 2x2.")
        row_len = len(grid[0])
        if any(len(r) != row_len for r in grid):
            raise ValueError("Все строки сетки Безье должны содержать одинаковое число вершин.")
        return grid

    def parse_doo_sabin_mesh(self):
        vertices = []
        faces = []
        reading_faces = False

        for raw_line in self.data_text.get("1.0", tk.END).splitlines():
            line = raw_line.strip().replace(",", ".")
            if not line:
                continue
            if line.upper().startswith("ГРАНИ"):
                reading_faces = True
                continue

            parts = line.split()
            if not reading_faces:
                if len(parts) != 3:
                    raise ValueError("Координаты вершины задаются тремя числами: x y z")
                vertices.append((float(parts[0]), float(parts[1]), float(parts[2])))
            else:
                if len(parts) < 3:
                    raise ValueError("Каждая грань должна содержать минимум 3 индекса вершин.")
                face = [int(p) for p in parts]
                faces.append(face)

        if len(vertices) < 3 or not faces:
            raise ValueError("Укажите минимум 3 вершины и блок ГРАНИ: с гранями.")
        for face in faces:
            for idx in face:
                if idx < 0 or idx >= len(vertices):
                    raise ValueError(f"Индекс вершины {idx} выходит за пределы [0..{len(vertices)-1}].")
        return vertices, faces

    def project_3d(self, x, y, z, yaw_deg, pitch_deg):
        az = math.radians(yaw_deg)
        ax = math.radians(pitch_deg)

        x1 = x * math.cos(az) - y * math.sin(az)
        y1 = x * math.sin(az) + y * math.cos(az)
        z1 = z

        y2 = y1 * math.cos(ax) - z1 * math.sin(ax)
        z2 = y1 * math.sin(ax) + z1 * math.cos(ax)
        return x1, z2

    def make_transformer(self, pts_2d):
        w = max(self.canvas.winfo_width(), 200)
        h = max(self.canvas.winfo_height(), 200)
        pad = 50
        xs = [p[0] for p in pts_2d]
        ys = [p[1] for p in pts_2d]
        dx = max(max(xs) - min(xs), 1e-6)
        dy = max(max(ys) - min(ys), 1e-6)
        scale = min((w - 2 * pad) / dx, (h - 2 * pad) / dy)
        cx = (min(xs) + max(xs)) / 2.0
        cy = (min(ys) + max(ys)) / 2.0
        return lambda pt: (w / 2.0 + (pt[0] - cx) * scale, h / 2.0 - (pt[1] - cy) * scale)

    def draw_polyline(self, pts, color, width=1.5, dash=None):
        if len(pts) >= 2:
            coords = [c for p in pts for c in p]
            self.canvas.create_line(*coords, fill=color, width=width, dash=dash)

    def draw_dots(self, pts, color, r=3.0):
        for x, y in pts:
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="")

    def log(self, text):
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert("1.0", text)

    def draw(self):
        self.canvas.delete("all")
        algo = self.algo_var.get()

        try:
            steps = int(self.steps_entry.get())
            if steps < 1:
                raise ValueError("Количество разбиений / итераций должно быть >= 1.")
            yaw = float(self.yaw_entry.get().replace(",", "."))
            pitch = float(self.pitch_entry.get().replace(",", "."))

            if algo == "Поверхность Безье":
                grid = self.parse_bezier_grid()
                surf = build_bezier_surface(grid, steps)

                p_grid = [[self.project_3d(*pt, yaw, pitch) for pt in row] for row in grid]
                p_surf = [[self.project_3d(*pt, yaw, pitch) for pt in row] for row in surf]
                all_2d = [p for r in p_grid for p in r] + [p for r in p_surf for p in r]
                to_px = self.make_transformer(all_2d)

                s_grid = [[to_px(p) for p in row] for row in p_grid]
                s_surf = [[to_px(p) for p in row] for row in p_surf]

                if self.show_orig_var.get():
                    for r in s_grid:
                        self.draw_polyline(r, "#8aa2be", width=1.2, dash=(4, 3))
                    for c in range(len(s_grid[0])):
                        self.draw_polyline([s_grid[r][c] for r in range(len(s_grid))], "#8aa2be", width=1.2, dash=(4, 3))
                    for r in s_grid:
                        self.draw_dots(r, "#1d4ed8", r=3.5)

                for r in s_surf:
                    self.draw_polyline(r, "#15803d", width=1.5)
                for c in range(len(s_surf[0])):
                    self.draw_polyline([s_surf[r][c] for r in range(len(s_surf))], "#15803d", width=1.5)

                if self.show_refined_var.get():
                    for r in s_surf:
                        self.draw_dots(r, "#d97706", r=2.3)

                self.log(
                    f"Поверхность Безье: сетка контрольных точек {len(grid)}x{len(grid[0])} "
                    f"(степень {len(grid)-1}x{len(grid[0])-1})\n"
                    f"Разбиений: {steps}x{steps} | Всего вершин поверхности: {(steps + 1) ** 2}"
                )

            else:
                verts, faces = self.parse_doo_sabin_mesh()
                iters = min(steps, 5)
                history = build_doo_sabin(verts, faces, iters)

                orig_v, orig_f = history[0]
                ref_v, ref_f = history[-1]

                p_orig = [self.project_3d(*v, yaw, pitch) for v in orig_v]
                p_ref = [self.project_3d(*v, yaw, pitch) for v in ref_v]
                to_px = self.make_transformer(p_orig + p_ref)

                s_orig = [to_px(p) for p in p_orig]
                s_ref = [to_px(p) for p in p_ref]

                if self.show_orig_var.get():
                    for face in orig_f:
                        poly = [s_orig[idx] for idx in face] + [s_orig[face[0]]]
                        self.draw_polyline(poly, "#8aa2be", width=1.2, dash=(4, 3))
                    self.draw_dots(s_orig, "#1d4ed8", r=3.5)

                for face in ref_f:
                    poly = [s_ref[idx] for idx in face] + [s_ref[face[0]]]
                    self.draw_polyline(poly, "#15803d", width=1.5)

                if self.show_refined_var.get():
                    self.draw_dots(s_ref, "#d97706", r=2.8)

                log_lines = [
                    f"Этап {step_idx}: вершин = {len(hv)}, граней = {len(hf)}"
                    for step_idx, (hv, hf) in enumerate(history)
                ]
                if len(history) > 1:
                    sample_pts = [(round(x, 3), round(y, 3), round(z, 3)) for x, y, z in history[1][0][:4]]
                    log_lines.append(f"Первые точки грани этапа 1: {sample_pts}")
                self.log("\n".join(log_lines))

        except ValueError as err:
            messagebox.showerror("Ошибка ввода", str(err))


if __name__ == "__main__":
    root = tk.Tk()
    SurfacesApp(root)
    root.mainloop()
