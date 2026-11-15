#!/usr/bin/env bash
# Plan and run the AUX route of domains/presence-edit.jsonld.
#   aux.sh plan   <goal> [problem]   print the planner's steps for a goal or composite method
#   aux.sh run    <goal> [problem]   plan, then run every step through `aux.sh action`
#   aux.sh action <name>             run one primitive action
#   aux.sh goals                     list the goals and composite methods of the domain
# Env: PERSONA_PLAN (planner binary; `pixi run build-planner` makes .planner/), DRY_RUN=1 (print, do not run),
#      GPU_HOST (ssh alias, default fedora), REPRO (path of the repro scripts on that host), HAIRDECK (HairDeck checkout on this machine).
set -euo pipefail
cd "$(dirname "$0")/.."
# The domain is its six modules, composed by the planner in this order (a method's alternatives are tried in the order the modules come):
# the measured-lag route in aux-motion is listed before the class prior inside it, so the measured route comes first when its inputs are on hand.
MODS=(presence-body presence-avatar omnigen2-edit aux-mesh aux-labels aux-motion aux-rig obstacle-course relay-loop)
DOMAIN=${DOMAIN:-$(printf "domains/modules/%s.jsonld," "${MODS[@]}" | sed 's/,$//')}
PLANNER=${PERSONA_PLAN:-.planner/.lake/build/bin/persona_plan}
REPRO_SRC=${REPRO_SRC:-$HOME/.hermes/cache/scratch/repro-space}   # usd_io.py and units.py live in the repro Space
USDPY="cd $REPRO_SRC && pixi run -q -e mac python"
GPU_HOST=${GPU_HOST:-fedora}; REPRO=${REPRO:-'$HOME/og2/spike/repro'}
HAIRDECK=${HAIRDECK:-$HOME/.hermes/cache/scratch/hairdeck}
OUT=${OUT:-out}; mkdir -p "$OUT"

plan() {  # goal problem -> $OUT/plan.json ; exit 3 when the planner refuses
  local goal=$1 problem=${2:-problems/aux-route-ready.jsonld}
  jq --arg g "$goal" '.todo_list=[{"goal":[{"pointer":$g,"eq":1}]}]' "$problem" > "$OUT/problem.json"
  "$PLANNER" "$DOMAIN" "$OUT/problem.json" "$OUT/plan.json" > "$OUT/planner.log" 2>&1 || { cat "$OUT/planner.log" >&2; exit 4; }
  if jq -e '.refused' "$OUT/plan.json" >/dev/null; then echo "refused: $(jq -r .refused "$OUT/plan.json") for $goal with $problem" >&2; exit 3; fi
}

gpu() { if [ "${DRY_RUN:-0}" = 1 ]; then echo "[dry] ssh $GPU_HOST $*"; else ssh -o BatchMode=yes "$GPU_HOST" "$@"; fi; }
local_() { if [ "${DRY_RUN:-0}" = 1 ]; then echo "[dry] $*"; else ( eval "$*" ); fi; }   # a subshell, so one step's cd cannot leak into the next
todo() { echo "action $1 has no command yet: $2" >&2; [ "${DRY_RUN:-0}" = 1 ] || exit 2; }
A3D='cd ~/og2/a3d-env && REPRO_ROOT=~/og2/spike ./run.sh python'   # the Segment environment on the GPU host

action() {
  case $1 in
    relabel-coco)        gpu "python3 $REPRO/relabel_coco.py ~/og2/rfdetr-seg/data ~/og2/rfdetr-seg/data_aux" ;;
    make-synth-set)      gpu "$A3D $REPRO/gen_synth.py ~/og2/synth_aux 360" ;;
    train-part-detector) gpu "$A3D $REPRO/train_synth.py ~/og2/synth_aux ~/og2/synth_aux-run1 15" ;;
    ingest-usd)          local_ "$USDPY repro/usd_io.py ingest \${SOURCE:?set SOURCE=<mesh>} $PWD/$OUT/stage.usda --unit \${UNIT:-cm} \${LABELS:+--labels \$LABELS --classmap \${CLASSMAP:?set CLASSMAP}}" ;;
    unitise-source)      local_ "$USDPY repro/usd_io.py deliver $PWD/$OUT/stage.usda $PWD/$OUT/segment_input.glb --unit-cube" ;;
    write-scale-sidecar) local_ "$USDPY repro/units.py selftest && test -s $PWD/$OUT/segment_input.glb.units.json" ;;
    restore-units)       local_ "$USDPY repro/usd_io.py restore $PWD/$OUT/stage.usda \${LABELLED:?set LABELLED=<Segment output glb>} $PWD/$OUT/stage_labelled.usda --frame voxel" ;;
    segment-labels)      gpu "$A3D $REPRO/garment.py --mode textured && $A3D $REPRO/rfdetr_maps.py ~/og2/spike/out/garment-textured textured" ;;
    close-labelling)     local_ "test -f $OUT/plan.json && echo 'labelling closed (composite marker)'" ;;
    build-warp)          gpu "cd ~/og2/warp-pixi && ~/.pixi/bin/pixi run build" ;;
    measure-motion-lag)  todo "$1" "no motion-lag measurement exists yet; it needs the Warp build and a body motion clip" ;;
    classify-soft-rigid) todo "$1" "needs the measured lag and a threshold" ;;
    make-spring-chains)  local_ "ls $PWD/$OUT/hair/*/chains_seed0.json" ;;   # HairDeck writes the chains in the same run as the cards
    make-hair-cards)     local_ "cd $HAIRDECK/HairDeck && HAIRDECK_ROOT=$HAIRDECK/ws .venv/bin/python scripts/image_to_hair.py \${PORTRAIT:?set PORTRAIT=<image>} --out $PWD/$OUT/hair --n 1" ;;
    rig-aux-parts)       todo "$1" "no code gives soft parts spring-bone chains and rigid parts a parent bone yet" ;;
    *) echo "unknown action: $1" >&2; exit 64 ;;
  esac
}

case ${1:-} in
  goals)  jq -r '.methods|keys[]' ${DOMAIN//,/ } | grep '^/aux/' ;;
  plan)   plan "${2:?goal}" "${3:-problems/aux-route-ready.jsonld}"; jq -r '.temporal|"total \(.total), consistent \(.consistent), origin \(.origin)"' "$OUT/plan.json"
          jq -r '.steps[]|"\(.start[11:19]) -> \(.end[11:19])  \(.duration)\t\(.action)"' "$OUT/plan.json" ;;
  run)    plan "${2:?goal}" "${3:-problems/aux-route-ready.jsonld}"; n=0
          for a in $(jq -r '.steps[].action' "$OUT/plan.json"); do n=$((n+1)); echo "== step $n: $a"; action "$a"; done
          echo "== done: $n steps for $2" ;;
  action) action "${2:?action}" ;;
  *) sed -n 2,9p "$0"; exit 64 ;;
esac
