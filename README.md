# Hostel Maintenance Complaint Prioritizer (GH-3, IIITA)

A lightweight, fieldwork-driven maintenance operations tool built for **Girls' Hostel-3 (GH-3), IIITA** to replace chronological (FIFO) physical register scanning with an objective priority queue and a floor-by-floor technician dispatch workflow.

---

## 1. Fieldwork Insights & Scoring Logic

On-site observation at the GH-3 caretaker desk highlighted four recurring operational issues:
1. **Register Burial (FIFO Bias):** Older unresolved complaints get buried on earlier pages of the physical register.
2. **Urgency Tag Inflation:** Students often mark minor issues (loose furniture, intermittent WiFi) as *"High"* urgency, delaying critical water/power repairs.
3. **48-Hour SLA Blind Spots:** Complaints open past 48 hours often go unnoticed until students escalate them repeatedly.
4. **Inefficient Technician Routing:** Technicians work floor-by-floor to avoid carrying ladders and tools up and down repeatedly, whereas the physical register lists issues chronologically across mixed floors.

Each `Open` complaint is scored dynamically using transparent weights in `prioritize.py`:

$$\text{Priority Score} = W_{\text{category}} + W_{\text{urgency}} + (0.5 \times \text{Hours Open}) + B_{\text{SLA}}$$

* **Category Base Weight:** `Electrical`: **40**, `Plumbing`: **40**, `WiFi`: **20**, `Furniture`: **15**
* **Urgency Bonus:** `High`: **15**, `Medium`: **10**, `Low`: **5**, `Blank/Missing`: **5**
* **Aging Multiplier:** **+0.5 points** per hour open
* **SLA Breach Bonus:** **+25.0 points** once pending $\ge 48$ hours

---

## 2. How to Run It

### Prerequisites
* Python 3.9+

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Option A: Run the CLI Prioritizer & Generate Technician Checklist
```bash
python prioritize.py
```
*(Reads `data.csv` by default, prints the ranked priority table + floor-by-floor checklist, and exports `technician_checklist.txt`. You can also pass a custom CSV file: `python prioritize.py path/to/file.csv`.)*

### Option B: Run the Caretaker & Warden Web Dashboard
```bash
streamlit run app.py
```
*(Opens a browser dashboard to log new complaints with room numbers straight into `data.csv`, mark tasks resolved, manually purge resolved records older than 7 days, and download/WhatsApp floor- and trade-divided work orders.)*

---

## 3. Real Output (Sample Run on `data.csv`)

Running `python prioritize.py` on `data.csv` (`27` total complaints: `15 Open`, `12 Resolved`) produces:

