# How it works

## How it works

- **Pose-swap engine**: Qwen Image 2.1. The generation node reproduces the native Qwen 2.1 pose-editing chain internally:

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
