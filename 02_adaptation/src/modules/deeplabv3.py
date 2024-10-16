import copy
import torch
from .mobilenetv2_conditional import MobileNetV2
from .torchvision_dlv3_conditional import DeepLabV3, DeepLabHead
from torchvision._internally_replaced_utils import load_state_dict_from_url


def _deeplabv3_mobilenetv2(
        backbone: MobileNetV2,
        num_classes: int,
        num_data_types: int,
) -> DeepLabV3:
    backbone = backbone.features

    out_pos = len(backbone) - 1
    out_inplanes = backbone[out_pos][0].out_channels
    classifier = DeepLabHead(out_inplanes, num_classes, num_data_types=num_data_types)

    return DeepLabV3(backbone, classifier)


def deeplabv3_mobilenetv2(
        num_classes: int = 21,
        in_channels: int = 3,
        num_conditions: int = 1,
) -> DeepLabV3:

    width_mult = 1
    backbone = MobileNetV2(width_mult=width_mult, in_channels=in_channels, num_conditions=num_conditions)
    model_urls = {
        0.5: 'https://github.com/d-li14/mobilenetv2.pytorch/raw/master/pretrained/mobilenetv2_0.5-eaa6f9ad.pth',
        1.: 'https://github.com/d-li14/mobilenetv2.pytorch/raw/master/pretrained/mobilenetv2_1.0-0c6065bc.pth'}
    state_dict = load_state_dict_from_url(model_urls[width_mult], progress=True)
    state_dict_updated = state_dict.copy()
    for k, v in state_dict.items():
        if 'features' not in k and 'classifier' not in k:
            state_dict_updated[k.replace('conv', 'features.18')] = v
            del state_dict_updated[k]

    if in_channels == 4:
        aux = torch.zeros((32, 4, 3, 3))
        aux[:, 0, :, :] = copy.deepcopy(state_dict_updated['features.0.0.weight'][:, 0, :, :])
        aux[:, 1, :, :] = copy.deepcopy(state_dict_updated['features.0.0.weight'][:, 1, :, :])
        aux[:, 2, :, :] = copy.deepcopy(state_dict_updated['features.0.0.weight'][:, 2, :, :])
        aux[:, 3, :, :] = copy.deepcopy(state_dict_updated['features.0.0.weight'][:, 2, :, :])
        state_dict_updated['features.0.0.weight'] = aux
    backbone.load_state_dict(state_dict_updated, strict=False)

    model = _deeplabv3_mobilenetv2(backbone, num_classes, num_conditions)
    model.task = 'segmentation'

    return model
