import math
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа — Вариант 6")
        self.root.geometry("1000x620")

        self.source_img = None
        self.result_img = None
        self.photo_source = None
        self.photo_result = None

        self.setup_ui()

    def setup_ui(self):
        top_bar = tk.Frame(self.root, bg="#f0f0f0", height=80)
        top_bar.pack(fill=tk.X, padx=10, pady=5)
        top_bar.pack_propagate(False)

        tk.Label(top_bar, text="Width 1", bg="#f0f0f0").place(x=10, y=10)
        self.input_w1 = tk.Entry(top_bar, width=6)
        self.input_w1.insert(0, "300")
        self.input_w1.place(x=65, y=10)

        tk.Label(top_bar, text="Height 1", bg="#f0f0f0").place(x=10, y=40)
        self.input_h1 = tk.Entry(top_bar, width=6)
        self.input_h1.insert(0, "300")
        self.input_h1.place(x=65, y=40)

        tk.Button(top_bar, text="Создать 1", command=self.create_canvas, width=10).place(x=120, y=8)
        tk.Button(top_bar, text="Открыть 2", command=self.open_file, width=10).place(x=210, y=8)

        self.label_w2 = tk.Label(top_bar, text="Width 2: -", bg="#f0f0f0")
        self.label_w2.place(x=210, y=38)

        self.label_h2 = tk.Label(top_bar, text="Height 2: -", bg="#f0f0f0")
        self.label_h2.place(x=210, y=55)

        tk.Label(top_bar, text="R", bg="#f0f0f0").place(x=320, y=10)
        self.input_r = tk.Entry(top_bar, width=5)
        self.input_r.insert(0, "40")
        self.input_r.place(x=340, y=10)

        tk.Button(top_bar, text="Перенести", command=self.copy_circle, width=11).place(x=420, y=8)
        tk.Button(top_bar, text="Координаты", command=self.draw_axes, width=12).place(x=520, y=8)
        tk.Button(top_bar, text="ln(x)", command=self.draw_graph, width=12).place(x=520, y=40)
        tk.Button(top_bar, text="Сохранить", command=self.save_file, width=11).place(x=630, y=8)

        bottom_bar = tk.Frame(self.root)
        bottom_bar.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_box = tk.Frame(bottom_bar, bd=2, relief="groove")
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(
            left_box,
            text="Новое изображение (Результат)",
            font=("Arial", 10, "bold")
        ).pack(side=tk.TOP, pady=4)

        self.canvas_result = tk.Canvas(left_box, bg="#fcfcfc")
        self.canvas_result.pack(fill=tk.BOTH, expand=True)

        right_box = tk.Frame(bottom_bar, bd=2, relief="groove")
        right_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(
            right_box,
            text="Исходное изображение",
            font=("Arial", 10, "bold")
        ).pack(side=tk.TOP, pady=4)

        self.canvas_source = tk.Canvas(right_box, bg="#fcfcfc")
        self.canvas_source.pack(fill=tk.BOTH, expand=True)

    def create_canvas(self):
        try:
            w = int(self.input_w1.get())
            h = int(self.input_h1.get())
            if w <= 0 or h <= 0:
                raise ValueError
            self.result_img = Image.new("RGB", (w, h), "white")
            self.show_result()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные размеры Width 1 и Height 1.")

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp"), ("Все файлы", "*.*")]
        )
        if not path:
            return
        try:
            self.source_img = Image.open(path).convert("RGB")
            w, h = self.source_img.size
            self.label_w2.config(text=f"Width 2:  {w}")
            self.label_h2.config(text=f"Height 2: {h}")
            self.show_source()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def copy_circle(self):
        if self.result_img is None or self.source_img is None:
            messagebox.showerror("Ошибка", "Сначала создайте холст (Создать 1) и откройте файл (Открыть 2).")
            return

        try:
            radius = int(self.input_r.get())
            if radius <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте значение радиуса R.")
            return

        w_res, h_res = self.result_img.size
        w_src, h_src = self.source_img.size

        center_src_x = radius
        center_src_y = h_src // 2

        center_res_x = w_res // 2 - radius
        center_res_y = h_res // 2 - radius

        radius_sq = radius * radius

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius_sq:
                    src_x = center_src_x + dx
                    src_y = center_src_y + dy

                    res_x = center_res_x + dx
                    res_y = center_res_y + dy

                    if 0 <= src_x < w_src and 0 <= src_y < h_src:
                        if 0 <= res_x < w_res and 0 <= res_y < h_res:
                            pixel_color = self.source_img.getpixel((src_x, src_y))
                            self.result_img.putpixel((res_x, res_y), pixel_color)

        self.show_result()

    def draw_axes(self):
        if self.result_img is None:
            messagebox.showerror("Ошибка", "Сначала создайте новое изображение.")
            return

        drawer = ImageDraw.Draw(self.result_img)
        w, h = self.result_img.size

        center_x, center_y = w // 2, h // 2

        drawer.line((center_x, h - 10, center_x, 10), fill="black", width=1)
        drawer.line((center_x - 4, 18, center_x, 10), fill="black", width=1)
        drawer.line((center_x + 4, 18, center_x, 10), fill="black", width=1)

        drawer.line((10, center_y, w - 10, center_y), fill="black", width=1)
        drawer.line((w - 18, center_y - 4, w - 10, center_y), fill="black", width=1)
        drawer.line((w - 18, center_y + 4, w - 10, center_y), fill="black", width=1)

        for x in range(center_x, w - 10, 20):
            drawer.line((x, center_y - 2, x, center_y + 2), fill="black")
        for x in range(center_x, 10, -20):
            drawer.line((x, center_y - 2, x, center_y + 2), fill="black")

        for y in range(center_y, h - 10, 20):
            drawer.line((center_x - 2, y, center_x + 2, y), fill="black")
        for y in range(center_y, 10, -20):
            drawer.line((center_x - 2, y, center_x + 2, y), fill="black")

        drawer.text((center_x - 12, center_y + 4), "0", fill="black")
        drawer.text((w - 15, center_y + 8), "x", fill="black")
        drawer.text((center_x + 8, 8), "y", fill="black")

        self.show_result()

    def draw_graph(self):
        if self.result_img is None:
            messagebox.showerror("Ошибка", "Сначала создайте новое изображение.")
            return

        drawer = ImageDraw.Draw(self.result_img)
        w, h = self.result_img.size

        center_x, center_y = w // 2, h // 2
        scale_x = 20.0
        scale_y = 20.0

        drawer.text((center_x + 30, 20), "y = ln(x)", fill="blue")

        points = []
        for px in range(center_x + 1, w - 10):
            x = (px - center_x) / scale_x
            if x > 0:
                y = math.log(x)
                py = center_y - int(y * scale_y)
                if 0 <= py < h:
                    points.append((px, py))

        if len(points) > 1:
            drawer.line(points, fill="blue", width=2)

        self.show_result()

    def show_result(self):
        if self.result_img is None:
            return
        copy_img = self.result_img.copy()
        scale = min(420 / copy_img.width, 420 / copy_img.height, 1)
        new_size = (int(copy_img.width * scale), int(copy_img.height * scale))
        copy_img = copy_img.resize(new_size, Image.Resampling.LANCZOS)

        self.photo_result = ImageTk.PhotoImage(copy_img)
        self.canvas_result.delete("all")
        self.canvas_result.create_image(
            self.canvas_result.winfo_width() // 2 or 210,
            self.canvas_result.winfo_height() // 2 or 210,
            image=self.photo_result,
        )

    def show_source(self):
        if self.source_img is None:
            return
        copy_img = self.source_img.copy()
        scale = min(420 / copy_img.width, 420 / copy_img.height, 1)
        new_size = (int(copy_img.width * scale), int(copy_img.height * scale))
        copy_img = copy_img.resize(new_size, Image.Resampling.LANCZOS)

        self.photo_source = ImageTk.PhotoImage(copy_img)
        self.canvas_source.delete("all")
        self.canvas_source.create_image(
            self.canvas_source.winfo_width() // 2 or 210,
            self.canvas_source.winfo_height() // 2 or 210,
            image=self.photo_source,
        )

    def save_file(self):
        if self.result_img is None:
            messagebox.showerror("Ошибка", "Нет изображения для сохранения.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")],
        )
        if path:
            self.result_img.save(path)
            messagebox.showinfo("Успех", "Изображение успешно сохранено.")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()