import numpy as np
import time, os, sys, glob
from urllib.parse import urlparse
import matplotlib.pyplot as plt
import matplotlib as mpl
from cellpose import utils, io
from skimage.measure import label as skiLabel
from tifffile import TiffFile
import math, cv2, skimage, scipy, scipy.ndimage
import tifffile as tifff

from cellpose import models, io
from skimage import measure as skiMeasure

# --- Parameters ---
myModel = "cyto3"
chan = [0,0]
# dapi=0 # This variable is defined but not used.

# DEFINE CELLPOSE MODEL
## IMPROVEMENT: Renamed model to be more generic as this is a 2D workflow.
model = models.CellposeModel(gpu=True, pretrained_model=myModel)

## NOTE: zdim is only used in the commented-out filter section below.
# zdim = 0 

saveRaw = 1
diam_um = 15      # Expected cell diameter in microns
blurfactor = 1    # Set to 0 to disable blurring
pixelSize = 0.108 # Microns per pixel
excludeEdge = True
# Spacing = 0.25    # Z-spacing in microns. Not used in this 2D script.

folder = r"D:\\2025-07-05_pol2_brd4_sc-35_IF_perturbations\\dapiMasks"
outfolder = r"D:\\2025-07-05_pol2_brd4_sc-35_IF_perturbations\\dapiMasks_excludeEdge"

# This will create the output folder if it doesn't exist.
os.makedirs(outfolder, exist_ok=True)

## IMPROVEMENT: Use glob to directly find all .tif files. It's cleaner.
files = glob.glob(os.path.join(folder, '*0.tif'))
# cutoff = 11 # NOTE: This is only used in the commented-out filter section.

## FIXED: The 'anisotropy' calculation was for 3D and was not used. It has been removed.

for input_filepath in files:
    # --- Construct full input and output paths ---
    base_name = os.path.basename(input_filepath).rsplit('.', 1)[0]
    
    ## FIXED: Create a single output prefix to use for all saved files in this iteration.
    output_prefix = os.path.join(outfolder, f"{base_name}_cellpose")

    print(f"Processing: {input_filepath}")
    print(f"Saving results to: {output_prefix}_*.tif/npz/npy")

    # Use the full path to read the image
    img = io.imread(input_filepath)

    pxScale = pixelSize * 30 / diam_um
    print(f'Original size: {img.shape}')

    # always remember that python reads imgs as y(0), x(1) in 2D
    # Pre-allocate arrays
    img_scaled = np.zeros((round(img.shape[0] * pxScale), round(img.shape[1] * pxScale)))
    
    print(f'Rescaled size: {img_scaled.shape}')
    
    # Cellpose can have issues with pure-black pixels.
    # Replace them with a very low value from the image distribution.
    if np.any(img == 0):
        low_val = np.quantile(img[img > 0], 0.01)
        print(f'Min Intensity Value (1%): {low_val}')
        img[img == 0] = low_val

    ## FIXED: The if/else statement was redundant. The logic is now streamlined.
    # Rescale image so the effective diameter is ~30 pixels for Cellpose
    img_scaled = scipy.ndimage.zoom(img, pxScale, order=3)
    # Apply blur if specified
    if blurfactor > 0:
        img_blur = scipy.ndimage.gaussian_filter(img_scaled, blurfactor)
    else:
        img_blur = img_scaled
            
    print('Preprocessing done')

    # Run Cellpose evaluation
    masks_scaled_blur, flows_blur, styles_blur = model.eval(img_blur[:,:], diameter=30,
                                                            flow_threshold=0.4, 
                                                            cellprob_threshold=0.0,
                                                            batch_size=8)
    
    # Rescale the resulting masks back to the original image size
    # Use order=0 (nearest neighbor) to preserve integer label values
    masks = scipy.ndimage.zoom(masks_scaled_blur, 
                               (img.shape[0] / masks_scaled_blur.shape[0], img.shape[1] / masks_scaled_blur.shape[1]),
                               order=0)
    masks = masks.astype(np.uint16)

    if saveRaw == 1:
        ## FIXED: Use the dynamic 'output_prefix' instead of the static 'outname'.
        np.savez(f"{output_prefix}_segm_raw.npz", masks=masks)

    if excludeEdge:
        # >>> NEW SECTION: Exclude masks on the image border <<<
        print("Filtering masks that touch the image border...")
        
        # 1. Identify all unique mask labels that are on the border of the image.
        # We collect all label values from the first/last row and first/last column.
        edge_labels = np.concatenate([
            masks[0, :],          # Top row
            masks[-1, :],         # Bottom row
            masks[:, 0],          # Left column
            masks[:, -1]          # Right column
        ])
        
        # Get the unique, non-zero label IDs.
        # The background is label 0, so we must exclude it from the list of labels to remove.
        edge_labels = np.unique(edge_labels)
        edge_labels = edge_labels[edge_labels != 0]

        print(f"Found {len(edge_labels)} masks on the border to remove.")
        
        # 2. Create a boolean array where `True` corresponds to masks that should be removed.
        is_on_edge = np.isin(masks, edge_labels)
        
        # 3. Set the identified masks to 0 (background).
        masks_filtered = masks.copy()
        masks_filtered[is_on_edge] = 0
        
        # 4. Re-label the masks to be sequential (1, 2, 3, ...), which is good practice.
        # This removes any gaps in label numbers from the previous step.
        masks, _ = skiLabel(masks_filtered, return_num=True) 
        masks = masks.astype(np.uint16)
        # The `masks` variable now contains only the complete, non-edge-touching cells.
        # >>> END OF NEW SECTION <<<


    # Calculate properties of the final, filtered masks
    masks_regionprops = skiMeasure.regionprops_table(masks, properties=('label', 'area', 'centroid', 'bbox'))        

    # Save final results (which are now filtered)
    ## FIXED: Use the dynamic 'output_prefix' for all saved files.
    tifff.imwrite(f"{output_prefix}_cp_masks.tif", 
                  masks,
                  imagej=True,
                  resolution=(1/pixelSize, 1/pixelSize))
    
    np.savez(f"{output_prefix}_segm.npz", masks=masks)
    np.save(f"{output_prefix}_regionProps.npy", masks_regionprops)

    ## FIXED: Use the correct variable 'input_filepath' to avoid a NameError.
    print(f'Finished with {input_filepath}\n')