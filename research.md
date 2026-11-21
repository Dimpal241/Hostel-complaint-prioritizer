# Hostel Maintenance Complaint Prioritizer — Research & Problem Breakdown

## 1. The Person & Problem
- **User:** The hostel caretaker and warden in our girls' hostel who manage daily room maintenance complaints.
- **Context:** Over 500 resident students log electrical, plumbing, Wi-Fi, and furniture issues in a physical paper register.
- **Problem:** Because entries are written chronologically by date, urgent issues (like broken geysers, faulty door locks, or short circuits) get buried under minor requests.
- **Operational Bottleneck:** Even when urgency is noted, the caretaker has no quick way to track elapsed hours against repair SLAs or group pending tasks by floor.
- **Impact:** Critical repairs get delayed past acceptable limits, and visiting technicians waste time shuttling back and forth across floors.

---

## 2. Existing Solutions & Why They Don't Fit

### Solution 1: Gated Society Apps (e.g., MyGate, NoBrokerHood)
- **What they offer:** Comprehensive resident apps with built-in complaint ticketing, approval workflows, and status tracking.
- **Why they don't fit here:**
  - **Budget mismatch:** A college hostel will not pay high recurring subscription fees for full society ERP software just to log maintenance.
  - **Worker reality:** Our hostel relies on local daily-wage plumbers and electricians who come in for a few hours. They don't use smartphones or ticketing apps while working on-site.
  - **Feature bloat:** Most of their features (visitor gating, parcel tracking, society dues) are unnecessary overhead for a warden who just needs a clear daily repair list.

### Solution 2: Google Forms + Trello / Spreadsheets
- **What they offer:** Free digital submission forms that populate a Google Sheet or Kanban board cards.
- **Why they don't fit here:**
  - **Manual SLA tracking:** Spreadsheets and Trello boards are passive storage. They don't actively calculate how many hours have passed since submission or alert the caretaker when an SLA is breached.
  - **No automated floor grouping:** The caretaker still has to manually sort and cluster complaints so a technician can fix all Floor 2 issues before moving to Floor 3.
  - **High maintenance effort:** Trello requires regular manual dragging of cards across lists. In a busy hostel office, this manual upkeep quickly breaks down, sending staff back to paper.

---

## 3. Real Sources for Problem Framing & Logic

### Source 1: The Eisenhower Matrix: How to Prioritize Your To-Do List (Asana)
- **Link:** https://asana.com/resources/eisenhower-matrix
- **Notes:**
  1. Breaks down the urgent-important framework to distinguish genuine crises from noisy, low-impact tasks.
  2. Helps structure our scoring logic so safety and basic living hazards (water, electricity, locks) jump ahead of minor aesthetic or furniture fixes.
  3. Provides a clean model for deciding what needs immediate dispatch versus what can wait for scheduled batch repairs.

### Source 2: What is an SLA? Best Practices for Service Level Agreements (Atlassian)
- **Link:** https://www.atlassian.com/itsm/service-request-management/sla
- **Notes:**
  1. Explains how resolution targets and response clocks work in real-world service and incident management.
  2. Shows why assigning different SLA cutoffs by issue severity (e.g., 6 hours for geyser issues vs. 48 hours for table repairs) prevents service degradation.
  3. Demonstrates how tracking elapsed time against target windows allows a system to highlight at-risk and breached tickets automatically.
