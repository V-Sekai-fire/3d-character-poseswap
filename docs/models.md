# Required models

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
| Base model | `diffusion_models/qwen_image_edit_2511_int8_convrot.safetensors` | **int8 version, runs on 16GB VRAM. You must download it yourself** (the single-file version from the Comfy-Org / Qwen official 2511 repo). |
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
