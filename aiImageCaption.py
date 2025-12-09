from langchain_ollama import ChatOllama
import base64
from langchain_core.messages import HumanMessage
from langsmith import traceable
from dotenv import load_dotenv
import os
import shutil
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

def convert_heic_to_jpeg(heic_path, jpeg_path):
    try:
        with Image.open(heic_path) as img:
            # Convert to RGB mode, as JPEG typically uses RGB
            img.convert('RGB').save(jpeg_path, 'JPEG')
        print(f"Successfully converted '{heic_path}' to '{jpeg_path}'")
    except Exception as e:
        print(f"Error converting '{heic_path}': {e}")

def process_files_recursive(source_folder, destination_folder):
    """
    Iterates through files in a named folder and its subfolders,
    and copies them to a new destination folder.

    Args:
        source_folder (str): The path to the source folder.
        destination_folder (str): The path to the destination folder.
    """
    if not os.path.exists(source_folder):
        print(f"Error: Source folder '{source_folder}' does not exist.")
        return

    # Create the destination folder if it doesn't exist


    for root, _, files in os.walk(source_folder):
        # Walks through folder (root) contained in the source directory
        relative_path = os.path.relpath(root, source_folder)
        destination_folder_path =os.path.join(destination_folder, relative_path)
        print(f"walker root:'{root}' relative_path:'{relative_path}' destination_folder_path:'{destination_folder_path}'")
        # First make sure the destination folder doesn't already exist 
        if  os.path.exists(destination_folder_path):
            print(f"Error: Destination folder '{destination_folder_path}' already exists.")
            return
        else:
                os.makedirs(destination_folder_path, exist_ok=False)
        for file_name in files:
            source_file_path = os.path.join(root, file_name)
            destination_file_path = os.path.join(destination_folder_path, file_name)
            print(f"fileloop source_file_path:'{source_file_path}' destination_file_path:'{destination_file_path}' ")
            try:
                # For heif files
                # Use pillow_heif to make a jpg version of any heif file as temp.jpg
                # then use caption utility to make a new file name
                # then copy the file to the new directory with the new file name
                # for all other image files (only jpg and png supported)
                # just work out a new file name and copy to the new directory
                root, extension = os.path.splitext(source_file_path)
                if extension==".heif":
                    convert_heic_to_jpeg(source_file_path,"./temp.jpg")
                    shutil.copy2("./temp.jpg", destination_file_path)
                else:
                    if extension in [".jpg", ".png"]:
                        shutil.copy2(source_file_path, destination_file_path)
                print(f"Copied: '{source_file_path}' to '{destination_file_path}'")
            except IOError as e:
                print(f"Error copying '{source_file_path}': {e}")
            except Exception as e:
                print(f"An unexpected error occurred while copying '{source_file_path}': {e}")







# Set up the model, using the chatOllama provider package
llm = ChatOllama(
    model="llama3.2-vision:11b",
    base_url="http://mac:11434",
    num_ctx=2048,
    temperature=0.0,
)



@traceable
def getImageCaption(path:str):
    # Read and encode image
    print("Start encoding..")
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Create message with base64 image
    print("Making Message..")
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Create a short 10 word caption for this image."},
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{encoded_image}"
            },
        ]
    )

    # Invoke model
    print("Invoke message..")
    response = llm.invoke([message])
    return(response.content)

# if __name__ == "__main__":
#     # Path to your local image
#     image_path = "C:/Users/grace/OneDrive/Pictures/Korea/IMG_5482.jpeg"
#     print(f"\nResponse: {getImageCaption(image_path)}")


# Example usage:
if __name__ == "__main__":
    source_directory = r"C:\projects\aiImageCaption\images"  # Replace with your source folder path
    destination_directory = r"c:\temp\outImages" # Replace with your destination folder path

    process_files_recursive(source_directory, destination_directory)