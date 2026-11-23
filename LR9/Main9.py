import tkinter as tk
from tkinter import ttk, messagebox

LEFT = 1
TOP = 2
BOTTOM = 4
RIGHT = 8

def get_code(x, y, xmin, ymin, xmax, ymax):
    code = 0

    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT

    if y > ymax:
        code |= TOP
    elif y < ymin:
        code |= BOTTOM

    return code

def simple_clipping(x1, y1, x2, y2,
                    xmin, ymin, xmax, ymax):

    borders = ["left", "right", "bottom", "top"]

    for border in borders:

        code1 = get_code(x1, y1, xmin, ymin, xmax, ymax)
        code2 = get_code(x2, y2, xmin, ymin, xmax, ymax)

        if code1 == 0 and code2 == 0:
            return x1, y1, x2, y2

        if code1 & code2:
            return None

        if border == "left":
            if x1 < xmin or x2 < xmin:
                if x2 == x1:
                    return None

                t = (xmin - x1) / (x2 - x1)
                x = xmin
                y = y1 + t * (y2 - y1)

                if x1 < xmin:
                    x1, y1 = x, y
                else:
                    x2, y2 = x, y

        elif border == "right":
            if x1 > xmax or x2 > xmax:
                if x2 == x1:
                    return None

                t = (xmax - x1) / (x2 - x1)
                x = xmax
                y = y1 + t * (y2 - y1)

                if x1 > xmax:
                    x1, y1 = x, y
                else:
                    x2, y2 = x, y

        elif border == "bottom":
            if y1 < ymin or y2 < ymin:
                if y2 == y1:
                    return None

                t = (ymin - y1) / (y2 - y1)
                x = x1 + t * (x2 - x1)
                y = ymin

                if y1 < ymin:
                    x1, y1 = x, y
                else:
                    x2, y2 = x, y

        else:
            if y1 > ymax or y2 > ymax:
                if y2 == y1:
                    return None

                t = (ymax - y1) / (y2 - y1)
                x = x1 + t * (x2 - x1)
                y = ymax

                if y1 > ymax:
                    x1, y1 = x, y
                else:
                    x2, y2 = x, y

    code1 = get_code(x1, y1, xmin, ymin, xmax, ymax)
    code2 = get_code(x2, y2, xmin, ymin, xmax, ymax)

    if code1 == 0 and code2 == 0:
        return x1, y1, x2, y2

    return None

def cohen_sutherland(x1, y1, x2, y2,
                     xmin, ymin, xmax, ymax):

    while True:

        code1 = get_code(x1, y1, xmin, ymin, xmax, ymax)
        code2 = get_code(x2, y2, xmin, ymin, xmax, ymax)

        if code1 == 0 and code2 == 0:
            return x1, y1, x2, y2

        if code1 & code2:
            return None

        if code1 != 0:
            code_out = code1
        else:
            code_out = code2

        if code_out & TOP:
            if y2 == y1:
                return None

            x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
            y = ymax

        elif code_out & BOTTOM:
            if y2 == y1:
                return None

            x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
            y = ymin

        elif code_out & RIGHT:
            if x2 == x1:
                return None

            y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
            x = xmax

        else:
            if x2 == x1:
                return None

            y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
            x = xmin

        if code_out == code1:
            x1, y1 = x, y
        else:
            x2, y2 = x, y

def midpoint_clipping(x1, y1, x2, y2,
                      xmin, ymin, xmax, ymax):

    dx = x2 - x1
    dy = y2 - y1

    length = (dx ** 2 + dy ** 2) ** 0.5

    if length == 0:
        if get_code(x1, y1, xmin, ymin, xmax, ymax) == 0:
            return x1, y1, x2, y2
        return None

    epsilon = max(length / 10000, 0.0001)

    stack = [(0.0, 1.0, 0)]
    visible_parts = []

    while stack:

        t1, t2, depth = stack.pop()

        ax = x1 + dx * t1
        ay = y1 + dy * t1

        bx = x1 + dx * t2
        by = y1 + dy * t2

        code1 = get_code(ax, ay, xmin, ymin, xmax, ymax)
        code2 = get_code(bx, by, xmin, ymin, xmax, ymax)

        if code1 == 0 and code2 == 0:
            visible_parts.append((t1, t2))
            continue

        if code1 & code2:
            continue

        if length * (t2 - t1) <= epsilon or depth >= 45:

            tm = (t1 + t2) / 2

            mx = x1 + dx * tm
            my = y1 + dy * tm

            if get_code(mx, my, xmin, ymin, xmax, ymax) == 0:
                visible_parts.append((t1, t2))

            continue

        tm = (t1 + t2) / 2

        stack.append((tm, t2, depth + 1))
        stack.append((t1, tm, depth + 1))

    if not visible_parts:
        return None

    t_min = min(part[0] for part in visible_parts)
    t_max = max(part[1] for part in visible_parts)

    return (
        x1 + dx * t_min,
        y1 + dy * t_min,
        x1 + dx * t_max,
        y1 + dy * t_max
    )

