<img width="1615" height="486" alt="image" src="https://github.com/user-attachments/assets/0f35cd8d-efb8-4540-a2bc-e4022fbdc3c6" />

# comfyui-aicg3d-PoseSwap

Project author/maintainer: JGRFW. The source code is under the MIT License. See [LICENSE](LICENSE) for the copyright notice and [AUTHORS.md](AUTHORS.md) for upstream authors and asset sources.

> [!IMPORTANT]
> This repository is not an asset pack with cleared rights. Third-party assets are in the repository, but that doesn't mean the project author owns, licenses, endorses or guarantees them for redistribution or commercial use.
> MIT covers only the project source code. The images and indexes in `garments/` and `portraits/` are third-party assets outside MIT. Model weights are not shipped with the repository.
> The pose library has been removed from this repository. No license was found for the garment library that covers redistribution. The portrait library is labeled CC0, but it also asks that it not be redistributed. Before you publish the full asset pack, read [LEGAL_AND_SAFETY.md](LEGAL_AND_SAFETY.md), [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). A disclaimer is not a substitute for permission.
>
> Before use, read [DISCLAIMER.md](DISCLAIMER.md), [NOTICE](NOTICE) and [AUTHORS.md](AUTHORS.md) in full. If you are a rights holder and think some content shouldn't be distributed, contact the author through a GitHub Issue to have it taken down.
>
> Content notice: the garment index includes adult-oriented categories. The project is for adults only. Do not use it to sexualize minors, to sexualize anyone without consent, to impersonate real people, or for any other illegal purpose.

A fully standalone ComfyUI plugin. Its pipeline is **swap head and hair → swap pose with Qwen Image 2.1 → swap the full outfit**. You can also use Qwen-Image-Edit-2511 for a single high-fidelity outfit swap.

The recommended setup is the "dual-wrapper" workflow. One subgraph takes the four asset inputs, and one "one-click replace" subgraph does the swaps. Each of the three results goes from its own output to a standard PreviewImage node.

"I generate a character and pick a pose, and the character comes out in that pose. I pick an outfit, and they change clothes on the spot."

## Library sources and distribution status

The current GitHub `main` repo and the full development directory keep two local libraries (garments and portraits). You can also build a code-only package for cases where the libraries are kept outside the plugin. Both modes support environment variables that point to external library directories.

For asset sources, licenses and responsibility notes, see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [PORTRAIT_LIBRARY_NOTICE.md](PORTRAIT_LIBRARY_NOTICE.md).

| Dependency | Description |
| --- | --- |
| **Pose library** | **Removed from this repository.** Supply your own pose reference images (for example, connect a LoadImage node to `pose_image`). |
| **Garment library** | **Included in the main GitHub repo** (`garments/`: 1407 garment reference images and an index). The code-only package excludes it by default. |
| **Portrait library** | **Included in the main GitHub repo as a compressed version** (`portraits/`: 1499 WebP images, thumbnails and an index). The code-only package excludes it by default. |
| **Gallery pages and routes** | Provided by this plugin (`web/garment_gallery.html` and the `/aicg3d_pose/*` routes). It calls no external plugins. |
| **ComfyUI** | 0.43+ (with the native Qwen Image 2.1 and Qwen-Image-Edit-2511 nodes: `nodes_qwen.py` / `nodes_flux.py` / `nodes_cfg.py` / `nodes_model_advanced.py`) |
| **Model weights** | The standard `models/` directory (see the tables below). This is ComfyUI's general location and doesn't belong to any plugin. |

> To use it, others only need to: ① copy the whole plugin directory into their ComfyUI `custom_nodes/`; ② prepare the weight files listed under "Required models" below; ③ restart ComfyUI. The GitHub main repo includes the local garment and portrait libraries. With the code-only package, point the `AICG3D_*_LIBRARY` environment variables at external asset directories.

## Installation

