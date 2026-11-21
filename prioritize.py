#!/usr/bin/env python3
"""
Hostel Maintenance Complaint Prioritizer (GH-3, IIITA)
======================================================
Prioritizes student maintenance complaints based on on-site fieldwork insights:
1. Category weights prioritize safety and basic utilities (Electrical & Plumbing).
2. Urgency tags add smaller bonus points (to prevent student over-tagging from skewing the queue).
3. Pending time multiplier ensures older complaints don't get buried in the physical register.
4. SLA breach bonus flags any complaint open past the 48-hour threshold.
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

# ==============================================================================
# CONFIGURATION & SCORING WEIGHTS (Easy to tune)
# ==============================================================================

# Base category weights (Electrical & Plumbing prioritized over WiFi & Furniture)
CATEGORY_WEIGHTS = {
    "Electrical": 40,
    "Plumbing": 40,
    "WiFi": 20,
    "Furniture": 15,
}
DEFAULT_CATEGORY_WEIGHT = 15

# Urgency bonus points (smaller boost so student over-tagging doesn't dominate)
URGENCY_SCORES = {
    "High": 15,
    "Medium": 10,
    "Low": 5,
}
DEFAULT_URGENCY_SCORE = 5  # Safe default if blank, missing, or unrecognized

# Aging & SLA parameters
PENDING_HOURS_MULTIPLIER = 0.5  # Points added per hour open
SLA_HOURS_THRESHOLD = 48.0      # Target maximum resolution time in hours
SLA_BREACH_BONUS = 25.0         # Penalty bonus added when open >= 48 hours

# Reference time for pending hours calculation:
# Set to None to use current system time (datetime.now()),
# or set to a string like "2026-11-21 17:00" to match fieldwork observation time.
REFERENCE_DATETIME = None

# Default output file for technician floor checklist
CHECKLIST_OUTPUT_FILE = "technician_checklist.txt"


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def parse_datetime(dt_str: str):
    """Safely parse a datetime string using common formats."""
    if not dt_str or not dt_str.strip():
        return None
    cleaned = dt_str.strip()
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def get_reference_time(latest_logged_dt=None):
    """
    Determine the reference time for calculating pending hours.
    Falls back gracefully if the system clock is set behind the dataset timestamps.
    """
    if REFERENCE_DATETIME:
        parsed = parse_datetime(REFERENCE_DATETIME)
        if parsed:
            return parsed

    now = datetime.now()
    # If the system clock is earlier than the latest dataset entry (e.g. running on an older date machine),
    # use the latest logged datetime + 1 hour so pending hours are positive and accurate.
    if latest_logged_dt and now < latest_logged_dt:
        return latest_logged_dt

    return now


def calculate_priority(row: dict, ref_time: datetime) -> dict:
    """Calculate priority score and metadata for an open complaint."""
    cid = row.get("complaint_id", "").strip() or "UNKNOWN"
    floor = row.get("floor", "").strip() or "N/A"
    
    # 1. Category Base Weight (case-insensitive)
    raw_cat = row.get("category", "").strip()
    matched_cat = next(
        (k for k in CATEGORY_WEIGHTS if k.lower() == raw_cat.lower()),
        None
    )
    category = matched_cat if matched_cat else (raw_cat.capitalize() if raw_cat else "Other")
    cat_weight = CATEGORY_WEIGHTS.get(category, DEFAULT_CATEGORY_WEIGHT)

    # 2. Urgency Bonus (case-insensitive with safe fallback)
    raw_urg = row.get("urgency", "").strip()
    matched_urg = next(
        (k for k in URGENCY_SCORES if k.lower() == raw_urg.lower()),
        None
    )
    urgency_label = matched_urg if matched_urg else ("None" if not raw_urg else raw_urg.capitalize())
    urg_bonus = URGENCY_SCORES.get(matched_urg, DEFAULT_URGENCY_SCORE)

    # 3. Pending Hours Calculation
    logged_dt = parse_datetime(row.get("logged_datetime", ""))
    if logged_dt:
        delta_seconds = (ref_time - logged_dt).total_seconds()
        pending_hours = max(0.0, delta_seconds / 3600.0)
    else:
        pending_hours = 0.0

    # 4. Aging Score & SLA Check
    aging_score = pending_hours * PENDING_HOURS_MULTIPLIER
    is_sla_breached = pending_hours >= SLA_HOURS_THRESHOLD
    sla_bonus = SLA_BREACH_BONUS if is_sla_breached else 0.0

    # 5. Total Priority Score
    total_score = cat_weight + urg_bonus + aging_score + sla_bonus

    return {
        "complaint_id": cid,
        "floor": floor,
        "category": category,
        "urgency": urgency_label,
        "logged_datetime": row.get("logged_datetime", "").strip(),
        "pending_hours": pending_hours,
        "is_sla_breached": is_sla_breached,
        "cat_weight": cat_weight,
        "urg_bonus": urg_bonus,
        "aging_score": aging_score,
        "sla_bonus": sla_bonus,
        "total_score": round(total_score, 1),
    }


def calculate_avg_resolution_time(all_rows):
    """Calculate average resolution time in hours from Resolved complaints."""
    durations = []
    for r in all_rows:
        if r.get("status", "").strip().lower() == "resolved":
            logged = parse_datetime(r.get("logged_datetime", ""))
            resolved = parse_datetime(r.get("resolved_datetime", ""))
            if logged and resolved and resolved >= logged:
                diff_hours = (resolved - logged).total_seconds() / 3600.0
                durations.append(diff_hours)
    if durations:
        return round(sum(durations) / len(durations), 1), len(durations)
    return None, 0


def generate_floor_checklist(scored_complaints, ref_time, source_filename="data.csv"):
    """
    Generate a floor-by-floor dispatch checklist for visiting technicians.
    Tasks within each floor are sorted descending by priority score.
    """
    # Group complaints by floor
    floors_dict = {}
    for item in scored_complaints:
        fl = str(item.get("floor", "Unknown")).strip()
        floors_dict.setdefault(fl, []).append(item)

    # Sort floors numerically if possible, otherwise alphabetically
    def floor_sort_key(fl_str):
        try:
            return (0, int(fl_str))
        except ValueError:
            return (1, fl_str)

    sorted_floors = sorted(floors_dict.keys(), key=floor_sort_key)

    lines = []
    lines.append("=" * 82)
    lines.append("        HOSTEL MAINTENANCE -- FLOOR-BY-FLOOR TECHNICIAN CHECKLIST        ")
    lines.append("=" * 82)
    lines.append(f"Generated Snapshot : {ref_time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Source Data        : {source_filename}")
    lines.append(f"Total Open Tasks   : {len(scored_complaints)}")
    lines.append("=" * 82)

    for fl in sorted_floors:
        fl_tasks = sorted(
            floors_dict[fl],
            key=lambda x: (x["total_score"], x["pending_hours"]),
            reverse=True
        )
        floor_label = f"FLOOR {fl}" if not fl.lower().startswith("floor") else fl.upper()
        lines.append(f"\n[{floor_label}] - {len(fl_tasks)} Task(s) Pending")
        lines.append("-" * 82)

        for task in fl_tasks:
            rank_str = f"#{task.get('rank', '-')}"
            cid = task["complaint_id"]
            cat = task["category"]
            urg = task["urgency"]
            pending = f"{task['pending_hours']:.1f} hrs"
            score = f"{task['total_score']:.1f}"
            sla_tag = "[SLA BREACHED]" if task["is_sla_breached"] else "[SLA OK]"

            lines.append(
                f"  [ ] {rank_str:<4} | {cid:<4} | {cat:<11} | Urgency: {urg:<6} | {pending:>9} | Score: {score:>5} | {sla_tag}"
            )

    lines.append("\n" + "=" * 82)
    lines.append("                      END OF TECHNICIAN DISPATCH LIST                      ")
    lines.append("=" * 82 + "\n")

    return "\n".join(lines)


def save_checklist(checklist_text: str, filepath: str = CHECKLIST_OUTPUT_FILE):
    """Save the floor checklist to a file for printing or caretaker sharing."""
    out_path = Path(filepath)
    with open(out_path, mode="w", encoding="utf-8") as f:
        f.write(checklist_text)
    return out_path


def load_complaints(filepath: Path):
    """Read CSV, handle malformed entries, and return all rows plus open rows."""
    if not filepath.exists():
        print(f"Error: File '{filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    all_rows = []
    open_rows = []

    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print("Error: CSV file appears to be empty.", file=sys.stderr)
            sys.exit(1)

        for row in reader:
            if not any(row.values()):
                continue  # skip empty lines
            all_rows.append(row)
            status = row.get("status", "").strip().lower()
            if status == "open":
                open_rows.append(row)

    return all_rows, open_rows


def display_results(all_rows, scored_complaints, ref_time, source_filename="data.csv", top_n=None):
    """Print summary stats, priority table, and floor-by-floor technician checklist."""
    total_count = len(all_rows)
    open_count = len(scored_complaints)
    breached_count = sum(1 for c in scored_complaints if c["is_sla_breached"])
    avg_res_time, resolved_count = calculate_avg_resolution_time(all_rows)

    avg_res_str = (
        f"{avg_res_time:.1f} hours ({resolved_count} resolved complaints)"
        if avg_res_time is not None
        else "N/A (no resolved complaints)"
    )

    print("\n" + "=" * 76)
    print("      HOSTEL MAINTENANCE COMPLAINT PRIORITIZER (GH-3, IIITA)      ")
    print("=" * 76)
    print(f"Reference Timestamp : {ref_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Total Complaints    : {total_count}")
    print(f"Open Complaints     : {open_count}")
    print(f"SLA Breached (>48h) : {breached_count} (Urgent Caretaker Attention Needed)")
    print(f"Avg Resolution Time : {avg_res_str}")
    print("=" * 76)

    if not scored_complaints:
        print("\nNo open complaints found. All issues are resolved!")
        return

    # Determine rows to display (all open complaints by default, or top_n if specified)
    display_rows = scored_complaints[:top_n] if top_n is not None else scored_complaints
    heading = (
        f"\n>>> Top {len(display_rows)} Highest-Priority Complaints for Dispatch:\n"
        if top_n is not None
        else f"\n>>> All {len(display_rows)} Unresolved (Open) Complaints Ranked by Priority:\n"
    )
    print(heading)

    headers = ["Rank", "ID", "Floor", "Category", "Urgency", "Pending", "SLA Status", "Score"]
    col_widths = [5, 6, 7, 13, 9, 11, 12, 7]

    header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    separator_line = "-+-".join("-" * w for w in col_widths)

    print(header_line)
    print(separator_line)

    for rank, item in enumerate(display_rows, 1):
        sla_tag = "BREACHED" if item["is_sla_breached"] else "OK"
        pending_str = f"{item['pending_hours']:.1f} hrs"
        row_vals = [
            f"#{rank}",
            item["complaint_id"],
            f"Floor {item['floor']}",
            item["category"],
            item["urgency"],
            pending_str,
            sla_tag,
            f"{item['total_score']:.1f}",
        ]
        row_line = " | ".join(f"{v:<{w}}" for v, w in zip(row_vals, col_widths))
        print(row_line)

    print("-" * len(header_line))
    print(f"Scoring breakdown: Category(15-40) + Urgency(5-15) + (Hours * {PENDING_HOURS_MULTIPLIER}) + SLA Bonus({int(SLA_BREACH_BONUS)})\n")

    # Generate and display Floor-by-Floor Technician Checklist
    checklist_text = generate_floor_checklist(scored_complaints, ref_time, source_filename=source_filename)
    print(checklist_text)

    # Save to file
    saved_file = save_checklist(checklist_text, CHECKLIST_OUTPUT_FILE)
    print(f"[Exported printable technician checklist to: {saved_file.resolve()}]\n")


# ==============================================================================
# MAIN SCRIPT EXECUTION
# ==============================================================================

def main():
    # Allow custom CSV path via command line argument
    if len(sys.argv) > 1 and sys.argv[1] not in ("-h", "--help"):
        csv_path = Path(sys.argv[1])
    elif len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage: python prioritize.py [path_to_complaints.csv]")
        print("Default reads 'data.csv' in the current working directory.")
        sys.exit(0)
    else:
        csv_path = Path("data.csv")

    all_rows, open_rows = load_complaints(csv_path)

    # Find the latest logged timestamp in the dataset
    latest_dt = None
    for r in all_rows:
        parsed = parse_datetime(r.get("logged_datetime", ""))
        if parsed and (latest_dt is None or parsed > latest_dt):
            latest_dt = parsed

    ref_time = get_reference_time(latest_logged_dt=latest_dt)

    # Score all open complaints
    scored = [calculate_priority(r, ref_time) for r in open_rows]

    # Sort descending by priority score (secondary sort by pending hours if tied)
    scored.sort(key=lambda x: (x["total_score"], x["pending_hours"]), reverse=True)

    # Assign overall rank to each open complaint
    for rank, item in enumerate(scored, 1):
        item["rank"] = rank

    # Display results and generate technician checklist
    display_results(all_rows, scored, ref_time, source_filename=csv_path.name)


if __name__ == "__main__":
    main()
