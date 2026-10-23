#!/usr/bin/env bash
# Benchmark Runner (queue-based concurrency)

set -euo pipefail

# =========================================================
# Configuration
# =========================================================

DOMAINS=(
    "attraction" 
    "attraction_cafe" 
    "attraction_dessert"
    "attraction_food_dining_cafe" "bar" "cafe" "cruise"
    "dessert" "flight" "flight_hotel_attraction_rental"
    "flight_hotel_bar" "food_and_dining" "food_and_dining_hotel"
    "hotel" "hotel_attraction_rental" "hotel_rental"
    "hotel_rental_food_bar" "kayak_rental" "live_show"
    "live_show_food_dining"
    "vehicle_rental" "vehicle_rental_attraction"
    "vehicle_rental_food_and_dining_hotel"
    "multi_8domain" "multi_11domain"
)

MODEL="${MODEL_NAME:-openai/gpt-oss-20b}"

BATCH_SIZE=30
N=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =========================================================
# Per-domain config
# =========================================================

declare -A MAX_TURNS_MAP=(
    ["attraction"]=25 ["bar"]=25 ["cafe"]=25 ["cruise"]=25
    ["dessert"]=25 ["flight"]=25 ["food_and_dining"]=25
    ["hotel"]=25 ["kayak_rental"]=25 ["live_show"]=25
    ["sport_event"]=25 ["train"]=25 ["vehicle_rental"]=25

    ["attraction_cafe"]=25 ["attraction_dessert"]=25
    ["attraction_food_dining_cafe"]=25
    ["flight_hotel_attraction_rental"]=25
    ["flight_hotel_bar"]=25
    ["food_and_dining_hotel"]=25
    ["hotel_attraction_rental"]=25
    ["hotel_rental"]=25
    ["hotel_rental_food_bar"]=25
    ["live_show_food_dining"]=25
    ["vehicle_rental_attraction"]=25
    ["vehicle_rental_food_and_dining_hotel"]=25

    ["multi_8domain"]=50 ["multi_11domain"]=50
)

declare -A TOTALS_MAP=(
    ["attraction"]=25 ["bar"]=25 ["cafe"]=25 ["cruise"]=25
    ["dessert"]=25 ["flight"]=25 ["food_and_dining"]=25
    ["hotel"]=25 ["kayak_rental"]=25 ["live_show"]=25
    ["sport_event"]=25 ["train"]=25 ["vehicle_rental"]=25

    ["attraction_cafe"]=20 ["attraction_dessert"]=20
    ["attraction_food_dining_cafe"]=20
    ["flight_hotel_attraction_rental"]=20
    ["flight_hotel_bar"]=20
    ["food_and_dining_hotel"]=20
    ["hotel_attraction_rental"]=20
    ["hotel_rental"]=20
    ["hotel_rental_food_bar"]=20
    ["live_show_food_dining"]=20
    ["vehicle_rental_attraction"]=20
    ["vehicle_rental_food_and_dining_hotel"]=20

    ["multi_8domain"]=5
    ["multi_11domain"]=5
)

# =========================================================
# Globals & State
# =========================================================

GRAND_PASS=0
GRAND_FAIL=0
GRAND_TOTAL=0

declare -A DOMAIN_PASS_MAP
declare -A DOMAIN_FAIL_MAP

# Initialize domain trackers
for d in "${DOMAINS[@]}"; do
    DOMAIN_PASS_MAP[$d]=0
    DOMAIN_FAIL_MAP[$d]=0
done

# Queue state
PIDS=()
IDS=()
FAIL=0
ERRORS=()

# =========================================================
# Helpers
# =========================================================

log() { echo "[INFO] $1"; }
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; }

# =========================================================
# Functions
# =========================================================

launch_job() {
    local domain="$1"
    local id="$2"
    local run_id="$3"
    local log_dir="$4"
    local max_turns="$5"

    nohup uv run python "$SCRIPT_DIR/scripts/run_simulation.py" \
        --domain "$domain" \
        --conversation_id "$id" \
        --max_turns "$max_turns" \
        --assistant_model_name "$MODEL" \
        --run_dir "$run_id" \
        --save \
        > "$log_dir/${id}.log" 2>&1 &

    local pid=$!

    PIDS+=("$pid")
    IDS+=("$id")

    echo "$pid" > "$log_dir/${id}.pid"

    log "Started conversation_id=$id (PID=$pid)"
}