The project needs no extra `pip install`. Image loading uses the Pillow, NumPy and PyTorch that ship with ComfyUI.

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/JGRFW/comfyui-aicg3d-PoseSwap.git
```

Then download the model weights, which the repo doesn't include, as described in [MODEL_REQUIREMENTS.md](MODEL_REQUIREMENTS.md), and restart ComfyUI.
Build a code-only release package with `python scripts/package_open_source.py`. It excludes the third-party libraries by default.

### First-time portrait library setup

The GitHub `main` repo includes `portraits/img/` and `portraits/data/`. If you downloaded the code-only package, or an installer copied only the source, the page shows "Portrait library not installed yet". In that case, configure an external library with the command below, or download the full repo from GitHub.

First obtain a compatible `comfyui-portrait-gallery/library` from a legitimate source, then run:

```bash
python scripts/configure_portrait_library.py --source "C:\path\to\comfyui-portrait-gallery\library"
```

After restarting ComfyUI, click "Browse portrait library" in the node to search. You can also put the library in the plugin's `portraits/` directory or set the `AICG3D_PORTRAIT_LIBRARY` environment variable. The install status endpoint is `/aicg3d_pose/portraits/status`.

## Nodes

```
                        pose_image (one wire)
[LoadImage etc.] ───────────────────────────►  [Pose-swap generation]
 any pose reference IMAGE                       PoseQwen21
 · the pose library was removed;                · person_image (character reference)
   supply your own pose image                   · pose_image (from the node at left)
                                                · model/sampling parameters
                                                · outputs the pose-swapped image
                                                   │
                                                   │ image (character after pose swap)
                                                   ▼
                         garment_image (one wire)
[Garment select] ───────────────────────►  [Outfit-swap generation]
 PoseQwen21GarmentSelect                     PoseQwen21PoseSwap
 · garment_id + "Browse garment library"     · person_image (after pose swap)
   button + preview                          · garment_image (from the node at left)
 · outputs garment_image / id / description  · garment_description (shoe/sock/style text)
 · description ───────────────────────────►  · enable switch: when off, the node does nothing and passes through
                                             · model/sampling parameters
                                             · outputs the outfit-swapped image
