#!/bin/sh

# Synology boot hook for the two Alphabet NAS -> ECS reverse tunnels.
# Install as /usr/local/etc/rc.d/zhuojian-nas-tunnels.sh, owned by root and mode 700.

PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
HOME_DIR=/var/services/homes/mawen
KNOWN_HOSTS="$HOME_DIR/.ssh/known_hosts"
REMOTE_USER=zjnas-tunnel
REMOTE_PORT=10445
LOCAL_SMB_HOST=127.0.0.1
LOCAL_SMB_PORT=445

worker() {
    label="$1"
    host="$2"
    key="$3"
    ssh_pid=""

    terminate_worker() {
        if [ -n "$ssh_pid" ]; then
            kill "$ssh_pid" 2>/dev/null || true
            wait "$ssh_pid" 2>/dev/null || true
        fi
        exit 0
    }

    trap terminate_worker TERM INT

    while :; do
        /bin/ssh -NT \
            -i "$key" \
            -o BatchMode=yes \
            -o ConnectTimeout=10 \
            -o ExitOnForwardFailure=yes \
            -o IdentitiesOnly=yes \
            -o LogLevel=ERROR \
            -o ServerAliveCountMax=3 \
            -o ServerAliveInterval=30 \
            -o StrictHostKeyChecking=yes \
            -o UserKnownHostsFile="$KNOWN_HOSTS" \
            -R "127.0.0.1:${REMOTE_PORT}:${LOCAL_SMB_HOST}:${LOCAL_SMB_PORT}" \
            "${REMOTE_USER}@${host}" &
        ssh_pid=$!
        wait "$ssh_pid"
        ssh_pid=""
        sleep 5
    done
}

pid_file() {
    printf '/var/run/zhuojian-nas-tunnel-%s.pid' "$1"
}

log_file() {
    printf '/var/log/zhuojian-nas-tunnel-%s.log' "$1"
}

start_one() {
    label="$1"
    host="$2"
    key="$3"
    pidfile="$(pid_file "$label")"

    if [ -s "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        return 0
    fi

    rm -f "$pidfile"
    /bin/nohup /bin/sh "$0" worker "$label" "$host" "$key" \
        >>"$(log_file "$label")" 2>&1 &
    pid=$!
    printf '%s\n' "$pid" >"$pidfile"
    sleep 1
    kill -0 "$pid" 2>/dev/null
}

stop_one() {
    label="$1"
    pidfile="$(pid_file "$label")"

    if [ ! -s "$pidfile" ]; then
        return 0
    fi

    pid="$(cat "$pidfile")"
    kill "$pid" 2>/dev/null || true
    count=0
    while kill -0 "$pid" 2>/dev/null && [ "$count" -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pidfile"
}

status_one() {
    label="$1"
    pidfile="$(pid_file "$label")"
    if [ -s "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        printf '%s running pid=%s\n' "$label" "$(cat "$pidfile")"
        return 0
    fi
    printf '%s stopped\n' "$label"
    return 1
}

start_all() {
    start_one aifabei-hk-01 8.218.208.205 "$HOME_DIR/.ssh/zhuojian_nas_8_218_208_205"
    start_one aifabei-hk-48 47.243.48.78 "$HOME_DIR/.ssh/zhuojian_nas_47_243_48_78"
}

stop_all() {
    stop_one aifabei-hk-01
    stop_one aifabei-hk-48
}

status_all() {
    result=0
    status_one aifabei-hk-01 || result=1
    status_one aifabei-hk-48 || result=1
    return "$result"
}

case "${1:-}" in
    worker)
        shift
        worker "$@"
        ;;
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        start_all
        ;;
    status)
        status_all
        ;;
    *)
        printf 'usage: %s {start|stop|restart|status}\n' "$0" >&2
        exit 2
        ;;
esac
