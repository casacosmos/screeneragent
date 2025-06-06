#!/usr/bin/env python3
# flood_helpers.py
"""
Light-weight helpers for FEMA flood work

Public API
----------
get_flood_data(longitude, latitude, **kw)      -> dict
generate_flood_maps(longitude, latitude, **kw) -> dict

Both helpers delegate the heavy lifting to the private functions that already
exist in `comprehensive_flood_tool.py`, so keep that file unchanged and on the
Python path.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# --------------------------------------------------------------------------- #
#  import the "private" helpers from your big flood module                    #
# --------------------------------------------------------------------------- #

try:
    from comprehensive_flood_tool import (
        _extract_flood_information,
        _generate_firmette_safe,
        _generate_preliminary_safe,
        _generate_abfe_safe,
    )
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "flood_helpers requires comprehensive_flood_tool.py on your PYTHONPATH\n"
        f"Original import error: {e}"
    )

# Also reuse its I/O utilities
from output_directory_manager import get_output_manager
from query_coordinates_data import (
    query_coordinate_data,
    extract_panel_information,
)

# --------------------------------------------------------------------------- #
#  PUBLIC:  get_flood_data                                                    #
# --------------------------------------------------------------------------- #

def get_flood_data(
    *,
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    save_raw_files: bool = True,
) -> Dict[str, Any]:
    """
    Fetch FEMA/NFHL info & normalise it into a JSON-ready dict.
    Generates **no maps**.

    Returns the same dictionary structure you're used to seeing in the big
    monolithic tool, minus the `reports_generated` block.
    """
    if location_name is None:
        location_name = f"({latitude:.5f}, {longitude:.5f})"

    mgr = get_output_manager()
    
    # Use external project directory if configured
    if os.environ.get('ENV_PROJECT_DIR'):
        external_dir = os.environ['ENV_PROJECT_DIR']
        mgr.current_project_dir = external_dir
        mgr.current_project_name = os.path.basename(external_dir)
        print(f"📁 Flood data using external project directory: {external_dir}")
    elif not mgr.current_project_dir:
        mgr.create_project_directory(location_name, (longitude, latitude))

    result: Dict[str, Any] = {
        "analysis_metadata": {
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude},
            "analysis_time": datetime.utcnow().isoformat(timespec="seconds"),
        },
        "flood_information": {},
        "raw_data_summary": {},
        "errors": [],
    }

    try:
        # ---- raw FEMA services ---------------------------------------------
        raw = query_coordinate_data(longitude, latitude, location_name)
        panel_info = extract_panel_information(raw)
        result["flood_information"] = _extract_flood_information(panel_info)
        result["raw_data_summary"] = raw["summary"]

        # ---- optional persisting of raw JSON -------------------------------
        if save_raw_files:
            log_dir = mgr.get_subdirectory("logs")
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            fname = os.path.join(
                log_dir,
                f"flood_raw_{longitude:.5f}_{latitude:.5f}_{ts}.json".replace("-", "neg"),
            )
            with open(fname, "w") as fh:
                json.dump(raw, fh, indent=2, default=str)
            result["raw_data_summary"]["raw_json_path"] = fname

        result["success"] = True
        return result

    except Exception as exc:  # pragma: no cover
        result["errors"].append(str(exc))
        result["success"] = False
        return result


# --------------------------------------------------------------------------- #
#  PUBLIC:  generate_flood_maps                                               #
# --------------------------------------------------------------------------- #

def generate_flood_maps(
    *,
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    include_abfe: bool = True,
    timeout_sec: int = 120,
) -> Dict[str, Any]:
    """
    Produce up to three PDFs (FIRMette, Preliminary Comparison, ABFE)
    and return their metadata.

    The PDFs are written into the **current** project's `reports/` directory.
    """
    import concurrent.futures

    if location_name is None:
        location_name = f"({latitude:.5f}, {longitude:.5f})"

    mgr = get_output_manager()
    
    # Use external project directory if configured
    if os.environ.get('ENV_PROJECT_DIR'):
        external_dir = os.environ['ENV_PROJECT_DIR']
        mgr.current_project_dir = external_dir
        mgr.current_project_name = os.path.basename(external_dir)
        print(f"📁 Flood maps using external project directory: {external_dir}")
    elif not mgr.current_project_dir:
        mgr.create_project_directory(location_name, (longitude, latitude))

    reports = {
        "firmette": {"requested": True, "success": False},
        "preliminary_comparison": {"requested": True, "success": False},
        "abfe_map": {"requested": include_abfe, "success": False},
    }
    errors: list[str] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futs = {
            "firmette": pool.submit(
                _generate_firmette_safe, longitude, latitude, location_name, mgr
            ),
            "preliminary_comparison": pool.submit(
                _generate_preliminary_safe, longitude, latitude, location_name, mgr
            ),
        }
        if include_abfe:
            futs["abfe_map"] = pool.submit(
                _generate_abfe_safe, longitude, latitude, location_name, mgr
            )

        for name, fut in futs.items():
            try:
                meta = fut.result(timeout=timeout_sec)
                reports[name].update(meta)
            except Exception as exc:  # pragma: no cover
                reports[name]["success"] = False
                reports[name]["error"] = str(exc)
                errors.append(f"{name} map failed: {exc}")

    return {"reports_generated": reports, "errors": errors}

# --------------------------------------------------------------------------- #
# End of file                                                                 #
# --------------------------------------------------------------------------- #
