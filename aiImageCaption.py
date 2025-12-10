from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage 
from langsmith import traceable
from dotenv import load_dotenv
from PIL import Image
from pillow_heif import register_heif_opener
from pydantic import BaseModel
import os
import base64
import shutil
import argparse
import re
import time

class File_Keywords(BaseModel):
        keywords: list[str]  # A list of strings

load_dotenv(dotenv_path=".env", override=True)

def dir_path(file_path):
    """
    Validates a file path using a regular expression.
    This regex attempts to cover common valid path patterns across OS.
    """
    # This regex attempts to validate a path with optional drive letter (Windows),
    # and segments of alphanumeric characters, underscores, hyphens, and dots,
    # separated by forward or backward slashes, ending with an optional filename and extension.
    # It does not cover all edge cases or OS-specific restrictions.
    regex = r"^(?:[a-zA-Z]:[\\/]|[/])?(?:(?:[\w\-. ]+[\\/])*(?:[\w\-. ]+))?$"
    if re.fullmatch(regex, file_path):
        return file_path
    else:
        raise argparse.ArgumentError('Not a path')

parser = argparse.ArgumentParser(
                    prog='aiImageCaption',
                    description="Create a copy of image files based on scanning a directory. " +
                    "The files will be given new more descriptive names based on AI analysis " +
                    "of the images. heic files will be converted to jpg files")
parser.add_argument("source",type=dir_path, help="Source directory containing images and subdirectories to be captioned")
parser.add_argument("destination", type=dir_path, help="Destination directory , where updated files are placed")
parser.add_argument('-m', '--model', nargs='?',  default="llama3.2-vision:11b", type=str,
                    help='Optional Ollama hosted vision model. Defaults to llama3.2-vision:11b if not specified')
parser.add_argument('-u', '--url', nargs='?',  default="http://mac:11434", type=str,
                    help='Optional base URL for Ollama. Defaults to http://mac:11434 if not specified')

register_heif_opener()




def convert_heic_to_jpeg(heic_path, jpeg_path):
    try:
        with Image.open(heic_path) as img:
            # Convert to RGB mode, as JPEG typically uses RGB
            img.convert('RGB').save(jpeg_path, 'JPEG')
        print(f"Successfully converted '{heic_path}' to '{jpeg_path}'")
    except Exception as e:
        print(f"Error converting '{heic_path}': {e}")

def process_files(source_folder, destination_folder,model,base_url):
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
        print("")
        # print(f"walker root:'{root}' relative_path:'{relative_path}' destination_folder_path:'{destination_folder_path}'")
        # First make sure the destination folder doesn't already exist 
        if  os.path.exists(destination_folder_path):
            print(f"Error: Destination folder '{destination_folder_path}' already exists.")
            return
        else:
                os.makedirs(destination_folder_path, exist_ok=False)
        for file_name in files:
            source_file_path = os.path.join(root, file_name)
            destination_file_path = os.path.join(destination_folder_path, file_name)
            # print(f"fileloop source_file_path:'{source_file_path}' destination_file_path:'{destination_file_path}' root:'{root} ")
            try:
                # For heic files
                # Use pillow_heif to make a jpg version of any heif file as temp.jpg
                # then use caption utility to make a new file name
                # then copy the file to the new directory with the new file name
                # for all other image files (only jpg and png supported)
                # just work out a new file name and copy to the new directory
                fileroot, extension = os.path.splitext(source_file_path)
                print(f"extension:'{extension}'")
                if extension.lower()==".heic":
                    convert_heic_to_jpeg(source_file_path,"./temp.jpg")
                    # new_file_Path = os.path.join(destination_folder_path, file_name)
                    jpg_file_path=destination_file_path.replace(extension,".jpg")
                    shutil.copy2("./temp.jpg", jpg_file_path)
                    print(f"Copied: ./temp.jpg to '{jpg_file_path}'")
                    destination_file_path=jpg_file_path
                else:
                    if extension.lower() in [".jpg", ".png"]:
                        shutil.copy2(source_file_path, destination_file_path)
                        print(f"Copied: '{source_file_path}' to '{destination_file_path}'")
            except IOError as e:
                print(f"Error copying '{source_file_path}': {e}")
            except Exception as e:
                print(f"An unexpected error occurred while copying '{source_file_path}': {e}")
            keywords=getImageCaption(destination_file_path,model,base_url)
            print(keywords,"/n")


@traceable
def getImageCaption(image_path:str,model:str,base_url:str):
    time.sleep(1)
        # Set up the model, using the chatOllama provider package
    llm = ChatOllama(
        model=model,
        base_url=base_url,
        temperature=0.0,
)
    # Read and encode image

    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Create message with base64 image
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Describe the image with a collection of up to 10 keywords. "},
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{encoded_image}"
            },
        ]
    )

    # Invoke model
    structured_llm = llm.with_structured_output(File_Keywords, method="json_schema")
    print("Analyze Image...")
    response = structured_llm.invoke([message])
    # Remove duplicates from the list
    unique_list = list(set(response.keywords))
    return(unique_list)

# if __name__ == "__main__":
#     # Path to your local image
#     image_path = "C:/Users/grace/OneDrive/Pictures/Korea/IMG_5482.jpeg"
#     print(f"\nResponse: {getImageCaption(image_path)}")


# Example usage:
if __name__ == "__main__":
    args = parser.parse_args()
    source_directory = args.source
    destination_directory = args.destination
    print(source_directory,destination_directory)

    process_files(source_directory, destination_directory,args.model,args.url)