wait_one() {
    wait -n
    local status=$?

    # find finished job
    for i in "${!PIDS[@]}"; do
        if ! kill -0 "${PIDS[$i]}" 2>/dev/null; then
            local cid="${IDS[$i]}"

            if (( status == 0 )); then
                pass "conversation_id=$cid"
            else
                fail "conversation_id=$cid"
                FAIL=$((FAIL + 1))
                ERRORS+=("$cid")
            fi

            unset 'PIDS[$i]'
            unset 'IDS[$i]'

            PIDS=("${PIDS[@]}")
            IDS=("${IDS[@]}")
            break
        fi
    done
}

validate() {
    local d="$1"
    [[ -n "${MAX_TURNS_MAP[$d]+x}" ]] || { echo "Missing MAX_TURNS_MAP for $d"; exit 1; }
    [[ -n "${TOTALS_MAP[$d]+x}" ]] || { echo "Missing TOTALS_MAP for $d"; exit 1; }
}

# =========================================================
# Main
# =========================================================

echo "========================================"
echo "Benchmark Runner (QUEUE MODE)"
echo "Model: $MODEL"
echo "Domains: ${#DOMAINS[@]}"
echo "Batch size: $BATCH_SIZE"
echo "Runs: $N"
echo "========================================"

# Loop 1: Iterate over runs
for run_num in $(seq 1 "$N"); do
    
    RUN_TS=$(date +%Y%m%d_%H%M%S)
    echo ""
    echo "========================================"
    echo "STARTING RUN $run_num / $N"
    echo "========================================"

    # Loop 2: Iterate over all domains for the current run
    for DOMAIN in "${DOMAINS[@]}"; do

        validate "$DOMAIN"

        MAX_TURNS="${MAX_TURNS_MAP[$DOMAIN]}"
        TOTAL="${TOTALS_MAP[$DOMAIN]}"

        log "DOMAIN=$DOMAIN | max_turns=$MAX_TURNS | total=$TOTAL | run=$run_num"

        RUN_ID="run_${RUN_TS}_${run_num}"
        LOG_DIR="$SCRIPT_DIR/logs/$MODEL/$DOMAIN/$RUN_ID"
        mkdir -p "$LOG_DIR"

        PIDS=()
        IDS=()
        FAIL=0
        ERRORS=()

        for id in $(seq 1 "$TOTAL"); do

            launch_job "$DOMAIN" "$id" "$RUN_ID" "$LOG_DIR" "$MAX_TURNS"

            while (( ${#PIDS[@]} >= BATCH_SIZE )); do
                wait_one
            done
        done

        while (( ${#PIDS[@]} > 0 )); do
            wait_one
        done

        PASS=$((TOTAL - FAIL))

        # Track totals per domain across runs
        DOMAIN_PASS_MAP[$DOMAIN]=$((DOMAIN_PASS_MAP[$DOMAIN] + PASS))
        DOMAIN_FAIL_MAP[$DOMAIN]=$((DOMAIN_FAIL_MAP[$DOMAIN] + FAIL))

        # Track grand totals
        GRAND_PASS=$((GRAND_PASS + PASS))
        GRAND_FAIL=$((GRAND_FAIL + FAIL))
        GRAND_TOTAL=$((GRAND_TOTAL + TOTAL))

        echo ""
        echo "Result for $DOMAIN (Run $run_num): $PASS/$TOTAL passed"

        if (( ${#ERRORS[@]} > 0 )); then
            echo "Failed IDs: ${ERRORS[*]}"
        fi
        echo "----------------------------------------"
    done
done

# =========================================================
# Final Summaries
# =========================================================

echo ""
echo "========================================"
echo "DOMAIN SUMMARIES (Across $N Runs)"
echo "========================================"
for DOMAIN in "${DOMAINS[@]}"; do
    D_TOTAL=$((TOTALS_MAP[$DOMAIN] * N))
    D_PASS=${DOMAIN_PASS_MAP[$DOMAIN]}
    D_FAIL=${DOMAIN_FAIL_MAP[$DOMAIN]}
    echo "Domain: $DOMAIN | Passed: $D_PASS/$D_TOTAL | Failed: $D_FAIL/$D_TOTAL"
done

echo ""
echo "========================================"
echo "FINAL GRAND RESULT: $GRAND_PASS/$GRAND_TOTAL passed"
echo "========================================"
