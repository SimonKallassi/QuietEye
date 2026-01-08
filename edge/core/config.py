from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass(frozen=True)
class CameraConfig:
    camera_id: str
    name: str
    rtsp_url: str
    zones: List[str]


@dataclass(frozen=True)
class SiteConfig:
    site_id: str
    device_id: str
    cameras: List[CameraConfig]


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing YAML config: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSON config: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_site_config(cameras_yaml: Path) -> SiteConfig:
    raw = load_yaml(cameras_yaml)

    site_id = raw.get("site_id")
    device_id = raw.get("device_id")
    cameras = raw.get("cameras", [])

    if not site_id or not device_id:
        raise ValueError("configs/cameras.yaml must include site_id and device_id")

    parsed_cameras: List[CameraConfig] = []
    for c in cameras:
        if "camera_id" not in c or "rtsp_url" not in c:
            raise ValueError("Each camera must have camera_id and rtsp_url in cameras.yaml")

        parsed_cameras.append(
            CameraConfig(
                camera_id=str(c["camera_id"]),
                name=str(c.get("name", c["camera_id"])),
                rtsp_url=str(c["rtsp_url"]),
                zones=list(c.get("zones", [])),
            )
        )

    return SiteConfig(site_id=site_id, device_id=device_id, cameras=parsed_cameras)

