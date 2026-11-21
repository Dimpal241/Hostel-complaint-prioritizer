#!/usr/bin/env python3

import csv
import urllib.parse
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Import scoring logic, weights, and helpers directly from prioritize.py
import prioritize

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CSV_FILEPATH = Path("data.csv")
RETENTION_DAYS = 7  # Days to keep Resolved complaints before auto-cleaning
FIELDNAMES = [
    "complaint_id",
    "floor",
    "room_no",
    "category",
    "urgency",
    "logged_datetime",
    "resolved_datetime",
    "status",
]


# ==============================================================================
# DATA ACCESS & CLEANUP FUNCTIONS
# ==============================================================================

def load_data(filepath: Path = CSV_FILEPATH):
    """Load all rows from CSV, creating the file with headers if it doesn't exist."""
    if not filepath.exists():
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        return []

    rows = []
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if any(r.values()):
                rows.append(r)
    return rows


def save_data(rows, filepath: Path = CSV_FILEPATH):
    """Save all complaint rows to CSV."""
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in rows:
            clean_row = {fn: r.get(fn, "") for fn in FIELDNAMES}
            writer.writerow(clean_row)


def cleanup_old_resolved(rows, ref_time: datetime, retention_days: int = RETENTION_DAYS):
    """
    Remove Resolved rows older than retention_days.
    Returns (cleaned_rows, removed_count).
    """
    kept_rows = []
    removed_count = 0
    cutoff_seconds = retention_days * 86400.0

    for r in rows:
        if r.get("status", "").strip().lower() == "resolved":
            res_dt = (
                prioritize.parse_datetime(r.get("resolved_datetime", ""))
                or prioritize.parse_datetime(r.get("logged_datetime", ""))
            )
            if res_dt:
                age_seconds = (ref_time - res_dt).total_seconds()
                if age_seconds > cutoff_seconds:
                    removed_count += 1
                    continue
        kept_rows.append(r)

    return kept_rows, removed_count


