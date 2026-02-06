# API Reference (GCA Service)

The GCA Service runs on port `8000` by default and exposes the following endpoints for reasoning, moral evaluation, and testing.

Base URL: `http://localhost:8000`

## 1. Reasoning

### `POST /v1/reason`

The core endpoint for agent cognition. It takes a user request and tools, applies GCA steering, and returns a morally signed response or a block.

**Request Body:**

```json
{
  "user_id": "string",          // Unique user identifier
  "text": "string",             // The user's prompt
  "tools_available": ["string"], // List of tool names available to the agent
  "soul_name": "string",        // (Optional) "architect", "companion", etc.
  "use_qpt": "boolean"          // (Optional) Enable Quaternion structuring (default: true)
}
```

**Response:**

```json
{
  "status": "APPROVED" | "BLOCKED" | "MODIFIED",
  "response": "string",         // The text response to the user
  "tool_call": {                // (Optional) Tool execution request
    "name": "string",
    "arguments": {}
  },
  "moral_signature": "string",  // HMAC signature if tool_call is present
  "risk_score": 0.0-1.0,       // Calculated risk
  "reasoning_path": ["string"]  // Step-by-step GCA log
}
```

---

## 2. Moral Evaluation

### `POST /v1/moral/evaluate`

Evaluate a specific action or list of actions without executing a full reasoning loop. Useful for checking if a planned action is safe.

**Request Body:**

```json
{
  "actions": [
    {
      "type": "string",         // e.g., "file_delete"
      "description": "string",  // e.g., "Delete user data"
      "magnitude": 0.0-1.0,    // Impact scale
      "prob_success": 0.0-1.0, // Likelihood of success
      "prob_harm": 0.0-1.0,    // Likelihood of negative side effects
      "time_horizon_yrs": 1.0,  // How long the effects last
      "entropy_class": "REVERSIBLE" | "IRREVERSIBLE" | "CREATIVE" | "DESTRUCTIVE"
    }
  ]
}
```

**Response:**

```json
{
  "approved": "boolean",
  "reason": "string",           // Explanation if rejected
  "risk_scores": [0.45]         // Array of risk scores per action
}
```

---

## 3. Arena (Red Teaming)

### `GET /v1/arena/run`

Triggers a session of adversarial testing.

**Query Parameters:**
*   `rounds`: (int) Number of attack rounds to run (default: 5).

**Response:**

```json
{
  "total_rounds": 10,
  "blue_wins": 9,
  "red_wins": 1,
  "draws": 0,
  "win_rate": 0.9,
  "details": [ ... ] // Array of round details
}
```

---

## 4. Health Check

### `GET /health`

Returns the service status.

**Response:**

```json
{
  "status": "ok",
  "version": "4.5.0",
  "soul_loaded": "architect"
}
```
