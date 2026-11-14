# Verification

## Verification

These notes come from the upstream project and predate the pose library removal. They haven't been re-run here.

- `py_compile` passes. `node --check web/garment_qwen21.js` passes.
- `node --check web/portrait_qwen21.js` passes. The portrait library and node outputs have been verified through the local interface.
- `node --check web/pipeline_qwen21.js` passes. The four-in-one asset input subgraph, the one-click replace subgraph and the three standard output previews have all been loaded and checked in the frontend.
- Self-served routes: `/aicg3d_pose/garments/catalog`, `/aicg3d_pose/garments/assets/`, `/aicg3d_pose/garments/gallery`.
- Portrait routes: `/aicg3d_pose/portraits/catalog`, `/aicg3d_pose/portraits/thumb/`, `/aicg3d_pose/portraits/gallery`.
- Garments load from the plugin's `garments/`, bundled with this plugin.
- Portraits load from the plugin's `portraits/`, with no dependency on an external library or the `E:` drive.
- Qwen 2.1 multi-reference, single outfit swap, single face swap and the full three-stage chain have all run successfully through the API.
- Sequential preview events were verified to arrive in the order `head swap → pose swap → outfit swap`.
- The full dual-subgraph chain ran successfully in about `90.5 seconds`. The three outputs produced `768 × 1344` previews in turn, and a custom `640 × 960` test output matched exactly.
- Model dropdowns were moved back to the real loader nodes inside the subgraph, so the main wrapper node no longer falsely reports "unknown model / missing model".
- Full generation needs a GPU and the models above. Verify after installing and restarting.
