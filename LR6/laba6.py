import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np

SUPPORTED_EXTS = [
    '.png', '.jpg', '.jpeg', '.bmp', '.ppm', '.pbm'
]

FILETYPES = [
    ('Все поддерживаемые', ' '.join(f'*{e}' for e in SUPPORTED_EXTS)),
    ('PNG', '*.png'),
    ('JPEG', '*.jpg *.jpeg'),
    ('BMP', '*.bmp'),
    ('PPM/PGM/PBM', '*.ppm *.pgm *.pbm'),
    ('Все файлы', '*.*'),
]

def read_image(path):
    img = Image.open(path).convert('RGBA')
    bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    return np.array(bg.convert('RGB'), dtype=np.uint8)

def save_image(path, arr):
    img = Image.fromarray(arr.astype(np.uint8), mode='RGB')
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        img.save(path, quality=95, subsampling=0)
    else:
        img.save(path)

def affine_direct(src, angle=30.0, dx=20, dy=10):
    h, w, _ = src.shape
    dst = np.full_like(src, 255)

    cx, cy = w / 2.0, h / 2.0
    rad = np.radians(angle)
    cos_a, sin_a = np.cos(rad), np.sin(rad)

    ii, jj = np.meshgrid(np.arange(w), np.arange(h))

    xp = cx + (ii - cx - dx) * cos_a + (jj - cy - dy) * sin_a
    yp = cy - (ii - cx - dx) * sin_a + (jj - cy - dy) * cos_a

    xi = np.round(xp).astype(np.int32)
    yi = np.round(yp).astype(np.int32)

    mask = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    dst[mask] = src[yi[mask], xi[mask]]
    return dst

def affine_inverse(src, angle=30.0, dx=20, dy=10):

    h, w, _ = src.shape
    dst = np.full_like(src, 255)

    cx, cy = w / 2.0, h / 2.0

    rad = np.radians(-angle)
    cos_a, sin_a = np.cos(rad), np.sin(rad)
    inv_dx, inv_dy = -dx, -dy

    ii, jj = np.meshgrid(np.arange(w), np.arange(h))

    xp = cx + (ii - cx - inv_dx) * cos_a + (jj - cy - inv_dy) * sin_a
    yp = cy - (ii - cx - inv_dx) * sin_a + (jj - cy - inv_dy) * cos_a

    xi = np.round(xp).astype(np.int32)
    yi = np.round(yp).astype(np.int32)

    mask = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    dst[mask] = src[yi[mask], xi[mask]]

    return dst

