import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №1 — Вариант 6")
        self.root.geometry("650x550")

        self.image = None
        self.photo = None

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.btn_open = tk.Button(
            btn_frame, 
            text="Открыть фото", 
            command=self.open_image, 
            font=("Arial", 10)
        )
        self.btn_open.pack(side=tk.LEFT, padx=5)

        self.btn_process = tk.Button(
            btn_frame, 
            text="Обработать", 
            command=self.process_image, 
            font=("Arial", 10), 
            state=tk.DISABLED
        )
        self.btn_process.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(
            btn_frame, 
            text="Сохранить", 
            command=self.save_image, 
            font=("Arial", 10), 
            state=tk.DISABLED
        )
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.root, bg="lightgray")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def open_image(self):
        input_file = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp"),
                ("Все файлы", "*.*")
            ]
        )
        if not input_file:
            return

        try:
            self.image = Image.open(input_file).convert("RGB")
            self.display_image()
            self.btn_process.config(state=tk.NORMAL)
            self.btn_save.config(state=tk.DISABLED)
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{error}")

    def display_image(self):
        if self.image is None:
            return

        w, h = self.image.size
        max_w, max_h = 600, 450
        scale = min(max_w / w, max_h / h, 1.0)
        new_w, new_h = int(w * scale), int(h * scale)

        resized_img = self.image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized_img)

        self.canvas.delete("all")
        self.canvas.config(width=new_w, height=new_h)
        self.canvas.create_image(new_w // 2, new_h // 2, anchor=tk.CENTER, image=self.photo)

    def process_image(self):
        if self.image is None:
            return

        try:
            width, height = self.image.size

            # Вариант 6:
            # Левый верхний угол — (0, 0, 127)
            self.image.putpixel((0, 0), (0, 0, 127))
            # Центр верхней строки — (0, 127, 0)
            self.image.putpixel((width // 2, 0), (0, 127, 0))
            # Правый нижний угол — (127, 0, 0)
            self.image.putpixel((width - 1, height - 1), (127, 0, 0))

            self.display_image()
            self.btn_save.config(state=tk.NORMAL)
            messagebox.showinfo("Готово", "Точки успешно поставлены!")

        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось обработать изображение:\n{error}")


    def save_image(self):
            if self.image is None:
                messagebox.showerror("Ошибка", "Нет изображения для сохранения.")
                return

            try:
                output_file = filedialog.asksaveasfilename(
                    title="Сохранить обработанное изображение",
                    defaultextension=".png",
                    filetypes=[
                        ("PNG", "*.png"),
                        ("JPEG", "*.jpg"),
                        ("BMP", "*.bmp"),
                        ("PBM", "*.pbm")
                    ]
                )

                if output_file:
                    if output_file.lower().endswith(".pbm"):
                        pbm_img = self.image.convert("1")
                        pbm_img.save(output_file)
                    else:
                        self.image.save(output_file) 

                    messagebox.showinfo("Успех", f"Изображение успешно сохранено:\n{output_file}")

            except Exception as error:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{error}")

root = tk.Tk()
app = ImageApp(root)
root.mainloop()
