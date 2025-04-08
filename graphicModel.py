from torchview import draw_graph
import os
import torch
from ultralytics import YOLO
import torch.nn as nn

# --- Load YOLO model ---
model_path = os.path.join(os.getcwd(), "app", "single_model0.3.1.pt")
custom_yolo = YOLO(model_path)
custom_model = custom_yolo.model  # This is the nn.Module you need

# --- Dummy input for tracing ---
dummy_input = torch.randn(1, 3, 640, 640)

# --- Draw architecture graph ---
graph = draw_graph(
    custom_model,
    input_data=dummy_input,
    graph_dir='LR',             # Left-to-right layout for posters
    save_graph=True,
    filename="yolo_architecture"  # Will save as PNG by default
)
