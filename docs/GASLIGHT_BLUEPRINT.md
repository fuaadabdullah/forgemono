# GASLIGHT — FULL DEVELOPMENT BLUEPRINT

A complete, drop-in document for VS Code. This file contains everything you need to start building **Gaslight** in Unity + Python FastAPI.

This is structured so you can follow it top-to-bottom while building.

---

## 0. PROJECT OVERVIEW

**Title:** Gaslight
**Engine:** Unity (2D URP)
**Backend:** FastAPI (Python)
**Gameplay:** 2D exploration + chat-driven narrative
**Core Loop:** Walk around mansion, talk to NPCs, get gaslit, consult Goblin, unlock endings
**Deliverables:** 4 missions, 6 endings

---

## 1. UNITY PROJECT SETUP

## 1.1 Create the project

* Open Unity Hub
* New Project → **2D (URP)** template
* Project name: `Gaslight`

## 1.2 Packages you must add

* From Package Manager → Install:

  * 2D Pixel Perfect
  * 2D Animation (optional)
  * URP 2D Lights

## 1.3 Pixel Perfect Camera Setup

* Add a GameObject: `Main Camera`
* Attach: **Pixel Perfect Camera** component
* Settings:

  * Assets Pixels Per Unit (PPU): **32**
  * Reference Resolution: **320 x 180**
  * Upscale Render Texture: ON
  * Pixel Snapping: ON

---

## 2. SCENE BLUEPRINT

Use this structure in your **Hierarchy**:

```text
Mansion_Hallway
├─ Lighting2D
├─ Backgrounds
│  ├─ BG_Back
│  ├─ BG_Mid
│  └─ FG_Decor
├─ Player
│  ├─ SpriteRenderer
│  ├─ Animator
│  └─ PlayerController2D.cs
├─ NPCs
│  ├─ Samira
│  │  ├─ SpriteRenderer
│  │  ├─ NPCInteractable.cs
│  │  └─ BoxCollider2D (Is Trigger = ON)
├─ UI_Canvas
│  ├─ ChatPanel
│  └─ GoblinPanel
└─ Managers
   ├─ GameStateManager.cs
   ├─ ChatUIManager.cs
   ├─ BackendClient.cs
   └─ AudioManager.cs
```

---

## 3. CORE UNITY SCRIPTS (C#)

Paste into files exactly as shown.

## 3.1 PlayerController2D.cs

```csharp

using UnityEngine;

public class PlayerController2D : MonoBehaviour
{
    public float speed = 3f;
    private Rigidbody2D rb;
    private Vector2 move;

    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    void Update()
    {
        move = new Vector2(Input.GetAxisRaw("Horizontal"), 0);
    }

    void FixedUpdate()
    {
        rb.velocity = new Vector2(move.x * speed, rb.velocity.y);
    }
}
```

## 3.2 NPCInteractable.cs

```csharp
using UnityEngine;

public class NPCInteractable : MonoBehaviour
{
    public string npcId;
    public int mission;

    private bool canTalk = false;

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player")) canTalk = true;
    }

    void OnTriggerExit2D(Collider2D other)
    {
        if (other.CompareTag("Player")) canTalk = false;
    }

    void Update()
    {
        if (canTalk && Input.GetKeyDown(KeyCode.E))
        {
            ChatUIManager.Instance.OpenChat(npcId, mission);
        }
    }
}
```

## 3.3 ChatUIManager.cs

```csharp

using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class ChatUIManager : MonoBehaviour
{
    public static ChatUIManager Instance;

    public GameObject chatPanel;
    public TMP_Text npcText;
    public TMP_Text goblinText;
    public TMP_InputField input;

    private string currentNpc;
    private int currentMission;

    void Awake() => Instance = this;

    public void OpenChat(string npcId, int mission)
    {
        currentNpc = npcId;
        currentMission = mission;
        chatPanel.SetActive(true);
        npcText.text = "";
        goblinText.text = "";
    }

    public async void SendMessageToBackend()
    {
        string userMessage = input.text;
        input.text = "";

        var response = await BackendClient.Instance.RouteMessage(currentNpc, currentMission, userMessage);

        npcText.text = response.npc_response;
        goblinText.text = response.goblin_hint;
    }
}
```

