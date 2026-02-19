from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.middleware.token_validator import validate_signed_request
from backend.services.db_service import get_connection
from backend.services.ollama_service import generate_response
from backend.services.parameter_cache import load_parameters_once
from backend.services.patient_context_loader import load_patient_context
from backend.services.context_cache import get_cached_context, set_cached_context
from backend.services.memory_cache import get_memory

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
def chat_ai(body: ChatRequest, context=Depends(validate_signed_request)):

    print("🔥 CHAT API HIT")

    pid_hash = context["pid"]
    question = body.question.lower()

    print("Question:", question)

    try:

        # ======================================================
        # ⚡ PREDEFINED FACTUAL QUESTIONS (NO LLM NEEDED)
        # ======================================================

        GREETING_WORDS = ["hi", "hello", "hey"]

        PREDEFINED_QUERIES = {
            "what is my name": "Name",
            "my name": "Name",
            "who am i": "Name",
            "what is my age": "Age",
            "my age": "Age",
            "what is my gender": "Gender",
            "my gender": "Gender"
        }

        # 👋 Greeting detected → Fetch Name only
        if question.strip() in GREETING_WORDS:

            print("👋 GREETING → DIRECT DB RESPONSE")

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT Name
                FROM Patient
                WHERE encode(digest(PatientID::text, 'sha256'), 'hex') = %s
            """, (pid_hash,))

            patient = cursor.fetchone()

            cursor.close()
            conn.close()

            if patient:
                return {"answer": f"Hi {patient[0]} 👋 How can I help you with your report today?"}
            else:
                return {"answer": "Hello 👋 How can I help you today?"}

        # 📌 Other factual queries
        for key, column in PREDEFINED_QUERIES.items():
            if key in question:

                print(f"⚡ FACTUAL QUERY → FETCH {column}")

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(f"""
                    SELECT {column}
                    FROM Patient
                    WHERE encode(digest(PatientID::text, 'sha256'), 'hex') = %s
                """, (pid_hash,))

                result = cursor.fetchone()

                cursor.close()
                conn.close()

                if result:
                    return {"answer": f"Your {column.lower()} is {result[0]}."}

        # ======================================================
        # 🧠 PARAMETER MATCHING
        # ======================================================

        parameters = load_parameters_once()

        matched_param = None
        for param in parameters:
            if param in question:
                matched_param = param
                break

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT PatientID
            FROM Patient
            WHERE encode(digest(PatientID::text, 'sha256'), 'hex') = %s
        """, (pid_hash,))

        patient = cursor.fetchone()

        if not patient:
            cursor.close()
            conn.close()
            return {"answer": "Patient not found"}

        patient_id = patient[0]
        chat_memory = get_memory(patient_id)

        # ======================================================
        # ❗ GENERAL QUESTION → LOAD CONTEXT + LLM
        # ======================================================
        if not matched_param:

            print("🧠 GENERAL QUESTION")

            cursor.close()
            conn.close()

            context_data = get_cached_context(patient_id)

            if not context_data:
                print("📥 LOADING CONTEXT FROM DB")
                context_data = load_patient_context(patient_id)
                set_cached_context(patient_id, context_data)
            else:
                print("⚡ USING CACHED CONTEXT")

            final_prompt = f"""
Answer the following question based on the patient report.

Question: {question}

Patient Report:
{context_data}
"""

            ai_reply = generate_response(final_prompt, chat_memory)
            return {"answer": ai_reply}

        # ======================================================
        # ❗ LAB PARAMETER QUESTION
        # ======================================================

        print("🧾 LAB PARAMETER DETECTED → FETCH VALUE")

        cursor.execute("""
            SELECT tp.TestParameterId, tp.ParameterName
            FROM TestParameter tp
            JOIN TestResult tr
            ON tp.TestParameterId = tr.TestParameterId
            WHERE tr.PatientID = %s
            AND LOWER(tp.ParameterName) = LOWER(%s)
            LIMIT 1
        """, (patient_id, matched_param))

        param = cursor.fetchone()

        if not param:
            cursor.close()
            conn.close()
            return {"answer": f"{matched_param} not found in your report"}

        param_id = param[0]
        parameter_name = param[1]

        cursor.execute("""
            SELECT ResultValue
            FROM TestResult
            WHERE PatientID = %s
            AND TestParameterId = %s
        """, (patient_id, param_id))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result or result[0] is None:
            return {
                "answer": f"{parameter_name} test is available but no result value is recorded in your report."
            }

        lab_value = result[0]

        prompt = f"""
Patient's {parameter_name} test result is {lab_value}.

Explain in 2-3 short simple lines:
- Is this normal or abnormal?
- What does it mean for health?
"""

        ai_explanation = generate_response(prompt, chat_memory)
        return {"answer": ai_explanation}

    except Exception as e:
        print("❌ ERROR:", e)
        return {"answer": str(e)}
