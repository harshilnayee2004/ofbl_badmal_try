#!/usr/bin/env python3
"""
Cleanup Script for Badmal 2.0 Inspection System
Deletes Carrier, Box, and Primer/Fuze Lots, along with all associated inspection records,
inspection logs, and media files on disk.

Usage:
  python cleanup_lots.py --all -y                  # Delete everything immediately
  python cleanup_lots.py --all                     # Delete all lots with confirmation
  python cleanup_lots.py --lot-id 5                # Delete a specific lot by ID
  python cleanup_lots.py --lot-number LOT123       # Delete a specific lot by lot number
  python cleanup_lots.py --type carrier            # Delete only carrier lots
  python cleanup_lots.py --type box                # Delete only box lots
  python cleanup_lots.py --type fuze               # Delete only primer/fuze lots
  python cleanup_lots.py --keep-files              # Delete DB records only, leave files on disk
  python cleanup_lots.py --stats                   # View summary statistics only
"""

import os
import sys
import shutil
import argparse
from typing import List, Optional
from sqlmodel import Session, select, delete

# Ensure script can import web_server modules when executed from any cwd
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from core.database import engine
from core.config import settings

# Import all models to ensure complete relational coverage
from models.lot_model import Lot
from models.carrier_model import Carrier
from models.carrier_6al_inspection_model import Carrier6ALInspection
from models.carrier_log_model import CarrierLog

from models.box_model import Box
from models.box_h2a_inspection_model import BoxH2AInspection
from models.box_log_model import BoxLog

from models.primer_model import Primer, Primer as Fuze
from models.primer_1al_inspection_model import Primer1ALInspection
from models.primer_log_model import PrimerLog, PrimerLog as FuzeLog


def get_counts(db: Session):
    """Return record counts across all lot-related tables."""
    return {
        "lots": len(db.exec(select(Lot)).all()),
        "carriers": len(db.exec(select(Carrier)).all()),
        "carrier_6al_inspections": len(db.exec(select(Carrier6ALInspection)).all()),
        "carrier_logs": len(db.exec(select(CarrierLog)).all()),
        "boxes": len(db.exec(select(Box)).all()),
        "box_h2a_inspections": len(db.exec(select(BoxH2AInspection)).all()),
        "box_logs": len(db.exec(select(BoxLog)).all()),
        "primers": len(db.exec(select(Primer)).all()),
        "primer_1al_inspections": len(db.exec(select(Primer1ALInspection)).all()),
        "primer_logs": len(db.exec(select(PrimerLog)).all()),
    }


def print_stats(counts: dict, title: str = "Current Database State"):
    print("\n" + "=" * 55)
    print(f" {title.center(51)} ")
    print("=" * 55)
    print(f"  - Lots (Total)              : {counts['lots']}")
    print(f"  - Carriers                  : {counts['carriers']}")
    print(f"  - Carrier Inspections (6A/L): {counts['carrier_6al_inspections']}")
    print(f"  - Carrier Logs              : {counts['carrier_logs']}")
    print(f"  - Boxes                     : {counts['boxes']}")
    print(f"  - Box Inspections (H2A/M/G) : {counts['box_h2a_inspections'] + counts['box_m104_inspections'] + counts['box_g70_inspections']}")
    print(f"  - Box Logs                  : {counts['box_logs']}")
    print(f"  - Primers / Fuzes           : {counts['fuzes']}")
    print(f"  - Primer Inspections (1A/L) : {counts['primer_1al_inspections']}")
    print(f"  - Primer Logs               : {counts['fuze_logs']}")
    print("=" * 55 + "\n")


def remove_lot_files(lot: Lot):
    """Safely delete lot media files/directory from disk."""
    if not lot.files_path:
        return
    
    # Check both relative to LOT_DETAILS_PATH and direct path
    candidate_paths = [
        lot.files_path,
        os.path.join(settings.LOT_DETAILS_PATH, lot.files_path),
        os.path.join(SCRIPT_DIR, settings.LOT_DETAILS_PATH, lot.files_path)
    ]

    for p in candidate_paths:
        if os.path.exists(p) and os.path.isdir(p):
            try:
                shutil.rmtree(p)
                print(f"  [Disk] Removed directory: {p}")
            except Exception as e:
                print(f"  [Disk] Warning: Could not remove directory {p}: {e}")


