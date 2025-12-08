## Image File Converter and Naming utility

This uses Langchain and a Image capable LLM to rename image files based on there image content. If working with HEIC
image files it will first convert them to jpg. It is run from the command line with arguments to a folder of images
to convert , and an output folder in which to write the converted images. The utility supports multi-layer folder structures of images.

### Technical

This uses python and pythons UV package manager and uses a virtual python environment.
Use the following packages added via uv

- uv add langchain
- uv add langchain-ollama
- uv add pillow
- uv add pillow-heif
- uv add python-dotenv

I use the [llama3.2-vision:11b](https://ollama.com/library/llama3.2-vision:11b) LLM for working with the image content and generation the file names.
