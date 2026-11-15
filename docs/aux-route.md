# The AUX route: label garment parts, decide rigid or soft, rig them

The domain `domains/presence-edit.jsonld` carries this route as the `/aux/*` goals. Problem `problems/aux-route-2026-11-15.jsonld` is the desk as it stands and the planner refuses it as `unreachable`. Problem `problems/aux-route-ready.jsonld` adds a host compiler and a body motion clip and the planner returns the 13 steps below. The same plan files are in `plans/`.

The goal is to separate the AUX parts (skirt, sleeve, collar, cape, loose trims) from the body, and to know for each whether it is rigid (follows a bone) or soft (needs spring bones). SkinTokens rigs the body. The decisions behind the steps are in RFD66606-2495.

## Steps, in the planner's order

| # | Action | What it does | State on 2026-11-15 |
|---|---|---|---|
| 1 | `relabel-coco` | Map all 46 Fashionpedia-class source classes into Skirt, Sleeve, Collar, Cape, Accessory, Fitted and Detail. Each annotation keeps `src_class` and gets a `motion` prior. `repro/relabel_coco.py`. | Done. 28,400 annotations in, 28,400 out. Cape has 22 train and 2 test instances, so it cannot be scored. |
| 2 | `make-synth-set` | Render GarmentCodeData drapes on the neutral body into a COCO set with exact masks, split by garment. `repro/gen_synth.py`. | Done for Skirt, Sleeve and Collar (1,841 train images, 262 valid, 239 test). Fitted is not yet in it, so a regeneration is needed. |
| 3 | `train-part-detector` | Fine-tune RF-DETR-Seg-Small. `repro/train_synth.py`. | Trained on the 3-class set: validation mask AP 0.382 after 15 epochs. Not scored on the test split or on photographs. |
| 4 | `ingest-usd`, `unitise-source` | Ingest the source into OpenUSD in its own units (`metersPerUnit` and the up axis are stage metadata; parts are keyed by integer ids, never by names), then deliver the unit-cube GLB for Segment with its sidecar made from the stage. `repro/usd_io.py`, `repro/units.py`. | Done and tested on the tested garment: 1.544 m tall in cm, unit cube 0.99999, sidecar scale 0.00647727. |
| 5 | `segment-labels` | Alchemy3D-Segment with maps from the detector. | Works on one GarmentCode garment: garment vs body ARI 0.58 with exact-label maps. One garment, one body. |
| 6 | `write-scale-sidecar` | Check the sidecar and the round trip, with controls that must fail (wrong scale, wrong frame, wrong sidecar). `units.py sidecar-from-height` makes one for a mesh that has no unit. | Done. Self-test passes, controls fail by 3.4, 368 and 118 cm. |
| 7 | `restore-units`, `close-labelling` | The inverse of unitising: put Segment's labelled output (unit cube, Z-up) back on the real-size stage. It pairs by vertex index and is only accepted when the geometry confirms it. | Accepted for the same vertex order (2.3e-6 cm over 29,784 vertices). Refused, with the reason, for the same surface in a shuffled order (152 cm off). A geometric correspondence through the cage guest is not built: the guest exports no coordinates, and its cage does not bind on garment shells yet. |
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

## Decisions since the first draft

- No weld step. The weld was a workaround for what turned out to be the unit bug, and the corrected runs show it changes almost nothing.
- `model_explode` (the add-on that `explode`/`implode` refer to; there is no `explode.elf` file in the tree) welds vertices by position, so it cannot separate the stitched panels of a drape: a split into 18 panels with duplicated seam vertices still came out as one piece. It does separate real shells. On the dressed mesh it gives two pieces, body and garment, the garment moved 157 cm up, boxes 3.3 cm apart, and undoing the offset puts all 53,536 vertices back within 7.5e-6 cm.
- Part ids are integers (glTF node index where there is one, else file order), and a face carries an integer `aux:part`. Names are display labels only.

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

## Durations as spans, and what was measured

An action states `duration` (its length). `start` is the earliest it may begin and `end` the latest it may finish, as the planner reads them: a step's earliest end must not pass its `end`, or the plan is `consistent: false`. Stating all three gives a range, as an OpenTelemetry span does: the typical length inside a window that holds every run seen. When an exact duration is not known, state `duration` as the typical value and `end` from the slowest run. The planner counts whole seconds, so values are rounded up.

Measured on fedora (RTX 4090, 2026-11-15, 5 runs each, the first cold from disk; `tools/measure/time_loads.py`, raw runs in `tests/evidence/load_times.json`, written into the domain by `pixi run set-durations`):

| Action | Typical | Slowest run | Deadline from origin |
|---|---|---|---|
| `load-qwen25vl-conditioner` | PT4S (warm median 3.2 s) | 4.4 s cold | 5 s |
| `load-omnigen2-transformer` | PT4S (3.3 s) | 11.4 s cold | 12 s |
| `load-omnigen2-vae` | PT1S (0.10 s) | 0.28 s | 1 s |
| `load-editscore-lora` | PT1S (0.006 s) | 0.05 s | 1 s |
| `merge-editscore-lora` | PT1S (0.17 s) | 0.33 s | 13 s (after the transformer) |
| `edit` | PT1M7S | one sample, no range | none |

The warm medians add to 6.74 s against the 7.0 s the whole load took in `baseline.log`, which includes moving the pipeline to the GPU. A run one second slower than the slowest measured run makes the plan inconsistent, and the test checks that it does.

## Unit tests for the actions

`pixi run test-actions` runs `tests/test_actions.py` over every action of `domains/presence-edit.jsonld` (35 today). Each action gets:

- **Golden.** The plan for a state holding exactly its preconditions is `[action]`, starts at the origin, ends at origin plus its duration, and the total equals that duration. The expectation is worked out from the action's text in the domain, not from the planner. `tests/golden/actions.json` keeps it, with the dry-run command, so a change to an action appears in review. After an intended change run `pixi run test-actions-update` and read the diff.
- **Control.** Dropping each precondition in turn makes the planner refuse, an action name that does not exist is refused, and `tools/aux.sh action <unknown>` exits 64. For the ranged actions, one second past the slowest measured run makes the plan inconsistent.
- **Invariant.** Two runs give identical bytes; asking for the action twice succeeds (it keeps its own preconditions); the duration is ISO 8601 with a basis of measured, estimate or composite; a dry run writes nothing except `out/`; the typical duration lies inside the measured range; the group total grows with the durations; the warm medians add to no more than the logged whole-load time.

Planted faults the test catches: a tampered golden, a changed duration, a dropped precondition and a deadline one second too tight.

### What the test found

- **14 actions still have no duration.** These are `fetch-clips`, `encode-packets`, `route-model`, `route-relay`, `seal-and-take`, `judge`, `agree`, `skip-agree`, `play-curve`, `check-mul-mat`, `fit-anny`, `follow`, `snapshot` and `score`. No log of a timed run exists for them here, so none was invented; each fails 2 checks until it is measured. They need a timed run, then a span in `tests/evidence/`.
- **A repeated step is listed twice, not run twice.** Asking for `[ingest-usd, ingest-usd]` returns two rows, both 08:00:00 to 08:00:05. The planner lists a step once with its earliest times and again with its latest times, so the second row is the latest window of the same step, and the total stays PT5S. An earlier note in this session called this an overlap of two copies, which was wrong. The window is the planner's own range output.
- **The schedule does not know about the single GPU.** Independent steps overlap. The domain has no resource constraint, so the total of the AUX plan is a lower bound while GPU actions share one card.
