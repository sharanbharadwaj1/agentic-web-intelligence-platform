planner_agent_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "fetch_static",
                        "fetch_selenium",
                        "extract_rule",
                        "summarize",
                        "finish"
                    ],
                },
                "reason": {"type": "string"},
            },
            "required": ["action", "reason"],
        }
