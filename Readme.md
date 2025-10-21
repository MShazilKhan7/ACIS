# 🤖 AI Curriculum Intelligence System - Demo Link: https://youtu.be/hFsC48gCLsU?si=fFkLngwFOAAs5AZ6

**AI Curriculum Intelligence System** is a Python-based project designed to provide educational analytics, including feedback analysis, performance tracking, trend identification, recommendation generation, and report management.

The project leverages **Streamlit** for an interactive user interface and multiple **MCP (Multi-Channel Processing)** agent servers for backend processing.

---

## 🛠️ Project Setup

### 1. Clone the Repository

```bash
git clone <repository_url>
cd <repository_folder>
```

### 2. Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

### 1. Run the Main Streamlit App

```bash
streamlit run app.py
```

### 2. Run MCP Agent Servers

Each MCP agent server should be run in a **separate terminal**:

```bash
python src_code\agents\feedback_mcp_server.py
python src_code\agents\performance_mcp_server.py
python src_code\agents\recommender_mcp_server.py
python src_code\agents\report_mcp_server.py
python src_code\agents\trend_mcp_server.py
```

> ⚠️ **Note:** Make sure all required MCP servers are running before using the Streamlit app to avoid connectivity errors.

---

## 📁 Project Structure

```
AI-Curriculum-Intelligence-System/
│
├─ deployment/app.py                # Main Streamlit app
├─ requirements.txt                 # Project dependencies
├─ README.md                        # Project documentation
├─ src_code/
│   └─ agents/
│       ├─ feedback_mcp_server.py
│       ├─ performance_mcp_server.py
│       ├─ recommender_mcp_server.py
│       ├─ report_mcp_server.py
│       └─ trend_mcp_server.py
```

---

## ⚡ Features

* **Feedback Analysis:** Analyze course feedback and sentiment.
* **Performance Tracking:** Monitor students’ performance metrics.
* **Trend Analysis:** Identify course trends and engagement patterns.
* **Recommendations:** Generate curriculum improvement insights.
* **Report Generation:** Compile and export analytical reports.
* **Interactive Dashboard:** Streamlit-based user interface for visualization.

---

## 📌 Notes

* Keep the virtual environment activated while running the project.
* Install any additional Python packages if required.
* Ensure all MCP agent servers are running before interacting with the main app.

---

✨ *Developed with Python & Streamlit for smarter education analytics.*
