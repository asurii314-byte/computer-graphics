import os
import re
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None

W, H = 900, 620
COLORS = {
    "ЦДА": "#e53935",
    "Брезенхем": "#1e88e5",
    "Целочисленный": "#43a047",
    "Встроенный": "#8e24aa",
}

sgn = lambda val: (val > 0) - (val < 0)

def cda(x1, y1, x2, y2):
    """ЦДА"""
    dx, dy = x2 - x1, y2 - y1
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        return [(round(x1), round(y1))]

    x_inc, y_inc = dx / steps, dy / steps
    x, y = x1, y1
    pts = []
    for _ in range(steps + 1):
        pts.append((round(x), round(y)))
        x += x_inc
        y += y_inc
    return pts


def br_float(x1, y1, x2, y2):
    """Брезенхем"""
    x, y, x2, y2 = round(x1), round(y1), round(x2), round(y2)
    dx, dy = abs(x2 - x), abs(y2 - y)
    sx, sy = sgn(x2 - x), sgn(y2 - y)
    steep = dy > dx

    if steep:
        dx, dy = dy, dx
    if dx == 0:
        return [(x, y)]

    m = dy / dx
    e = m - 0.5
    pts = []

    for _ in range(dx + 1):
        pts.append((x, y))
        if e >= 0:
            if steep:
                x += sx
            else:
                y += sy
            e -= 1.0

        if steep:
            y += sy
        else:
            x += sx
        e += m
    return pts


def br_int(x1, y1, x2, y2):
    """Целочисленный"""
    x, y, x2, y2 = round(x1), round(y1), round(x2), round(y2)
    dx, dy = abs(x2 - x), abs(y2 - y)
    sx, sy = sgn(x2 - x), sgn(y2 - y)
    steep = dy > dx

    if steep:
        dx, dy = dy, dx
    if dx == 0:
        return [(x, y)]

    err = 2 * dy - dx
    pts = []

    for _ in range(dx + 1):
        pts.append((x, y))
        if err >= 0:
            if steep:
                x += sx
            else:
                y += sy
            err -= 2 * dx

        if steep:
            y += sy
        else:
            x += sx
        err += 2 * dy
    return pts

ALG = {
    "ЦДА": cda,
    "Брезенхем": br_float,
    "Целочисленный": br_int,
}

def rasterize_polyline(points, alg):
    pixels = []
    for p1, p2 in zip(points, points[1:]):
        pixels.extend(alg(*p1, *p2))
    return list(dict.fromkeys(pixels))

