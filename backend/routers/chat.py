from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.middleware.token_validator import validate_signed_request
from backend.services.db_service import get_connection


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
        conn = get_connection()
        cursor = conn.cursor()
        print("✅ DB CONNECTED")

        # 🔹 Get real PatientID
        cursor.execute("""
            SELECT PatientID
            FROM Patient
            WHERE encode(digest(PatientID::text, 'sha256'), 'hex') = %s
        """, (pid_hash,))

        patient = cursor.fetchone()
        print("Patient:", patient)

        if not patient:
            return {"answer": "Patient not found"}

        patient_id = patient[0]

        # 🔹 Check if parameter exists
        keyword = question.split()[0]
        print("SEARCH KEYWORD:", keyword)

        cursor.execute("""
            SELECT tp.TestParameterId, tp.ParameterName
            FROM TestParameter tp
            JOIN TestResult tr
            ON tp.TestParameterId = tr.TestParameterId
            WHERE tr.PatientID = %s
            AND LOWER(tp.ParameterName) LIKE LOWER(%s)
            LIMIT 1
        """, (patient_id, f"%{keyword}%"))


        param = cursor.fetchone()
        print("Parameter:", param)

        if not param:
            return {"answer": f"{question} not found in report"}

        param_id = param[0]

        # 🔹 Get result value
        cursor.execute("""
            SELECT ResultValue
            FROM TestResult
            WHERE PatientID = %s
            AND TestParameterId = %s
        """, (patient_id, param_id))

        result = cursor.fetchone()
        print("Result:", result)

        cursor.close()
        conn.close()

        if not result:
            return {"answer": f"No result found for {question}"}

        return {
            "answer": f"{param[1]} value is {result[0]}"
        }

    except Exception as e:
        print("❌ ERROR:", e)
        return {"answer": str(e)}
