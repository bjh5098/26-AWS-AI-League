#!/bin/bash
# deploy.sh — Lambda 함수 빠른 배포 스크립트
# 사용법: ./deploy.sh [tool_name]
#   tool_name: pathfinding_tool | coin_collector_tool | state_query_tool | all (기본값)

set -e

# .env 로드
if [ -f .env ]; then
  set -a; source .env; set +a
else
  echo "ERROR: .env 파일이 없습니다. cp .env.template .env 후 값을 채워주세요."
  exit 1
fi

TOOL=${1:-all}
TIMESTAMP=$(date '+%H:%M:%S')

deploy_tool() {
  TOOL_FILE="$1"
  FUNC_NAME="$2"

  echo "[$TIMESTAMP] 배포 중: $FUNC_NAME ..."

  # zip 패키징 (pathfinder 포함)
  rm -f /tmp/function.zip
  zip -j /tmp/function.zip "tools/${TOOL_FILE}.py" algorithms/pathfinder.py 2>/dev/null || \
  zip -j /tmp/function.zip "tools/${TOOL_FILE}.py"

  # Lambda 업데이트
  aws lambda update-function-code \
    --function-name "$FUNC_NAME" \
    --zip-file fileb:///tmp/function.zip \
    --region "${AWS_REGION:-ap-northeast-2}" \
    --output text --query 'FunctionName' > /dev/null

  # 배포 완료 대기
  aws lambda wait function-updated \
    --function-name "$FUNC_NAME" \
    --region "${AWS_REGION:-ap-northeast-2}"

  echo "[$TIMESTAMP] ✓ $FUNC_NAME 배포 완료"
}

case "$TOOL" in
  pathfinding_tool)
    deploy_tool "pathfinding_tool" "${LAMBDA_FUNCTION_NAME_PREFIX:-ai-league}-pathfinding"
    ;;
  coin_collector_tool)
    deploy_tool "coin_collector_tool" "${LAMBDA_FUNCTION_NAME_PREFIX:-ai-league}-coin-collector"
    ;;
  state_query_tool)
    deploy_tool "state_query_tool" "${LAMBDA_FUNCTION_NAME_PREFIX:-ai-league}-state-query"
    ;;
  all)
    deploy_tool "pathfinding_tool" "${LAMBDA_FUNCTION_NAME_PREFIX:-ai-league}-pathfinding"
    deploy_tool "coin_collector_tool" "${LAMBDA_FUNCTION_NAME_PREFIX:-ai-league}-coin-collector"
    deploy_tool "state_query_tool" "${LAMBDA_FUNCTION_NAME_PREFIX:-ai-league}-state-query"
    echo ""
    echo "✓ 전체 배포 완료"
    ;;
  *)
    echo "사용법: ./deploy.sh [pathfinding_tool|coin_collector_tool|state_query_tool|all]"
    exit 1
    ;;
esac
