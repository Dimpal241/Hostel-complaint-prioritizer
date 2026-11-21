# Project Reflection

### What I Got Wrong at the Start
At the start, I thought the problem was just digitizing the GH-3 register and sorting complaints by the "Urgency" tag students wrote down. After talking to the caretaker and watching how maintenance actually works, I realized two things: students mark almost every minor issue as "High" urgency. I initially thought of solving the problem by letting the warden decide the urgency but taking into account human error and absence of the warden I later changed my approach from relying solely on an urgency filter to assigning category based weighted priority of tasks.

Secondly, technicians do not follow a global priority list across floors. They inspect one floor at a time and work by trade (electrician, plumber, carpenter), so a single mixed ranking was not practical for field dispatch. 

### What I Would Cut
If I started over, I would avoid maintaining two separate interfaces (`prioritize.py` and `app.py`). A single lightweight web dashboard with a manual archive button is enough for the caretaker desk without duplicating display logic.

### Where AI Helped
AI was genuinely useful for fast UI scaffolding in Streamlit, generating the HTML structure for printable `.doc` work orders, formatting pre-filled WhatsApp share links, and writing clean edge-case checks for blank urgency tags or missing timestamps. It helped with writing the code for all the desired features addressing the problem statement.

### Where AI Wasted Time
AI wasted time by over-complicating things early on—for example, by suggesting to address problems according to floor number instead of `Room no.` considering it as confidential information that warden is already aware of which I later realized while adding technician list feature was a mistake as Room No. is a necessary requirement for the technician.
It also wasted time by adding silent auto-cleanup on startup, which unexpectedly deleted 5 rows from `data.csv` during testing.
Fixing those assumptions and re-verifying full-file rewrites took longer than writing simple logic directly.