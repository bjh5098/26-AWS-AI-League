import json
import re


def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        print(f"DEBUG: Received event: {body}")

        text = body.get('text', body.get('input', body.get('question', '')))

        if not text:
            return _err(400, 'text, input, or question parameter is required')

        result = {
            "patient_id": None,
            "first_name": None,
            "last_name": None,
            "provider_name": None,
            "insurance_id": None
        }

        # insurance_id 먼저 파싱 (patient_id와 혼동 방지)
        m = re.search(r'insurance[_\s]?id[:\s#]+([A-Z0-9\-]+)', text, re.IGNORECASE)
        if m:
            result["insurance_id"] = m.group(1).strip()

        # patient_id: "patient_id: X", "patient id: X", "ID: X" (insurance_id 제외)
        m = re.search(r'patient[_\s]?id[:\s#]+([A-Z0-9\-]+)', text, re.IGNORECASE)
        if m:
            result["patient_id"] = m.group(1).strip()
        else:
            # 단독 "ID: X" 패턴 (insurance_id 앞에 오지 않는 경우만)
            m = re.search(r'(?<![a-z_])id[:\s#]+([A-Z0-9\-]+)', text, re.IGNORECASE)
            if m and m.group(1) != result["insurance_id"]:
                result["patient_id"] = m.group(1).strip()

        # first_name / last_name: 대문자로 시작하는 이름 2개
        # "Patient: John Smith", "patient name is Alice Kim" 처리
        m = re.search(r'patient[:\s]+(?:name\s+)?(?:is\s+)?([A-Z][a-z]+)\s+([A-Z][a-z]+)', text, re.IGNORECASE)
        if m:
            result["first_name"] = m.group(1)
            result["last_name"] = m.group(2)

        # provider_name: "Provider: Dr. Jane Doe", "Provider: Jane Doe", "Dr. Jane Doe"
        m = re.search(r'(?:provider|doctor)[:\s]+(?:Dr\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text, re.IGNORECASE)
        if m:
            result["provider_name"] = m.group(1).strip()
        else:
            m = re.search(r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
            if m:
                result["provider_name"] = m.group(1).strip()

        print(f"RESULT: {result}")
        return {'statusCode': 200, 'body': json.dumps(result)}

    except Exception as e:
        print(f"ERROR: {e}")
        return _err(500, str(e))


def _err(code, msg):
    return {'statusCode': code, 'body': json.dumps({'error': msg})}