def generate_floor_word_doc(floor_id: str, tasks: list, ref_time: datetime) -> str:
    """
    Generate a clean Word document (.doc) tailored strictly for technicians.
    Contains only actionable information: Checkbox, ID, Room, Category, Urgency, Logged Date/Time, and Notes space.
    Excludes all internal algorithm formulas, weights, and priority scores.
    """
    rows_html = []
    for t in tasks:
        cid = t.get("complaint_id", "")
        room = t.get("room_no", "") or "N/A"
        cat = t.get("category", "")
        urg = t.get("urgency", "Normal") or "Normal"
        logged = t.get("logged_datetime", "")
        is_breached = t.get("is_sla_breached", False)

        urg_style = "color: #b71c1c; font-weight: bold;" if is_breached or urg.lower() == "high" else "color: #222;"
        urg_text = "OVERDUE (>48h)" if is_breached else urg

        rows_html.append(f"""
        <tr>
          <td style="text-align: center; font-size: 15pt; border: 1px solid #bbb; padding: 10px;">[ &nbsp; ]</td>
          <td style="border: 1px solid #bbb; padding: 10px; font-weight: bold; font-size: 12pt;">{cid}</td>
          <td style="border: 1px solid #bbb; padding: 10px; font-weight: bold;">{room}</td>
          <td style="border: 1px solid #bbb; padding: 10px;">{cat}</td>
          <td style="border: 1px solid #bbb; padding: 10px; {urg_style}">{urg_text}</td>
          <td style="border: 1px solid #bbb; padding: 10px; color: #555;">{logged}</td>
          <td style="border: 1px solid #bbb; padding: 10px; width: 200px;"></td>
        </tr>""")

    table_rows_str = "\n".join(rows_html)
    date_str = ref_time.strftime("%d %b %Y, %I:%M %p")

    return f"""<!DOCTYPE html>
<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head>
<meta charset="utf-8">
<title>Work Order - Floor {floor_id}</title>
<style>
  body {{
    font-family: Calibri, Arial, sans-serif;
    margin: 28px;
    color: #111;
  }}
  .header-box {{
    border-bottom: 2px solid #0d47a1;
    padding-bottom: 8px;
    margin-bottom: 14px;
  }}
  h2 {{
    color: #0d47a1;
    margin: 0 0 6px 0;
    font-size: 18pt;
  }}
  .meta-info {{
    font-size: 10.5pt;
    color: #444;
    margin-bottom: 12px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 10.5pt;
  }}
  th {{
    background-color: #f1f5f9;
    color: #0d47a1;
    border: 1px solid #bbb;
    padding: 10px;
    text-align: left;
    font-weight: bold;
  }}
  .sig-table {{
    width: 100%;
    border: none;
    margin-top: 45px;
    font-size: 11pt;
  }}
  .sig-table td {{
    border: none;
    padding: 20px 0;
  }}
</style>
</head>
<body>
  <div class="header-box">
    <h2>HOSTEL MAINTENANCE WORK ORDER -- FLOOR {floor_id}</h2>
    <div class="meta-info">
      <strong>Hostel:</strong> Girls' Hostel-3 (GH-3), IIITA &nbsp;&nbsp;|&nbsp;&nbsp;
      <strong>Date:</strong> {date_str} &nbsp;&nbsp;|&nbsp;&nbsp;
      <strong>Total Tasks on Floor:</strong> {len(tasks)}
    </div>
  </div>

  <p><em>Please complete repairs on this floor and mark tick [✓] in the Done box once resolved.</em></p>

  <table>
    <thead>
      <tr>
        <th style="width: 55px; text-align: center;">Done</th>
        <th style="width: 70px;">ID</th>
        <th style="width: 85px;">Room</th>
        <th style="width: 120px;">Category</th>
        <th style="width: 130px;">Urgency</th>
        <th style="width: 150px;">Logged Time</th>
        <th>Technician Notes</th>
      </tr>
    </thead>
    <tbody>
      {table_rows_str}
    </tbody>
  </table>

  <table class="sig-table">
    <tr>
      <td style="width: 50%;"><strong>Technician Signature:</strong> _______________________</td>
      <td style="width: 50%;"><strong>Caretaker Signature:</strong> _______________________</td>
    </tr>
  </table>
</body>
</html>"""


def generate_floor_whatsapp_text(floor_id: str, tasks: list) -> str:
    """Generate concise, clean WhatsApp message for a technician for a specific floor."""
    lines = [
        f"*GH-3 HOSTEL MAINTENANCE -- FLOOR {floor_id}*",
        f"Tasks to attend ({len(tasks)}):",
        "------------------------------------",
    ]
    for t in tasks:
        cid = t.get("complaint_id", "")
        room = t.get("room_no", "") or "N/A"
        cat = t.get("category", "")
        urg = t.get("urgency", "") or "Normal"
        is_breached = t.get("is_sla_breached", False)
        status_tag = "⚠️ OVERDUE" if is_breached else urg
        lines.append(f"[ ] *{cid}* | Room *{room}* | {cat} ({status_tag})")
    lines.append("------------------------------------")
    lines.append("Please complete all tasks on this floor before moving.")
    return "\n".join(lines)


def get_next_complaint_id(rows) -> str:
    """Generate next sequential complaint ID (e.g. C60)."""
    max_num = 0
    for r in rows:
        cid = r.get("complaint_id", "").strip().upper()
        if cid.startswith("C") and cid[1:].isdigit():
            max_num = max(max_num, int(cid[1:]))
    return f"C{max_num + 1}"


def mark_complaint_resolved(cid: str, filepath: Path = CSV_FILEPATH):
    """Mark a specific complaint as Resolved with current timestamp."""
    rows = load_data(filepath)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    updated = False

    for r in rows:
        if r.get("complaint_id", "").strip().upper() == cid.strip().upper():
            r["status"] = "Resolved"
            r["resolved_datetime"] = now_str
            updated = True
            break

    if updated:
        ref_time = prioritize.get_reference_time()
        cleaned_rows, _ = cleanup_old_resolved(rows, ref_time, RETENTION_DAYS)
        save_data(cleaned_rows, filepath)

    return updated


