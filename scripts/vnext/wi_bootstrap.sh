#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Reusable project enrollment. The project is the current directory unless
# --repo names another checkout. The protocol root is this script's repository.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_root="$(cd "${script_dir}/.." && pwd)"
protocol_root="${WI_PROTOCOL_ROOT:-$default_root}"
exec python3 "${script_dir}/wi_bootstrap.py" --protocol-root "${protocol_root}" "$@"
