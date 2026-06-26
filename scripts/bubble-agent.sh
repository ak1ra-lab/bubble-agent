#!/usr/bin/env bash

# Run your coding agent in a bubble. (Bash implementation)
#
# Uses bubblewrap to sandbox coding agents with configurable
# bind mounts. Kept in sync with bubble-agent (Python).
#
# Config: ~/.config/bubble-agent/bubble-agent.conf

set -o errexit -o nounset -o errtrace

# Configuration
readonly CONFIG_DIR="${BUBBLE_AGENT_CONFIG_DIR:-${HOME}/.config/bubble-agent}"
readonly CONFIG_FILE="${BUBBLE_AGENT_CONFIG_FILE:-${CONFIG_DIR}/bubble-agent.conf}"
readonly TARGET_BIN="${BUBBLE_AGENT_BIN:-opencode}"

# Logging Subsystem
declare -g LOG_LEVEL="${LOG_LEVEL:-INFO}"
declare -g -A LOG_PRIORITY=(
    ["DEBUG"]=10
    ["INFO"]=20
    ["WARNING"]=30
    ["ERROR"]=40
    ["CRITICAL"]=50
)

log_color() {
    local color="${1}"
    shift
    if [[ -t 2 ]]; then
        printf "\x1b[0;%sm%s\x1b[0m\n" "${color}" "${*}" >&2
    else
        printf "%s\n" "${*}" >&2
    fi
}

log_message() {
    local color="${1}"
    local level="${2}"
    shift 2

    if [[ "${LOG_PRIORITY[${level}]}" -lt "${LOG_PRIORITY[${LOG_LEVEL}]}" ]]; then
        return 0
    fi

    log_color "${color}" "${*}"
}

log_error() { log_message 31 "ERROR" "${@}"; }
log_info() { log_message 32 "INFO" "${@}"; }
log_warning() { log_message 33 "WARNING" "${@}"; }
log_debug() { log_message 34 "DEBUG" "${@}"; }

# Dependency Check
require_command() {
    local missing=()
    for c in "${@}"; do
        if ! command -v "${c}" >/dev/null 2>&1; then
            missing+=("${c}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Required command(s) not installed: ${missing[*]}"
        exit 1
    fi
}

# Expand ~ and environment variables ($VAR, ${VAR}) in a path string
expand_env_vars() {
    local str="$1"
    local var_name var_value

    str="${str/#\~/${HOME}}"

    while [[ "${str}" =~ \$\{([A-Za-z_][A-Za-z0-9_]*)\} ]]; do
        var_name="${BASH_REMATCH[1]}"
        var_value="${!var_name}"
        str="${str//\$\{${var_name}\}/${var_value}}"
    done

    while [[ "${str}" =~ \$([A-Za-z_][A-Za-z0-9_]*) ]]; do
        var_name="${BASH_REMATCH[1]}"
        var_value="${!var_name}"
        str="${str//\$${var_name}/${var_value}}"
    done

    echo "${str}"
}

# Load bind mounts from config file into the target array
# Also collects path-prepend and path-append entries
load_config_binds() {
    local config_file="$1"
    local -n out_args="$2"
    local -n out_path_prepend="$3"
    local -n out_path_append="$4"
    local has_explicit_path=0
    local count=0

    log_info "Loading binds from: ${config_file}"
    log_info "----------------------------------------"

    while IFS= read -r line || [[ -n "${line}" ]]; do
        [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue

        local bind_type src dest
        IFS=':' read -r bind_type src dest <<<"${line}"
        [[ -z "${bind_type}" || -z "${src}" ]] && continue
        if [[ -z "${dest}" && ! "${bind_type}" =~ ^(env|setenv|path-prepend|path-append)$ ]]; then
            continue
        fi

        src="$(expand_env_vars "${src}")"
        dest="$(expand_env_vars "${dest}")"

        case "${bind_type}" in
            bind | ro-bind)
                if [[ -e "${src}" ]]; then
                    out_args+=(--"${bind_type}" "${src}" "${dest}")
                    log_info "[${bind_type}] ${src} -> ${dest}"
                    count=$((count + 1))
                else
                    log_warning "[${bind_type}] SKIP: ${src} (not found)"
                fi
                ;;
            bind-try | ro-bind-try | symlink)
                out_args+=(--"${bind_type}" "${src}" "${dest}")
                log_info "[${bind_type}] ${src} -> ${dest}"
                count=$((count + 1))
                ;;
            env | setenv)
                if [[ "${src}" == "PATH" ]]; then
                    has_explicit_path=1
                fi
                out_args+=(--setenv "${src}" "${dest}")
                log_info "[env] ${src}=${dest}"
                count=$((count + 1))
                ;;
            path-prepend)
                out_path_prepend+=("${src}")
                log_info "[path-prepend] ${src}"
                count=$((count + 1))
                ;;
            path-append)
                out_path_append+=("${src}")
                log_info "[path-append] ${src}"
                count=$((count + 1))
                ;;
        esac
    done <"${config_file}"

    log_info "----------------------------------------"
    log_info "Total custom binds loaded: ${count}"
    log_info ""

    return "${has_explicit_path}"
}