def append_complaint(floor: str, room_no: str, category: str, urgency: str, filepath: Path = CSV_FILEPATH) -> str:
    """Create and append a new open complaint to the CSV."""
    rows = load_data(filepath)
    next_id = get_next_complaint_id(rows)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_row = {
        "complaint_id": next_id,
        "floor": str(floor).strip(),
        "room_no": str(room_no).strip() if str(room_no).strip() else "N/A",
        "category": str(category).strip(),
        "urgency": "" if urgency.lower().startswith("blank") else str(urgency).strip(),
        "logged_datetime": now_str,
        "resolved_datetime": "",
        "status": "Open",
    }
    rows.append(new_row)

    ref_time = prioritize.get_reference_time()
    cleaned_rows, _ = cleanup_old_resolved(rows, ref_time, RETENTION_DAYS)
    save_data(cleaned_rows, filepath)

    return next_id


# ==============================================================================
# STREAMLIT UI SETUP
# ==============================================================================

st.set_page_config(
    page_title="Hostel Complaint Prioritizer",
    page_icon="🏢",
    layout="wide",
)

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #1976d2;
    }
    .breach-alert {
        color: #d32f2f;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.title("🏢 Girls' Hostel-3 (GH-3) Maintenance Desk")
st.caption("Caretaker Operational Tool — Real-time Priority Queue & Floor Dispatch")

# Load and auto-cleanup data on initial load
all_rows = load_data(CSV_FILEPATH)

# Determine reference timestamp
latest_dt = None
for r in all_rows:
    p_dt = prioritize.parse_datetime(r.get("logged_datetime", ""))
    if p_dt and (latest_dt is None or p_dt > latest_dt):
        latest_dt = p_dt
ref_time = prioritize.get_reference_time(latest_logged_dt=latest_dt)

# Run auto-cleanup for resolved complaints older than RETENTION_DAYS
cleaned_rows, auto_removed = cleanup_old_resolved(all_rows, ref_time, RETENTION_DAYS)
if auto_removed > 0:
    save_data(cleaned_rows, CSV_FILEPATH)
    all_rows = cleaned_rows
    st.toast(f"🧹 Auto-cleaned {auto_removed} resolved complaint(s) older than {RETENTION_DAYS} days.", icon="ℹ️")

# Filter open complaints and compute priority scores
open_rows = [r for r in all_rows if r.get("status", "").strip().lower() == "open"]
scored_open = []
for r in open_rows:
    item = prioritize.calculate_priority(r, ref_time)
    item["room_no"] = (r.get("room_no") or "").strip() or "N/A"
    scored_open.append(item)

scored_open.sort(key=lambda x: (x["total_score"], x["pending_hours"]), reverse=True)

# Assign overall rank
for rank, item in enumerate(scored_open, 1):
    item["rank"] = rank

sla_breached_count = sum(1 for c in scored_open if c["is_sla_breached"])


# ==============================================================================
# 1. TOP SUMMARY (Only 2 numbers: Total Open & SLA Breached)
# ==============================================================================

col1, col2 = st.columns(2)
with col1:
    st.metric(
        label="Total Open Complaints",
        value=len(scored_open),
        help="All active maintenance tickets requiring technician dispatch.",
    )

with col2:
    st.metric(
        label="SLA Breached (>48 hrs)",
        value=sla_breached_count,
        delta=f"{sla_breached_count} Overdue" if sla_breached_count > 0 else "All within SLA",
        delta_color="inverse" if sla_breached_count > 0 else "normal",
        help="Complaints pending for more than 48 hours without resolution.",
    )

st.divider()


# ==============================================================================
# SIDEBAR: LOG NEW COMPLAINT & DATABASE CLEANUP
# ==============================================================================

with st.sidebar:
    st.header("📝 Log New Complaint")
    next_id_preview = get_next_complaint_id(all_rows)
    st.caption(f"Next Complaint ID: **{next_id_preview}**")

    with st.form("new_complaint_form", clear_on_submit=True):
        new_floor = st.selectbox("Floor", options=["0", "1", "2", "3"], index=0)
        new_room = st.text_input(
            "Room Number",
            placeholder="e.g., 005, 104, 212",
            help="Enter the room number on the selected floor.",
        )
        new_category = st.selectbox(
            "Category",
            options=["Electrical", "Plumbing", "WiFi", "Furniture"],
            index=0,
            help="Electrical and Plumbing are given higher base weights due to safety and water necessity.",
        )
        new_urgency = st.selectbox(
            "Urgency Tag",
            options=["High", "Medium", "Low", "Blank (None)"],
            index=1,
            help="Select 'Blank (None)' if the resident did not write an urgency in the register.",
        )

        submitted = st.form_submit_button("Submit Complaint", type="primary", use_container_width=True)
        if submitted:
            if not new_room.strip():
                st.warning("Please enter a Room Number before submitting.")
            else:
                created_id = append_complaint(new_floor, new_room, new_category, new_urgency, CSV_FILEPATH)
                st.success(f"Complaint **{created_id}** (Room {new_room.strip()}) logged successfully!")
                st.rerun()

    st.markdown("---")
    st.header("🧹 Database Maintenance")
    st.caption(f"Resolved complaints older than **{RETENTION_DAYS} days** are purged automatically on load/update.")

    if st.button("Clean Up Old Resolved Rows Now", use_container_width=True):
        cleaned_now, removed_now = cleanup_old_resolved(all_rows, ref_time, RETENTION_DAYS)
        save_data(cleaned_now, CSV_FILEPATH)
        if removed_now > 0:
            st.success(f"Removed {removed_now} resolved record(s) older than {RETENTION_DAYS} days.")
        else:
            st.info("Database is already clean! No resolved rows older than 7 days.")
        st.rerun()


# ==============================================================================
# MAIN TABS
# ==============================================================================

tab1, tab2 = st.tabs(["📋 Prioritized Tasks", "🛠️ Technician Floor Checklist & Send"])

# ------------------------------------------------------------------------------
# TAB 1: PRIORITIZED TASKS
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("All Open Complaints Ranked by Caretaker Priority")
    st.caption("Active complaints sorted in order of priority (overdue and critical utility issues ranked highest).")

    if not scored_open:
        st.success("🎉 All complaints are resolved! No pending tasks.")
    else:
        # Quick resolve action bar
        with st.container():
            res_col1, res_col2 = st.columns([3, 1])
            with res_col1:
                resolve_options = [
                    f"{c['complaint_id']} — Floor {c['floor']} (Room {c['room_no']}) | {c['category']} | Urgency: {c['urgency']} | {c['pending_hours']:.1f}h open"
                    for c in scored_open
                ]
                selected_resolve_str = st.selectbox(
                    "Select a complaint to mark as Resolved:",
                    options=resolve_options,
                    index=0,
                    label_visibility="collapsed",
                )
            with res_col2:
                if st.button("Mark as Resolved ✅", type="primary", use_container_width=True):
                    cid_to_mark = selected_resolve_str.split(" ")[0]
                    mark_complaint_resolved(cid_to_mark, CSV_FILEPATH)
                    st.success(f"Complaint {cid_to_mark} marked as Resolved!")
                    st.rerun()

        # Build clean display table
        table_data = []
        for c in scored_open:
            sla_display = "🚨 BREACHED (>48h)" if c["is_sla_breached"] else "✅ OK"
            table_data.append(
                {
                    "Rank": f"#{c['rank']}",
                    "ID": c["complaint_id"],
                    "Floor": f"Floor {c['floor']}",
                    "Room": c["room_no"],
                    "Category": c["category"],
                    "Urgency": c["urgency"],
                    "Logged Timestamp": c["logged_datetime"],
                    "Pending Time": f"{c['pending_hours']:.1f} hrs",
                    "SLA Status": sla_display,
                    "Priority Score": c["total_score"],
                }
            )

        df = pd.DataFrame(table_data)

        def highlight_breaches(row):
            if "BREACHED" in str(row["SLA Status"]):
                return ["background-color: #fff3f3; color: #b71c1c; font-weight: 600;"] * len(row)
            return [""] * len(row)

        styled_df = df.style.apply(highlight_breaches, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)


# ------------------------------------------------------------------------------
# TAB 2: TECHNICIAN FLOOR CHECKLIST & SEND
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Technician Work Orders (Floor-by-Floor)")
    st.caption("Organized floor-by-floor so technicians complete all tasks on one level before moving ladders and tools.")

    if not scored_open:
        st.info("No open complaints. Nothing to dispatch!")
    else:
        floors_dict = {}
        for c in scored_open:
            fl = str(c.get("floor", "N/A"))
            floors_dict.setdefault(fl, []).append(c)

        def floor_num_key(f_str):
            try:
                return (0, int(f_str))
            except ValueError:
                return (1, f_str)

        sorted_floor_keys = sorted(floors_dict.keys(), key=floor_num_key)

        # Master combined download option
        all_floors_doc = generate_floor_word_doc("ALL FLOORS", scored_open, ref_time)
        master_col1, master_col2 = st.columns([1, 1])
        with master_col1:
            st.download_button(
                label="📄 Download All Floors Combined Work Order (.doc)",
                data=all_floors_doc,
                file_name="technician_all_floors_work_order.doc",
                mime="application/msword",
                use_container_width=True,
            )
        with master_col2:
            all_wa_lines = ["*GH-3 HOSTEL MAINTENANCE -- ALL FLOORS SUMMARY*", ""]
            for fl_k in sorted_floor_keys:
                all_wa_lines.append(generate_floor_whatsapp_text(fl_k, floors_dict[fl_k]))
                all_wa_lines.append("")
            all_wa_text = "\n".join(all_wa_lines).strip()
            st.link_button(
                label="📲 WhatsApp All Floors Summary",
                url=f"https://wa.me/?text={urllib.parse.quote(all_wa_text)}",
                use_container_width=True,
            )

        st.markdown("---")

        # Per-Floor Sections with Separate Download & Send Buttons
        for fl in sorted_floor_keys:
            tasks = sorted(floors_dict[fl], key=lambda x: (x["total_score"], x["pending_hours"]), reverse=True)
            floor_label = f"Floor {fl}"

            with st.container(border=True):
                head_col, dl_col, wa_col = st.columns([2, 1.5, 1.5])
                with head_col:
                    st.markdown(f"### 🏢 {floor_label} &nbsp; `({len(tasks)} Pending Tasks)`")

                floor_doc = generate_floor_word_doc(fl, tasks, ref_time)
                with dl_col:
                    st.download_button(
                        label=f"📥 Download {floor_label} Work Order (.doc)",
                        data=floor_doc,
                        file_name=f"technician_floor_{fl}_work_order.doc",
                        mime="application/msword",
                        key=f"dl_floor_{fl}",
                        use_container_width=True,
                    )

                with wa_col:
                    floor_wa_text = generate_floor_whatsapp_text(fl, tasks)
                    floor_wa_url = f"https://wa.me/?text={urllib.parse.quote(floor_wa_text)}"
                    st.link_button(
                        label=f"📲 WhatsApp {floor_label}",
                        url=floor_wa_url,
                        key=f"wa_floor_{fl}",
                        use_container_width=True,
                    )

                # Show clean task list without internal algorithm math
                for t in tasks:
                    cid = t["complaint_id"]
                    room = t["room_no"]
                    cat = t["category"]
                    urg = t["urgency"] or "Normal"
                    logged = t["logged_datetime"]
                    sla_tag = "🚨 OVERDUE (>48h)" if t["is_sla_breached"] else "✅ OK"
                    st.markdown(
                        f"- `[ ]` **{cid}** | Room **{room}** — **{cat}** &nbsp;|&nbsp; Urgency: `{urg}` &nbsp;|&nbsp; "
                        f"Logged: `{logged}` &nbsp;|&nbsp; `{sla_tag}`"
                    )