import os
import torch
from ultralytics import YOLO
import torch.nn as nn

# --- Load your trained model ---
model_path = os.path.join(os.getcwd(), "app", "single_model0.3.1.pt")
custom_yolo = YOLO(model_path)
custom_model = custom_yolo.model  # This is the actual nn.Module

# --- Load the regular YOLOv11 model ---
baseline_model = YOLO('yolov11').model

# --- Function to collect Conv2d layers ---
def get_conv_weights(model):
    conv_dict = {}
    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            conv_dict[name] = module.weight.detach().clone()
    return conv_dict

# --- Get weights for both models ---
custom_convs = get_conv_weights(custom_model)
baseline_convs = get_conv_weights(baseline_model)

# --- Compare weights ---
print("\n🔍 Modified Conv Layers:")
for name in custom_convs:
    if name in baseline_convs:
        if not torch.equal(custom_convs[name], baseline_convs[name]):
            print(f"Layer '{name}' has changed.")
    else:
        print(f"Layer '{name}' not found in baseline model (possibly custom added).")
