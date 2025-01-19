# **Process Briefings**

## **Description**
This project demonstrates an approach to prepare public data for **Retrieval-Augmented Generation (RAG)** using advanced AI models. The resulting output is designed to work with a local Large Language Model (LLM) setup on modest hardware. For context, check out `Blog.md`, which is the relevant part from a blog post on https://meanmedianmoose.ca. 

The configuration utilizes:
- **Ollama** for model management.
- **OpenWebUI** as the front-end interface.
- **nginx** for secure communication.
- **Docker** for containerizing the application and nginx.

### **Data Source**
The demo data is based on a slightly cleaned version of the [Health Canada Deputy Minister Briefing Materials](https://www.canada.ca/en/health-canada/corporate/about-health-canada/proactive-disclosure/briefing-documents/2024-main-transition-e-binder.html) published by the Government of Canada. 

### **Available Output**
The goal is a tool that supports **natural-language queries** about the **structure, operations, strategic goals, and challenges** of Canada’s health ministry.

Three processed outputs are included in this repository:
- `dmbriefing_qwen2.5-14b.json`
- `dmbriefing_qwen2.5-72b.json`
- `dmbriefing_llama3.3.json`

Use `dmbriefing_qwen2.5-72b.json` for the best results. This file can be loaded into an LLM's knowledge base for optimal query responses.

---

## **Getting Started**
### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/process-briefings.git
cd process-briefings
```

### **2. Set Up Docker**
Ensure Docker is installed and running on your system. Use the provided `Dockerfile` to build and run the necessary containers:
```bash
docker build -t process-briefings .
docker run -d -v $(pwd):/app process-briefings
```

### **3. Configure nginx**
Set up **nginx** as an SSL proxy for secure communication. Ensure you have the necessary SSL certificates and modify `nginx.conf` as needed. You can refer to [this sample configuration](https://github.com/dsartori/simple-proxy).

### **4. Start Ollama**
Run the Ollama service to manage the AI models:
```bash
ollama start
```

### **5. Launch OpenWebUI**
This command is pulled from the OpenWebUI Git repository: https://github.com/open-webui/open-webui. Check that URL for updates or the right docker command for your use case.
```bash
docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:cuda
```

### **6. Run the Script**
In the process-briefings Docker container shell:
```bash
python process_briefings.py dmbriefing.html dmbriefing_new.json
```

The first argument to `process_briefings.py` is the document to process, and the second argument is the output document.

### **7. Upload Documents**
- Open your web browser and navigate to:
```
https://<your_device_ip_or_name>
```
- Navigate to the **Knowledge** section in OpenWebUI.
- Select `+` to create a new Knowledge base for your data.
- Upload one of the provided JSON files (e.g., `dmbriefing_qwen2.5-72b.json`) to populate the model's knowledge base.

### **8. Create a Custom Model**
- Go to the **Models** section in OpenWebUI.
- Select `+` to create a custom model.
- Follow the prompts to configure and deploy your model. (For example, "Qwen2.5:14b" or any high-quality midsized LLM.)
- Add a tailored system prompt to guide the AI’s responses. You can find a sample prompt [here](https://gist.github.com/dsartori/35de7f2ed879d5a5e50f6362dea2281b)

---


## **License**
This project is yours to use under the MIT License. See `LICENSE` for more details.

