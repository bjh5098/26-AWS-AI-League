"""
dark_prophet_tool.py — Lambda Tool: Dark Prophet (c4) 웹 스크래핑 챌린지
AgentCore Gateway를 통해 호출됨. 인터넷에서 정보를 검색하고 반환.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import html
import re


def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        print(f"DEBUG: Received event: {body}")

        query = body.get('query', '')
        url = body.get('url', '')
        action = body.get('action', 'search')

        if not query and not url:
            return _err(400, 'query 또는 url 파라미터가 필요합니다')

        if action == 'fetch' and url:
            result = _fetch_url(url)
        else:
            result = _search_web(query)

        print(f"RESULT: {str(result)[:200]}")
        return {'statusCode': 200, 'body': json.dumps(result, ensure_ascii=False)}

    except Exception as e:
        print(f"ERROR: {e}")
        return _err(500, str(e))


def _search_web(query: str) -> dict:
    """DuckDuckGo HTML 검색으로 실시간 정보 수집."""
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

    req = urllib.request.Request(
        search_url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; AI-Agent/1.0)'}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')

        snippets = _extract_snippets(content)
        return {
            'success': True,
            'query': query,
            'results': snippets[:5],
            'source': 'duckduckgo',
        }
    except urllib.error.URLError as e:
        return {'success': False, 'error': f'검색 실패: {str(e)}', 'query': query}


def _fetch_url(url: str) -> dict:
    """특정 URL의 텍스트 내용 수집."""
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; AI-Agent/1.0)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')

        text = _html_to_text(content)
        return {
            'success': True,
            'url': url,
            'content': text[:3000],
        }
    except urllib.error.URLError as e:
        return {'success': False, 'error': f'URL 접근 실패: {str(e)}', 'url': url}


def _extract_snippets(html_content: str) -> list:
    """DuckDuckGo HTML에서 검색 결과 스니펫 추출."""
    snippets = []
    # result__snippet 클래스에서 텍스트 추출
    pattern = r'class="result__snippet"[^>]*>(.*?)</a>'
    matches = re.findall(pattern, html_content, re.DOTALL)
    for m in matches:
        text = html.unescape(re.sub(r'<[^>]+>', '', m)).strip()
        if text:
            snippets.append(text)

    # 결과 없으면 일반 텍스트 추출 시도
    if not snippets:
        text = _html_to_text(html_content)
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 30]
        snippets = lines[:5]

    return snippets


def _html_to_text(html_content: str) -> str:
    """HTML에서 순수 텍스트 추출."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _err(code, msg):
    return {'statusCode': code, 'body': json.dumps({'error': msg}, ensure_ascii=False)}
