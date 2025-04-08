import os
import torch
from ultralytics import YOLO
import torch.nn as nn

# --- Load your trained model ---
model_path = os.path.join(os.getcwd(), "app", "single_model0.3.1.pt")
custom_yolo = YOLO(model_path)
custom_model = custom_yolo.model  # nn.Module object

# --- Function to collect Conv2d layers ---
def get_conv_weights(model):
    conv_dict = {}
    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            conv_dict[name] = module.weight.detach().clone()
    return conv_dict

# --- Get Conv2d layers ---
custom_convs = get_conv_weights(custom_model)

# --- Print out the Conv2d layers and their shapes ---
print("\n Conv2d Layers in Custom Model:")
for name, weight in custom_convs.items():
    print(f"{name}: {tuple(weight.shape)}")
