#!/usr/bin/env bash
set -euo pipefail

_cmo_env_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

_cmo_detect_build_dir() {
  local root_dir="$1"
  local candidate
  for candidate in \
    "${CMO_BUILD_DIR:-}" \
    "build-workshop" \
    "build-gpu" \
    "build" \
    "build-facade-local"
  do
    [[ -n "${candidate}" ]] || continue
    if [[ "${candidate}" != /* ]]; then
      candidate="${root_dir}/${candidate}"
    fi
    if [[ -d "${candidate}" ]] && compgen -G "${candidate}/ef_py*.so" >/dev/null; then
      printf '%s\n' "${candidate}"
      return 0
    fi
    if [[ -d "${candidate}" && -e "${candidate}/ef_py" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

_cmo_has_ef_py_artifact() {
  local build_dir="$1"
  [[ -n "${build_dir}" ]] || return 1
  if compgen -G "${build_dir}/ef_py*.so" >/dev/null; then
    return 0
  fi
  [[ -e "${build_dir}/ef_py" ]]
}

_cmo_resolve_build_candidate() {
  local root_dir="$1"
  local candidate
  for candidate in \
    "${CMO_BUILD_DIR:-}" \
    "build-workshop" \
    "build-gpu" \
    "build" \
    "build-facade-local"
  do
    [[ -n "${candidate}" ]] || continue
    if [[ "${candidate}" != /* ]]; then
      candidate="${root_dir}/${candidate}"
    fi
    if [[ -d "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

cmo_activate_env() {
  local root_dir
  root_dir="$(_cmo_env_root)"
  local venv_python="${root_dir}/.venv/bin/python"

  if [[ ! -x "${venv_python}" ]]; then
    echo "[cmo_env] missing repository virtualenv: ${venv_python}" >&2
    echo "[cmo_env] create it with: python -m venv .venv" >&2
    return 1
  fi

  export CMO_REPO_ROOT="${root_dir}"
  export CMO_PYTHON="${venv_python}"

  local build_dir
  build_dir="$(_cmo_detect_build_dir "${root_dir}" || true)"
  if [[ -n "${build_dir}" ]]; then
    export CMO_BUILD_DIR="${build_dir}"
    export PYTHONPATH="${build_dir}:${root_dir}${PYTHONPATH:+:${PYTHONPATH}}"
  else
    export PYTHONPATH="${root_dir}${PYTHONPATH:+:${PYTHONPATH}}"
  fi
}

cmo_python() {
  cmo_activate_env
  "${CMO_PYTHON}" "$@"
}

cmo_env_summary() {
  cmo_activate_env
  cat <<EOF
CMO_REPO_ROOT=${CMO_REPO_ROOT}
CMO_PYTHON=${CMO_PYTHON}
CMO_BUILD_DIR=${CMO_BUILD_DIR:-}
PYTHONPATH=${PYTHONPATH:-}
EOF
}

cmo_env_validate() {
  local root_dir
  root_dir="$(_cmo_env_root)"
  local venv_python="${root_dir}/.venv/bin/python"
  local build_dir=""
  local build_candidate=""

  if [[ ! -d "${root_dir}" ]]; then
    echo "[cmo_env] repository root is not accessible: ${root_dir}" >&2
    return 1
  fi

  if [[ ! -x "${venv_python}" ]]; then
    echo "[cmo_env] missing repository virtualenv: ${venv_python}" >&2
    echo "[cmo_env] create it with: python -m venv .venv" >&2
    return 2
  fi

  build_dir="$(_cmo_detect_build_dir "${root_dir}" || true)"
  if [[ -n "${build_dir}" ]]; then
    cat <<EOF
[cmo_env] validation ok
CMO_REPO_ROOT=${root_dir}
CMO_PYTHON=${venv_python}
CMO_BUILD_DIR=${build_dir}
EOF
    return 0
  fi

  build_candidate="$(_cmo_resolve_build_candidate "${root_dir}" || true)"
  if [[ -z "${build_candidate}" ]]; then
    echo "[cmo_env] missing build directory" >&2
    echo "[cmo_env] searched: ${CMO_BUILD_DIR:-build-workshop, build-gpu, build, build-facade-local}" >&2
    echo "[cmo_env] configure and build the project before running maintained workflows" >&2
    return 3
  fi

  if ! _cmo_has_ef_py_artifact "${build_candidate}"; then
    echo "[cmo_env] build directory exists but ef_py artifact is missing: ${build_candidate}" >&2
    echo "[cmo_env] expected one of: ${build_candidate}/ef_py*.so or ${build_candidate}/ef_py" >&2
    return 4
  fi

  echo "[cmo_env] validation failed for an unknown reason" >&2
  return 5
}

cmo_env_validate_rl() {
  cmo_activate_env
  "${CMO_PYTHON}" - <<'PY'
import importlib
import sys

required = ("ef_py", "gymnasium", "stable_baselines3", "torch")
failed = False

for name in required:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        failed = True
        print(f"[cmo_env] import failed: {name}: {exc}", file=sys.stderr)
        continue
    version = getattr(module, "__version__", None)
    location = getattr(module, "__file__", None)
    detail = []
    if version:
        detail.append(f"version={version}")
    if location:
        detail.append(f"file={location}")
    suffix = f" ({', '.join(detail)})" if detail else ""
    print(f"[cmo_env] import ok: {name}{suffix}")

if failed:
    print(
        "[cmo_env] RL validation failed; install the `.[rl]` extra or the "
        "equivalent direct dependencies, and rebuild ef_py if that import failed.",
        file=sys.stderr,
    )
    sys.exit(6)

print("[cmo_env] RL validation ok")
PY
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  if [[ $# -eq 0 ]]; then
    cmo_env_summary
    exit 0
  fi
  case "$1" in
    validate)
      shift
      cmo_env_validate "$@"
      ;;
    validate-rl)
      shift
      cmo_env_validate_rl "$@"
      ;;
    summary)
      shift
      cmo_env_summary "$@"
      ;;
    python)
      shift
      cmo_python "$@"
      ;;
    *)
      cmo_python "$@"
      ;;
  esac
fi
