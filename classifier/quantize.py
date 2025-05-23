import torch
from torchvision import models
from torch.quantization import quantize_fx, get_default_qconfig
import torchvision.transforms as transforms

# Device
device = torch.device("cpu")

# Load pretrained MobileNetV2
model_fp32 = models.mobilenet_v2(pretrained=True)
model_fp32.eval()
model_quantized = model_fp32

# # Prepare for FX graph mode quantization
# qconfig = get_default_qconfig("fbgemm")
# model_prepared = torch.ao.quantization.quantize_fx.prepare_fx(model_fp32, {"": qconfig})

# # Calibration (dummy data simulating real input)
# for _ in range(10):
#     dummy_input = torch.randn(1, 3, 224, 224)
#     model_prepared(dummy_input)

# # Convert to quantized model
# model_quantized = torch.ao.quantization.quantize_fx.convert_fx(model_prepared)

# Save
torch.save(model_quantized, "files/model.pt")
print("✅ Quantized MobileNetV2 saved as 'model.pt'")
