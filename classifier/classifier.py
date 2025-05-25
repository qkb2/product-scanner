import torch
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
import os


class ImageClassifier:
    def __init__(self, model_path="files/model.pt", version_path="files/v.txt"):
        self.model_path = model_path
        self.version_path = version_path
        self.model = None
        self.version = "NONE"
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        self.load_model()

    def load_model(self):
        try:
            with open(self.version_path, "r") as f:
                self.version = f.read().strip()
        except Exception as e:
            # Could log or print the error if needed
            print("Model v. unknown")
            self.version = "UNKNOWN"

        try:
            self.model = torch.load(self.model_path, map_location=torch.device("cpu"), weights_only=False)
            self.model.eval()
        except Exception as e:
            # Could log or print the error if needed
            print(f"Could not load model: {e}")
            self.model = None

    def classify_image(self, image_path: str) -> int:
        if self.model is None:
            raise RuntimeError("Model not loaded. Cannot classify image.")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = Image.open(image_path).convert("RGB")
        tensor = self.transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = self.model(tensor)
            _, predicted = torch.max(outputs, 1)
            return int(predicted.item())

    def get_version(self) -> str:
        return self.version