# Main function
main() {
    require_command bwrap "${TARGET_BIN}"

    local target_bin_path
    target_bin_path="$(command -v "${TARGET_BIN}")"

    local args=(
        --unshare-pid
        --die-with-parent
        --new-session
        --clearenv
        --setenv HOME "${HOME}"
        --setenv USER "${USER:-}"
        --setenv LOGNAME "${LOGNAME:-}"
        --setenv TERM "${TERM:-}"
        --setenv LANG "${LANG:-C.UTF-8}"
        --setenv SHELL "${SHELL:-/bin/sh}"
        --share-net
        --dev /dev
        --ro-bind /usr /usr
        --ro-bind /etc /etc
        --ro-bind-try /lib /lib
        --ro-bind-try /lib64 /lib64
        --ro-bind-try /lib32 /lib32
        --ro-bind-try /sys /sys
        --symlink usr/bin /bin
        --symlink usr/sbin /sbin
        --proc /proc
        --tmpfs /tmp
        --tmpfs /run
        --dir "/run/user/$(id -u)"
        --setenv XDG_RUNTIME_DIR "/run/user/$(id -u)"
        --dir /var
        --symlink ../tmp var/tmp
    )

    if [[ -L /etc/resolv.conf ]]; then
        local real_resolv
        real_resolv="$(realpath /etc/resolv.conf)"
        local real_dir
        real_dir="$(dirname "${real_resolv}")"
        if [[ -d "${real_dir}" ]]; then
            args+=(--ro-bind "${real_dir}" "${real_dir}")
            log_info "resolv.conf symlink resolved: /etc/resolv.conf -> ${real_resolv}"
        fi
    fi

    local path_prepend=() path_append=()
    local has_explicit_path=0

    if [[ -f "${CONFIG_FILE}" ]]; then
        has_explicit_path=0
        load_config_binds "${CONFIG_FILE}" args path_prepend path_append || has_explicit_path=$?
    fi

    # Build PATH: prepend dirs + inherited host PATH + append dirs (unless explicit)
    local merged_path
    if [[ "${has_explicit_path}" -eq 0 ]]; then
        local -a all_paths=()
        local -A seen=()
        for p in "${path_prepend[@]}"; do
            if [[ -n "${p}" && -z "${seen[${p}]:-}" ]]; then
                seen["${p}"]=1
                all_paths+=("${p}")
            fi
        done
        local IFS=':'
        for p in ${PATH}; do
            if [[ -n "${p}" && -z "${seen[${p}]:-}" ]]; then
                seen["${p}"]=1
                all_paths+=("${p}")
            fi
        done
        for p in "${path_append[@]}"; do
            if [[ -n "${p}" && -z "${seen[${p}]:-}" ]]; then
                seen["${p}"]=1
                all_paths+=("${p}")
            fi
        done
        merged_path="$(
            IFS=':'
            echo "${all_paths[*]}"
        )"
    fi

    if [[ -n "${merged_path:-}" ]]; then
        args+=(--setenv PATH "${merged_path}")
    fi

    log_debug "bwrap args: ${args[*]} -- ${target_bin_path} ${*}"
    exec bwrap "${args[@]}" -- "${target_bin_path}" "${@}"
}

main "${@}"
