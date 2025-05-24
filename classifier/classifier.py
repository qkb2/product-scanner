import torch
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import os

# Basic config
MODEL_PATH = "files/model.pt"  # fine-tuned ResNet model
VERSION_PATH = "files/v.txt"
CURRENT_VERSION = "NONE"


def load_model():
    try:
        with open(VERSION_PATH, "r") as f:
            global CURRENT_VERSION
            CURRENT_VERSION = f.read().strip()
    except Exception as e:
        pass

    model = torch.load(MODEL_PATH, map_location=torch.device("cpu"), weights_only=False)
    model.eval()
    return model


model = load_model()

transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)


def classify_image(image_path: str) -> int:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(tensor)
        _, predicted = torch.max(outputs, 1)
        return int(predicted.item())


def get_version() -> str:
    return CURRENT_VERSION
