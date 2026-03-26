# DEMO_SCENARIOS.md — Interview Demo Walkthrough

## HOW TO PRESENT THE DEMO

Open the app on localhost. Before typing anything, briefly explain:

"I built this over the past couple of days to show you how I'd approach building AI agents for Qosina. The database is seeded with your actual product catalog — real part numbers, real specs, real connection types from qosina.com. The API responses are formatted as OData JSON to match D365's format. Let me walk you through a few scenarios."

Then run through 3-4 of these scenarios. Don't rush. Let them see the tool calls happening. Pause on the approval queue items.

---

## SCENARIO 1: Customer Product Compatibility Query
**Purpose:** Shows product knowledge, compatibility mapping, inventory awareness

**Type this:**
> "A customer is asking what stopcocks are compatible with the 80147 needleless injection site. Do we have them in stock?"

**What the agent should do:**
1. Call `find_compatible_parts("80147")` → returns compatible stopcocks (11195, 99720, 99722)
2. Call `check_inventory("11195")` → shows stock with lot numbers and expiration
3. Call `check_inventory("99720")` → shows stock
4. Respond with specific part numbers, connection type info ("both use Luer Lock, ISO 80369-7 compliant"), stock levels with lot numbers

**What to point out to DJ and Tom:**
- "The agent cited specific part numbers and lot numbers — that's FDA traceability."
- "It checked compatibility based on connection types, not just guessing."
- "The tool activity feed shows exactly which tools were called and what data came back."
- "Notice the response format in the tool results — that's OData JSON matching D365's API format."

---

## SCENARIO 2: Proactive Inventory Management
**Purpose:** Shows the agent identifying problems and creating human-in-the-loop approvals

**Type this:**
> "Are there any parts running low on stock that we should reorder?"

**What the agent should do:**
1. Call `check_low_stock()` → returns parts below reorder point (91050 at 45/100, 97337 at 75/100, 14054 at 45/100)
2. For each low stock item, call `create_approval()` with type "reorder" and specific reorder recommendation
3. Respond with the findings and note that reorder recommendations have been submitted for review

**What to point out:**
- "Look at the approval queue — three new items just appeared. The agent identified the problem AND created actionable recommendations."
- "But notice what it did NOT do — it didn't place a purchase order. It can't. There's no tool for that. It submitted recommendations for a human to review."
- "That's human-in-the-loop enforced at the architecture level. The agent physically cannot modify your inventory or create a PO."
- Click Approve on one of them. "In production, this approval would trigger a Power Automate flow or a Celery task that creates the PO in D365."

---

## SCENARIO 3: Expiring Inventory Alert
**Purpose:** Shows regulatory awareness (lot tracking, expiration dates are FDA requirements)

**Type this:**
> "Do we have any inventory lots expiring in the next 6 months?"

**What the agent should do:**
1. Call `check_expiring_inventory(180)` → returns lot LOT-2023-0115 for part 11096 expiring July 2026
2. Call `create_approval()` with type "expiry_alert" recommending action (discount, return to vendor, or accelerated sales push)
3. Respond with specific lot numbers, expiration dates, quantities, and the recommendation

**What to point out:**
- "In a regulated medical device environment, expiring inventory isn't just a financial problem — it's a compliance issue. The agent flagged the specific lot number and expiration date."
- "Again, the recommendation went to the approval queue. A warehouse manager or quality team member would review this, not the AI."

---

## SCENARIO 4: Customer Intelligence / Cross-Sell
**Purpose:** Shows cross-system intelligence connecting order history with product compatibility

**Type this:**
> "Can you look at Acme Medical's recent order history and tell me if there are any cross-sell opportunities?"

**What the agent should do:**
1. Call `get_customer_order_history("CUST-001")` → returns monthly stopcock and connector orders, no tubing
2. Call `find_compatible_parts("11195")` → finds that stopcocks connect to tubing, extension lines, etc.
3. Call `create_approval()` with type "customer_outreach" recommending tubing cross-sell
4. Respond noting the pattern: "Acme orders stopcocks and connectors monthly but has never ordered compatible tubing or extension lines"

**What to point out:**
- "This is the kind of cross-system intelligence the JD describes. The agent connected order history data (what would live in D365 F&O) with product compatibility data to identify a business opportunity."
- "The outreach recommendation went to the approval queue — a sales rep would review and decide whether to contact the customer."
- "In production, this could also feed into ClickDimensions for marketing automation in the CRM."

---

## SCENARIO 5: Customer Churn Detection (optional, if time)
**Purpose:** Shows pattern analysis

**Type this:**
> "Are there any customers with declining order patterns we should be worried about?"

**What the agent should do:**
1. Call `get_customer_order_history("CUST-003")` (or it might look at multiple customers)
2. Identify MedLine Innovations' declining pattern: 300 → 150 → 50 → no orders since January
3. Call `create_approval()` with type "customer_outreach" flagging churn risk
4. Respond with the pattern and recommendation

---

## AFTER THE DEMO

Say: "The architecture here is the same as what I run in production at ToteTaxi. LangGraph agent, tool functions separated from orchestration, human-in-the-loop by design. The only thing that changes for Qosina's production environment is the data source — D365 OData endpoints instead of SQLite — and the deployment target — Azure instead of localhost. The agent, the tools, the streaming, and the approval workflow are identical."

Then transition back to conversation. Let them ask questions about the implementation.

---

## ANTICIPATED QUESTIONS ABOUT THE DEMO

**"How would this connect to our actual D365?"**
"Each tool function currently queries SQLite. In production, I'd replace the SQL query with an HTTP request to D365's OData endpoint. The tool function signature stays the same — it still takes a part_number and returns a dict. The agent doesn't know or care where the data comes from. I'd add Azure AD authentication for the API calls and probably cache frequently-accessed data like the product catalog in Redis."

**"How would you handle D365 authentication?"**
"D365 uses Azure AD OAuth2 with client credentials flow for service-to-service calls. You register an app in Azure AD, get a client ID and secret, request a token, and pass it as a Bearer token in the Authorization header. Standard OAuth2 — same pattern I use with other APIs."

**"What about performance? D365 APIs can be slow."**
"Two strategies. First, cache stable data — the product catalog doesn't change every minute. A Redis cache with a 15-minute TTL for product lookups would eliminate most API calls. Second, for slower queries, the SSE streaming means the user sees the agent thinking in real time instead of staring at a blank screen. And the tool activity feed shows them which data source is being queried, so they know what's happening."

**"How would you handle errors from D365?"**
"Same as I handle errors from Stripe and Onfleet in production. Each tool function has try/except around the API call. If D365 returns a 500 or times out, the tool returns an error message that the agent can relay: 'I wasn't able to check inventory right now — the system may be temporarily unavailable. Please try again or check D365 directly.' The agent doesn't crash — it handles the error gracefully."

**"Could this work with Power Platform instead?"**
"For simpler workflows — absolutely. Power Automate can trigger on events and route approvals. But for the AI reasoning part — analyzing order patterns, identifying cross-sell opportunities, understanding natural language product queries — that needs Claude. The two complement each other. Power Automate for the deterministic triggers and routing, Claude for the intelligent analysis."
