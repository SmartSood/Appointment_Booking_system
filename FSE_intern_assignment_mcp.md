## **🧠 Full-Stack Developer Intern Assignment – Agentic AI with MCP**

### **📌 Overview**

You're tasked with building a **smart doctor appointment and reporting assistant** that uses **MCP (Model Context Protocol)** to expose APIs and tools that can be dynamically discovered and invoked by an AI agent (LLM). Your solution should demonstrate agentic behavior—where the AI can decide what tools to use, when to use them, and how to combine them to fulfill user prompts.

---

### **🎯 Objective**

Build a minimal full-stack web application that integrates LLMs with backend logic using **MCP**, **FastAPI**, **React**, and APIs like **Google Calendar** and **Gmail/Email Service**. The goal is to allow:

1. **Patients can schedule doctor appointments** based on availability.  
2. **Doctors receive smart summary notifications** about their schedules and past visits.

---

### **🧩 Scenario 1: Patient Appointment Scheduling (LLM \+ Agent Flow)**

**Use Case:**  
 A patient types a natural language prompt like:

“I want to book an appointment with Dr. Ahuja tomorrow morning.”

**Expected Behavior:**

* Backend (FastAPI) should expose doctor availability from a **PostgreSQL** database via MCP.  
* AI agent should:

  * Parse the prompt.  
  * Use an MCP tool to **check the doctor’s availability**.  
  * If available, **schedule an appointment via Google Calendar API**.  
  * **Send an email confirmation** to the patient using any email service (Gmail preferred).  
* Display the result (success/failure) to the user via a React frontend.

  ### **🔁 Conversation Continuity (Multi-Prompt Support)**

Your application should support **multi-turn interactions**. For example:

* **Patient Prompt 1**: “I want to check Dr. Ahuja’s availability for Friday afternoon.”  
* *(System replies with available slots.)*  
* **Patient Prompt 2**: “Please book the 3 PM slot.”

The AI agent should be able to **maintain context between prompts** and respond accordingly, without needing the user to restate the entire intent. Use any method (session state, context chaining, etc.) that enables this behavior.  
---

### **🧩 Scenario 2: Doctor Summary Report and Notification**

**Use Case:**  
 At any point, the doctor should be able to get a **summary report**, such as:

“how many patients visited yesterday?”  
“How many appointments do I have today, tomorrow” "  
“How many patient with fever”

**Expected Behavior:**

* LLM should invoke MCP tools to:

  * Query the PostgreSQL database for relevant appointment stats.  
  * Summarize results in a human-readable report.

* Instead of using email (used in Scenario 1), **send this report via a different notification mechanism** (e.g., **Slack**, **WhatsApp**, or **in-app notification system**).

* Allow the doctor to trigger this report using either:

  * A natural language input.  
  * A dashboard button (frontend).

### **🔧 Tech Stack Requirements**

* **Frontend**: React JS (minimal, just enough to support interaction).  
* **Backend**: FastAPI with MCP tool/resource/prompt implementation.  
* **Database**: PostgreSQL for storing doctor schedules and appointments.  
* **LLM**: Can use any open-source or hosted LLM capable of tool-calling (e.g., OpenAI GPT, Claude, or Mistral).  
* **External APIs**:

  * Google Calendar API (for scheduling).  
  * Gmail or any transactional email service (SendGrid, Mailgun).  
  * Notification platform of your choice (Slack, WhatsApp Business API, Firebase, etc.).

---

### **📦 Deliverables**

1. Source code (GitHub repo) with:

   * Clean code and modular structure.  
   * `README.md` with setup steps, sample prompts, and API usage summary.

2. A short demo video (optional but preferred).  
3. Screenshots of:  
   * Prompt-based appointment booking.  
   * Notification to doctor with summarized stats.

---

### **🧠 Bonus (for standout submissions)**

* Implement simple **role-based login** (patient vs. doctor).  
* Add LLM-powered **auto-rescheduling** when the doctor is unavailable.  
* Add **prompt history tracking**.

---

### **⚠️ Evaluation Criteria**

* Understanding of MCP architecture (Client–Server–Tool/Prompt/Resource).  
* LLM-driven workflow orchestration.  
* API integration skill (especially asynchronous logic).  
* Full-stack fluency (React \<–\> FastAPI \<–\> DB/APIs).  
* Code readability, scalability, and agentic design.

