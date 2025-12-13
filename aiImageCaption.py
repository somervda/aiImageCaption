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

start_time=time.time()

DEBUG_MODE=False
def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)

register_heif_opener()

# Define a datatype to be used to formate the LLM output
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

# Setup arg parser (Defaults to the granite3.2-vision:2b model on my development PC)
parser = argparse.ArgumentParser(
                    prog='aiImageCaption',
                    description="Create a copy of image files based on scanning a directory. " +
                    "The files will be given new more descriptive names based on AI analysis " +
                    "of the images. heic files will be converted to jpg files")
parser.add_argument("source",type=dir_path, help="Source directory containing images and subdirectories to be captioned")
parser.add_argument("destination", type=dir_path, help="Destination directory , where updated files are placed")
parser.add_argument('-m', '--model', nargs='?',  default="granite3.2-vision:2b", type=str,
                    help='Optional Ollama hosted vision model. Defaults to granite3.2-vision:2b if not specified')
parser.add_argument('-u', '--url', nargs='?',  default="http://192.168.1.117:11434", type=str,
                    help='Optional base URL for Ollama. Defaults to http://192.168.1.117:11434 if not specified')


def convert_heic_to_jpeg(heic_path, jpeg_path):
    try:
        with Image.open(heic_path) as img:
            # Extract EXIF data (if present)
            exif_data = img.info.get('exif')
            # Convert to RGB mode if not already (important for saving as JPG)
            rgb_image = img.convert("RGB")
            # Save the image as JPG, including the extracted EXIF data
            if exif_data:
                rgb_image.save(jpeg_path, format="jpeg", exif=exif_data)
            else:
                rgb_image.save(jpeg_path, format="jpeg")
    except Exception as e:
        print(f"Error converting '{heic_path}': {e}")

def keywords_to_filename(file_path:str,keywords:list[str]):
    # Create a new file name based on image keywords and the original file name
    # Extracting the full filename
    filename = os.path.basename(file_path)
    # Extracting the directory name
    dirname = os.path.dirname(file_path)
    # Extracting the filename without extension and the extension
    root, ext = os.path.splitext(filename)
    # Rebuild the file name by <directory name>/<keywords separated by underscores>_<original file name>
    new_file_name=""
    for  keyword in keywords:
        new_file_name+= keyword +"_"
    new_file_name += filename
    debug_print(new_file_name)
    return os.path.join(dirname, new_file_name)

def process_files(source_folder, destination_folder):
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
    files_count_total=0
    for root, _, files in os.walk(source_folder):
        # Walks through folder (root) contained in the source directory
        for file_name in files:
            files_count_total+=1

    file_count=0
    for root, _, files in os.walk(source_folder):
        # Walks through folder (root) contained in the source directory
        relative_path = os.path.relpath(root, source_folder)
        destination_folder_path =os.path.join(destination_folder, relative_path)
        debug_print(f"walker root:'{root}' relative_path:'{relative_path}' destination_folder_path:'{destination_folder_path}'")
        # First make sure the destination folder doesn't already exist 
        if  os.path.exists(destination_folder_path):
            print(f"Error: Destination folder '{destination_folder_path}' already exists.")
            return
        else:
                os.makedirs(destination_folder_path, exist_ok=False)
        # Get a list of heic files in the folder, use this to decide which MOV files not to copy
        #  I don't want to copy the ones that match heic file names 
        heic_files=[]
        for file_name in files:
            fileroot, extension = os.path.splitext(file_name)
            if extension.lower()==".heic":
                heic_files.append(os.path.basename(fileroot))
        debug_print(heic_files)
        for file_name in files:
            file_count+=1
            print("\nFile:",file_count,"/" , files_count_total, "  ",round(time.time() - start_time,1))
            source_file_path = os.path.join(root, file_name)
            destination_file_path = os.path.join(destination_folder_path, file_name)
            try:
                fileroot, extension = os.path.splitext(source_file_path)
                debug_print(f"extension:'{extension}'")
                if extension.lower()==".heic":
                    # For heic files
                    # Use pillow_heif to make a jpg version of any heif file as temp.jpg
                    convert_heic_to_jpeg(source_file_path,"temp.jpg")
                    # new_file_Path = os.path.join(destination_folder_path, file_name)
                    jpg_file_path=destination_file_path.replace(extension,".jpg")
                    shutil.copy2("temp.jpg", jpg_file_path)
                    print(f"Copied: temp.jpg to '{jpg_file_path}'")
                    destination_file_path=jpg_file_path
                elif extension.lower() in [".jpg", ".png",".mp4",".jpeg",".gif",".bmp",".tif",".tiff"]:
                    # All other supported files other than mov, just copy
                    shutil.copy2(source_file_path, destination_file_path)
                    print(f"Copied: '{source_file_path}' to '{destination_file_path}'")
                elif extension.lower() in [".mov"]: 
                    # Only copy mov files if not sourced from a heic file snapshot
                    mov_fileroot, mov_extension = os.path.splitext(destination_file_path)
                    if not (os.path.basename(mov_fileroot) in heic_files):
                        shutil.copy2(source_file_path, destination_file_path)
                        print(f"Copied: '{source_file_path}' to '{destination_file_path}'")
            except IOError as e:
                print(f"Error copying '{source_file_path}': {e}")
            except Exception as e:
                print(f"An unexpected error occurred while copying '{source_file_path}': {e}")
            if extension.lower() in [".jpg", ".png",".heic",".jpg", ".png",".jpeg",".gif",".bmp",".tif",".tiff"]:
                # Still image files, try generating a better file name
                keywords=getImageKeywords(destination_file_path)
                new_file_name=keywords_to_filename(destination_file_path,keywords)
                try:
                    # Rename the file
                    os.rename(destination_file_path, new_file_name)
                    print(f"File '{destination_file_path}' successfully renamed to '{new_file_name}'.")
                except FileNotFoundError:
                    print(f"Error: The file '{destination_file_path}' was not found.")
                except OSError as e:
                    print(f"Error renaming file: {e}")
                




@traceable
def getImageKeywords(image_path:str):
    # Read and encode image
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    # Create message with base64 image
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Get a list of the top 4 keywords that describe on the image. "},
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{encoded_image}"
            },
        ]
    )

    # Use the structured output option on the llm to force output to follow the File_Keywords data type 
    # specified earlier using pydantic 
    structured_llm = llm.with_structured_output(File_Keywords, method="json_schema")
    response = structured_llm.invoke([message])
    # Remove duplicates from the list
    unique_list = list(set(response.keywords))
    # Remove special characters from list
    clean_unique_list=[]
    for keyword in unique_list:
        # This pattern matches any character that is NOT a letter, number, or space
        clean_keyword = re.sub(r'[^a-zA-Z0-9\s]', '', keyword).replace(" ","-")
        clean_unique_list.append(clean_keyword)
    return(clean_unique_list)

if __name__ == "__main__":
    args = parser.parse_args()
    source_directory = args.source
    destination_directory = args.destination
    print(source_directory,destination_directory)
    # Set up the model, using the chatOllama provider package
    llm = ChatOllama(
        model=args.model,
        base_url=args.url,
        temperature=0.0
        )

    process_files(source_directory, destination_directory)