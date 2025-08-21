import streamlit as st
from openai import OpenAI
import base64
from io import BytesIO

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Image Captioner",
    page_icon="🖼️",
    layout="centered",
)

# --- App Title and Description ---
st.title("🖼️ AI Image Captioner")
st.markdown(
    "Upload an image and let our AI generate a detailed caption for it."
)
st.divider()

# --- Functions for Image Processing and API Interaction ---
def get_caption_from_api(image_bytes):
    """
    Sends the image bytes to the OpenRouter API and returns a generated caption.

    Args:
        image_bytes (bytes): The byte data of the uploaded image.

    Returns:
        str: The generated caption or an error message.
    """
    try:
        # Get the API key from Streamlit's secrets manager
        api_key = st.secrets["OPENROUTER_API_KEY"]
        
        # Initialize the OpenAI client with the OpenRouter base URL and API key
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        
        # Encode the image to base64 for the API request
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Create the API call with multimodal content and a descriptive prompt
        response = client.chat.completions.create(
            model="meta-llama/llama-3.2-11b-vision-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Provide a detailed and descriptive caption for this image, including objects, colors, and the overall scene."
                        }
                    ]
                }
            ],
            temperature=0.5
        )
        
        # Extract the content from the response
        return response.choices[0].message.content
    
    except Exception as e:
        # Handle API-related errors, including a missing API key
        return f"An error occurred: Please ensure your API key is correctly configured. Error: {e}"

# --- Streamlit UI Components ---
uploaded_file = st.file_uploader(
    "Choose an image...",
    type=["jpg", "jpeg", "png"],
    help="Supported formats: JPG, JPEG, PNG. Max file size is 200MB."
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    st.write("")

    if st.button("Generate Caption", help="Click to generate a caption for the uploaded image."):
        with st.spinner("Generating caption..."):
            image_bytes = uploaded_file.getvalue()
            caption = get_caption_from_api(image_bytes)
            
            if "An error occurred" in caption:
                st.error(caption)
            else:
                st.success("Caption Generated!")
                st.info(f"**Caption:** {caption}")
