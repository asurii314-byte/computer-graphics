import numpy as np
from PIL import Image, ImageTk
from scipy.ndimage import convolve, gaussian_filter

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def apply_lpf(img: np.ndarray) -> np.ndarray:

    kernel = np.ones((3, 3), dtype=np.float64) / 9.0
    img_f = img.astype(np.float64)
    blurred = np.zeros_like(img_f)

    for c in range(img.shape[2]):
        blurred[:, :, c] = convolve(img_f[:, :, c], kernel, mode='nearest')

    diff = img_f - blurred
    out = np.abs(diff) * 4.0
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_hpf(img: np.ndarray) -> np.ndarray:

    h, w, c = img.shape
    img_f = img.astype(np.float64)
    out = np.zeros_like(img_f)
    mid = w // 2

    laplace_kernel = np.array([
        [-1.0, -1.0, -1.0],
        [-1.0,  8.0, -1.0],
        [-1.0, -1.0, -1.0]
    ], dtype=np.float64)

    # Левая половина: Лаплас
    for c_idx in range(c):
        left = img_f[:, :mid, c_idx]
        out[:, :mid, c_idx] = convolve(left, laplace_kernel, mode='nearest')

    # Правая половина: LoG
    for c_idx in range(c):
        right = img_f[:, mid:, c_idx]
        smoothed = gaussian_filter(right, sigma=1.0)
        out[:, mid:, c_idx] = convolve(smoothed, laplace_kernel, mode='nearest')

    out = np.abs(out)
    return np.clip(out, 0, 255).astype(np.uint8)

class FilterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Фильтрация изображений")
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)

        self.img_orig = None
        self.img_lpf = None
        self.img_hpf = None

        top_panel = ttk.Frame(root, padding=5)
        top_panel.pack(side=tk.TOP, fill=tk.X)

        f_open = ttk.Frame(top_panel)
        f_open.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Button(f_open, text="Открыть", width=14, command=self.open_image).pack(side=tk.LEFT)

        f_lpf = ttk.Frame(top_panel)
        f_lpf.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Button(f_lpf, text="ФНЧ (Исходное − ФНЧ №1)", width=60, command=self.run_lpf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(f_lpf, text="Сохранить", width=12, command=self.save_lpf_img).pack(side=tk.LEFT)

        f_hpf = ttk.Frame(top_panel)
        f_hpf.pack(side=tk.LEFT)
        ttk.Button(f_hpf, text="ФВЧ (Лаплас | Лапласиан гауссиана)", width=60, command=self.run_hpf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(f_hpf, text="Сохранить", width=12, command=self.save_hpf_img).pack(side=tk.LEFT)

        main_area = ttk.Frame(root, padding=5)
        main_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.label_orig = self.create_panel(main_area, 0, "Исходное")
        self.label_lpf = self.create_panel(main_area, 1, "ФНЧ (Исходное − ФНЧ №1)")
        self.label_hpf = self.create_panel(main_area, 2, "ФВЧ (Слева: Лаплас | Справа: Лапласиан гауссиана)")

        for i in range(3):
            main_area.columnconfigure(i, weight=1, minsize=200)
        main_area.rowconfigure(0, weight=1)

        self.root.update_idletasks()

    def create_panel(self, parent, col: int, title: str) -> tk.Label:
        frame = ttk.LabelFrame(parent, text=title, padding=2)
        frame.grid(row=0, column=col, sticky="nsew", padx=2, pady=2)

        lbl = ttk.Label(frame, anchor=tk.CENTER)
        lbl.pack(fill=tk.BOTH, expand=True)
        return lbl

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"), ("Все файлы", "*.*")]
        )
        if not path:
            return

        try:
            pil_img = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        self.img_orig = np.array(pil_img)
        self.img_lpf = None
        self.img_hpf = None

        self.show_image(self.label_orig, pil_img)
        self.show_image(self.label_lpf, None)
        self.show_image(self.label_hpf, None)

    def show_image(self, label: tk.Label, pil_img):
        if pil_img is None:
            label.config(image="", text="")
            label.image = None
            return

        self.root.update_idletasks()

        w = label.winfo_width()
        h = label.winfo_height()
        if w <= 1:
            w = 380
        if h <= 1:
            h = 550

        iw, ih = pil_img.size
        scale = min(w / iw, h / ih)
        new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
        resized = pil_img.resize(new_size, Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(resized)
        label.config(image=tk_img, text="")
        label.image = tk_img

    def run_lpf(self):
        if self.img_orig is None:
            messagebox.showwarning("Внимание", "Сначала откройте изображение.")
            return

        self.img_lpf = apply_lpf(self.img_orig)
        self.show_image(self.label_lpf, Image.fromarray(self.img_lpf))

    def run_hpf(self):
        if self.img_orig is None:
            messagebox.showwarning("Внимание", "Сначала откройте изображение.")
            return

        self.img_hpf = apply_hpf(self.img_orig)
        self.show_image(self.label_hpf, Image.fromarray(self.img_hpf))

    def save_lpf_img(self):
        if self.img_lpf is None:
            messagebox.showwarning("Внимание", "Сначала обработайте ФНЧ.")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить результат ФНЧ",
            defaultextension=".png",
            initialfile="lpf_result.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")]
        )
        if not path:
            return
        try:
            Image.fromarray(self.img_lpf).save(path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def save_hpf_img(self):
        if self.img_hpf is None:
            messagebox.showwarning("Внимание", "Сначала обработайте ФВЧ.")
            return
        path = filedialog.asksaveasfilename(
            title="Сохранить результат ФВЧ",
            defaultextension=".png",
            initialfile="hpf_result.png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")]
        )
        if not path:
            return
        try:
            Image.fromarray(self.img_hpf).save(path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")


def main():
    root = tk.Tk()
    FilterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()