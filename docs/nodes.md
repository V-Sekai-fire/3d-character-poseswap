# Nodes and usage

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

## Usage

1. Drag in the nodes (menu **image → Pose Gallery/Qwen2.1**, or **AICG3D/Image & Pose** if the AICG3D workbench is integrated).
2. **Pose swap**: connect `person_image` of "Pose-swap generation" to the character reference (an adult reference image). Connect your pose reference image (for example from LoadImage) to its `pose_image` input.
3. **Outfit swap (optional)**: connect `person_image` of "Outfit-swap generation" to the previous step's pose-swapped image. Connect `garment_image` of "Garment select" to its `garment_image` input (one wire). Then connect `description` of "Garment select" to `garment_description` of "Outfit-swap generation".
4. On the garment select node, click "**Browse garment library**", filter by category or keyword, and click "Use this garment".
5. Set `enable` on "Outfit-swap generation" to **True** when you want to change clothes. Set it to **False** otherwise, and the node passes through and has no effect.
6. Keep the default model paths and click run.

## Environment variables (optional)

- `AICG3D_GARMENT_LIBRARY`: custom garment library root (default is the bundled `garments/`).
- `AICG3D_PORTRAIT_LIBRARY`: overrides the default in-plugin `portraits/`. It can point to a compatible portrait library directory.
- `AICG3D_PORTRAIT_CACHE`: custom directory for the compressed portrait preview cache (default `user/aicg3d_portrait_cache/`).
