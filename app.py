import streamlit as st
from openai import OpenAI
import base64
from io import BytesIO
from gtts import gTTS
from PIL import Image # Import Pillow for image manipulation

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Advanced Image Captioner",
    page_icon="✨",
    layout="centered", # Keep centered layout for a clean look
    initial_sidebar_state="auto"
)

# --- Custom CSS for a more modern look ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Create a CSS file named 'style.css' in the same directory as your Python script
# content for style.css:
# .stButton > button {
#     background-color: #4CAF50;
#     color: white;
#     padding: 10px 20px;
#     border-radius: 5px;
#     border: none;
#     font-size: 16px;
#     cursor: pointer;
# }
# .stButton > button:hover {
#     background-color: #45a049;
# }
# .stFileUploader {
#     border: 2px dashed #4CAF50;
#     padding: 20px;
#     border-radius: 10px;
#     text-align: center;
# }
# .stTextInput > div > div > input {
#     border: 1px solid #4CAF50;
#     border-radius: 5px;
#     padding: 10px;
# }
# .caption-card {
#     background-color: #f0f2f6;
#     padding: 20px;
#     border-radius: 10px;
#     box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
#     margin-top: 20px;
# }
# .uploaded-image-card {
#     background-color: #e6f7ff;
#     padding: 15px;
#     border-radius: 10px;
#     box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
#     margin-bottom: 20px;
# }

try:
    local_css("style.css")
except FileNotFoundError:
    st.warning("`style.css` not found. Some custom styles may not apply.")

# --- App Title and Description ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>✨ AI Image Captioner</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; font-size: 1.1em;'>Upload an image, and our advanced AI will generate a detailed, spoken caption for it.</p>",
    unsafe_allow_html=True
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
        return f"An error occurred: Please ensure your API key is correctly configured in Streamlit secrets. Error: {e}"

# --- Streamlit UI Components ---

# File uploader in a central column
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    uploaded_file = st.file_uploader(
        "**Upload your image here:**",
        type=["jpg", "jpeg", "png"],
        help="Supported formats: JPG, JPEG, PNG. Max file size is 200MB.",
        label_visibility="collapsed"
    )

if uploaded_file is not None:
    # Display the uploaded image with size restrictions for viewing
    st.markdown("<div class='uploaded-image-card'>", unsafe_allow_html=True)
    st.subheader("🖼️ Your Uploaded Image")
    
    # Read image with PIL to resize for display
    image_for_display = Image.open(uploaded_file)
    
    # Create a BytesIO object to store the original image for the API call
    original_image_bytes_io = BytesIO()
    image_for_display.save(original_image_bytes_io, format=image_for_display.format or 'PNG')
    original_image_bytes = original_image_bytes_io.getvalue()
    
    # Resize the image for display purposes only
    max_width_for_display = 700 # Adjust as needed
    width, height = image_for_display.size
    if width > max_width_for_display:
        new_height = int(height * (max_width_for_display / width))
        image_for_display = image_for_display.resize((max_width_for_display, new_height), Image.LANCZOS)
    
    st.image(image_for_display, caption="Image for Display (Resized)", use_container_width=False)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("") # Add some space

    # Button to generate caption
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        if st.button("✨ Generate Caption", use_container_width=True):
            with st.spinner("🧠 Generating detailed caption..."):
                # Pass the original image bytes to the API
                caption = get_caption_from_api(original_image_bytes)
                
                if "An error occurred" in caption:
                    st.error(caption)
                else:
                    st.markdown("<div class='caption-card'>", unsafe_allow_html=True)
                    st.success("📝 Caption Generated! Click play to listen. 🔊")
                    st.info(f"**Caption:** {caption}")

                    # --- Text-to-Speech Functionality ---
                    try:
                        tts = gTTS(text=caption, lang='en')
                        audio_bytes_io = BytesIO()
                        tts.write_to_fp(audio_bytes_io)
                        
                        st.audio(audio_bytes_io.getvalue(), format='audio/mp3', start_time=0)
                    except Exception as tts_e:
                        st.warning(f"Could not generate audio: {tts_e}. Please check your internet connection or try again.")
                    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("⬆️ Please upload an image to get started!")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Powered by Streamlit & OpenRouter AI</p>", unsafe_allow_html=True)

# Example image for illustration
#