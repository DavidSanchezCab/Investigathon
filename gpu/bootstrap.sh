#!/usr/bin/env bash
set -euo pipefail
umask 077

WORK_DIR="${INVESTIGATHON_ROOT:-${HOME}/investigathon}"
mkdir -p "$WORK_DIR/logs" "$WORK_DIR/models" "$WORK_DIR/results" "$WORK_DIR/cache/huggingface"

# A second invocation must not overwrite the active invocation's status.
exec 9>"$WORK_DIR/.setup.lock"
if ! flock -n 9; then
    printf 'Another bootstrap is running; see %s/setup-status.txt\n' "$WORK_DIR" >&2
    exit 75
fi

LOG_FILE="$WORK_DIR/logs/bootstrap-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
STATUS_FILE="$WORK_DIR/setup-status.txt"
LLAMA_DIR="$WORK_DIR/llama.cpp"
BUILD_DIR="$LLAMA_DIR/build"
PYTHON="$WORK_DIR/.venv/bin/python"
CUDA_ROOT="/usr/local/cuda-12.8"
BUILD_PID=""
LLAMA_COMMIT="pending"
STAGE="initialization"
exec > >(tee -a "$LOG_FILE") 2>&1

write_status() {
    local status="$1" code="${2:-0}"
    local status_tmp="${STATUS_FILE}.tmp.$$"
    printf 'status=%s\nupdated_at=%s\nstage=%s\nexit_code=%s\nllama_cpp_commit=%s\nlog=%s\n' \
        "$status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$STAGE" "$code" "$LLAMA_COMMIT" "$LOG_FILE" \
        > "$status_tmp"
    mv -- "$status_tmp" "$STATUS_FILE"
}

on_exit() {
    local code=$?
    trap - EXIT INT TERM
    if [[ -n "$BUILD_PID" ]] && kill -0 "$BUILD_PID" 2>/dev/null; then
        # Only terminate the build started by this invocation.
        if command -v pkill >/dev/null 2>&1; then
            pkill -TERM -P "$BUILD_PID" 2>/dev/null || true
        fi
        kill -TERM "$BUILD_PID" 2>/dev/null || true
        wait "$BUILD_PID" 2>/dev/null || true
    fi
    if [[ "$code" -eq 0 ]]; then
        write_status success 0
        printf 'Bootstrap finished. No inference test has been run.\n'
    else
        write_status error "$code"
        printf 'Bootstrap failed at stage %s (exit %s). Log: %s\n' "$STAGE" "$code" "$LOG_FILE" >&2
    fi
    exit "$code"
}
trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
write_status running

for executable in python3.10 git cmake make flock tee; do
    command -v "$executable" >/dev/null 2>&1 || {
        printf 'Missing required executable: %s\n' "$executable" >&2
        exit 1
    }
done
[[ -x "$CUDA_ROOT/bin/nvcc" ]] || {
    printf 'CUDA compiler not found: %s/bin/nvcc\n' "$CUDA_ROOT" >&2
    exit 1
}
[[ -f "$WORK_DIR/gpu/fetch_models.py" ]] || {
    printf 'Upload gpu/fetch_models.py before running bootstrap.\n' >&2
    exit 1
}

export HF_HOME="$WORK_DIR/cache/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export PATH="$CUDA_ROOT/bin:$PATH"
export CUDACXX="$CUDA_ROOT/bin/nvcc"
export CUDAToolkit_ROOT="$CUDA_ROOT"
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2

STAGE="python_environment"
write_status running
if [[ ! -x "$PYTHON" ]] || ! "$PYTHON" -m pip --version >/dev/null 2>&1; then
    # Ubuntu's system Python may lack ensurepip. Bootstrap into our own directory
    # instead of installing system packages or requiring sudo.
    python3.10 -m pip install --disable-pip-version-check --no-cache-dir \
        --target "$WORK_DIR/bootstrap-tools" virtualenv
    PYTHONPATH="$WORK_DIR/bootstrap-tools" python3.10 -m virtualenv "$WORK_DIR/.venv"
fi
"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 10), sys.version'
"$PYTHON" -m pip install --disable-pip-version-check --upgrade pip
"$PYTHON" -m pip install --disable-pip-version-check -r "$WORK_DIR/gpu/requirements.txt"