```

When `enable` on the outfit-swap node is **False**, the node does nothing. It passes `person_image` through unchanged, loads no outfit model and generates nothing. Set it to **True** when you want to change clothes.

Don't leave out the `description` wire. The specific shoe and sock types in the library description are appended to the outfit-swap prompt. Qwen Edit tends to keep the original shoes if you just say "shoes". It replaces them reliably only when you spell out terms like `socks sandals`.

## Three ways to use it

| Route | Best for | Model size | Workflow |
| --- | --- | --- | --- |
| **Dual-wrapper sequential swap (recommended)** | Four-in-one asset input plus a one-click replace subgraph. The three results preview in order from three outputs. | Head/pose share one model set. Outfit swap uses another. | `example_workflows/aicg3d_qwen21_simple_replace.json` |
| **Qwen Image 2.1 three-stage preview** | 16GB VRAM. Swap head and hair, pose, and full outfit in one run, with a preview at each step. | int8 main model is about 6.76 GiB | `example_workflows/aicg3d_qwen21_three_stage.json` |
| **Qwen-Image-Edit-2511 node** | A single outfit swap that follows the garment image more faithfully. Suits those who already have quantized 2511 weights. | int8 is much smaller than bf16, which is about 38 GiB | The plugin's `PoseQwen21PoseSwap` node or `aicg3d_poseswap_pose_swap_edit.json` |

## Dual-wrapper sequential-swap workflow

Drag [example_workflows/aicg3d_qwen21_simple_replace.json](example_workflows/aicg3d_qwen21_simple_replace.json) into ComfyUI. The workflow chains these steps in order.

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

1. Drag [example_workflows/aicg3d_qwen21_three_stage.json](example_workflows/aicg3d_qwen21_three_stage.json) into ComfyUI.
2. `1. Base character` is the base image whose body and pose you want to keep. `2. Head-swap reference` is the face. `3. Hairstyle reference` is the hair.
3. For `4. Pose reference`, supply your own pose image as the motion reference. Choose the outfit for `5. Full-outfit reference` from the garment library.
4. Click run. The workflow outputs and saves three images in order: `1_head_hair`, `2_pose`, `3_outfit`.
5. If you don't need a head or hairstyle swap, replace that reference with the same base image, or connect that stage's output straight to the next stage. If you don't need an outfit swap, disable the `3. After full-outfit swap` save node.

The Qwen 2.1 edit nodes in the three stages default to `refine_prompt = false` and use the written Chinese prompts directly. The prompt enhancer runs only when you turn it on, and that adds time.

## Portrait reference node: face/head-swap reference selection

`PoseQwen21PortraitSelect` picks a front-facing or styled reference from the portrait library. It outputs `portrait_image`, `portrait_id`, `description` and `attribution`. Connect `portrait_image` to the identity reference input of the face/head-swap chain. The node doesn't run anything by itself.

- Library source: [AI モデル顔データベース (AI Model Face Database)](https://ai-portrait-gallery.pages.dev/), original author [あぎ (@agi_aibusi)](https://x.com/agi_aibusi).
- The original site is labeled CC0 1.0, but it also asks people to avoid directly redistributing the image data itself. To meet open-source distribution needs, this plugin includes a compressed copy. `PORTRAIT_LIBRARY_NOTICE.md` keeps that request and a reminder to check compliance yourself.
- The assets are stored in the plugin's `portraits/`: 1499 reference WebP images of up to 768×960, plus 360×450 WebP thumbnails, about 148 MiB in total.
- The portrait node reads the plugin's own `portraits/`. It doesn't depend on the `E:` drive, an external library plugin or the ComfyUI `user` cache.
- Every card and detail page keeps the original site, original author and CC0 license link. The full notice is in `PORTRAIT_LIBRARY_NOTICE.md`.
- This node is an independent, unofficial local indexing tool. It isn't an official version of the original author's work and has no endorsement from them. Don't use it to impersonate real people or for illegal purposes.

## How it works

- **Pose-swap engine**: Qwen Image 2.1. The generation node reproduces ComfyUI's native Qwen 2.1 pose-editing chain internally:

  ```
  character reference (image_2) ─┐
  pose reference image (image_1) ┤→ TextEncodeQwenImage21 → LoRA (pose adapter) → Cache → KSampler → VAEDecode → IMAGE
                                 │
          (the pose image is supplied by you, for example via LoadImage)
  ```

  - `image_1` = the pose reference image you supply. It decides action, posture and viewpoint.
  - `image_2` = the character reference image you generated or loaded. It preserves identity, hairstyle, clothing, art style, background and lighting.
  - The default prompt says to copy the pose exactly, lock the clothing unchanged, and keep the original's barefoot or socks-only state. It explicitly states "if the original is barefoot, stay barefoot" and "if only socks or tights, don't add shoes", so the model doesn't invent shoes when changing pose.

- **Outfit-swap engine**: Qwen-Image-Edit-2511 (4-step Lightning fast outfit swap, reproducing the official parameters of the nvzhuang outfit-swap chain):

  ```
  person image (after pose swap) ──FluxKontextImageScale──► VAEEncode (initial latent)
  garment image ───────────────┐
  → TextEncodeQwenImageEditPlus(image1=person, image2=garment, prompt=outfit prompt)
  → FluxKontextMultiReferenceLatentMethod(index_timestep_zero)
  → ModelSamplingAuraFlow(shift=3.1) + CFGNorm(1.0) + Lightning LoRA
  → KSampler(4 steps, cfg=1.0, euler/simple) → VAEDecode → IMAGE
  ```

  - The outfit prompt asks to keep the person's identity fully identical (face, skin tone, hairstyle, build) and the original pose as far as possible. It also asks to wear the garment faithfully (no redesign of color, fabric, pattern, neckline, sleeve length or hem), to drape naturally, and to keep the background lighting.
  - The new outfit prompt fully replaces the top, bottoms, socks/tights and shoes. If the reference image has a different shoe type, the old shoes must be removed and replaced, never kept or blended.
  - `garment_description` takes the garment library description (for example `socks sandals`). It makes up for small shoe areas being inconspicuous to the visual encoder.

## Usage

1. Drag in the nodes (menu **image → Pose Gallery/Qwen2.1**, or **AICG3D/Image & Pose** if the AICG3D workbench is integrated).
2. **Pose swap**: connect `person_image` of "Pose-swap generation" to the character reference (an adult reference image). Connect your pose reference image (for example from LoadImage) to its `pose_image` input.
3. **Outfit swap (optional)**: connect `person_image` of "Outfit-swap generation" to the previous step's pose-swapped image. Connect `garment_image` of "Garment select" to its `garment_image` input (one wire). Then connect `description` of "Garment select" to `garment_description` of "Outfit-swap generation".
4. On the garment select node, click "**Browse garment library**", filter by category or keyword, and click "Use this garment".
5. Set `enable` on "Outfit-swap generation" to **True** when you want to change clothes. Set it to **False** otherwise, and the node passes through and has no effect.
6. Keep the default model paths and click run.

## Required models (under the models/ directory)

### Pose swap (Qwen Image 2.1)

| Type | Default file | Notes / source |
| --- | --- | --- |
| Base model | `diffusion_models/qwen/qwen_image_2.1_bf16.safetensors` | Qwen-Image-2.1 (official Tongyi Qianwen) |
| Text/image encoder | `text_encoders/qwen3vl_8b_int8_convrot.safetensors` | Default in the recommended workflow. You can switch to the bf16 version in the node dropdown. |
| VAE | `vae/qwen_image_2.1_vae_bf16.safetensors` | The matching VAE for Qwen Image 2.1 |
| Pose adapter LoRA | `loras/qwen-image2.1/VNCCS_QI2_PoseStudioV1.1.safetensors` | HuggingFace `MIUProject/VNCCS_PoseStudio_QI2.1` |

Default sampling: 25 steps, CFG 1, Euler/simple, denoise 1, LoRA strength 1, resolution 1024.

### Head/hair swap + outfit swap (Qwen Image 2.1 three-stage workflow)

| Type | Default file | Notes |
| --- | --- | --- |
| Base model | `diffusion_models/qwen/qwen_image_2.1_int8_convrot.safetensors` | **Recommended for 16GB VRAM.** You can switch to bf16. |
| Text/image encoder | `text_encoders/qwen3vl_8b_int8_convrot.safetensors` | Qwen3-VL 8B int8 (type=qwen_image) |
| VAE | `vae/qwen_image_2.1_vae_bf16.safetensors` | Shared with pose swap |
| Head-swap model | `diffusion_models/qwen/qwen_image_2.1_int8_convrot.safetensors` | 8-step fast head swap |
| Outfit-swap model | `diffusion_models/qwen/qwen_image_2.1_int8_convrot.safetensors` | 20 steps by default. Sampler, scheduler and steps are adjustable. |

The recommended dual-wrapper workflow is actually configured as follows:
- Head swap and pose swap share `qwen_image_2.1_bf16`, `qwen3vl_8b_int8_convrot` and the same VAE.
- The pose stage then applies the pose LoRA.
- Outfit swap uses its own `qwen_image_2.1_int8_convrot` with the same CLIP/VAE.
- Head swap uses an 8-step sigma schedule, pose swap defaults to 25 steps, and outfit swap defaults to 20.

### Outfit swap (Qwen-Image-Edit-2511)

| Type | Default file | Notes / source |
| --- | --- | --- |
| Base model | `diffusion_models/qwen_image_edit_2511_int8_convrot.safetensors` | **int8 version, runs on 16GB VRAM. You must download it yourself** (the ComfyUI single-file version from the Comfy-Org / Qwen official 2511 repo). |
| Text/image encoder | `text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors` | Qwen2.5-VL 7B fp8 (type=qwen_image) |
| VAE | `vae/qwen_image_vae.safetensors` | The matching VAE for Qwen Image Edit |
| Lightning LoRA | `loras/Qwen-Edit-2511/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | 4-step fast (the fp32 version also works) |

