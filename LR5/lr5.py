import os
import struct
import zlib
import tkinter as tk
from tkinter import filedialog, messagebox


def clamp(v):
    return max(0, min(255, int(round(v))))


def load_bmp(filename):
    with open(filename, "rb") as f:
        data = f.read()
    if data[:2] != b"BM":
        raise ValueError("Не BMP файл")

    offset = struct.unpack_from("<I", data, 10)[0]
    w, h_signed = struct.unpack_from("<ii", data, 18)
    bpp = struct.unpack_from("<H", data, 28)[0]

    w, h = abs(w), abs(h_signed)
    bpp_bytes = bpp // 8
    row_size = ((w * bpp_bytes + 3) // 4) * 4
    top_down = h_signed < 0

    pixels = []
    for y in range(h):
        sy = y if top_down else h - 1 - y
        r_start = offset + sy * row_size
        row = []
        for x in range(w):
            p = r_start + x * bpp_bytes
            row.append((data[p + 2], data[p + 1], data[p])) 
        pixels.append(row)
    return w, h, pixels


def load_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".bmp":
        return load_bmp(filename)

    img = tk.PhotoImage(file=filename)
    w, h = img.width(), img.height()
    pixels = []
    for y in range(h):
        row = []
        for x in range(w):
            c = img.get(x, y)
            row.append(c if isinstance(c, tuple) else tuple(int(c.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)))
        pixels.append(row)
    return w, h, pixels


def save_bmp(filename, w, h, pixels):
    row_pad = (4 - (w * 3) % 4) % 4
    img_size = (w * 3 + row_pad) * h
    with open(filename, "wb") as f:
        f.write(b"BM" + struct.pack("<IHHI", 54 + img_size, 0, 0, 54))
        f.write(struct.pack("<IIIHHIIIIII", 40, w, h, 1, 24, 0, img_size, 2835, 2835, 0, 0))
        for y in range(h - 1, -1, -1):
            for r, g, b in pixels[y]:
                f.write(bytes((clamp(b), clamp(g), clamp(r))))
            f.write(b"\x00" * row_pad)


def save_ppm(filename, w, h, pixels):
    with open(filename, "wb") as f:
        f.write(f"P6\n{w} {h}\n255\n".encode("ascii"))
        for row in pixels:
            for r, g, b in row:
                f.write(bytes((clamp(r), clamp(g), clamp(b))))


def save_pgm(filename, w, h, pixels):
    with open(filename, "wb") as f:
        f.write(f"P5\n{w} {h}\n255\n".encode("ascii"))
        for row in pixels:
            for r, g, b in row:
                gray = clamp(0.299 * r + 0.587 * g + 0.114 * b)
                f.write(bytes((gray,)))


def save_pbm(filename, w, h, pixels):
    row_bytes = (w + 7) // 8
    with open(filename, "wb") as f:
        f.write(f"P4\n{w} {h}\n".encode("ascii"))
        for y in range(h):
            row = bytearray(row_bytes)
            for x in range(w):
                r, g, b = pixels[y][x]
                if (r + g + b) / 3 < 128:  
                    row[x // 8] |= 1 << (7 - (x % 8))
            f.write(row)


def save_png(filename, w, h, pixels):
    def chunk(kind, payload):
        crc = zlib.crc32(kind)
        crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)

    raw = bytearray()
    for row in pixels:
        raw.append(0)  # Filter type: None
        for r, g, b in row:
            raw.extend((clamp(r), clamp(g), clamp(b)))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    compressed = zlib.compress(bytes(raw))

    with open(filename, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", compressed))
        f.write(chunk(b"IEND", b""))


def save_image(filename, w, h, pixels):
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".bmp":
        save_bmp(filename, w, h, pixels)
    elif ext == ".png":
        save_png(filename, w, h, pixels)
    elif ext == ".pbm":
        save_pbm(filename, w, h, pixels)
    elif ext == ".pgm":
        save_pgm(filename, w, h, pixels)
    else:
        save_ppm(filename, w, h, pixels)


def negative_below_50(pixels):
    return [
        [
            (255 - r, 255 - g, 255 - b) if max(r, g, b) < 127.5 else (r, g, b)
            for r, g, b in row
        ]
        for row in pixels
    ]


def darken_base(base, overlay):
    h = min(len(base), len(overlay))
    w = min(len(base[0]), len(overlay[0]))

    def blend(c1, c2):
        if c2 == 0:
            return 0
        return clamp((1.0 - (1.0 - c1 / 255.0) / (c2 / 255.0)) * 255.0)

    result = [
        [
            tuple(blend(c1, c2) for c1, c2 in zip(base[y][x], overlay[y][x]))
            for x in range(w)
        ]
        for y in range(h)
    ]
    return w, h, result


class Lab5App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №5 — Попиксельные преобразования")
        self.root.geometry("900x700")

        self.base = None
        self.overlay = None
        self.processed = None
        self.result = None
        self.preview_refs = {}

        self.build_ui()

    def build_ui(self):
        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=10, pady=5)

        buttons = [
            ("1. Открыть основу", self.open_base),
            ("2. Открыть верхнее", self.open_overlay),
            ("3. Негатив < 50%", self.process_image),
            ("4. Затемнение основы", self.apply_overlay),
            ("Сохранить обработку", lambda: self.save_data(self.processed, "обработанное изображение")),
            ("Сохранить результат", lambda: self.save_data(self.result, "результат наложения")),
        ]
        for text, cmd in buttons:
            tk.Button(controls, text=text, command=cmd).pack(side="left", padx=3)

        self.status = tk.StringVar(value="Загрузите два изображения.")
        tk.Label(self.root, textvariable=self.status, anchor="w", font=("Arial", 10)).pack(fill="x", padx=12, pady=5)

        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        self.panels = []
        titles = ("Исходная основа", "Верхнее изображение", "После негатива", "Результат наложения")

        for i, title in enumerate(titles):
            frame = tk.LabelFrame(main, text=title, font=("Arial", 10, "bold"))
            frame.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")

            canvas = tk.Canvas(frame, bg="#202020", highlightthickness=0)
            canvas.pack(fill="both", expand=True, padx=6, pady=6)
            self.panels.append(canvas)

            main.grid_rowconfigure(i // 2, weight=1)
            main.grid_columnconfigure(i % 2, weight=1)

    def set_status(self, text):
        self.status.set(text)
        self.root.update_idletasks()

    def ask_file(self, title, is_save=False):
        if is_save:
            return filedialog.asksaveasfilename(
                title=title,
                defaultextension=".bmp",
                filetypes=[
                    ("BMP", "*.bmp"),
                    ("PNG", "*.png"),
                    ("Netpbm", "*.pbm *.pgm *.ppm"),
                    ("PPM", "*.ppm"),
                ],
            )
        return filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("Изображения", "*.png *.gif *.pbm *.pgm *.ppm *.bmp"),
                ("PNG", "*.png"),
                ("GIF", "*.gif"),
                ("BMP", "*.bmp"),
                ("Netpbm", "*.pbm *.pgm *.ppm"),
                ("Все файлы", "*.*"),
            ],
        )

    def open_base(self):
        fn = self.ask_file("Выберите изображение-основу")
        if fn:
            try:
                self.base = load_image(fn)
                self.processed = self.result = None
                self.show_panel(0, self.base[2])
                self.show_panel(2, None)
                self.show_panel(3, None)
                self.set_status(f"Основа загружена: {self.base[0]} × {self.base[1]}")
            except Exception as e:
                messagebox.showerror("Ошибка загрузки", str(e))

    def open_overlay(self):
        fn = self.ask_file("Выберите верхнее изображение")
        if fn:
            try:
                self.overlay = load_image(fn)
                self.result = None
                self.show_panel(1, self.overlay[2])
                self.show_panel(3, None)
                self.set_status(f"Верхнее изображение загружено: {self.overlay[0]} × {self.overlay[1]}")
            except Exception as e:
                messagebox.showerror("Ошибка загрузки", str(e))

    def process_image(self):
        if not self.base:
            return messagebox.showwarning("Нет изображения", "Сначала загрузите основу.")
        w, h, pixels = self.base
        self.processed = (w, h, negative_below_50(pixels))
        self.show_panel(2, self.processed[2])
        self.set_status("Готово: точки с V < 0.5 преобразованы в негатив.")

    def apply_overlay(self):
        if not self.processed or not self.overlay:
            return messagebox.showwarning("Ошибка", "Загрузите оба изображения и выполните обработку!")
        w, h, res_pixels = darken_base(self.processed[2], self.overlay[2])
        self.result = (w, h, res_pixels)
        self.show_panel(3, res_pixels)
        self.set_status(f"Готово: затемнение основы ({w} × {h}).")

    def save_data(self, image_data, title):
        if not image_data:
            return messagebox.showwarning("Нет результата", "Сначала выполните обработку.")
        fn = self.ask_file(f"Сохранить: {title}", is_save=True)
        if fn:
            try:
                save_image(fn, *image_data)
                self.set_status(f"Файл сохранён: {fn}")
                messagebox.showinfo("Сохранение", "Изображение успешно сохранено.")
            except Exception as e:
                messagebox.showerror("Ошибка сохранения", str(e))

    def show_panel(self, idx, pixels):
        canvas = self.panels[idx]
        canvas.delete("all")

        if not pixels:
            canvas.create_text(180, 100, text="Нет изображения", fill="white", font=("Arial", 12))
            return

        h, w = len(pixels), len(pixels[0])
        scale = min(1.0, 370 / w, 200 / h)
        pw, ph = max(1, int(w * scale)), max(1, int(h * scale))

        ppm_header = f"P6\n{pw} {ph}\n255\n".encode("ascii")
        ppm_body = bytearray()
        for py in range(ph):
            sy = min(h - 1, int(py / scale))
            for px in range(pw):
                sx = min(w - 1, int(px / scale))
                r, g, b = pixels[sy][sx]
                ppm_body.extend((clamp(r), clamp(g), clamp(b)))

        photo = tk.PhotoImage(data=ppm_header + ppm_body)
        self.preview_refs[idx] = photo

        cw = canvas.winfo_width() or 370
        ch = canvas.winfo_height() or 200
        canvas.create_image(cw // 2, ch // 2, image=photo, anchor="center")
        canvas.create_text(8, 8, text=f"{w} × {h}", fill="white", anchor="nw", font=("Arial", 9))


if __name__ == "__main__":
    root = tk.Tk()
    Lab5App(root)
    root.mainloop()