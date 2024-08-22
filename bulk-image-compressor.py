import os
import logging
from tkinter import Tk, Label, Button, filedialog, Checkbutton, IntVar, Scale
from PIL import Image, ImageFile
from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import resize
from concurrent.futures import ThreadPoolExecutor

ImageFile.LOAD_TRUNCATED_IMAGES = True

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_metadata_from_image(image):
    data = list(image.getdata())
    clean_image = Image.new(image.mode, image.size)
    clean_image.putdata(data)
    return clean_image

def resize_image(image, target_size=(1920, 1080)):
    image.thumbnail(target_size, Image.Resampling.LANCZOS)
    return image

def compress_image(input_path, output_path, quality=85, target_size=(1920, 1080), convert_to_webp=False):
    try:
        with Image.open(input_path) as img:
            img = remove_metadata_from_image(img)
            img = resize_image(img, target_size)
            if convert_to_webp:
                output_path = os.path.splitext(output_path)[0] + ".webp"
                img.save(output_path, 'WEBP', quality=quality)
            else:
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert('RGB')
                output_path = os.path.splitext(output_path)[0] + ".jpg"
                img.save(output_path, 'JPEG', optimize=True, quality=quality)
    except Exception as e:
        logging.error(f"Error compressing image: {e}")
        raise

def compress_video(input_path, output_path, target_bitrate='2000k'):
    try:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input video file does not exist: {input_path}")

        target_resolution = (1280, 720)
        clip = VideoFileClip(input_path)

        if clip.size[1] > target_resolution[1]:
            resized_clip = resize(clip, height=target_resolution[1])
        else:
            resized_clip = clip

        output_path = os.path.splitext(output_path)[0] + ".mp4"

        resized_clip.write_videofile(
            output_path,
            bitrate=target_bitrate,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='slow'
        )

    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error compressing video: {e}")
        raise

def get_file_size(file_path):
    return os.path.getsize(file_path)

def process_file(filename, input_folder, output_folder, quality, target_size, target_bitrate, convert_to_webp):
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)

    try:
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            compress_image(input_path, output_path, quality, target_size, convert_to_webp)
            compressed_size = get_file_size(output_path)
            return "Image", get_file_size(input_path), compressed_size, get_file_size(input_path) - compressed_size, 0

        elif filename.lower().endswith(('.mp4', '.avi', '.wmv', '.mov', '.mkv')):
            compress_video(input_path, output_path, target_bitrate)
            compressed_size = get_file_size(output_path)
            return "Video", get_file_size(input_path), compressed_size, get_file_size(input_path) - compressed_size, 0

        else:
            return None
    except Exception as e:
        logging.error(f"Error processing file {filename}: {e}")
        return None

def compress_files_in_folder(input_folder, output_folder, quality=85, target_size=(1920, 1080), target_bitrate='2000k', convert_to_webp=False):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_stats = {'original_sizes': [], 'compressed_sizes': [], 'savings': [], 'metadata_savings': 0}
    video_stats = {'original_sizes': [], 'compressed_sizes': [], 'savings': []}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for filename in os.listdir(input_folder):
            futures.append(executor.submit(process_file, filename, input_folder, output_folder, quality, target_size, target_bitrate, convert_to_webp))

        for future in futures:
            result = future.result()
            if result:
                file_type, original_size, compressed_size, saving, metadata_saving = result
                if file_type == "Image":
                    image_stats['original_sizes'].append(original_size)
                    image_stats['compressed_sizes'].append(compressed_size)
                    image_stats['savings'].append(saving)
                    image_stats['metadata_savings'] += metadata_saving
                elif file_type == "Video":
                    video_stats['original_sizes'].append(original_size)
                    video_stats['compressed_sizes'].append(compressed_size)
                    video_stats['savings'].append(saving)

    return image_stats, video_stats

def select_folder():
    input_folder = filedialog.askdirectory(title="Select Folder")
    if input_folder:
        output_folder = os.path.join(input_folder, 'compressed')
        quality = quality_scale.get()
        target_bitrate = f"{bitrate_scale.get()}k"
        convert_to_webp = webp_var.get()
        image_stats, video_stats = compress_files_in_folder(input_folder, output_folder, quality=quality, target_size=(1920, 1080), target_bitrate=target_bitrate, convert_to_webp=convert_to_webp)
        image_stats_summary = display_statistics(image_stats, "Image")
        video_stats_summary = display_statistics(video_stats, "Video")
        status_label.config(text=f"Files compressed in folder: {output_folder}\n\n{image_stats_summary}\n{video_stats_summary}")

def display_statistics(stats, file_type):
    if file_type == "Image":
        sizes = stats['original_sizes']
        compressed_sizes = stats['compressed_sizes']
        savings = stats['savings']
        return (f"Image Statistics:\n"
                f"Original Size: {sum(sizes) / 1024:.2f} KB\n"
                f"Compressed Size: {sum(compressed_sizes) / 1024:.2f} KB\n"
                f"Savings: {sum(savings) / 1024:.2f} KB\n"
                f"Metadata Savings: {stats['metadata_savings'] / 1024:.2f} KB")
    elif file_type == "Video":
        sizes = stats['original_sizes']
        compressed_sizes = stats['compressed_sizes']
        savings = stats['savings']
        return (f"Video Statistics:\n"
                f"Original Size: {sum(sizes) / 1024:.2f} KB\n"
                f"Compressed Size: {sum(compressed_sizes) / 1024:.2f} KB\n"
                f"Savings: {sum(savings) / 1024:.2f} KB")

def create_gui():
    root = Tk()
    root.title("File Compression Tool")
    root.geometry("500x600")

    global status_label, quality_scale, bitrate_scale, webp_var

    select_button = Button(root, text="Select Folder", command=select_folder, padx=20, pady=10)
    select_button.pack(pady=20)

    quality_label = Label(root, text="Image Quality (1-100):")
    quality_label.pack()
    quality_scale = Scale(root, from_=1, to_=100, orient="horizontal", length=300)
    quality_scale.set(85)
    quality_scale.pack(pady=10)

    bitrate_label = Label(root, text="Video Bitrate (k):")
    bitrate_label.pack()
    bitrate_scale = Scale(root, from_=500, to_=5000, orient="horizontal", length=300)
    bitrate_scale.set(2000)
    bitrate_scale.pack(pady=10)

    webp_var = IntVar()
    webp_checkbox = Checkbutton(root, text="Convert Images to WebP", variable=webp_var)
    webp_checkbox.pack(pady=10)

    status_label = Label(root, text="", justify="left", font=("Arial", 10))
    status_label.pack(pady=20, padx=20, fill="both", expand=True)

    footer_label = Label(root, text="Author: Wiktor Józwiak | Version: 1.0", font=("Arial", 8), anchor="center")
    footer_label.pack(side="bottom", pady=10, fill="x")

    root.mainloop()

if __name__ == "__main__":
    create_gui()