Default sampling: 4 steps, CFG 1, Euler/simple, denoise 1, LoRA strength 1, shift 3.1.
All model names are dropdowns. If your model files have different names, pick them from the dropdown.

> **On 16GB VRAM, always use the quantized 2511.** The bf16 base model is about 38GB and gets swapped in from disk constantly. A single outfit swap often takes more than 110 seconds. The int8/fp8 quantized weights are much smaller and usually cut the time a lot.
> Don't change Lightning from 4 steps to 25 steps for "more detail". Running the 4-step LoRA at 25 steps only makes it about 6 times slower, with no proportional quality gain.
>
> Measured on an RTX 5070 Ti 16GB, the full Qwen 2.1 three-stage chain (head/hair swap → 25-step pose swap → 8-step full-outfit swap) takes about 80 seconds. An outfit-only swap on the same 2511 bf16 chain often takes over 110 seconds. Qwen 2.1's strengths are mainly low VRAM use and multi-reference support. If garment detail is still inaccurate, run a separate outfit pass with the quantized 2511.

> **Pose LoRA versions**: V1.1 preserves clothing and follows the pose moderately (default). V2 follows the pose more strongly but changes the clothing. To use V2, download `VNCCS_QI2_PoseStudioV2.safetensors` into `loras/qwen-image2.1/` and pick it in the dropdown. Note that this filename has a trailing space on HF, so download it with the direct link using `%20` encoding, and remove the space when saving.