```text
====================================================================================
         HOSTEL MAINTENANCE COMPLAINT PRIORITIZER (GH-3, IIITA)         
====================================================================================
Reference Timestamp : 2026-11-21 22:50
Total Complaints    : 27
Open Complaints     : 15
SLA Breached (>48h) : 8 (Urgent Caretaker Attention Needed)
Avg Resolution Time : 54.9 hours (12 resolved complaints)
====================================================================================

>>> All 15 Unresolved (Open) Complaints Ranked by Priority:

Rank  | ID     | Floor   | Room   | Category      | Urgency   | Pending     | SLA Status   | Score  
------+--------+---------+--------+---------------+-----------+-------------+--------------+--------
#1    | C43    | Floor 2 | 215    | Electrical    | Low       | 133.3 hrs   | BREACHED     | 136.7  
#2    | C47    | Floor 0 | 009    | Electrical    | High      | 87.2 hrs    | BREACHED     | 123.6  
#3    | C48    | Floor 1 | 117    | Plumbing      | High      | 82.6 hrs    | BREACHED     | 121.3  
#4    | C46    | Floor 3 | 319    | Plumbing      | Low       | 100.8 hrs   | BREACHED     | 120.4  
#5    | C52    | Floor 2 | 211    | Plumbing      | Medium    | 53.3 hrs    | BREACHED     | 101.7  
#6    | C51    | Floor 0 | 016    | Electrical    | None      | 56.0 hrs    | BREACHED     | 98.0   
#7    | C49    | Floor 2 | 204    | WiFi          | High      | 72.7 hrs    | BREACHED     | 96.3   
#8    | C50    | Floor 3 | 302    | Furniture     | Low       | 61.8 hrs    | BREACHED     | 75.9   
#9    | C55    | Floor 2 | 219    | Electrical    | High      | 27.4 hrs    | OK           | 68.7   
#10   | C56    | Floor 0 | 002    | Plumbing      | High      | 15.3 hrs    | OK           | 62.6   
#11   | C53    | Floor 3 | 310    | WiFi          | High      | 38.6 hrs    | OK           | 54.3   
#12   | C59    | Floor 3 | 317    | Electrical    | Low       | 7.1 hrs     | OK           | 48.5   
#13   | C54    | Floor 1 | 108    | Furniture     | Medium    | 35.2 hrs    | OK           | 42.6   
#14   | C57    | Floor 1 | 115    | WiFi          | Medium    | 12.7 hrs    | OK           | 36.3   
#15   | C58    | Floor 2 | 206    | Furniture     | High      | 9.5 hrs     | OK           | 34.8   
----------------------------------------------------------------------------------------------------
Scoring breakdown: Category(15-40) + Urgency(5-15) + (Hours * 0.5) + SLA Bonus(25)

==============================================================================================
           HOSTEL MAINTENANCE -- FLOOR-BY-FLOOR TECHNICIAN CHECKLIST           
==============================================================================================
Generated Snapshot : 2026-11-21 22:50
Source Data        : data.csv
Total Open Tasks   : 15
==============================================================================================

[FLOOR 0] - 3 Task(s) Pending
----------------------------------------------------------------------------------------------
  [ ] #2   | C47  | Room 009  | Electrical  | Urgency: High   |  87.2 hrs | Score: 123.6 | [SLA BREACHED]
  [ ] #6   | C51  | Room 016  | Electrical  | Urgency: None   |  56.0 hrs | Score:  98.0 | [SLA BREACHED]
  [ ] #10  | C56  | Room 002  | Plumbing    | Urgency: High   |  15.3 hrs | Score:  62.6 | [SLA OK]

[FLOOR 1] - 3 Task(s) Pending
----------------------------------------------------------------------------------------------
  [ ] #3   | C48  | Room 117  | Plumbing    | Urgency: High   |  82.6 hrs | Score: 121.3 | [SLA BREACHED]
  [ ] #13  | C54  | Room 108  | Furniture   | Urgency: Medium |  35.2 hrs | Score:  42.6 | [SLA OK]
  [ ] #14  | C57  | Room 115  | WiFi        | Urgency: Medium |  12.7 hrs | Score:  36.3 | [SLA OK]

[FLOOR 2] - 5 Task(s) Pending
----------------------------------------------------------------------------------------------
  [ ] #1   | C43  | Room 215  | Electrical  | Urgency: Low    | 133.3 hrs | Score: 136.7 | [SLA BREACHED]
  [ ] #5   | C52  | Room 211  | Plumbing    | Urgency: Medium |  53.3 hrs | Score: 101.7 | [SLA BREACHED]
  [ ] #7   | C49  | Room 204  | WiFi        | Urgency: High   |  72.7 hrs | Score:  96.3 | [SLA BREACHED]
  [ ] #9   | C55  | Room 219  | Electrical  | Urgency: High   |  27.4 hrs | Score:  68.7 | [SLA OK]
  [ ] #15  | C58  | Room 206  | Furniture   | Urgency: High   |   9.5 hrs | Score:  34.8 | [SLA OK]

[FLOOR 3] - 4 Task(s) Pending
----------------------------------------------------------------------------------------------
  [ ] #4   | C46  | Room 319  | Plumbing    | Urgency: Low    | 100.8 hrs | Score: 120.4 | [SLA BREACHED]
  [ ] #8   | C50  | Room 302  | Furniture   | Urgency: Low    |  61.8 hrs | Score:  75.9 | [SLA BREACHED]
  [ ] #11  | C53  | Room 310  | WiFi        | Urgency: High   |  38.6 hrs | Score:  54.3 | [SLA OK]
  [ ] #12  | C59  | Room 317  | Electrical  | Urgency: Low    |   7.1 hrs | Score:  48.5 | [SLA OK]

==============================================================================================
                         END OF TECHNICIAN DISPATCH LIST                         
==============================================================================================

[Exported printable technician checklist to: technician_checklist.txt]
```

---

## 4. What It Gets Wrong (Limitations & Edge Cases)

1. **No Severity Granularity Within a Category:**
   * A broken study chair (`Furniture`) and a broken room door lock (`Furniture`) receive the exact same base weight (`15`). Similarly, a minor tap drip (`Plumbing`) and a burst pipe flooding a corridor (`Plumbing`) both receive a `40` base weight because the CSV schema tracks `category` without a sub-issue description.
2. **Aging Can Outrank Acute Fresh Emergencies:**
   * Because pending hours add `0.5 pts/hr` plus a `+25` SLA bonus after 48 hours, a 5.5-day-old `Low`-urgency electrical issue (`C43`, `133.3 hrs` $\rightarrow$ score `136.7`) ranks `#1`, ahead of a newer `High`-urgency electrical hazard (`C55`, `27.4 hrs` $\rightarrow$ score `68.7`), even if the newer issue poses an immediate safety risk.
3. **No Shared vs. Individual Impact Distinction:**
   * A WiFi access point outage affecting an entire corridor or a common washroom leak is weighted identically to a single-room issue because `room_no` records a single room number rather than tracking the number of affected residents.


---

## 5. Repository Files

* `app.py` — Streamlit web application for the warden/caretaker desk
* `prioritize.py` — Standalone CLI prioritizer and checklist exporter
* `data.csv` — Sanitized 27-complaint dataset (`C31`–`C59`, no student PII)
* `technician_checklist.txt` — Generated printable floor-by-floor dispatch list
* `fieldwork.md` — On-site observation notes and design rationale
* `requirements.txt` — Python dependencies (`streamlit`, `pandas`)

## Demo Video
[Watch the Project Walkthrough Demo]https://drive.google.com/file/d/12bDMXCdzL_Sd-f2Fos6S3EW1UaAmfzXY/view?usp=sharing
