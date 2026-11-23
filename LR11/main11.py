import math
import tkinter as tk
from tkinter import ttk, messagebox

def get_tetrahedron():
    vertices = [
        (1.0, 1.0, 1.0),
        (1.0, -1.0, -1.0),
        (-1.0, 1.0, -1.0),
        (-1.0, -1.0, 1.0),
    ]
    edges = [
        (0, 1), (0, 2), (0, 3),
        (1, 2), (1, 3), (2, 3)
    ]
    return vertices, edges


def get_dodecahedron():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    inv_phi = 1.0 / phi

    vertices = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                vertices.append((sx, sy, sz))

    for s1 in (-1.0, 1.0):
        for s2 in (-1.0, 1.0):
            vertices.append((0.0, s1 * inv_phi, s2 * phi))
            vertices.append((s1 * inv_phi, s2 * phi, 0.0))
            vertices.append((s1 * phi, 0.0, s2 * inv_phi))

    target_len = 2.0 / phi
    edges = []
    n = len(vertices)
    for i in range(n):
        for j in range(i + 1, n):
            dx = vertices[i][0] - vertices[j][0]
            dy = vertices[i][1] - vertices[j][1]
            dz = vertices[i][2] - vertices[j][2]
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if abs(dist - target_len) < 1e-4:
                edges.append((i, j))

    return vertices, edges

def rotate_3d(x, y, z, ax_deg, ay_deg, az_deg):
    ax = math.radians(ax_deg)
    ay = math.radians(ay_deg)
    az = math.radians(az_deg)

    y1 = y * math.cos(ax) - z * math.sin(ax)
    z1 = y * math.sin(ax) + z * math.cos(ax)
    x1 = x

    x2 = x1 * math.cos(ay) + z1 * math.sin(ay)
    z2 = -x1 * math.sin(ay) + z1 * math.cos(ay)
    y2 = y1

    x3 = x2 * math.cos(az) - y2 * math.sin(az)
    y3 = x2 * math.sin(az) + y2 * math.cos(az)
    z3 = z2

    return x3, y3, z3

def project_point(x, y, z, proj_type, rho, d):
    if proj_type == "Центральная проекция":
        zv = z + rho
        if zv <= 0.1:
            zv = 0.1
        xp = (d * x) / zv
        yp = (d * y) / zv
        return xp, yp
    else:
        return x, y


class ProjectiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Проективные преобразования")
        self.root.geometry("1120x720")
        self.root.minsize(900, 600)

        self.build_ui()
        self.draw_scene()

    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Проективные преобразования (Тетраэдр и Додекаэдр)",
            font=("Times New Roman", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        content = ttk.Frame(main_frame)
        content.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(content, width=270)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)

        ttk.Label(left, text="Платоново тело:").pack(anchor="w")
        self.shape_var = tk.StringVar(value="Додекаэдр")
        shape_cb = ttk.Combobox(
            left,
            textvariable=self.shape_var,
            values=["Тетраэдр", "Додекаэдр"],
            state="readonly"
        )
        shape_cb.pack(fill=tk.X, pady=(2, 8))
        shape_cb.bind("<<ComboboxSelected>>", lambda e: self.draw_scene())

        ttk.Label(left, text="Тип проекции:").pack(anchor="w")
        self.proj_var = tk.StringVar(value="Центральная проекция")
        proj_cb = ttk.Combobox(
            left,
            textvariable=self.proj_var,
            values=["Центральная проекция", "Ортогональная проекция"],
            state="readonly"
        )
        proj_cb.pack(fill=tk.X, pady=(2, 8))
        proj_cb.bind("<<ComboboxSelected>>", lambda e: self.draw_scene())

        self.ax_entry = self._add_field(left, "Угол поворота вокруг X (°):", "20")
        self.ay_entry = self._add_field(left, "Угол поворота вокруг Y (°):", "30")
        self.az_entry = self._add_field(left, "Угол поворота вокруг Z (°):", "10")
        self.rho_entry = self._add_field(left, "Расстояние до объекта ρ:", "5.0")
        self.d_entry = self._add_field(left, "Расстояние до экрана d:", "3.0")

        self.show_labels_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left,
            text="Подписывать вершины",
            variable=self.show_labels_var,
            command=self.draw_scene
        ).pack(anchor="w", pady=(4, 8))

        ttk.Button(left, text="Построить", command=self.draw_scene).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(left, text="Сбросить углы", command=self.reset_params).pack(fill=tk.X)

        right = ttk.Frame(content)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            right,
            bg="white",
            highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_scene())

        self.info_label = ttk.Label(right, text="", font=("Consolas", 9))
        self.info_label.pack(anchor="w", pady=(6, 0))

    def _add_field(self, parent, label, default):
        ttk.Label(parent, text=label).pack(anchor="w")
        entry = ttk.Entry(parent)
        entry.insert(0, default)
        entry.pack(fill=tk.X, pady=(1, 6))
        return entry

    def reset_params(self):
        for entry, val in [
            (self.ax_entry, "20"),
            (self.ay_entry, "30"),
            (self.az_entry, "10"),
            (self.rho_entry, "5.0"),
            (self.d_entry, "3.0"),
        ]:
            entry.delete(0, tk.END)
            entry.insert(0, val)
        self.draw_scene()

    def draw_scene(self):
        self.canvas.delete("all")

        try:
            ax = float(self.ax_entry.get().replace(",", "."))
            ay = float(self.ay_entry.get().replace(",", "."))
            az = float(self.az_entry.get().replace(",", "."))
            rho = float(self.rho_entry.get().replace(",", "."))
            d = float(self.d_entry.get().replace(",", "."))

            if rho <= 1.8:
                raise ValueError("Расстояние ρ должно быть больше 1.8, чтобы камера не попала внутрь фигуры.")
            if d <= 0:
                raise ValueError("Расстояние до проекционной плоскости d должно быть > 0.")

            shape = self.shape_var.get()
            proj_type = self.proj_var.get()

            if shape == "Тетраэдр":
                vertices, edges = get_tetrahedron()
            else:
                vertices, edges = get_dodecahedron()

            projected = []
            for vx, vy, vz in vertices:
                rx, ry, rz = rotate_3d(vx, vy, vz, ax, ay, az)
                px, py = project_point(rx, ry, rz, proj_type, rho, d)
                projected.append((px, py))

            w = max(self.canvas.winfo_width(), 200)
            h = max(self.canvas.winfo_height(), 200)
            scale = min(w, h) * 0.22

            screen_pts = [
                (w / 2.0 + px * scale, h / 2.0 - py * scale)
                for px, py in projected
            ]

            for i, j in edges:
                x1, y1 = screen_pts[i]
                x2, y2 = screen_pts[j]
                self.canvas.create_line(x1, y1, x2, y2, fill="#1d4ed8", width=2)

            for idx, (sx, sy) in enumerate(screen_pts):
                self.canvas.create_oval(
                    sx - 3.5, sy - 3.5, sx + 3.5, sy + 3.5,
                    fill="#dc2626", outline="black", width=1
                )
                if self.show_labels_var.get():
                    self.canvas.create_text(
                        sx + 7, sy - 7,
                        text=f"V{idx}",
                        font=("Segoe UI", 8),
                        fill="#111827",
                        anchor="w"
                    )

            self.info_label.config(
                text=f"Фигура: {shape} (вершин: {len(vertices)}, рёбер: {len(edges)}) | "
                     f"Проекция: {proj_type}  Поворот: ({ax}°, {ay}°, {az}°)"
            )

        except ValueError as err:
            messagebox.showerror("Ошибка ввода", str(err))


if __name__ == "__main__":
    root = tk.Tk()
    ProjectiveApp(root)
    root.mainloop()