## Environment variables (optional)

- `AICG3D_GARMENT_LIBRARY`: custom garment library root (default is the bundled `garments/`).
- `AICG3D_PORTRAIT_LIBRARY`: overrides the default in-plugin `portraits/`. It can point to a compatible portrait library directory.
- `AICG3D_PORTRAIT_CACHE`: custom directory for the compressed portrait preview cache (default `ComfyUI/user/aicg3d_portrait_cache/`).

## Optional: integrate into the AICG3D short-drama workbench

The plugin is adapted to `comfyui-AICG3D`. Its registry lazily imports this plugin. After a restart, the AICG3D menu shows
**AICG3D/Image & Pose → AICG3D PoseSwap → Garment select / Face-swap reference select / One-click replace / Pose-swap generation / Outfit-swap generation**.
If the standalone plugin is missing, AICG3D loads as usual and the workbench is unaffected.

## Verification

These notes come from the upstream project and predate the pose library removal. They haven't been re-run here.

- `py_compile` passes. `node --check web/garment_qwen21.js` passes.
- `node --check web/portrait_qwen21.js` passes. The portrait library and node outputs have been verified through the local interface.
- `node --check web/pipeline_qwen21.js` passes. The four-in-one asset input subgraph, the one-click replace subgraph and the three standard output previews have all been loaded and checked in the ComfyUI frontend.
- Self-served routes: `/aicg3d_pose/garments/catalog`, `/aicg3d_pose/garments/assets/`, `/aicg3d_pose/garments/gallery`.
- Portrait routes: `/aicg3d_pose/portraits/catalog`, `/aicg3d_pose/portraits/thumb/`, `/aicg3d_pose/portraits/gallery`.
- Garments load from the plugin's `garments/`, bundled with this plugin.
- Portraits load from the plugin's `portraits/`, with no dependency on an external library or the `E:` drive.
- Qwen 2.1 multi-reference, single outfit swap, single face swap and the full three-stage chain have all run successfully through the ComfyUI API.
- Sequential preview events were verified to arrive in the order `head swap → pose swap → outfit swap`.
- The full dual-subgraph chain ran successfully in about `90.5 seconds`. The three outputs produced `768 × 1344` previews in turn, and a custom `640 × 960` test output matched exactly.
- Model dropdowns were moved back to the real loader nodes inside the subgraph, so the main wrapper node no longer falsely reports "unknown model / missing model".
- Full generation needs a running ComfyUI, a GPU and the models above. Verify after installing and restarting.
