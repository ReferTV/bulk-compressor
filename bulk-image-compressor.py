import os
from tkinter import Tk, Label, Button, filedialog
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

def compress_image(input_path, output_path, quality=85):
    with Image.open(input_path) as img:
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(output_path, optimize=True, quality=quality)

def get_file_size(file_path):
    return os.path.getsize(file_path)

def compress_images_in_folder(input_folder, output_folder, quality=85):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    original_sizes = []
    compressed_sizes = []
    savings = []

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            original_size = get_file_size(input_path)
            original_sizes.append(original_size)

            compress_image(input_path, output_path, quality)

            compressed_size = get_file_size(output_path)
            compressed_sizes.append(compressed_size)

            saving = original_size - compressed_size
            savings.append(saving)

    return original_sizes, compressed_sizes, savings

def display_statistics(original_sizes, compressed_sizes, savings):
    total_savings = sum(savings)
    avg_saving = total_savings / len(savings) if savings else 0
    max_saving = max(savings) if savings else 0
    min_saving = min(savings) if savings else 0

    original_total = sum(original_sizes)
    compressed_total = sum(compressed_sizes)
    total_saved_percentage = (total_savings / original_total) * 100 if original_total else 0

    stats = (
        f"Average Data Saved: {avg_saving / 1024:.2f} KB\n"
        f"Maximum Data Saved: {max_saving / 1024:.2f} KB\n"
        f"Minimum Data Saved: {min_saving / 1024:.2f} KB\n"
        f"Total Data Saved: {total_savings / 1024:.2f} KB\n"
        f"Total Original Size: {original_total / 1024:.2f} KB\n"
        f"Total Compressed Size: {compressed_total / 1024:.2f} KB\n"
        f"Percentage of Data Saved: {total_saved_percentage:.2f}%\n"
    )

    return stats

def select_folder():
    input_folder = filedialog.askdirectory(title="Select Folder")
    if input_folder:
        output_folder = os.path.join(input_folder, 'compressed')
        original_sizes, compressed_sizes, savings = compress_images_in_folder(input_folder, output_folder, quality=85)
        stats = display_statistics(original_sizes, compressed_sizes, savings)
        status_label.config(text=f"Images compressed in folder: {output_folder}\n\n{stats}")

def create_gui():
    root = Tk()
    root.title("Image Compression Tool")
    root.geometry("500x400")

    select_button = Button(root, text="Select Folder", command=select_folder, font=("Arial", 12))
    select_button.pack(pady=20)

    global status_label
    status_label = Label(root, text="", justify="left", font=("Arial", 10))
    status_label.pack(pady=20, padx=20, fill="both", expand=True)

    footer_label = Label(root, text="Author: Wiktor Józwiak | Version: 1.0", font=("Arial", 8), anchor="center")
    footer_label.pack(side="bottom", pady=10, fill="x")

    root.mainloop()

if __name__ == "__main__":
    create_gui()