def delete_lots_by_instances(db: Session, lots_to_delete: List[Lot], delete_files: bool = True) -> int:
    """Cascade delete specified lots and all associated records."""
    if not lots_to_delete:
        print("No matching lots found to delete.")
        return 0

    lot_ids = [lot.id for lot in lots_to_delete if lot.id is not None]

    print(f"\nProceeding to delete {len(lot_ids)} lot(s) (IDs: {lot_ids})...")

    # 1. Clean disk files if requested
    if delete_files:
        for lot in lots_to_delete:
            remove_lot_files(lot)

    # 2. Collect child entities
    carriers = db.exec(select(Carrier).where(Carrier.lot_id.in_(lot_ids))).all()
    carrier_ids = [c.id for c in carriers if c.id is not None]
    carrier_insp_ids = [c.carrier_6al_inspection_id for c in carriers if c.carrier_6al_inspection_id is not None]

    boxes = db.exec(select(Box).where(Box.lot_id.in_(lot_ids))).all()
    box_ids = [b.id for b in boxes if b.id is not None]
    box_h2a_ids = [b.box_h2a_inspection_id for b in boxes if b.box_h2a_inspection_id is not None]

    fuzes = db.exec(select(Fuze).where(Fuze.lot_id.in_(lot_ids))).all()
    fuze_ids = [f.id for f in fuzes if f.id is not None]
    primer_1al_ids = [f.primer_1al_inspection_id for f in fuzes if f.primer_1al_inspection_id is not None]

    # 3. Delete Logs
    if fuze_ids:
        db.exec(delete(FuzeLog).where(FuzeLog.fuze_id.in_(fuze_ids)))
    if box_ids:
        db.exec(delete(BoxLog).where(BoxLog.box_id.in_(box_ids)))
    if carrier_ids:
        db.exec(delete(CarrierLog).where(CarrierLog.carrier_id.in_(carrier_ids)))
    db.commit()

    # 4. Delete Primers & Primer Inspections
    if fuze_ids:
        db.exec(delete(Fuze).where(Fuze.id.in_(fuze_ids)))
    if primer_1al_ids:
        db.exec(delete(Primer1ALInspection).where(Primer1ALInspection.id.in_(primer_1al_ids)))
    db.commit()

    # 5. Delete Boxes & Box Inspections
    if box_ids:
        db.exec(delete(Box).where(Box.id.in_(box_ids)))
    if box_h2a_ids:
        db.exec(delete(BoxH2AInspection).where(BoxH2AInspection.id.in_(box_h2a_ids)))
    db.commit()

    # 6. Delete Carriers & Carrier Inspections
    if carrier_ids:
        db.exec(delete(Carrier).where(Carrier.id.in_(carrier_ids)))
    if carrier_insp_ids:
        db.exec(delete(Carrier6ALInspection).where(Carrier6ALInspection.id.in_(carrier_insp_ids)))
    db.commit()

    # 7. Delete Lots
    db.exec(delete(Lot).where(Lot.id.in_(lot_ids)))
    db.commit()

    print(f" Successfully deleted {len(lot_ids)} lot(s) and all related records.")
    return len(lot_ids)


