# 💸 Your Personal Finance Manager 🤖💬

Ever dreamed of having your **own personal accountant** to manage your finances like a pro? This app makes it possible through a smart **Agentic AI solution** built around a **collaborative chat** with specialized agents. 🚀

---
![banner](https://azfunctionsstorage2025.blob.core.windows.net/files-upload-by-users/banner.png)

## 🧩 The Problem: Why is managing money so hard?

Personal finance is **crucial for a good life**. Here's why it matters:

✅ Provides **economic security** to handle emergencies without debt  
✅ Offers **freedom** to make big life decisions independently  
✅ Reduces **financial stress**, boosting mental health  
✅ Helps achieve **concrete goals** like studying, traveling, or buying a home  
✅ Ensures a **dignified and stable retirement**

But the reality is:
- People use everything from notebooks to complex apps—often without guidance  
- Consistent **manual data entry** is tedious and error-prone  
- Most tools don’t offer **meaningful analysis** like a real financial advisor

---

## 💡 The Solution: A Chatroom with Agents That Work for You 💬✨

We've built a **collaborative AI experience** where different expert agents work together to help you make smart financial decisions. All this happens through a **group chat interface**:

### 🧠 Meet Your Finance Agents

- **👨‍💼 HostAgent**  
  Manages the conversation context and answers questions about personal finance and how the app works.

- **🛠️ SetupAgent**  
  Helps you configure your accounts, payment methods, and spending/income categories.

- **💳 TransactionsAgent**  
  Registers your financial transactions with minimal friction.

- **📷 VisionAgent**  
  Reads receipts and invoices to extract key information automatically.

- **📊 AnalyzerAgent**  
  Analyzes your data to offer insights, summaries, projections, and visualizations.

---

## ⚙️ Architecture

![architecture_diagram](https://azfunctionsstorage2025.blob.core.windows.net/files-upload-by-users/architecture-diagram-v1.png)
### 🖥️ Application Components

- **🔗 Chainlit**: A web app with a user-friendly conversational interface.  
- **🧠 Semantic Kernel**: Orchestrates conversations by choosing the right agent for each message.  
- **🖼️ Blob Storage**: Stores uploaded images from users.  

### 🧑‍💻 Agents on Azure

We use **Azure AI Agent Service** to deploy and manage most agents:

- 📁 **HostAgent**: Uses vector-based documents to answer finance and app-related questions.
- 🏦 **SetupAgent**: Registers accounts and categories using Logic Apps.
- 💸 **TransactionsAgent**: Fetches and records transactions in the database.
- 📈 **AnalyzerAgent**: Retrieves and analyzes user data to generate reports.
- 👁️ **VisionAgent**: Defined in the semantic kernel using GPT-4o-Mini with multimodal capabilities.

### 🛠️ Tools Used

- **Logic Apps** (via OpenAPI):
  - `create_account` → Creates user accounts
  - `create_category` → Defines spending/income categories
  - `record_transactions` → Saves financial transactions
  - `fetch_data_using_sql_query` → Pulls user data for analysis

### 📚 Knowledge & Data

- 🧠 **Vector Store**: A document repository with app and finance knowledge, used by HostAgent.  
- 🗄️ **Relational Database**: Stores all user data—accounts, categories, and transactions—for use by the agents.

---

## 🚀 What Makes This Solution Unique?

✔️ Natural conversations with multiple AI agents  
✔️ Fast data entry via intelligent automation  
✔️ Automatic document reading (receipts/invoices)  
✔️ Personalized financial analytics  
✔️ All in one place — inside a chat interface

---

## 🧪 What’s Next?

Here’s what we’re working on to make your personal finance assistant even smarter:

1. 📊 **Advanced analysis** of your spending habits with auto-generated reports and visual charts  
2. 🚨 **Proactive alerts** to help you stay within your budget  
3. 💡 **Smart financial advice** for paying off debt or making investments  
4. 🧾 **Expense optimization** by comparing product/service alternatives online  
5. 🧠 **Financial education** tailored for kids, teens, and adults  
6. ♿ **Accessibility-first design**, with support for audio and visual channels  
7. 🧾 **Automated tax filing** to simplify annual declarations

---
## 💬 Contact

Questions or suggestions? Reach out or open an issue. We love feedback! 💌

