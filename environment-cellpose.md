# Segmentation environment (`cellpose-gpu`)

Step 1 (3D nuclear segmentation) runs in the **existing** `cellpose-gpu` conda env, not the
analysis venv, because it needs the GPU torch/cellpose stack.

Interpreter: `C:/ProgramData/Anaconda3/envs/cellpose-gpu/python.exe`

Already present in that env:
- cellpose 4.0.5 (Cellpose-SAM), torch 1.13.1+cu116, scikit-image 0.24, numpy 1.26.4,
  scipy 1.15.3, tifffile, opencv.

Known env quirks handled in `eporca.segment` (see code comments):
- torch 1.13 has no bfloat16 kernel for the SAM encoder's `F.interpolate` -> run the model
  in float32 (`use_bf16: false`).
- The machine has 3 GPUs; only the RTX 3080 Ti (`cuda:1`) is bf16-capable, and it's the
  fastest, so segmentation pins `CUDA_VISIBLE_DEVICES=1` (config `segmentation.gpu_index`).
- torch 1.13 requires int64 tensor indices; cellpose 4.0.5 casts to int32 in
  `get_masks_torch` -> a runtime shim casts those indices to long.

Install the package + zarr into this env (zarr lets segmentation read the OME-Zarr; pin
numpy/scipy so torch is not disturbed):

```
C:/ProgramData/Anaconda3/envs/cellpose-gpu/python.exe -m pip install \
    zarr "numpy==1.26.4" "scipy==1.15.3"
C:/ProgramData/Anaconda3/envs/cellpose-gpu/python.exe -m pip install -e . --no-deps
```