def func_transform(src):

    h, w, _ = src.shape
    dst = np.full_like(src, 255)

    cx = w / 2.0
    scale_k = w / 6.0
    scale_sx = w / 15.0

    ii, jj = np.meshgrid(np.arange(w), np.arange(h))

    xp = cx + scale_sx * np.sinh((ii - cx) / scale_k)
    yp = jj.astype(np.float64)

    xi = np.round(xp).astype(np.int32)
    yi = np.round(yp).astype(np.int32)

    mask = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    dst[mask] = src[yi[mask], xi[mask]]
    return dst

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Преображение")

        self.original = None
        self.affine = None
        self.restored = None
        self.func = None
        self.name = None

        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(top, text='Загрузить изображение', command=self.load).pack(side=tk.LEFT, padx=3)
        tk.Button(top, text='Аффинное', command=self.do_affine).pack(side=tk.LEFT, padx=3)
        tk.Button(top, text='Обратное аффинное', command=self.do_affine_inverse).pack(side=tk.LEFT, padx=3)
        tk.Button(top, text='Функциональное', command=self.do_func).pack(side=tk.LEFT, padx=3)

        tk.Label(top, text='Угол (°):').pack(side=tk.LEFT, padx=(10, 2))
        self.e_angle = tk.Entry(top, width=6)
        self.e_angle.insert(0, '30.0')
        self.e_angle.pack(side=tk.LEFT)

        tk.Label(top, text='dx:').pack(side=tk.LEFT, padx=(10, 2))
        self.e_dx = tk.Entry(top, width=6)
        self.e_dx.insert(0, '20')
        self.e_dx.pack(side=tk.LEFT)

        tk.Label(top, text='dy:').pack(side=tk.LEFT, padx=(10, 2))
        self.e_dy = tk.Entry(top, width=6)
        self.e_dy.insert(0, '10')
        self.e_dy.pack(side=tk.LEFT)

        bottom = tk.Frame(self.root)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        tk.Button(bottom, text='Сохранить аффинное',
                  command=lambda: self.save(self.affine, 'affine')).pack(side=tk.LEFT, padx=3)
        tk.Button(bottom, text='Сохранить обратное',
                  command=lambda: self.save(self.restored, 'restored')).pack(side=tk.LEFT, padx=3)
        tk.Button(bottom, text='Сохранить функциональное',
                  command=lambda: self.save(self.func, 'func')).pack(side=tk.LEFT, padx=3)

        img_frame = tk.Frame(self.root)
        img_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.labels = {}
        titles = [
            ('orig', 'Исходное'),
            ('affine', 'Аффинное (Поворот + Сдвиг)'),
            ('restored', 'Обратное аффинное'),
            ('func', 'Функциональное (asinh)'),
        ]
        for idx, (key, title) in enumerate(titles):
            f = tk.LabelFrame(img_frame, text=title, width=350, height=350)
            f.grid(row=idx // 2, column=idx % 2, padx=5, pady=5, sticky='nsew')
            f.grid_propagate(False)
            lbl = tk.Label(f)
            lbl.pack(fill=tk.BOTH, expand=True)
            self.labels[key] = lbl

        img_frame.rowconfigure(0, weight=1)
        img_frame.rowconfigure(1, weight=1)
        img_frame.columnconfigure(0, weight=1)
        img_frame.columnconfigure(1, weight=1)

    def _show(self, key, arr):
        h, w, _ = arr.shape
        scale = min(340 / w, 340 / h, 1.0)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        pil = Image.fromarray(arr).resize((nw, nh), Image.NEAREST)
        tkimg = ImageTk.PhotoImage(pil)
        lbl = self.labels[key]
        lbl.configure(image=tkimg)
        lbl.image = tkimg

    def _get_params(self):
        try:
            angle = float(self.e_angle.get())
            dx = int(self.e_dx.get())
            dy = int(self.e_dy.get())
            return angle, dx, dy
        except ValueError:
            messagebox.showerror('Ошибка', 'Угол должен быть числом, а dx и dy — целыми числами.')
            return None

    def load(self):
        path = filedialog.askopenfilename(title='Выберите изображение', filetypes=FILETYPES)
        if not path:
            return
        try:
            self.original = read_image(path)
            self.name = path
            self._show('orig', self.original)
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))

    def do_affine(self):
        if self.original is None:
            messagebox.showwarning('Внимание', 'Сначала загрузите изображение')
            return
        params = self._get_params()
        if params is None:
            return
        angle, dx, dy = params
        self.affine = affine_direct(self.original, angle=angle, dx=dx, dy=dy)
        self._show('affine', self.affine)

    def do_affine_inverse(self):
        if self.affine is None:
            messagebox.showwarning('Внимание', 'Сначала выполните прямое аффинное')
            return
        params = self._get_params()
        if params is None:
            return
        angle, dx, dy = params
        self.restored = affine_inverse(self.affine, angle=angle, dx=dx, dy=dy)
        self._show('restored', self.restored)

    def do_func(self):
        if self.original is None:
            messagebox.showwarning('Внимание', 'Сначала загрузите изображение')
            return
        self.func = func_transform(self.original)
        self._show('func', self.func)

    def save(self, arr, suffix):
        if arr is None:
            messagebox.showwarning('Внимание', 'Нет результата для сохранения')
            return
        base = os.path.splitext(os.path.basename(self.name))[0] if self.name else 'result'
        path = filedialog.asksaveasfilename(
            title='Сохранить изображение',
            initialfile=f'{base}_{suffix}.png',
            defaultextension='.png',
            filetypes=FILETYPES
        )
        if not path:
            return
        try:
            save_image(path, arr)
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось сохранить:\n{e}')


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('800x820')
    app = App(root)
    root.mainloop()