# The AUX route: label garment parts, decide rigid or soft, rig them

The domain `domains/presence-edit.jsonld` carries this route as the `/aux/*` goals. Problem `problems/aux-route-2026-11-15.jsonld` is the desk as it stands and the planner refuses it as `unreachable`. Problem `problems/aux-route-ready.jsonld` adds a host compiler and a body motion clip and the planner returns the 13 steps below. The same plan files are in `plans/`.

The goal is to separate the AUX parts (skirt, sleeve, collar, cape, loose trims) from the body, and to know for each whether it is rigid (follows a bone) or soft (needs spring bones). SkinTokens rigs the body. The decisions behind the steps are in RFD66606-2495.

## Steps, in the planner's order

| # | Action | What it does | State on 2026-11-15 |
|---|---|---|---|
| 1 | `relabel-coco` | Map all 46 Fashionpedia-class source classes into Skirt, Sleeve, Collar, Cape, Accessory, Fitted and Detail. Each annotation keeps `src_class` and gets a `motion` prior. `repro/relabel_coco.py`. | Done. 28,400 annotations in, 28,400 out. Cape has 22 train and 2 test instances, so it cannot be scored. |
| 2 | `make-synth-set` | Render GarmentCodeData drapes on the neutral body into a COCO set with exact masks, split by garment. `repro/gen_synth.py`. | Done for Skirt, Sleeve and Collar (1,841 train images, 262 valid, 239 test). Fitted is not yet in it, so a regeneration is needed. |
| 3 | `train-part-detector` | Fine-tune RF-DETR-Seg-Small. `repro/train_synth.py`. | Trained on the 3-class set: validation mask AP 0.382 after 15 epochs. Not scored on the test split or on photographs. |
| 4 | `unitise-source` | Put the source GLB into the unit cube before Segment. | Done. Without it the lookup distance was 94 and not 0.0007, and labels were random. |
| 5 | `segment-labels` | Alchemy3D-Segment with maps from the detector. | Works on one GarmentCode garment: garment vs body ARI 0.58 with exact-label maps. One garment, one body. |
| 6 | `write-scale-sidecar` | Write scale and offset next to each unit-cube mesh, with the metric size from a body-height prior. | Scale recorded for the tested garment (`unit_frame.json`). Not yet a step in the code. |
| 7 | `close-labelling` | Composite: labels plus sidecar. | Planner only. |
| 8 | `build-warp` | Build the NvidiaWarp-GarmentCode fork on fedora, with its compiler and CUDA from pixi (`tools/warp/pixi.toml`: gcc 12.4, CUDA 12.6, Python 3.11). | **Built** on 2026-11-15. `warp.so` is 108 MB; `pixi run check` lists `cuda:0` (RTX 4090, sm_89) and imports `XPBDIntegrator`. No drape has been run on it yet. Fedora's own gcc 16 is not used. |
| 9 | `measure-motion-lag` | Drape, move the body, measure which vertices lag. | Not started. Needs step 8 and a body motion clip. |
| 10 | `classify-soft-rigid` | Composite: label plus lag gives soft or rigid. | Not started. Threshold unset. |
| 11 | `make-hair-cards` | HairDeck, portrait to hair cards. | Ran on 9 poseswap portraits on the Mac (MPS): 54 to 153 cards, 35 s of compute each. Output not inspected beyond the mask. |
| 12 | `make-spring-chains` | HairDeck chain model: path, joints and stiffness. | Runs with step 11. Output is in a normalised frame, with the head proxy 0.128 high against a real head near 0.23, so about 1.8 before it fits ANNY. |
| 13 | `rig-aux-parts` | Soft parts get chains, rigid parts a parent bone. | Not started. |

## Time

Each action states an ISO-8601 `duration` and a `duration_basis` that says measured or estimate. The planner starts a step when every earlier step that sets a fact it needs has ended, so independent steps overlap, and the plan's total is the latest end. With an origin of 2026-11-15T08:00:00Z the full route is `PT1H31M1S` and it ends at 09:31:01Z.

- Critical path: `build-warp` (30 min, estimate), `measure-motion-lag` (1 h, estimate), `classify-soft-rigid`, `rig-aux-parts`. Labelling (`make-synth-set` 8 min 32 s and `train-part-detector` 19 min 24 s, both measured) finishes at 08:28:56 and is not on the critical path. Hair cards run beside everything (1 min 28 s, measured).
- Measured: synthetic set, detector training and hair cards. Everything else is an estimate and should be replaced as it is timed.
- A control: giving `make-synth-set` an end of 08:05:00Z, which its 8 min 32 s cannot meet, makes the plan report `consistent: false`.

## Running it

`pixi run build-planner` builds the Lean planner (needs elan). Then:

- `pixi run aux-goals` lists the goals and composite methods.
- `pixi run aux-plan /aux/soft_rigid_known` prints the schedule for a goal.
- `pixi run aux-run /aux/rigged` plans, then runs the steps in plan order. `DRY_RUN=1` prints the commands. A step with no command stops the run with exit 2 and says why. A refused plan exits 3.
- `pixi run goal-<name>` runs one goal, for example `goal-labelled-parts`. `pixi run aux-today` plans today's desk and is refused.
- `pixi run aux-action <name>` runs one primitive action.

GPU steps run over ssh on `GPU_HOST` (default `fedora`). Steps run one after another in plan order, so the overlaps in the schedule are what is allowed, not what runs. Tested on 2026-11-15: `goal-coco-relabelled` ran the relabel on fedora (28,400 annotations in and out) and `goal-hair-cards` ran HairDeck on one portrait. `unitise-source`, `write-scale-sidecar`, `measure-motion-lag`, `classify-soft-rigid` and `rig-aux-parts` have no command yet.

## Composite methods

`/aux/labelled_parts` (labels and sidecar), `/aux/soft_rigid_known` (labelled parts and measured lag) and `/aux/rigged` (labelled parts, the soft or rigid decision and the chains). Each is a method over goals, so the planner expands it into the primitive steps above.

## Decisions and rules worth keeping

- Motion lag is measured from the start. Clearance from the body is a first signal only. One drape: skirt vertices median 4.7 cm off the body, sleeve 0.7 cm, bodice and waistband 0.65 cm.
- Sleeve and Collar are `measure`, because they can be tight or flared.
- Lapel and epaulette are Detail and not Collar. Dress is Fitted, so its skirt part is not split out. Loose trims (bow, ribbon, tassel, fringe, ruffle, flower) are Accessory. Hood joins Collar. These are choices, not measurements.
- Units: any mesh that comes from outside Alchemy3D's own pipeline goes into the unit cube first, and its scale is written to a sidecar at that moment.
- HairDeck's released card model was trained on VRoid head hair, and its mask step drops tails and ears on purpose. Whether tails work is untested.
- SAM 3 and DINOv3 are gated. The weights used here are mirror copies whose SHA-256 matches the pins in HairDeck's downloader. The licences still apply.

## Open

- A body motion clip, and a first drape on the built Warp fork.
- Regenerate the synthetic set with the Fitted class and a measured `motion`.
- Score the detector on the held-out test garment and on photographs, then rerun Segment with its maps.
- The soft threshold, and whether lag from one motion clip generalises.