STAGE="llama_cpp_source"
write_status running
if [[ ! -e "$LLAMA_DIR" ]]; then
    git init "$LLAMA_DIR"
    git -C "$LLAMA_DIR" remote add origin https://github.com/ggml-org/llama.cpp.git
    git -C "$LLAMA_DIR" fetch --depth 1 origin 9ae73e68f5a78933c0d988bbd17bf4647ad6a0b2
    git -C "$LLAMA_DIR" checkout --detach FETCH_HEAD
elif [[ ! -d "$LLAMA_DIR/.git" ]]; then
    printf 'Existing llama.cpp directory is not a Git checkout; refusing to replace it.\n' >&2
    exit 1
fi
ORIGIN_URL="$(git -C "$LLAMA_DIR" remote get-url origin)"
case "$ORIGIN_URL" in
    https://github.com/ggml-org/llama.cpp|https://github.com/ggml-org/llama.cpp.git) ;;
    *) printf 'Unexpected llama.cpp origin: %s\n' "$ORIGIN_URL" >&2; exit 1 ;;
esac
git -C "$LLAMA_DIR" diff --quiet HEAD -- || {
    printf 'Tracked llama.cpp source files are modified; refusing an unrecorded build.\n' >&2
    exit 1
}
# Keep an existing checkout at its current commit; never pull implicitly.
LLAMA_COMMIT="$(git -C "$LLAMA_DIR" rev-parse HEAD)"
printf '%s\n' "$LLAMA_COMMIT" > "$WORK_DIR/llama.cpp.commit"
printf 'Using llama.cpp commit %s\n' "$LLAMA_COMMIT"

STAGE="configure_cuda"
write_status running
cmake -S "$LLAMA_DIR" -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DGGML_CUDA=ON \
    -DCMAKE_CUDA_COMPILER="$CUDA_ROOT/bin/nvcc" \
    -DCUDAToolkit_ROOT="$CUDA_ROOT" \
    -DCMAKE_CUDA_ARCHITECTURES=75 \
    -DLLAMA_CURL=OFF \
    -DLLAMA_OPENSSL=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TOOLS=ON \
    -DLLAMA_BUILD_SERVER=ON \
    -DLLAMA_BUILD_APP=OFF

STAGE="build_and_download"
write_status running
# Four workers fit the measured RAM budget on the assigned four-vCPU host.
cmake --build "$BUILD_DIR" --target llama-cli llama-server --parallel 4 &
BUILD_PID=$!
FETCH_CODE=0
"$PYTHON" "$WORK_DIR/gpu/fetch_models.py" || FETCH_CODE=$?
BUILD_CODE=0
wait "$BUILD_PID" || BUILD_CODE=$?
BUILD_PID=""
if [[ "$FETCH_CODE" -ne 0 || "$BUILD_CODE" -ne 0 ]]; then
    printf 'Download exit code: %s; build exit code: %s\n' "$FETCH_CODE" "$BUILD_CODE" >&2
    exit 1
fi

STAGE="conversion_dependencies"
write_status running
# CPU-only Torch avoids downloading CUDA wheels for the conversion process.
"$PYTHON" -m pip install --disable-pip-version-check torch==2.11.0 \
    --index-url https://download.pytorch.org/whl/cpu
"$PYTHON" -m pip install --disable-pip-version-check \
    -r "$LLAMA_DIR/requirements/requirements-convert_lora_to_gguf.txt"
"$PYTHON" -m pip check
"$PYTHON" -m pip freeze > "$WORK_DIR/requirements.lock.txt"

STAGE="convert_adapters"
write_status running
for adapter in hacker control; do
    "$PYTHON" "$LLAMA_DIR/convert_lora_to_gguf.py" \
        --base "$WORK_DIR/models/base-config" \
        --outtype f16 \
        --outfile "$WORK_DIR/models/${adapter}.gguf" \
        "$WORK_DIR/models/$adapter"
done

STAGE="validate_adapters"
write_status running
"$PYTHON" "$WORK_DIR/gpu/validate_adapters.py"

STAGE="complete"