def purge_entire_lots_directory():
    """Wipe everything inside the lots_details directory."""
    target_dirs = [
        os.path.join(SCRIPT_DIR, settings.LOT_DETAILS_PATH),
        settings.LOT_DETAILS_PATH
    ]
    for d in target_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            for item in os.listdir(d):
                item_path = os.path.join(d, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    elif os.path.isfile(item_path) and not item.startswith("."):
                        os.remove(item_path)
                except Exception as e:
                    print(f"Warning: Could not remove {item_path}: {e}")
            print(f"  [Disk] Cleaned all contents inside: {d}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up Lots, Carriers, Boxes, Primers/Fuzes, and media in Badmal 2.0."
    )
    parser.add_argument("--all", "-a", action="store_true", help="Delete all lots across all types")
    parser.add_argument("--lot-id", "-i", type=int, help="Delete a specific lot by ID")
    parser.add_argument("--lot-number", "-n", type=str, help="Delete a specific lot by Lot Number")
    parser.add_argument("--type", "-t", choices=["carrier", "box", "fuze", "primer"], help="Delete only lots of a given type")
    parser.add_argument("--keep-files", action="store_true", help="Do not delete media folders from disk")
    parser.add_argument("--stats", "-s", action="store_true", help="Show database record counts and exit")
    parser.add_argument("--yes", "-y", action="store_true", help="Bypass interactive confirmation prompt")

    args = parser.parse_args()

    with Session(engine) as db:
        initial_counts = get_counts(db)

        if args.stats:
            print_stats(initial_counts, "Current Database Record Counts")
            return

        print_stats(initial_counts, "Initial Database Status")

        # Determine target lots
        lots_to_delete: List[Lot] = []

        if args.lot_id:
            lots = db.exec(select(Lot).where(Lot.id == args.lot_id)).all()
            lots_to_delete.extend(lots)
        elif args.lot_number:
            lots = db.exec(select(Lot).where(Lot.lot_number == args.lot_number)).all()
            lots_to_delete.extend(lots)
        elif args.type:
            t = args.type.lower()
            if t == "carrier":
                lots = db.exec(select(Lot).where(Lot.carrier_type != None)).all()
            elif t == "box":
                lots = db.exec(select(Lot).where(Lot.box_type != None)).all()
            elif t in ["fuze", "primer"]:
                lots = db.exec(select(Lot).where(Lot.fuze_type != None)).all()
            lots_to_delete.extend(lots)
        elif args.all:
            lots_to_delete = db.exec(select(Lot)).all()
        else:
            # Interactive choice if no specific argument passed
            print("Select Cleanup Action:")
            print("  1. Delete ALL lots (Carriers, Boxes, Primers)")
            print("  2. Delete only Carrier lots")
            print("  3. Delete only Box lots")
            print("  4. Delete only Primer/Fuze lots")
            print("  5. View Statistics only")
            print("  0. Cancel & Exit")

            choice = input("\nEnter choice [0-5]: ").strip()
            if choice == "1":
                lots_to_delete = db.exec(select(Lot)).all()
            elif choice == "2":
                lots_to_delete = db.exec(select(Lot).where(Lot.carrier_type != None)).all()
            elif choice == "3":
                lots_to_delete = db.exec(select(Lot).where(Lot.box_type != None)).all()
            elif choice == "4":
                lots_to_delete = db.exec(select(Lot).where(Lot.fuze_type != None)).all()
            elif choice == "5":
                return
            else:
                print("Aborted. No changes made.")
                return

        if not lots_to_delete:
            print("No matching lots found to delete.")
            return

        print(f"\n[!] Selected {len(lots_to_delete)} lot(s) for permanent deletion.")
        for lot in lots_to_delete[:10]:
            print(f"    - ID: {lot.id:3d} | Lot Number: {str(lot.lot_number):15s} | Type: {lot.carrier_type or lot.box_type or lot.fuze_type or 'General'}")
        if len(lots_to_delete) > 10:
            print(f"    ... and {len(lots_to_delete) - 10} more.")

        # Confirmation prompt
        if not args.yes:
            confirm = input("\nAre you SURE you want to permanently delete these lots and all child records? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("Deletion cancelled by user. No data was modified.")
                return

        # Execute deletion
        delete_lots_by_instances(db, lots_to_delete, delete_files=not args.keep_files)

        if args.all and not args.keep_files:
            purge_entire_lots_directory()

        final_counts = get_counts(db)
        print_stats(final_counts, "Database Status After Cleanup")


if __name__ == "__main__":
    main()
