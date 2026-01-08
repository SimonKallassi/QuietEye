from __future__ import annotations

from pathlib import Path

from edge.client import QuietEyeBackendClient
from edge.core.config import load_site_config
from edge.core.events import QuietEyeEvent


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cameras_yaml = repo_root / "configs" / "cameras.yaml"

    site = load_site_config(cameras_yaml)

    # Pick first camera for a simple “wiring test”
    cam = site.cameras[0] if site.cameras else None
    if not cam:
        raise RuntimeError("No cameras found in configs/cameras.yaml")

    # Create a fake event (this proves edge->backend plumbing)
    evt = QuietEyeEvent(
        event_type="AFTER_HOURS_PRESENCE",
        site_id=site.site_id,
        device_id=site.device_id,
        camera_id=cam.camera_id,
        zone=(cam.zones[0] if cam.zones else None),
        confidence=0.99,
        extra={"note": "quieteye edge wiring test"},
    )

    client = QuietEyeBackendClient.from_env()
    result = client.post_event(evt)

    print("✅ Event posted successfully.")
    print(result)


if __name__ == "__main__":
    main()
