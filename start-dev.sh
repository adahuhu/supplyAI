#!/bin/bash
# SupplyAI 本地开发一键启动 — 同时拉起后端 + 前端静态服务。
#
# 用法:
#   ./start-dev.sh         # 启动并打印日志
#   Ctrl-C 停止两个进程
#
# 端口:
#   后端: http://127.0.0.1:8000  (POST /api/supplyai/...)
#   前端: http://127.0.0.1:5173/SupplyAI.html
#   API 调试: http://127.0.0.1:5173/api-smoke.html
#   后端文档: http://127.0.0.1:8000/docs

set -e
cd "$(dirname "$0")"

# 允许新机器只配置 supplyai-backend/.env 即可启动。
# 仅导出 KEY=VALUE 简单行；复杂 shell 表达式仍建议用户自己 export。
if [[ -f "supplyai-backend/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "supplyai-backend/.env"
  set +a
fi

# ── 前置检查 ────────────────────────────────────────────
if [[ -z "$SUPPLY_DASH_API_KEY" && -z "$DASHSCOPE_API_KEY" ]]; then
  echo "✘ 未检测到 SUPPLY_DASH_API_KEY 或 DASHSCOPE_API_KEY 环境变量。"
  echo "  请复制 supplyai-backend/env.example 为 supplyai-backend/.env 并填写 API key。"
  echo "  AI 端点(/ai/explain, /ai/chat)启动后会立即报错。"
  exit 1
fi

# 自部署 endpoint 证书 hostname 不匹配时自动绕过(本地开发)
export SUPPLY_DASH_VERIFY_SSL=${SUPPLY_DASH_VERIFY_SSL:-false}
export AI_PROVIDER=${AI_PROVIDER:-dashscope}

KEY_PREVIEW="${SUPPLY_DASH_API_KEY:-$DASHSCOPE_API_KEY}"
echo "✓ AI provider=$AI_PROVIDER"
echo "✓ AI key=${KEY_PREVIEW:0:6}…(长度 ${#KEY_PREVIEW})"
[[ -n "$SUPPLY_DASH_URL" ]] && echo "✓ AI url=$SUPPLY_DASH_URL"
echo "✓ verify_ssl=$SUPPLY_DASH_VERIFY_SSL"
echo

# 端口占用清理
for port in 8000 5173; do
  pid=$(lsof -ti:$port 2>/dev/null || true)
  if [[ -n "$pid" ]]; then
    echo "→ 端口 $port 被 PID $pid 占用,先 kill"
    kill $pid 2>/dev/null || true
    sleep 1
  fi
done

# 1. 后端 (uv-managed)
cd supplyai-backend
echo "→ 启动后端 (uvicorn :8000)…"
uv run uvicorn supplyai.main:app --host 127.0.0.1 --port 8000 --no-access-log &
BACKEND_PID=$!
cd ..

# 2. 前端静态文件
cd SupplyAI
echo "→ 启动前端静态服务 (:5173)…"
python3 -m http.server 5173 --bind 127.0.0.1 >/dev/null 2>&1 &
FRONTEND_PID=$!
cd ..

cleanup() {
  echo
  echo "→ 停止后端 (PID $BACKEND_PID) + 前端 (PID $FRONTEND_PID)…"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  wait 2>/dev/null
  exit 0
}
trap cleanup INT TERM

sleep 3
echo
echo "════════════════════════════════════════════════════════"
echo " ✓ SupplyAI 已启动 (按 Ctrl-C 停止)"
echo
echo " 主页:      http://127.0.0.1:5173/SupplyAI.html"
echo " API 调试:  http://127.0.0.1:5173/api-smoke.html"
echo " 后端文档:  http://127.0.0.1:8000/docs"
echo "════════════════════════════════════════════════════════"
echo
wait
