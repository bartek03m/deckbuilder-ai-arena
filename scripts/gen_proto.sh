#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."      # always run from the repo root

python -m grpc_tools.protoc \
  -I proto \
  --python_out=server \
  --pyi_out=server \
  --grpc_python_out=server \
  proto/salon_proto/game.proto

#to generate in Git Bash: bash scripts/gen_proto.sh