def svg_read(file_path):
    root = ET.parse(file_path).getroot()
    for elem in root.iter():
        if elem.tag.split("}")[-1] in ("polyline", "polygon") and elem.get("points"):
            raw = [float(c) for c in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", elem.get("points"))]
            if len(raw) != 8:
                raise ValueError("В SVG должно быть 4 вершины (8 координат).")
            return [(raw[i], raw[i + 1]) for i in range(0, 8, 2)]
    raise ValueError("Полилиния не найдена в SVG.")

class App:
    def __init__(self, root):
        self.root = root
        self.points = []
        self.selected_alg = tk.StringVar(value="Все алгоритмы")
        
        self.root.title("Лабораторная №3 — Растеризация")
        self.root.geometry("1200x680")
        self.root.resizable(False, False)

        left = tk.Frame(root, width=250)
        left.pack(side="left", fill="y", padx=10, pady=10)
        left.pack_propagate(False) 

        self.entries = []
        for i in range(4):
            f = tk.Frame(left)
            f.pack(pady=2, fill="x")
            tk.Label(f, text=f"P{i+1}:").pack(side="left")
            ex = tk.Entry(f, width=7)
            ey = tk.Entry(f, width=7)
            ex.pack(side="left", padx=2)
            ey.pack(side="left")
            self.entries.append((ex, ey))

        tk.Button(left, text="Построить", command=self.build).pack(fill="x", pady=5)
        tk.Button(left, text="Очистить", command=self.clear).pack(fill="x")

        tk.OptionMenu(
            left, self.selected_alg,
            "Все алгоритмы", *ALG.keys(), "Встроенный",
            command=lambda _: self.draw()
        ).pack(fill="x", pady=10)

        tk.Button(left, text="Открыть SVG", command=self.open_svg).pack(fill="x", pady=2)
        tk.Button(left, text="Сохранить", command=self.save).pack(fill="x", pady=2)

        self.status = tk.Label(left, text="Введите точки", justify="left", wraplength=230, anchor="w")
        self.status.pack(fill="x", pady=10)

        right = tk.Frame(root)
        right.pack(side="right", fill="both", expand=True)
        self.cv = tk.Canvas(right, bg="white", width=W, height=H)
        self.cv.pack(padx=10, pady=10)

    def build(self):
        try:
            self.points = [
                (float(x.get().replace(",", ".")), float(y.get().replace(",", ".")))
                for x, y in self.entries
            ]
            self.draw()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите правильные числа во все поля.")

    def open_svg(self):
        fp = filedialog.askopenfilename(filetypes=[("SVG файлы", "*.svg")])
        if not fp:
            return
        try:
            self.points = svg_read(fp)
            for (x, y), (ex, ey) in zip(self.points, self.entries):
                ex.delete(0, tk.END)
                ex.insert(0, str(x))
                ey.delete(0, tk.END)
                ey.insert(0, str(y))
            self.draw()
        except Exception as e:
            messagebox.showerror("Ошибка SVG", str(e))

    def draw(self):
        if len(self.points) != 4:
            return
        self.cv.delete("all")

        pts = [(round(x), round(y)) for x, y in self.points]
        mode = self.selected_alg.get()
        active_algs = list(ALG.keys()) + ["Встроенный"] if mode == "Все алгоритмы" else [mode]

        for alg_name in active_algs:
            color = COLORS[alg_name]
            if alg_name == "Встроенный":
                flat_coords = [c for p in pts for c in p]
                self.cv.create_line(flat_coords, fill=color, width=2)
            else:
                pixels = rasterize_polyline(pts, ALG[alg_name])
                for x, y in pixels:
                    if 0 <= x < W and 0 <= y < H:
                        self.cv.create_rectangle(x, y, x + 1, y + 1, fill=color, outline=color)

        for i, (x, y) in enumerate(pts, 1):
            if 0 <= x < W and 0 <= y < H:
                self.cv.create_oval(x - 4, y - 4, x + 4, y + 4, fill="black")
                self.cv.create_text(x + 8, y - 8, text=f"P{i}")

        info = "\n".join(f"P{i+1} = {p}" for i, p in enumerate(self.points))
        self.status.config(text=f"Режим: {mode}\n\n{info}")

    def save(self):
        if not self.points:
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".bmp",
            filetypes=[
                ("BMP", "*.bmp"),
                ("PNG", "*.png"),
                ("SVG", "*.svg"),
                ("PBM", "*.pbm"),
            ]
        )
        if not fp:
            return

        ext = os.path.splitext(fp)[1].lower()
        pts = [(round(x), round(y)) for x, y in self.points]
        mode = self.selected_alg.get()
        active = list(ALG.keys()) + ["Встроенный"] if mode == "Все алгоритмы" else [mode]

        if ext == ".svg":
            lines = []
            for alg_name in active:
                color = COLORS[alg_name]
                if alg_name == "Встроенный":
                    pts_str = " ".join(f"{x},{y}" for x, y in pts)
                    lines.append(f'<polyline points="{pts_str}" stroke="{color}" fill="none" stroke-width="2"/>')
                else:
                    for p1, p2 in zip(pts, pts[1:]):
                        lines.append(f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="{color}"/>')

            svg_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="100%" height="100%" fill="white"/>{"".join(lines)}</svg>'
            with open(fp, "w", encoding="utf-8") as f:
                f.write(svg_str)

        elif ext == ".pbm":
            px = set()
            for a in active:
                if a != "Встроенный":
                    px.update(rasterize_polyline(pts, ALG[a]))

            with open(fp, "w", encoding="ascii") as f:
                f.write(f"P1\n{W} {H}\n")
                for y in range(H):
                    row = ["1" if (x, y) in px else "0" for x in range(W)]
                    f.write(" ".join(row) + "\n")

        elif Image:
            img = Image.new("RGB", (W, H), "white")
            draw = ImageDraw.Draw(img)

            for alg_name in active:
                hex_c = COLORS[alg_name].lstrip("#")
                color_rgb = tuple(int(hex_c[i:i + 2], 16) for i in (0, 2, 4))

                if alg_name == "Встроенный":
                    draw.line(pts, fill=color_rgb, width=2)
                else:
                    for x, y in rasterize_polyline(pts, ALG[alg_name]):
                        if 0 <= x < W and 0 <= y < H:
                            draw.point((x, y), fill=color_rgb)
            img.save(fp)

        messagebox.showinfo("Успех", "Файл успешно сохранен!")

    def clear(self):
        self.points = []
        self.cv.delete("all")
        for ex, ey in self.entries:
            ex.delete(0, tk.END)
            ey.delete(0, tk.END)
        self.status.config(text="Введите точки")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()