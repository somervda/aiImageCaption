from langchain_ollama import ChatOllama
import base64
from langchain_core.messages import HumanMessage
from langsmith import traceable
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)


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

if __name__ == "__main__":
    # Path to your local image
    image_path = "C:/Users/grace/OneDrive/Pictures/Korea/IMG_5482.jpeg"
    print(f"\nResponse: {getImageCaption(image_path)}")