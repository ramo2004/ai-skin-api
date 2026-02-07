
import base64
import json
from dotenv import load_dotenv
import os
import mimetypes
from openai import AsyncOpenAI

load_dotenv(".env")

api_key = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)
vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt-5.1")


async def classify_image(image_bytes, filename, user_context=None):
    # Guess the MIME type from the filename
    mime_type, _ = mimetypes.guess_type(filename)
    
    if mime_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise ValueError("Unsupported image format")
    
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # 1. Construct Patient Profile String
    profile_str = ""
    if user_context:
        age = user_context.get("age", "Unknown")
        gender = user_context.get("gender", "Unknown")
        skin = user_context.get("skin_type", "Unknown")
        profile_str = f"\nPatient Context: {age} year old {gender} with {skin} skin."

    # 2. Enhanced System Message
    system_message = (
    "You are a dermatology expert. Analyze the image to classify the primary skin condition."
    "\n\nOPTIONS:"
    "\n1. Whiteheads (closed comedones)"
    "\n2. Blackheads (open comedones)"
    "\n3. Papules (red, inflamed bumps)"
    "\n4. Pustules (red bumps with pus)"
    "\n5. Nodules (deep, painful lumps)"
    "\n6. Cystic Acne (large, pus-filled bumps)"
    "\n7. Fungal Acne (small, uniform pustules)"
    "\n8. Acne Scars (discoloration)"
    "\n9. Rosacea (flushing, visible veins)"
    "\n10. Perioral Dermatitis (rash around mouth)"
    "\n11. Folliculitis (hair follicle inflammation)"
    "\n12. Clear Skin (no pathology)"
    "\n\nRULES:"
    "\n- If the image is BLURRY, dark, or not a close-up of human skin: Return only 'Invalid Image'."
    "\n- If uncertain (confidence 50-80%): List the Top 2 likely conditions to help the user."
    "\n- If <50% confident: Return 'Uncertain'."
    "\n- Exclude cosmetic aging signs (wrinkles/crows feet) for now."
    "\n- Use the provided Patient Context to inform recommendations (e.g., avoid harsh drying agents for Dry/Sensitive skin)."
    )

    response = await client.chat.completions.create(
        model=vision_model,
        messages=[
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Analyze this image and return valid JSON only. "
                            "Required schema: "
                            "{\"classification\":\"string\",\"confidence\":number}. "
                            "confidence must be from 0.0 to 1.0. "
                            f"{profile_str}"
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}}
                ]
            }
        ],
        response_format={ "type": "json_object" },
        max_tokens=800
    )

    parsed = json.loads(response.choices[0].message.content)
    classification = parsed.get("classification", "Uncertain")
    overall_confidence = parsed.get("confidence", 0.5)

    try:
        overall_confidence = max(0.0, min(1.0, float(overall_confidence)))
    except (TypeError, ValueError):
        overall_confidence = 0.5

    return {
        "classification": classification,
        "confidence": overall_confidence
    }

async def analyze_ingredients(image_bytes, filename, user_context=None):
    """
    Analyzes an image of a product label to identify comedogenic ingredients.
    """
    # Guess the MIME type from the filename
    mime_type, _ = mimetypes.guess_type(filename)
    
    if mime_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise ValueError("Unsupported image format")
    
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')

    context_str = ""
    if user_context:
        skin = user_context.get("skin_type", "Unknown")
        context_str = f" The user has {skin} skin."

    system_message = (
        f"You are an expert Cosmetic Chemist. Your task is to identify 'comedogenic' (pore-clogging) ingredients from a product label.{context_str}"
        "\n\nINSTRUCTIONS:"
        "\n1. OCR the text from the image."
        "\n2. Identify any ingredients known to be comedogenic (e.g., Isopropyl Myristate, Coconut Oil, Algin, Carrageenan, Cocoa Butter, etc.)."
        "\n3. Assign a Risk Level based on the presence of high-rating clogging ingredients."
        "\n4. Flag ingredients specifically harmful to the user's skin type (e.g., Alcohol/Fragrance for Sensitive, heavy oils for Oily)."
        "\n\nOUTPUT FORMAT (JSON ONLY):"
        "\n{"
        "\n  \"has_risky_ingredients\": true/false,"
        "\n  \"risk_level\": \"High\" | \"Medium\" | \"Low\" | \"Safe\","
        "\n  \"risky_ingredients\": ["
        "\n    { \"name\": \"Ingredient Name\", \"reason\": \"Why it clogs (e.g. Rating 4/5)\", \"rating\": 1-5 }"
        "\n  ],"
        "\n  \"summary\": \"Brief 1-sentence analysis.\""
        "\n}"
        "\n\nRULES:"
        "\n- If the image is not a product label or text is unreadable, return {\"has_risky_ingredients\": false, \"risk_level\": \"Unknown\", \"summary\": \"Could not read label.\"}."
        "\n- Be strict. Acne-prone users rely on this."
    )

    try:
        response = await client.chat.completions.create(
            model=vision_model,
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze the ingredients in this image for acne risks. Return valid JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}}
                    ]
                }
            ],
            response_format={ "type": "json_object" },
            max_tokens=600
        )
        
        # Parse the JSON response
        import json
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"Error in analyze_ingredients: {e}")
        # Fallback error response
        return {
            "has_risky_ingredients": false,
            "risk_level": "Error",
            "summary": "Failed to analyze ingredients. Please try again.",
            "risky_ingredients": []
        }
