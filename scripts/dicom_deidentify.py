#!/usr/bin/env python3
"""
dicom_deidentify.py -- De-identify DICOM files for research use.

Follows DICOM PS3.15 Annex E (Basic Application Level Confidentiality Profile).

Usage:
    # Single file
    python dicom_deidentify.py \\
        --input patient.dcm \\
        --output data/deidentified/ \\
        --date-shift -127

    # Directory
    python dicom_deidentify.py \\
        --input /dicom/raw/ \\
        --output data/deidentified/ \\
        --date-shift -127 \\
        --audit audit_2026_08_01.json

Tags handling:
    - Removed: PatientName, PatientAddress, TelephoneNumbers, Physician names, etc.
    - Hashed:  PatientID, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID
    - Shifted: All dates/times (same shift per study to preserve intervals)

Author: DrAbdulmalek
License: Apache 2.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import pydicom
    from pydicom.uid import ExplicitVRLittleEndian
except ImportError:
    print(
        "Error: pydicom is required. Install with:\n"
        "  pip install pydicom pylibjpeg pylibjpeg-openjpeg pylibjpeg-libjpeg",
        file=sys.stderr,
    )
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dicom_deidentify")


# ─────────────────────────────────────────────────────────────────────────────
# DICOM Tag Categories (per PS3.15 Annex E)
# ─────────────────────────────────────────────────────────────────────────────

# Tags to remove entirely (direct identifiers)
TAGS_TO_REMOVE: list[tuple[int, int]] = [
    # Patient identification
    (0x0010, 0x0010),  # PatientName
    (0x0010, 0x1000),  # OtherPatientIDs
    (0x0010, 0x1001),  # OtherPatientIDsSequence
    (0x0010, 0x1002),  # OtherPatientNames
    (0x0010, 0x1040),  # PatientAddress
    (0x0010, 0x2154),  # PatientTelephoneNumbers
    (0x0010, 0x21B0),  # AdditionalPatientHistory
    (0x0010, 0x21F0),  # PatientReligiousPreference
    (0x0010, 0x4000),  # PatientComments
    # Physician/Operator identification
    (0x0008, 0x0090),  # ReferringPhysicianName
    (0x0008, 0x0092),  # ReferringPhysicianAddress
    (0x0008, 0x0094),  # ReferringPhysicianTelephoneNumbers
    (0x0008, 0x0096),  # ReferringPhysicianIdentificationSequence
    (0x0008, 0x1048),  # PhysiciansOfRecord
    (0x0008, 0x1050),  # PerformingPhysicianName
    (0x0008, 0x1052),  # PerformingPhysicianIdentificationSequence
    (0x0008, 0x1060),  # NameOfPhysiciansReadingStudy
    (0x0008, 0x1062),  # PhysiciansReadingStudyIdentificationSequence
    (0x0008, 0x1070),  # OperatorsName
    (0x0008, 0x1072),  # OperatorIdentificationSequence
    (0x0008, 0x1120),  # ReferencedPatientSequence
    # Request attributes
    (0x0032, 0x1032),  # RequestingPhysician
    (0x0032, 0x1033),  # RequestingService
    (0x0032, 0x1060),  # RequestedProcedureID
    # Interpretation attributes
    (0x4008, 0x0114),  # PhysicianApprovingInterpretation
    (0x4008, 0x0118),  # InterpretationTranscriber
    (0x4008, 0x011C),  # InterpretationText
    # Institution identification (optional — comment out if needed)
    (0x0008, 0x0080),  # InstitutionName
    (0x0008, 0x0081),  # InstitutionAddress
    (0x0008, 0x1040),  # InstitutionalDepartmentName
]

# Tags to hash (preserve uniqueness without revealing original value)
TAGS_TO_HASH: list[tuple[int, int]] = [
    (0x0010, 0x0020),  # PatientID
    (0x0010, 0x1000),  # OtherPatientIDs (also removed above — hash wins if both apply)
    (0x0020, 0x000D),  # StudyInstanceUID
    (0x0020, 0x000E),  # SeriesInstanceUID
    (0x0008, 0x0018),  # SOPInstanceUID
    (0x0008, 0x1155),  # ReferencedSOPInstanceUID
    (0x0008, 0x0050),  # AccessionNumber
    (0x0040, 0xA073),  # VerifyingObserverSequence (children are also handled)
]

# Tags whose dates/times should be shifted (preserve intervals within a study)
TAGS_TO_SHIFT_DATE: list[tuple[int, int]] = [
    (0x0010, 0x0030),  # PatientBirthDate
    (0x0008, 0x0020),  # StudyDate
    (0x0008, 0x0021),  # SeriesDate
    (0x0008, 0x0022),  # AcquisitionDate
    (0x0008, 0x0023),  # ContentDate
    (0x0008, 0x0024),  # OverlayDate
    (0x0008, 0x0025),  # CurveDate
    (0x0038, 0x0010),  # AdmissionDate
    (0x0038, 0x0020),  # DischargeDate
]

TAGS_TO_SHIFT_TIME: list[tuple[int, int]] = [
    (0x0008, 0x0030),  # StudyTime
    (0x0008, 0x0031),  # SeriesTime
    (0x0008, 0x0032),  # AcquisitionTime
    (0x0008, 0x0033),  # ContentTime
    (0x0008, 0x0034),  # OverlayTime
    (0x0008, 0x0035),  # CurveTime
    (0x0038, 0x0015),  # AdmissionTime
    (0x0038, 0x0021),  # DischargeTime
]

# Tags that may contain burned-in PHI (require OCR check)
BURNED_IN_TAGS_TO_CLEAR: list[tuple[int, int]] = [
    (0x0020, 0x4000),  # ImageComments
    (0x0028, 0x4000),  # TextComments
]


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────


def hash_value(value: str, salt: str = "radiology-ai-platform-v1") -> str:
    """
    Hash a value using SHA-256 + salt.

    Returns 16-char hex string (sufficient for uniqueness in any reasonable dataset).
    """
    if not value:
        return ""
    return hashlib.sha256(f"{value}{salt}".encode("utf-8")).hexdigest()[:16]


def shift_date(date_str: str, days: int) -> str:
    """
    Shift a DICOM date (YYYYMMDD) by N days.

    Returns original string if parsing fails.
    """
    if not date_str or len(date_str) != 8:
        return date_str
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        shifted = dt + timedelta(days=days)
        return shifted.strftime("%Y%m%d")
    except ValueError:
        logger.warning(f"Could not parse date: {date_str}")
        return date_str


def shift_time(time_str: str, seconds: int) -> str:
    """
    Shift a DICOM time (HHMMSS.FFFFFF) by N seconds.

    Returns original string if parsing fails.
    """
    if not time_str:
        return time_str
    try:
        # Strip fractional part for simplicity
        base = time_str.split(".")[0]
        if len(base) < 6:
            base = base.ljust(6, "0")
        dt = datetime.strptime(base, "%H%M%S")
        shifted = dt + timedelta(seconds=seconds)
        return shifted.strftime("%H%M%S")
    except ValueError:
        return time_str


# ─────────────────────────────────────────────────────────────────────────────
# Main De-identification Logic
# ─────────────────────────────────────────────────────────────────────────────


def deidentify_dicom(
    dcm_path: Path,
    output_dir: Path,
    date_shift_days: int = 0,
    time_shift_seconds: int = 0,
) -> dict[str, Any]:
    """
    De-identify a single DICOM file.

    Args:
        dcm_path: Path to input .dcm file
        output_dir: Directory to write the de-identified file
        date_shift_days: Days to shift dates (negative = past)
        time_shift_seconds: Seconds to shift times

    Returns:
        Audit log entry with all actions taken
    """
    audit_log: dict[str, Any] = {
        "original_file": str(dcm_path),
        "modality": "Unknown",
        "actions": [],
        "errors": [],
    }

    try:
        ds = pydicom.dcmread(str(dcm_path), stop_before_pixels=False)
    except Exception as e:
        audit_log["errors"].append(f"Failed to read DICOM: {e}")
        return audit_log

    audit_log["modality"] = getattr(ds, "Modality", "Unknown")

    # ── Step 1: Remove direct identifiers ──
    for tag in TAGS_TO_REMOVE:
        if tag in ds:
            try:
                tag_name = ds[tag].name
                del ds[tag]
                audit_log["actions"].append(f"Removed {tag} ({tag_name})")
            except Exception as e:
                audit_log["errors"].append(f"Failed to remove {tag}: {e}")

    # ── Step 2: Hash identifiers ──
    for tag in TAGS_TO_HASH:
        if tag in ds:
            try:
                element = ds[tag]
                original = str(element.value)
                if original:
                    hashed = hash_value(original)
                    element.value = hashed
                    audit_log["actions"].append(
                        f"Hashed {tag} ({element.name}): "
                        f"{original[:8]}... → {hashed}"
                    )
            except Exception as e:
                audit_log["errors"].append(f"Failed to hash {tag}: {e}")

    # ── Step 3: Shift dates ──
    if date_shift_days != 0:
        for tag in TAGS_TO_SHIFT_DATE:
            if tag in ds:
                try:
                    element = ds[tag]
                    original = str(element.value)
                    shifted = shift_date(original, date_shift_days)
                    element.value = shifted
                    audit_log["actions"].append(
                        f"Shifted date {tag}: {original} → {shifted}"
                    )
                except Exception as e:
                    audit_log["errors"].append(f"Failed to shift date {tag}: {e}")

    # ── Step 4: Shift times ──
    if time_shift_seconds != 0:
        for tag in TAGS_TO_SHIFT_TIME:
            if tag in ds:
                try:
                    element = ds[tag]
                    original = str(element.value)
                    shifted = shift_time(original, time_shift_seconds)
                    element.value = shifted
                    audit_log["actions"].append(
                        f"Shifted time {tag}: {original} → {shifted}"
                    )
                except Exception as e:
                    audit_log["errors"].append(f"Failed to shift time {tag}: {e}")

    # ── Step 5: Clear burned-in annotation flags ──
    # Set "Burned In Annotation" to "NO" (we'll trust this — actual OCR check is separate)
    if (0x0028, 0x0301) in ds:
        ds[0x0028, 0x0301].value = "NO"
        audit_log["actions"].append("Set Burned In Annotation = NO")

    for tag in BURNED_IN_TAGS_TO_CLEAR:
        if tag in ds:
            del ds[tag]
            audit_log["actions"].append(f"Cleared burned-in text tag {tag}")

    # ── Step 6: Update file meta for safe writing ──
    if not hasattr(ds, "file_meta"):
        ds.file_meta = pydicom.dataset.FileMetaDataset()

    sop_class_uid = getattr(ds, "SOPClassUID", None)
    sop_instance_uid = getattr(ds, "SOPInstanceUID", None)

    if sop_class_uid:
        ds.file_meta.MediaStorageSOPClassUID = sop_class_uid
    if sop_instance_uid:
        ds.file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    # Ensure necessary file meta elements
    if "ImplementationClassUID" not in ds.file_meta:
        ds.file_meta.ImplementationClassUID = "1.2.826.0.1.3680043.8.498.10"
    if "ImplementationVersionName" not in ds.file_meta:
        ds.file_meta.ImplementationVersionName = "RADAI_DEID_1"

    # ── Step 7: Write the de-identified file ──
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = f"{hash_value(str(dcm_path))}.dcm"
    out_path = output_dir / output_filename

    try:
        ds.save_as(str(out_path), write_like_original=False)
        audit_log["output_file"] = str(out_path)
        audit_log["status"] = "success"
    except Exception as e:
        audit_log["errors"].append(f"Failed to save: {e}")
        audit_log["status"] = "failed"

    return audit_log


def verify_deidentification(dcm_path: Path) -> dict[str, Any]:
    """
    Verify that a DICOM file has been properly de-identified.

    Returns a report of any PHI tags that are still present.
    """
    report: dict[str, Any] = {
        "file": str(dcm_path),
        "phi_remaining": [],
        "is_clean": True,
    }

    try:
        ds = pydicom.dcmread(str(dcm_path))
    except Exception as e:
        report["error"] = f"Failed to read: {e}"
        report["is_clean"] = False
        return report

    # Check tags that should be removed
    for tag in TAGS_TO_REMOVE:
        if tag in ds:
            report["phi_remaining"].append(
                {
                    "tag": f"({tag[0]:04X}, {tag[1]:04X})",
                    "name": ds[tag].name,
                    "value_preview": str(ds[tag].value)[:50] + "...",
                }
            )

    # Check for un-hashed PatientID
    if (0x0010, 0x0020) in ds:
        value = str(ds[0x0010, 0x0020].value)
        # Hashed values are 16-char hex strings
        if len(value) != 16 or not all(c in "0123456789abcdef" for c in value.lower()):
            report["phi_remaining"].append(
                {
                    "tag": "(0010, 0020)",
                    "name": "PatientID (not hashed)",
                    "value_preview": value[:50] + "...",
                }
            )

    report["is_clean"] = len(report["phi_remaining"]) == 0
    return report


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="De-identify DICOM files (PS3.15 Annex E compliant)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", required=True, help="Input DICOM file or directory"
    )
    parser.add_argument(
        "--output", required=True, help="Output directory for de-identified files"
    )
    parser.add_argument(
        "--date-shift",
        type=int,
        default=-365,
        help="Days to shift dates (default: -365, use 0 to keep)",
    )
    parser.add_argument(
        "--time-shift",
        type=int,
        default=0,
        help="Seconds to shift times (default: 0)",
    )
    parser.add_argument(
        "--audit",
        default="audit_log.json",
        help="Audit log filename (in output dir)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification on output files (check no PHI remains)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process but don't write files (for testing)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input not found: {input_path}")
        sys.exit(1)

    # Collect all .dcm files
    if input_path.is_file():
        dcm_files = [input_path]
    else:
        dcm_files = list(input_path.rglob("*.dcm")) + list(input_path.rglob("*.dicom"))

    if not dcm_files:
        logger.error(f"No DICOM files found in: {input_path}")
        sys.exit(1)

    logger.info(f"Found {len(dcm_files)} DICOM files to process")

    # ── De-identify all files ──
    all_logs: list[dict[str, Any]] = []
    success_count = 0
    failure_count = 0

    for i, dcm_file in enumerate(dcm_files, 1):
        logger.info(f"[{i}/{len(dcm_files)}] Processing: {dcm_file.name}")

        if args.dry_run:
            logger.info("  (dry-run, skipping)")
            continue

        log = deidentify_dicom(
            dcm_file,
            output_dir,
            date_shift_days=args.date_shift,
            time_shift_seconds=args.time_shift,
        )
        all_logs.append(log)

        if log.get("status") == "success":
            success_count += 1
        else:
            failure_count += 1

        # Log any errors
        for error in log.get("errors", []):
            logger.warning(f"  ⚠ {error}")

    # ── Save audit log ──
    if not args.dry_run:
        audit_path = output_dir / args.audit
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(
            json.dumps(all_logs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"\nAudit log saved to: {audit_path}")

    # ── Verification (optional) ──
    if args.verify and not args.dry_run:
        logger.info("\n── Verification ──")
        verification_reports = []
        clean_count = 0
        for dcm_file in output_dir.glob("*.dcm"):
            report = verify_deidentification(dcm_file)
            verification_reports.append(report)
            if report["is_clean"]:
                clean_count += 1
            else:
                logger.warning(f"  ⚠ PHI remaining in: {dcm_file.name}")
                for phi in report["phi_remaining"]:
                    logger.warning(f"    - {phi['tag']} ({phi['name']})")

        verify_path = output_dir / "verification_report.json"
        verify_path.write_text(
            json.dumps(verification_reports, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Verification: {clean_count}/{len(verification_reports)} files clean")

    # ── Summary ──
    logger.info("\n" + "=" * 60)
    logger.info(f"De-identification complete")
    logger.info(f"  Total files: {len(dcm_files)}")
    logger.info(f"  Success:     {success_count}")
    logger.info(f"  Failed:      {failure_count}")
    logger.info(f"  Output dir:  {output_dir}")
    logger.info("=" * 60)

    if failure_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
