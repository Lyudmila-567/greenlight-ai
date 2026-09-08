# Greenlight AI 🎬

A data-grounded, multi-agent AI system designed to brainstorm, refine, and validate film ideas against real-world market insights.

# Greenlight AI 🎬

A data-grounded, multi-agent AI system designed to brainstorm, refine, and validate film ideas against real-world market insights.

## 🔗 Project Links
*   **Live Web MVP:** [Deploy Link on Render][https://greenlight-ai-backend.onrender.com/]
*   **Video Demonstration:** [YouTube Presentation Link](https://youtu.be/HNYiRfVxjVo)

## 🛠️ Built With
![Python](https://shields.io)
![FastAPI](https://shields.io)
![Google Cloud](https://shields.io)
![ClickHouse](https://shields.io)
![Grafana](https://shields.io)
![Pydantic](https://shields.io)

*Note on Tech Stack:* Driven by the **Google GenAI SDK (Vertex AI)** for intelligent orchestration and **Model Context Protocol (MCP)** for secure data grounding.

## 💡 Inspiration
The core inspiration behind this project was to push technical boundaries by architecting a multi-agent AI system. 
The goal was to design a collaborative network of **AI Agents** ($A_1, A_2, \dots, A_n$) 
that functions as a cohesive team to help creators brainstorm, refine, and validate new film ideas.  

To solve the common industry problem of AI hallucinations, the multi-agent system is mathematically grounded in real-world data constraints:  

$$ V(Idea) = A_{orch}(f(MarketData, HistoricalTrends)) $$

This ensures that every generated concept is deeply anchored in actual market realities, filtering out unrealistic or unfeasible tropes from the very beginning.

## 🚀 What It Does
- **Multi-Agent Orchestration:** Activates a core engine that delegates tasks and coordinates workflows between analytical and creative AI agents.  
- **Real-World Data Grounding:** Implements semantic filtering that prevents hallucinated or impossible script ideas by anchoring them to historical industry data.  
- **Film Concept & Plot Generation:** Delivers a fully structured film idea, complete with a detailed narrative arc, character premises, and thematic direction.  
- **Data-Driven Marketing Analytics:** Automates calculations of target audience demographics, projected market positioning, and financial feasibility metrics based on current industry trends:  

$$ MarketFit = \sum (GenreTrend 	imes AudienceDemand) $$

## 🛠️ How We Built It
During development, I mastered AI Orchestration, managing data streaming and state synchronization across multiple intelligent agents. The final deliverable is a fully functional **MVP (Minimum Viable Product)** deployed as an interactive website. 

The system processes user inputs, applies real-world filters, and synthesizes viable cinematic concepts using the following core stack:
- **Python** & **FastAPI** (Hosted on **Render**)
- **Google GenAI SDK** (Powered by **Vertex AI**)
- **ClickHouse** (High-performance columnar database)
- **MCP** (Model Context Protocol for advanced agent tooling)
- **Pydantic** (Robust data validation and settings management)
- **Grafana** (Real-time infrastructure observability)

## ⚠️ Challenges We Ran Into
The biggest constraint of this project was severe time limitations. Initially, the planned architecture was highly complex, which threatened the delivery of a working product before the deadline.  

To overcome this, the entire system architecture was completely refactored and streamlined mid-project. I pivoted from a sprawling multi-layered network to a simplified, highly efficient framework specifically designed to guarantee a working MVP.  

### Key Takeaways from the Pivot:
- **Agile Simplification:** Stripping away non-essential layers allowed a heavy focus on the core value: grounding the AI agents in real-world data.  
- **Modular Foundation:** Although simplified to meet immediate timelines, the system was built with clean, modular interfaces.  
- **Ready for Scale:** The architecture remains highly scalable and is perfectly positioned for future integration of new options, advanced tools, and automated pipelines.

## 🏆 Accomplishments That We're Proud Of
- **High-Value Business Concept:** Engineered an innovative incubation system designed to solve a tangible entertainment industry problem. By filtering out unfeasible ideas early, the platform acts as a commercial gatekeeper, saving studios immense pre-production costs.
- **Bridging Data Analytics & Software Engineering:** Successfully harmonized heavy data analytics with production-ready software development. The system seamlessly bridges data ingestion via ClickHouse with dynamic user-driven workflows, creating a unified full-stack pipeline:  

$$ SystemSynergy = DataAnalytics 	imes AIOrchestration $$

- **Empirical Concept Validation:** Designed a robust architecture for Human-in-the-Loop validation. Even within a simulated environment, establishing a pathway where real human focus groups stream telemetry data provides an undeniable, bulletproof verification metric for movie concept viability.  
- **Architectural Resilience:** Successfully navigated high-pressure time constraints by entirely re-engineering a complex multi-layered system into a lean framework without losing the project's core analytical power.

## 🧠 What We Learned
- **Ruthless Prioritisation:** Delivering a fully functioning, interactive web MVP under tight timelines proved the immense value of keeping code agile, identifying non-essentials, and knowing when to pivot to ship a stable product.  
- **AI Orchestration Dynamics:** Managing multiple AI Agents taught me how to structure precise semantic constraints. I learned how to effectively ground models in real-world parameters to eliminate hallucinations and keep creative outputs deterministic.  
- **Data Stack Competency:** Gained hands-on experience handling rapid analytical queries using ClickHouse and setting up infrastructure observability via Grafana to track agent throughput.
- **Exploring Corporate AI Frameworks:** Researching **IBM Bob** opened up new perspectives on how enterprise-grade automation tools handle complex workflows, giving me a solid blueprint for the next developmental phase.

## 🔮 What's Next for Greenlight AI
Now that the core MVP foundation is stable and ready for scale, the roadmap focuses on turning this tool into an enterprise-grade validation pipeline. The immediate backlog includes:  

1. **Human-in-the-Loop Focus Groups:** Integrating real human focus groups to review the generated film plots and marketing strategies. The next step is to build an automated streaming pipeline to collect audience reaction data as telemetry, introducing a quantitative validation metric:

$$ ValidationScore = \int_{0}^{T} Engagement(t) dt $$

2. **Full IBM Bob Integration:** Dedicating focused development time to fully implement IBM Bob into the orchestration layer, utilizing its enterprise automation capabilities to handle complex background agent workflows.  
3. **AI Teaser Generation Engine:** Integrating generative video tools to automatically produce visual, high-quality cinematic trailers based on the approved AI plots.  
4. **Interactive Marketing Dashboards:** Expanding the current Grafana setup to display user-facing predictive revenue models and demographic breakdowns directly on the website platform.  
5. **Advanced Feature Expansion:** Leveraging the current modular architecture to seamlessly plug in new user options, such as customizable budget constraints, regional trend filters, and genre-blending modifiers.
