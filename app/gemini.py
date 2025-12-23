import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def generate_health_advice(data: dict) -> dict:
    """
    AI Engine — Works in TWO modes:
    1️⃣ Chat Mode → if user sends: { "query": "What is diabetes?" }
    2️⃣ Health Analysis Mode → if health form data is passed
    """

    # ----------------- CHATBOT MODE -----------------
    if "query" in data:
        user_query = data["query"].strip()
        if not user_query:
            return {"summary": "Please enter a message."}

        chat_prompt = f"""
        You are a friendly AI medical assistant.

        User Question:
        "{user_query}"

        Respond clearly and helpfully in plain text. Avoid extreme medical claims.
        """

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(chat_prompt)
            reply = (response.text or "").strip()

            return {"summary": reply or "I couldn’t understand. Please rephrase."}

        except Exception as e:
            print("❌ Chatbot Gemini Error:", repr(e))
            return {"summary": "⚠ AI connection failed. Try again later."}

    # ----------------- HEALTH DATA ANALYSIS MODE -----------------
    try:
        print("\n📌 Incoming Health Data:", data)

        prompt = f"""
        You are an expert AI health assistant. Analyze the following user data:

        Age: {data['age']}
        Gender: {data['gender']}
        Height: {data['height']} inches
        Weight: {data['weight']} kg
        Blood Pressure: {data['bloodPressureSys']}/{data['bloodPressureDia']}
        Heart Rate: {data['heartRate']} bpm
        Sleep: {data['sleepHours']} hrs/day
        Water Intake: {data['waterIntake']} L/day
        Workout: {data['workoutMinutes']} min/day

        Provide output ONLY in this exact JSON format:

        {{
          "summary": "short summary",
          "risk_level": "Low" | "Moderate" | "High",
          "diet": "- item 1\\n- item 2",
          "fitness": "- item 1\\n- item 2",
          "goals": "- goal 1\\n- goal 2"
        }}
        
        No markdown, no extra text.
        """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        raw_text = (response.text or "").strip()
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()

        # Try parsing JSON
        try:
            return json.loads(cleaned)
        except:
            pass

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

        # Fallback if AI does not follow JSON rules
        return {
            "summary": cleaned,
            "risk_level": "Moderate",
            "diet": "- Drink more water",
            "fitness": "- Walk 30 min daily",
            "goals": "- Improve sleep",
        }

    except Exception as e:
        print("❌ Health analysis Gemini Error:", repr(e))
        return {
            "summary": "AI health analysis unavailable due to server issue.",
            "risk_level": "Unknown",
            "diet": "",
            "fitness": "",
            "goals": "",
        }