class ClippingApp:

    def __init__(self, root):

        self.root = root

        self.root.title("Отсечение отрезков")
        self.root.geometry("1050x750")
        self.root.minsize(850, 600)

        self.current_data = None
        self.results = []

        self.create_interface()

    def create_interface(self):

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        settings_frame = ttk.LabelFrame(
            main_frame,
            text="Координаты окна отсечения",
            padding=10
        )
        settings_frame.pack(fill=tk.X)

        ttk.Label(settings_frame, text="Xmin:").grid(
            row=0, column=0, padx=5, pady=5
        )

        self.xmin_entry = ttk.Entry(settings_frame, width=12)
        self.xmin_entry.insert(0, "100")
        self.xmin_entry.grid(row=0, column=1, padx=5)

        ttk.Label(settings_frame, text="Ymin:").grid(
            row=0, column=2, padx=5
        )

        self.ymin_entry = ttk.Entry(settings_frame, width=12)
        self.ymin_entry.insert(0, "100")
        self.ymin_entry.grid(row=0, column=3, padx=5)

        ttk.Label(settings_frame, text="Xmax:").grid(
            row=1, column=0, padx=5, pady=5
        )

        self.xmax_entry = ttk.Entry(settings_frame, width=12)
        self.xmax_entry.insert(0, "400")
        self.xmax_entry.grid(row=1, column=1, padx=5)

        ttk.Label(settings_frame, text="Ymax:").grid(
            row=1, column=2, padx=5
        )

        self.ymax_entry = ttk.Entry(settings_frame, width=12)
        self.ymax_entry.insert(0, "300")
        self.ymax_entry.grid(row=1, column=3, padx=5)

        input_frame = ttk.LabelFrame(
            main_frame,
            text="Координаты отрезков",
            padding=10
        )
        input_frame.pack(fill=tk.X, pady=10)

        ttk.Label(
            input_frame,
            text="Введите координаты: x1 y1 x2 y2"
        ).pack(anchor="w")

        self.lines_text = tk.Text(
            input_frame,
            height=6,
            font=("Arial", 10)
        )
        self.lines_text.pack(fill=tk.X, pady=5)

        self.lines_text.insert(
            "1.0",
            "50 150 450 250\n"
            "150 150 350 250\n"
            "200 50 200 350\n"
            "50 50 80 80\n"
            "450 100 450 300\n"
            "50 350 450 50"
        )

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(
            control_frame,
            text="Алгоритм:"
        ).pack(side=tk.LEFT, padx=5)

        self.algorithm = tk.StringVar(
            value="Простой способ"
        )

        algorithm_box = ttk.Combobox(
            control_frame,
            textvariable=self.algorithm,
            values=[
                "Простой способ",
                "Коэна-Сазерленда",
                "Разбиение средней точкой"
            ],
            state="readonly",
            width=30
        )
        algorithm_box.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Построить и отсечь",
            command=self.run_clipping
        ).pack(side=tk.LEFT, padx=10)

        ttk.Button(
            control_frame,
            text="Очистить",
            command=self.clear_canvas
        ).pack(side=tk.LEFT, padx=5)

        # Область рисования
        self.canvas = tk.Canvas(
            main_frame,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=10)

        # Обозначения цветов
        legend = ttk.Frame(main_frame)
        legend.pack(fill=tk.X)

        ttk.Label(
            legend,
            text="Красный пунктир — исходные отрезки"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            legend,
            text="Зелёный — видимая часть"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            legend,
            text="Синий — окно отсечения"
        ).pack(side=tk.LEFT, padx=5)

        self.canvas.bind(
            "<Configure>",
            lambda event: self.redraw()
        )

    def read_data(self):

        try:

            xmin = float(self.xmin_entry.get().replace(",", "."))
            ymin = float(self.ymin_entry.get().replace(",", "."))
            xmax = float(self.xmax_entry.get().replace(",", "."))
            ymax = float(self.ymax_entry.get().replace(",", "."))

            if xmin >= xmax or ymin >= ymax:
                raise ValueError(
                    "Левая и нижняя границы должны быть меньше правой и верхней."
                )

            segments = []

            lines = self.lines_text.get(
                "1.0", tk.END
            ).splitlines()

            for number, line in enumerate(lines, start=1):

                line = line.strip()

                if not line:
                    continue

                parts = line.replace(",", ".").split()

                if len(parts) != 4:
                    raise ValueError(
                        f"Строка {number}: введите четыре числа."
                    )

                x1, y1, x2, y2 = map(float, parts)

                segments.append((x1, y1, x2, y2))

            if not segments:
                raise ValueError("Введите хотя бы один отрезок.")

            return xmin, ymin, xmax, ymax, segments

        except ValueError as error:

            messagebox.showerror("Ошибка ввода", str(error))
            return None

    def run_clipping(self):

        data = self.read_data()

        if data is None:
            return

        xmin, ymin, xmax, ymax, segments = data

        self.current_data = data
        self.results = []

        if self.algorithm.get() == "Простой способ":
            function = simple_clipping

        elif self.algorithm.get() == "Коэна-Сазерленда":
            function = cohen_sutherland

        else:
            function = midpoint_clipping

        for segment in segments:

            result = function(
                *segment,
                xmin, ymin, xmax, ymax
            )

            self.results.append(result)

        self.draw_scene(
            xmin, ymin, xmax, ymax,
            segments, self.results
        )

        visible = sum(
            result is not None for result in self.results
        )

        messagebox.showinfo(
            "Результат",
            f"Всего отрезков: {len(segments)}\n"
            f"Видимых: {visible}\n"
            f"Удалено полностью: {len(segments) - visible}"
        )

    def clear_canvas(self):

        self.canvas.delete("all")
        self.current_data = None
        self.results = []

    def redraw(self):

        if self.current_data is not None:

            xmin, ymin, xmax, ymax, segments = self.current_data

            self.draw_scene(
                xmin, ymin, xmax, ymax,
                segments, self.results
            )

    def draw_scene(self, xmin, ymin, xmax, ymax,
                   segments, results):

        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        all_x = [xmin, xmax]
        all_y = [ymin, ymax]

        for x1, y1, x2, y2 in segments:
            all_x.extend([x1, x2])
            all_y.extend([y1, y2])

        min_x = min(all_x)
        max_x = max(all_x)

        min_y = min(all_y)
        max_y = max(all_y)

        range_x = max(max_x - min_x, 1)
        range_y = max(max_y - min_y, 1)

        margin = 40

        scale = min(
            (width - 2 * margin) / range_x,
            (height - 2 * margin) / range_y
        )

        def to_canvas(x, y):

            canvas_x = margin + (x - min_x) * scale
            canvas_y = height - margin - (y - min_y) * scale

            return canvas_x, canvas_y

        for x1, y1, x2, y2 in segments:

            a = to_canvas(x1, y1)
            b = to_canvas(x2, y2)

            self.canvas.create_line(
                a[0], a[1],
                b[0], b[1],
                fill="red",
                width=2,
                dash=(6, 4)
            )

        left_top = to_canvas(xmin, ymax)
        right_bottom = to_canvas(xmax, ymin)

        self.canvas.create_rectangle(
            left_top[0], left_top[1],
            right_bottom[0], right_bottom[1],
            outline="blue",
            width=3
        )

        for result in results:

            if result is not None:

                x1, y1, x2, y2 = result

                a = to_canvas(x1, y1)
                b = to_canvas(x2, y2)

                self.canvas.create_line(
                    a[0], a[1],
                    b[0], b[1],
                    fill="green",
                    width=4
                )

                self.canvas.create_oval(
                    a[0] - 3, a[1] - 3,
                    a[0] + 3, a[1] + 3,
                    fill="green",
                    outline=""
                )

                self.canvas.create_oval(
                    b[0] - 3, b[1] - 3,
                    b[0] + 3, b[1] + 3,
                    fill="green",
                    outline=""
                )

if __name__ == "__main__":

    root = tk.Tk()

    app = ClippingApp(root)

    root.mainloop()