## 3.4 BackendClient.cs (Unity → FastAPI)

```csharp
using UnityEngine;
using System.Threading.Tasks;
using UnityEngine.Networking;

public class BackendClient : MonoBehaviour
{
    public static BackendClient Instance;
    public string apiUrl = "http://localhost:8000/route";

    void Awake() => Instance = this;

    [System.Serializable]
    public class RouteResponse
    {
        public string npc_response;
        public string goblin_hint;
        public string mission_status;
        public int next_step;
    }

    public async Task<RouteResponse> RouteMessage(string npc, int mission, string message)
    {
        var payload = JsonUtility.ToJson(new
        {
            npc_id = npc,
            mission = mission,
            message = message
        });

        UnityWebRequest req = new UnityWebRequest(apiUrl, "POST");
        byte[] body = System.Text.Encoding.UTF8.GetBytes(payload);
        req.uploadHandler = new UploadHandlerRaw(body);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");

        var operation = req.SendWebRequest();
        while (!operation.isDone) await Task.Yield();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError(req.error);
            return new RouteResponse { npc_response = "Backend error.", goblin_hint = "" };
        }

        return JsonUtility.FromJson<RouteResponse>(req.downloadHandler.text);
    }
}
```

---

## 4. FASTAPI BACKEND BOILERPLATE

Place this in your Python folder as `main.py`.

```python

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RouteRequest(BaseModel):
    npc_id: str
    mission: int
    message: str

class RouteResponse(BaseModel):
    npc_response: str
    goblin_hint: str
    mission_status: str
    next_step: int

@app.post("/route", response_model=RouteResponse)
def route_message(req: RouteRequest):

    return RouteResponse(
        npc_response=f"NPC({req.npc_id}) responds to: {req.message}",
        goblin_hint="Goblin side-comment...",
        mission_status="in_progress",
        next_step=req.mission + 1,
    )
```

Run backend:

```bash
uvicorn main:app --reload --port 8000
```

---

## 5. NPC PERSONALITIES (REFERENCE)

### Samira (Sister)

* Love-bombs Ayah
* Twists facts softly
* Gaslighting type: Minimizing

### Layla (Cousin)

* Passive aggressive
* Pretends Ayah is childish
* Gaslighting type: Shifting blame

### Idris (Family friend)

* Overly logical
* Makes Ayah “prove” her feelings
* Gaslighting type: Reality denial

### Mariam (Friend)

* Fake empathy
* Speaks in contradictions
* Gaslighting type: Rewriting events

---

## 6. GOBLIN DIALOGUE STYLE

* Honest but evil-coded
* Talks like a gremlin with clarity
* Always tells the truth but in the most toxic, chaotic way
* Breaks the fourth wall with Ayah only

Example tone:
“Girl, they lying through they teeth. I ain’t gon’ sugarcoat it. They cooking you alive out there.”

---

## 7. MISSION SCRIPTS

### Mission 1: "You’re imagining it"

Goal: Teach player the signs of minimization.

### Mission 2: "You’re overreacting"

Goal: Reframe emotional manipulation.

### Mission 3: "That never happened"

Goal: Force player to navigate memory denial.

### Mission 4: "We’re doing this for your own good"

Goal: Confront control disguised as love.

Each mission ends with a backend-controlled branch.

---

## 8. DAILY CHECK-IN WORKFLOW

Use this while building:

1. 30 minutes asset import
2. 1 hour scripting (Unity or backend)
3. 1 hour mission/dialogue writing
4. 1 hour scene building
5. 30 minutes polish/testing

Repeat daily.

---

## 9. FINAL BUILD PIPELINE

1. Build backend first (make sure it runs without errors)
2. Link Unity → BackendClient URL
3. Test all 4 missions
4. Implement endings
5. Export Windows/Mac build

---

## END OF DOCUMENT
