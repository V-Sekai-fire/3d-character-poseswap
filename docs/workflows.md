# Workflows

## Three ways to use it

| Route | Best for | Model size | Workflow |
| --- | --- | --- | --- |
| **Dual-wrapper sequential swap (recommended)** | Four-in-one asset input plus a one-click replace subgraph. The three results preview in order from three outputs. | Head/pose share one model set. Outfit swap uses another. | `example_workflows/aicg3d_qwen21_simple_replace.json` |
| **Qwen Image 2.1 three-stage preview** | 16GB VRAM. Swap head and hair, pose, and full outfit in one run, with a preview at each step. | int8 main model is about 6.76 GiB | `example_workflows/aicg3d_qwen21_three_stage.json` |
| **Qwen-Image-Edit-2511 node** | A single outfit swap that follows the garment image more faithfully. Suits those who already have quantized 2511 weights. | int8 is much smaller than bf16, which is about 38 GiB | The plugin's `PoseQwen21PoseSwap` node or `aicg3d_poseswap_pose_swap_edit.json` |

## Dual-wrapper sequential-swap workflow

Drag [example_workflows/aicg3d_qwen21_simple_replace.json](../example_workflows/aicg3d_qwen21_simple_replace.json) into the editor. The workflow chains these steps in order.

The canvas has two wrapper nodes and three standard preview nodes:

```text
Asset input (four-in-one) → One-click replace: head → pose → outfit
One-click replace output 1 → Preview 1 · head swap
One-click replace output 2 → Preview 2 · pose swap
One-click replace output 3 → Preview 3 · outfit swap
```

The one-click replace subgraph has three switches:

- `Head-swap switch`: when off, the base image goes straight to the pose stage.
- `Pose-swap switch`: when off, the head-swap result goes straight to the outfit stage.
- `Outfit-swap switch`: when off, the pose-swap result is output directly.

All three previews connect to subgraph output ports. The subgraph still runs the three stages in order. Previews 1, 2 and 3 therefore refresh one after another, rather than all appearing at the end.

The model configuration is merged. Head swap and pose swap share the same main model, encoder, LoRA and VAE. Outfit swap uses its own main model and encoder, so the same model isn't loaded twice.

Common parameters of the one-click replace subgraph:

- `Custom width / height`: both default to `0`, which keeps the input image's aspect ratio. The long side is capped at 1344 to avoid pointless upscaling. Enter a specific width or height to override.
- `Outfit-swap steps`: default `20`. Raise it to `25–30` if garment detail is still unstable.
- `Sampler / scheduler`: affect only the outfit-swap stage. Default `euler / simple`.

The three-stage workflow separates "swap face/hairstyle" from "swap outfit". This avoids changing too much at once, which makes the face, hairstyle and clothing interfere with each other. Merging multiple reference images into one Qwen 2.1 edit also works, but it is less stable and harder to roll back than the staged approach.

## How to use the three-stage workflow

1. Drag [example_workflows/aicg3d_qwen21_three_stage.json](../example_workflows/aicg3d_qwen21_three_stage.json) into the editor.
2. `1. Base character` is the base image whose body and pose you want to keep. `2. Head-swap reference` is the face. `3. Hairstyle reference` is the hair.
3. For `4. Pose reference`, supply your own pose image as the motion reference. Choose the outfit for `5. Full-outfit reference` from the garment library.
4. Click run. The workflow outputs and saves three images in order: `1_head_hair`, `2_pose`, `3_outfit`.
5. If you don't need a head or hairstyle swap, replace that reference with the same base image, or connect that stage's output straight to the next stage. If you don't need an outfit swap, disable the `3. After full-outfit swap` save node.

The Qwen 2.1 edit nodes in the three stages default to `refine_prompt = false` and use the written Chinese prompts directly. The prompt enhancer runs only when you turn it on, and that adds time.
