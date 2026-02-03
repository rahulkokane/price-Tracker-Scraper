from .mobile import extract_mobile_attributes
from .laptop import extract_laptop_attributes
from .tablet import extract_tablet_attributes
from .tv import extract_tv_attributes
from .appliance import extract_appliance_attributes
from .audio import extract_audio_attributes
from .camera import extract_camera_attributes
from .generic import extract_generic_attributes
from .utils import clean_attributes


def extract_attributes(category: str, title: str) -> dict:
    if not category:
        return {}

    c = category.lower()

    if "mobile" in c or "smartphone" in c:
        attrs = extract_mobile_attributes(title)

    elif "laptop" in c:
        attrs = extract_laptop_attributes(title)

    elif "tablet" in c or "ipad" in c:
        attrs = extract_tablet_attributes(title)

    elif "tv" in c or "television" in c:
        attrs = extract_tv_attributes(title)

    elif any(x in c for x in ["ac", "refrigerator", "washing", "appliance"]):
        attrs = extract_appliance_attributes(title)

    elif any(x in c for x in ["headphone", "earbud", "speaker", "audio"]):
        attrs = extract_audio_attributes(title)

    elif "camera" in c:
        attrs = extract_camera_attributes(title)

    else:
        attrs = {}

    return clean_attributes(attrs)
