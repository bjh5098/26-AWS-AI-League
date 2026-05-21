"""
blue_brain_tool.py — Lambda Tool: Blue Brain (c2) 코드 실행 챌린지
AgentCore Gateway를 통해 호출됨. Python 코드를 실행하고 결과를 반환.
"""

import json
import sys
import io
import traceback
import math
import statistics


def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        print(f"DEBUG: Received event: {body}")

        code = body.get('code', '')
        question = body.get('question', '')

        if not code and not question:
            return _err(400, 'code 또는 question 파라미터가 필요합니다')

        # 질문만 있으면 코드로 변환하여 실행
        if question and not code:
            code = _question_to_code(question)

        result = _execute_code(code)
        print(f"RESULT: {result}")
        return {'statusCode': 200, 'body': json.dumps(result, ensure_ascii=False)}

    except Exception as e:
        print(f"ERROR: {e}")
        return _err(500, str(e))


def _execute_code(code: str) -> dict:
    """Python 코드를 안전하게 실행하고 결과 반환."""
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    allowed_globals = {
        '__builtins__': {
            'print': print,
            'range': range,
            'len': len,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'sorted': sorted,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'isinstance': isinstance,
            'type': type,
            'bool': bool,
            'pow': pow,
            'divmod': divmod,
            'bin': bin,
            'hex': hex,
            'oct': oct,
            'ord': ord,
            'chr': chr,
        },
        'math': math,
        'statistics': statistics,
    }
    local_vars = {}

    old_stdout = sys.stdout
    sys.stdout = stdout_capture
    try:
        exec(code, allowed_globals, local_vars)
        output = stdout_capture.getvalue()
        result_val = local_vars.get('result', output.strip() if output.strip() else None)
        return {
            'success': True,
            'output': output,
            'result': result_val,
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }
    finally:
        sys.stdout = old_stdout


def _question_to_code(question: str) -> str:
    """수학/알고리즘 질문을 Python 코드로 변환하는 템플릿."""
    return f"""
import math
import statistics

# Question: {question}
# TODO: 에이전트가 이 질문에 맞는 코드를 생성하여 전달해야 함
result = "Code execution required"
print(result)
"""


def _err(code, msg):
    return {'statusCode': code, 'body': json.dumps({'error': msg}, ensure_ascii=False)}
