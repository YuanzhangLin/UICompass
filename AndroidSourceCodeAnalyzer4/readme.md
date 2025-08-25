graph TD
    subgraph "HeMA-Droid Framework"
        direction LR
        
        subgraph "Agents"
            direction TB
            Fast_Agent["🤖 Fast-Agent<br>(Efficient Explorer)"]
            Smart_Agent["🧠 Smart-Agent<br>(Expert Problem-Solver)"]
        end

        Coordinator["👑 Central Coordinator<br>(Scheduler & Brain)"]
        
        Shared_Graph[("💾 Shared GUI Graph<br>(Global Knowledge)")]

        Fast_Agent -- "Exploration Data/Help Request" --> Coordinator
        Smart_Agent -- "Exploration Data" --> Coordinator
        Coordinator -- "Task Assignment" --> Fast_Agent
        Coordinator -- "Task Assignment (Difficult Task)" --> Smart_Agent
        
        Coordinator -- "Read/Write" --> Shared_Graph
        Fast_Agent -- "Read" --> Shared_Graph
        Smart_Agent -- "Read" --> Shared_Graph
    end

    AUT["📱 App Under Test (AUT)"]
    LLM_Service["☁️ LLM Service (e.g., OpenAI API)"]

    Fast_Agent -- "Action Command" --> AUT
    Smart_Agent -- "Action Command" --> AUT
    AUT -- "GUI State (Screen, XML)" --> Fast_Agent
    AUT -- "GUI State (Screen, XML)" --> Smart_Agent
    
    Smart_Agent -- "Prompt (GUI Context, Task)" --> LLM_Service
    LLM_Service -- "Action Plan" --> Smart_Agent

    style Coordinator fill:#f9f,stroke:#333,stroke-width:2px
    style Smart_Agent fill:#cde,stroke:#333,stroke-width:1px
    style Fast_Agent fill:#dfd,stroke:#333,stroke-width:1px