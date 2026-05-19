"""
memory_patterns.py — AgentCore Memory 활용 패턴

에이전트가 힌트·코인위치·방문경로를 기억하고 재활용하는 유틸리티.
"""

import json
import os
import boto3
from typing import Any, Optional


def get_runtime_client():
    return boto3.client('bedrock-agent-runtime', region_name=os.environ.get('AWS_REGION', 'ap-northeast-2'))


def store_memory(memory_id: str, content: str, source_type: str = 'INGESTED_TEXT') -> bool:
    """
    AgentCore Memory에 정보 저장.

    Args:
        memory_id: 메모리 ID (.env의 MEMORY_ID)
        content: 저장할 텍스트 내용
        source_type: 메모리 소스 유형

    Returns:
        성공 여부
    """
    try:
        client = get_runtime_client()
        client.ingest_knowledge_base_documents(
            knowledgeBaseId=memory_id,
            documents=[{
                'content': {'text': content},
                'metadata': {'type': source_type}
            }]
        )
        return True
    except Exception as e:
        print(f"[Memory] 저장 실패: {e}")
        return False


def retrieve_memory(
    agent_id: str,
    agent_alias_id: str,
    memory_id: str,
    query: str
) -> list:
    """
    AgentCore Memory에서 관련 정보 조회.

    Args:
        agent_id: 에이전트 ID
        agent_alias_id: 에이전트 별칭 ID
        memory_id: 메모리 ID
        query: 검색 쿼리

    Returns:
        관련 메모리 항목 목록
    """
    try:
        client = get_runtime_client()
        response = client.get_agent_memory(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            memoryId=memory_id,
            memoryType='SESSION_SUMMARY',
        )
        return response.get('memoryContents', [])
    except Exception as e:
        print(f"[Memory] 조회 실패: {e}")
        return []


def clear_memory(agent_id: str, agent_alias_id: str, memory_id: str) -> bool:
    """메모리 초기화 (새 게임 시작 시 사용)."""
    try:
        client = get_runtime_client()
        client.delete_agent_memory(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            memoryId=memory_id,
        )
        return True
    except Exception as e:
        print(f"[Memory] 초기화 실패: {e}")
        return False
