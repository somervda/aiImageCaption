from PIL import Image
from pillow_heif import register_heif_opener

# Register the HEIF opener to enable Pillow to handle HEIC files
register_heif_opener()

def convert_heic_to_jpeg(heic_path, jpeg_path):
    try:
        with Image.open(heic_path) as img:
            # Convert to RGB mode, as JPEG typically uses RGB
            img.convert('RGB').save(jpeg_path, 'JPEG')
        print(f"Successfully converted '{heic_path}' to '{jpeg_path}'")
    except Exception as e:
        print(f"Error converting '{heic_path}': {e}")

# Example usage
heic_file = "./images/IMG_4167.HEIC"  # Replace with your HEIC file path
jpeg_file = "./images/output.jpg"  # Replace with your desired output JPG file path
convert_heic_to_jpeg(heic_file, jpeg_file)