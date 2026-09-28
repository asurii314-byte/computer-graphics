import math
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageTk


class App:

  def __init__(self, root):
    self.root = root
    self.root.title("Растеризатор")
    self.root.geometry("950x780")

    self.img = None
    self.items = None

    self.methods = {
        "equation": "Уравнение окружности",
        "parametric": "Параметрическое",
        "bresenham": "Алгоритм Брезенхема",
        "builtin": "Встроенные средства",
    }

    top = ttk.Frame(root, padding=10)
    top.pack(side=tk.TOP, fill=tk.X)

    box = ttk.LabelFrame(top, text="Параметры", padding=5)
    box.pack(side=tk.LEFT, padx=(0, 10))

    ttk.Label(box, text="X0:").pack(side=tk.LEFT, padx=(0, 2))
    self.x_entry = ttk.Entry(box, width=6)
    self.x_entry.insert(0, "0")
    self.x_entry.pack(side=tk.LEFT, padx=(0, 8))

    ttk.Label(box, text="Y0:").pack(side=tk.LEFT, padx=(0, 2))
    self.y_entry = ttk.Entry(box, width=6)
    self.y_entry.insert(0, "0")
    self.y_entry.pack(side=tk.LEFT, padx=(0, 8))

    ttk.Label(box, text="R:").pack(side=tk.LEFT, padx=(0, 2))
    self.r_entry = ttk.Entry(box, width=6)
    self.r_entry.insert(0, "120")
    self.r_entry.pack(side=tk.LEFT, padx=(0, 8))

    self.status = ttk.Label(top, text="Трикветр метод: не выбран")
    self.status.pack(side=tk.LEFT, padx=(10, 0))

    m_frame = ttk.Frame(root, padding=(10, 0))
    m_frame.pack(fill=tk.X, pady=(0, 5))
    for key, name in self.methods.items():
      ttk.Button(
          m_frame, text=name, command=lambda m=key: self.draw_scene(m)
      ).pack(side=tk.LEFT, padx=3)

    t_frame = ttk.Frame(root, padding=(10, 0))
    t_frame.pack(fill=tk.X, pady=(0, 5))

    ttk.Button(t_frame, text="Загрузить SVG", command=self.load_svg).pack(
        side=tk.LEFT, padx=3
    )
    ttk.Button(t_frame, text="Экспорт в SVG", command=self.save_svg).pack(
        side=tk.LEFT, padx=3
    )
    ttk.Button(t_frame, text="Сохранить PBM", command=self.save_pbm).pack(
        side=tk.LEFT, padx=3
    )
    ttk.Button(t_frame, text="Сохранить BMP", command=self.save_bmp).pack(
        side=tk.LEFT, padx=3
    )
    ttk.Button(t_frame, text="Очистить", command=self.clear_all).pack(
        side=tk.LEFT, padx=3
    )

    ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X)

    c_frame = ttk.Frame(root)
    c_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    self.canvas = tk.Canvas(
        c_frame,
        width=800,
        height=600,
        bg="white",
        highlightthickness=1,
        highlightbackground="#888",
    )
    self.canvas.pack(pady=15)


  def get_inputs(self):
    try:
      x0 = float(self.x_entry.get())
      y0 = float(self.y_entry.get())
      r = float(self.r_entry.get())
      if r <= 0:
        messagebox.showerror("Ошибка", "Радиус должен быть больше 0.")
        return None
      return x0, y0, r
    except ValueError:
      messagebox.showerror("Ошибка", "Введите числа.")
      return None

  def get_geometry(self):
    params = self.get_inputs()
    if not params:
      return None

    x0, y0, r = params
    d = r / math.sqrt(3)

    c1 = (x0, y0 - d)
    c2 = (x0 + r / 2, y0 + d / 2)
    c3 = (x0 - r / 2, y0 + d / 2)

    arcs = [
        (c1, r, 0.0, math.pi),
        (c2, r, 2 * math.pi / 3, 5 * math.pi / 3),
        (c3, r, -2 * math.pi / 3, math.pi / 3),
    ]
    circle = ((x0, y0), d * 1.15, 0.0, 2 * math.pi)

    return {"x0": x0, "y0": y0, "r": r, "curves": arcs + [circle]}

  def prepare_canvas(self):
    w, h = 800, 600
    self.img = Image.new("RGB", (w, h), "white")
    x0 = float(self.x_entry.get() or 0)
    y0 = float(self.y_entry.get() or 0)
    self.center_x = w / 2 + x0
    self.center_y = h / 2 - y0

  def to_pixel(self, x, y):
    px = int(round(self.center_x + x))
    py = int(round(self.center_y - y))
    return px, py

  @staticmethod
  def is_angle_valid(angle, start, end):
    norm = lambda a: a % (2 * math.pi)
    s, e, a = norm(start), norm(end), norm(angle)
    if abs(end - start - 2 * math.pi) < 1e-4:
      return True
    return s <= a <= e if s <= e else (a >= s or a <= e)

  #растеризация прямых
  def line_eq(self, draw, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
      draw.rectangle([x1 - 1, y1 - 1, x1 + 1, y1 + 1], fill="black")
      return

    if abs(dx) >= abs(dy):
      k = dy / dx
      b = y1 - k * x1
      start_x, end_x = sorted([x1, x2])
      for x in range(int(start_x), int(end_x) + 1):
        y = int(round(k * x + b))
        draw.rectangle([x - 1, y - 1, x + 1, y + 1], fill="black")
    else:
      m = dx / dy
      c = x1 - m * y1
      start_y, end_y = sorted([y1, y2])
      for y in range(int(start_y), int(end_y) + 1):
        x = int(round(m * y + c))
        draw.rectangle([x - 1, y - 1, x + 1, y + 1], fill="black")

  def line_param(self, draw, x1, y1, x2, y2):
    steps = max(int(math.hypot(x2 - x1, y2 - y1)), 1)
    pts = []
    for i in range(steps + 1):
      t = i / steps
      px = int(round(x1 + t * (x2 - x1)))
      py = int(round(y1 + t * (y2 - y1)))
      pts.append((px, py))

    for i in range(len(pts) - 1):
      draw.line([pts[i], pts[i + 1]], fill="black", width=3)

  def line_bresenham(self, draw, x1, y1, x2, y2):
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    x, y = x1, y1
    while True:
      draw.rectangle([x - 1, y - 1, x + 1, y + 1], fill="black")
      if x == x2 and y == y2:
        break
      e2 = 2 * err
      if e2 > -dy:
        err -= dy
        x += sx
      if e2 < dx:
        err += dx
        y += sy

  #растеризация дуг
  def arc_eq(self, draw, cx, cy, r, start, end):
    r_int = int(round(r))
    for dx in range(-r_int, r_int + 1):
      val = r**2 - dx**2
      if val >= 0:
        dy = math.sqrt(val)
        for sign in (1, -1):
          wy = cy + sign * dy
          wx = cx + dx
          angle = math.atan2(wy - cy, wx - cx)
          if self.is_angle_valid(angle, start, end):
            px, py = self.to_pixel(wx, wy)
            draw.rectangle([px - 1, py - 1, px + 1, py + 1], fill="black")

  def arc_param(self, draw, cx, cy, r, start, end):
    step = 1.0 / max(r, 1)
    count = int((end - start) / step) + 1
    pts = []
    for i in range(count):
      t = start + i * step
      wx = cx + r * math.cos(t)
      wy = cy + r * math.sin(t)
      pts.append(self.to_pixel(wx, wy))

    for i in range(len(pts) - 1):
      draw.line([pts[i], pts[i + 1]], fill="black", width=3)

  def arc_bresenham(self, draw, cx, cy, r, start, end):
    x = 0
    y = int(round(r))
    d = 3 - 2 * y

    def put_pixel(wx, wy):
      angle = math.atan2(wy - cy, wx - cx)
      if self.is_angle_valid(angle, start, end):
        px, py = self.to_pixel(wx, wy)
        draw.rectangle([px - 1, py - 1, px + 1, py + 1], fill="black")

    def draw_octants(px, py):
      put_pixel(cx + px, cy + py)
      put_pixel(cx - px, cy + py)
      put_pixel(cx + px, cy - py)
      put_pixel(cx - px, cy - py)
      put_pixel(cx + py, cy + px)
      put_pixel(cx - py, cy + px)
      put_pixel(cx + py, cy - px)
      put_pixel(cx - py, cy - px)

    while y >= x:
      draw_octants(x, y)
      x += 1
      if d > 0:
        y -= 1
        d = d + 4 * (x - y) + 10
      else:
        d = d + 4 * x + 6


  def draw_scene(self, method):
    self.prepare_canvas()
    draw = ImageDraw.Draw(self.img)

    ru_name = self.methods.get(method, method)
    self.status.config(text=f"Трикветр метод: {ru_name}")

    if self.items is not None:
      for item in self.items:
        if item["type"] == "line":
          p1 = (int(round(item["x1"])), int(round(item["y1"])))
          p2 = (int(round(item["x2"])), int(round(item["y2"])))

          if method == "builtin":
            draw.line([p1, p2], fill="black", width=3)
          elif method == "parametric":
            self.line_param(draw, p1[0], p1[1], p2[0], p2[1])
          elif method == "equation":
            self.line_eq(draw, p1[0], p1[1], p2[0], p2[1])
          elif method == "bresenham":
            self.line_bresenham(draw, p1[0], p1[1], p2[0], p2[1])

        elif item["type"] == "circle":
          cx, cy, r = item["cx"], item["cy"], item["r"]
          box = (cx - r, cy - r, cx + r, cy + r)
          if method == "builtin":
            draw.ellipse(box, outline="black", width=3)
          else:
            wx, wy = cx - 400, 300 - cy
            if method == "parametric":
              self.arc_param(draw, wx, wy, r, 0, 2 * math.pi)
            elif method == "equation":
              self.arc_eq(draw, wx, wy, r, 0, 2 * math.pi)
            elif method == "bresenham":
              self.arc_bresenham(draw, wx, wy, r, 0, 2 * math.pi)

    else:
      geom = self.get_geometry()
      if not geom:
        return

      for (cx, cy), r, start, end in geom["curves"]:
        if method == "builtin":
          px, py = self.to_pixel(cx, cy)
          box = (px - r, py - r, px + r, py + r)
          if abs(end - start - 2 * math.pi) < 1e-4:
            draw.ellipse(box, outline="black", width=3)
          else:
            draw.arc(
                box,
                start=-math.degrees(end),
                end=-math.degrees(start),
                fill="black",
                width=3,
            )
        elif method == "parametric":
          self.arc_param(draw, cx, cy, r, start, end)
        elif method == "equation":
          self.arc_eq(draw, cx, cy, r, start, end)
        elif method == "bresenham":
          self.arc_bresenham(draw, cx, cy, r, start, end)

    self.update_canvas()

  def load_svg(self):
    path = filedialog.askopenfilename(
        filetypes=[("SVG файлы", "*.svg"), ("Все файлы", "*.*")]
    )
    if not path:
      return

    try:
      tree = ET.parse(path)
      root = tree.getroot()
      items = []

      for elem in root.iter():
        tag = elem.tag.split("}")[-1]

        if tag == "line":
          items.append({
              "type": "line",
              "x1": float(elem.attrib.get("x1", 0)),
              "y1": float(elem.attrib.get("y1", 0)),
              "x2": float(elem.attrib.get("x2", 0)),
              "y2": float(elem.attrib.get("y2", 0)),
          })
        elif tag == "circle":
          items.append({
              "type": "circle",
              "cx": float(elem.attrib.get("cx", 0)),
              "cy": float(elem.attrib.get("cy", 0)),
              "r": float(elem.attrib.get("r", 0)),
          })
        elif tag == "path":
          d = elem.attrib.get("d", "")
          tokens = re.findall(r"[a-zA-Z]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
          i = 0
          cx, cy, sx, sy = 0.0, 0.0, 0.0, 0.0
          cmd = ""
          while i < len(tokens):
            t = tokens[i]
            if t.isalpha():
              cmd = t
              i += 1
            else:
              if cmd == "M":
                cmd = "L"

            if cmd in ("M", "m"):
              cx = float(tokens[i]) + (cx if cmd == "m" else 0)
              cy = float(tokens[i + 1]) + (cy if cmd == "m" else 0)
              sx, sy = cx, cy
              i += 2
            elif cmd in ("L", "l"):
              nx = float(tokens[i]) + (cx if cmd == "l" else 0)
              ny = float(tokens[i + 1]) + (cy if cmd == "l" else 0)
              items.append(
                  {"type": "line", "x1": cx, "y1": cy, "x2": nx, "y2": ny}
              )
              cx, cy = nx, ny
              i += 2
            elif cmd in ("Z", "z"):
              if cx != sx or cy != sy:
                items.append(
                    {"type": "line", "x1": cx, "y1": cy, "x2": sx, "y2": sy}
                )
                cx, cy = sx, sy
            else:
              i += 1

      if not items:
        messagebox.showwarning("Внимание", "SVG не содержит элементов.")
        return

      self.items = items
      messagebox.showinfo("Успех", f"Загружено элементов: {len(items)}")
      self.draw_scene("builtin")

    except Exception as err:
      messagebox.showerror("Ошибка SVG", f"Не удалось прочитать SVG:\n{err}")

  def save_svg(self):
    geom = self.get_geometry()
    if not geom:
      return

    path = filedialog.asksaveasfilename(
        defaultextension=".svg",
        filetypes=[("SVG файлы", "*.svg"), ("Все файлы", "*.*")],
    )
    if not path:
      return

    w, h = 800, 600
    cx0, cy0 = w / 2 + geom["x0"], h / 2 - geom["y0"]

    with open(path, "w", encoding="utf-8") as f:
      f.write(
          f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">\n'
      )
      f.write('  <g stroke="black" stroke-width="2" fill="none">\n')

      for (cx, cy), r, start, end in geom["curves"]:
        if abs(end - start - 2 * math.pi) < 1e-4:
          scx, scy = cx0 + cx, cy0 - cy
          f.write(f'    <circle cx="{scx:.2f}" cy="{scy:.2f}" r="{r:.2f}"/>\n')
        else:
          step = 0.04
          count = int((end - start) / step) + 1
          pts = []
          for i in range(count):
            t = start + i * step
            wx = cx + r * math.cos(t)
            wy = cy + r * math.sin(t)
            pts.append((cx0 + wx, cy0 - wy))

          for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            f.write(
                f'    <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}"'
                f' y2="{y2:.2f}"/>\n'
            )

      f.write("  </g>\n</svg>\n")

    messagebox.showinfo("Успех", f"SVG сохранен:\n{path}")

  def save_pbm(self):
    if self.img is None:
      messagebox.showwarning("Внимание", "Сначала постройте изображение.")
      return

    path = filedialog.asksaveasfilename(
        defaultextension=".pbm",
        filetypes=[("PBM", "*.pbm"), ("Все файлы", "*.*")],
    )
    if not path:
      return

    try:
      gray = self.img.convert("L")
      w, h = gray.size
      pixels = gray.load()

      with open(path, "w", encoding="ascii") as f:
        f.write(f"P1\n# Created by Triquetra Rasterizer (ASCII PBM)\n{w} {h}\n")
        buffer = []
        for y in range(h):
          for x in range(w):
            val = "1" if pixels[x, y] < 128 else "0"
            buffer.append(val)
            if len(buffer) >= 35:
              f.write(" ".join(buffer) + "\n")
              buffer = []
        if buffer:
          f.write(" ".join(buffer) + "\n")

      messagebox.showinfo("Успех", f"PBM файл сохранен:\n{path}")
    except Exception as err:
      messagebox.showerror("Ошибка", f"Не удалось сохранить PBM:\n{err}")

  def save_bmp(self):
    if self.img is None:
      messagebox.showwarning("Внимание", "Сначала постройте изображение.")
      return
    path = filedialog.asksaveasfilename(
        defaultextension=".bmp", filetypes=[("BMP", "*.bmp")]
    )
    if path:
      self.img.save(path, "BMP")
      messagebox.showinfo("Успех", "BMP сохранен.")

  def update_canvas(self):
    if self.img is None:
      return
    self.photo = ImageTk.PhotoImage(self.img)
    self.canvas.delete("all")
    self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

  def clear_all(self):
    self.img = None
    self.items = None
    self.canvas.delete("all")
    self.status.config(text="Трикветр метод: не выбран")


if __name__ == "__main__":
  root = tk.Tk()
  app = App(root)
  root.mainloop()