from fastapi import FastAPI, HTTPException, Request
import tensorflow.lite as tflite
import numpy as np
import uvicorn
from PIL import Image
from fastapi.middleware.cors import CORSMiddleware
import io
import requests  # ✅ Import to fetch image from Firebase URL

app = FastAPI()

# ✅ Allow all origins (for now, restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to specific domains later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load TensorFlow Lite Model
interpreter = tflite.Interpreter(model_path="acne_model.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_image(image_bytes):
    """Preprocess image to match model input shape"""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((224, 224))  # Resize to model input shape
    img_array = np.array(image).astype(np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    return img_array

@app.post("/classify")
async def classify_image(request: Request):
    """Accepts an image URL from Firebase and classifies it."""
    try:
        data = await request.json()
        image_url = data.get("image_url")

        if not image_url:
            raise HTTPException(status_code=400, detail="Missing image_url")

        # ✅ Download image from Firebase URL
        response = requests.get(image_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch image")

        img_array = preprocess_image(response.content)

        # ✅ Run inference
        interpreter.set_tensor(input_details[0]['index'], img_array)
        interpreter.invoke()
        prediction = interpreter.get_tensor(output_details[0]['index'])

        acne_classes = ["Blackheads", "Whiteheads", "Papules", "Pustules", "Nodules", "Cysts"]
        predicted_label = acne_classes[np.argmax(prediction)]

        return {"classification": predicted_label, "confidence": float(np.max(prediction))}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
