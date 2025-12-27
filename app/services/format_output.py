import os
import json
from typing import Dict, Any
from google.genai import Client, types
from dotenv import load_dotenv


load_dotenv()

client = Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)
SYSTEM_PROMPT = """
انت مساعد ذكي بتشرح رحلات مواصلات للناس بطريقة بسيطة ولطيفة.
المدخل JSON فيه:
- نقطة البداية
- نقطة النهاية
- مجموعة رحلات جاهزة

كل رحلة فيها:
- المسار (أسماء خطوط)
- السعر
- زمن التنقل
- إجمالي المشي

المطلوب:
- اكتب بالعامية المصرية
- اشرح كل رحلة في فقرة منفصلة
- استخدم أسماء الخطوط زي ما هي، متترجمهاش
- اذكر السعر، زمن التنقل، والمسافة اللي هتمشيها في كل رحلة
- استخدم رموز تعبيرية مناسبة زي 🚶‍♂️ للمشي،
- 🚌 للباص، 🚇 للمترو، و💰 للسعر
- خلي الشرح بسيط وسهل ولطيف يفهمه أي حد
- لو مفيش رحلات قول: "مع الأسف مفيش رحلات مناسبة دلوقتي."
"""

def format_server_journeys_for_user_llm(
    journeys: list,
    origin: str,
    dest: str
) -> str:
    try:
        if not journeys:
            return "مع الأسف مفيش رحلات مناسبة دلوقتي."

        clean_journeys = []
        for j in journeys:
            clean_journeys.append({
                "path": j.get("readable_path", []),
                "money": j.get("costs", {}).get("money", 0),
                "walk_m": int(j.get("costs", {}).get("walk", 0)),
                "time_min": int(j.get("costs", {}).get("transport_time", 0))
            })

        payload = {
            "origin": origin,
            "destination": dest,
            "journeys": clean_journeys
        }

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[json.dumps(payload, ensure_ascii=False)],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature= 0,
                response_mime_type="text/plain"
            )
        )

        return response.text

    except Exception as e:
        print(f"[LLM FORMAT ERROR] {e}")
        return "حصلت مشكلة واحنا بنجهز الرحلات، جرب تاني."
