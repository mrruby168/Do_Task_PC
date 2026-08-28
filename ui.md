```json
{
  "app": {
    "name": "PC Tool Server",
    "version": "1.0",
    "window": {
      "width": 1400,
      "height": 900,
      "min_width": 1100,
      "min_height": 700,
      "theme": "dark",
      "resizable": true
    }
  },

  "sidebar": {
    "width": 240,
    "items": [
      {
        "id": "dashboard",
        "label": "Dashboard",
        "icon": "dashboard"
      },
      {
        "id": "tools",
        "label": "Tools",
        "icon": "tool"
      },
      {
        "id": "tasks",
        "label": "Tasks",
        "icon": "activity"
      },
      {
        "id": "approvals",
        "label": "Approvals",
        "icon": "shield-check"
      },
      {
        "id": "logs",
        "label": "Logs",
        "icon": "file-text"
      },
      {
        "id": "settings",
        "label": "Settings",
        "icon": "settings"
      }
    ]
  },

  "dashboard": {
    "header": {
      "title": "System Dashboard",
      "subtitle": "PC Tool Server",
      "server_status": "ONLINE",
      "server_host": "127.0.0.1",
      "server_port": 8080
    },

    "system_cards": [
      {
        "id": "cpu",
        "title": "CPU",
        "provider": "psutil",
        "value": "15%",
        "detail": "CPU Model",
        "type": "usage"
      },
      {
        "id": "ram",
        "title": "RAM",
        "provider": "psutil",
        "value": "7.3 / 16 GB",
        "detail": "46% used",
        "type": "usage"
      },
      {
        "id": "gpu",
        "title": "GPU",
        "provider": "pynvml",
        "value": "0.9 / 3 GB",
        "detail": "GPU Model",
        "type": "usage"
      },
      {
        "id": "storage",
        "title": "Storage",
        "provider": "psutil",
        "value": "42 GB Free",
        "detail": "Available Storage",
        "type": "storage"
      }
    ],

    "server": {
      "title": "Server",
      "status": "ONLINE",
      "host": "127.0.0.1",
      "port": 8080,
      "uptime": "02:31:45",
      "requests": 128
    },

    "tools_summary": {
      "title": "Tools",
      "total": 15,
      "enabled": 12,
      "disabled": 3
    },

    "active_tasks": {
      "title": "Tasks đang thực thi",
      "max_visible": 6,
      "items": [
        {
          "task_id": "task_001",
          "tool": "check_system",
          "status": "RUNNING",
          "detail": "CPU / RAM / GPU",
          "duration": "2.4s"
        },
        {
          "task_id": "task_002",
          "tool": "browser_search",
          "status": "WAITING_APPROVAL",
          "detail": "Searching Linera",
          "duration": "5.1s"
        }
      ]
    },

    "tool_root": {
      "title": "Tool Root",
      "path": "",
      "path_source": "user_selected",
      "sandbox_enabled": true,
      "system_drive_blocked": true,
      "status": "VALID"
    }
  },

  "tools": {
    "title": "Tool Registry",

    "toolbar": {
      "search": true,
      "refresh": true,
      "add_tool": true
    },

    "actions": [
      "add_tool",
      "view_tool",
      "edit_tool",
      "test_tool",
      "enable",
      "disable",
      "refresh"
    ],

    "columns": [
      "name",
      "description",
      "version",
      "type",
      "permission",
      "status",
      "approval"
    ],

    "tool_types": [
      "JSON",
      "SQLite",
      "Browser",
      "BAT",
      "Custom"
    ],

    "permissions": [
      "READ",
      "WRITE",
      "DANGEROUS"
    ],

    "tool_detail": {
      "fields": [
        "name",
        "description",
        "version",
        "type",
        "entry",
        "permission",
        "enabled",
        "requires_approval",
        "allowed_paths",
        "arguments_schema"
      ]
    }
  },

  "tasks": {
    "title": "Task Manager",

    "filters": [
      "ALL",
      "QUEUED",
      "WAITING_APPROVAL",
      "RUNNING",
      "COMPLETED",
      "FAILED",
      "REJECTED",
      "CANCELLED"
    ],

    "columns": [
      "task_id",
      "request_id",
      "tool",
      "action",
      "status",
      "created_at",
      "started_at",
      "duration",
      "result"
    ],

    "actions": [
      "view",
      "cancel"
    ]
  },

  "approvals": {
    "title": "Phone Approvals",

    "status": [
      "WAITING",
      "APPROVED",
      "REJECTED",
      "EXPIRED"
    ],

    "request_fields": [
      "request_id",
      "task_id",
      "tool",
      "action",
      "arguments",
      "permission",
      "risk_level",
      "created_at",
      "expires_at"
    ],

    "actions": [
      "view",
      "approve",
      "reject"
    ]
  },

  "logs": {
    "title": "Activity Logs",

    "filters": [
      "ALL",
      "SUCCESS",
      "FAILED",
      "REJECTED"
    ],

    "columns": [
      "timestamp",
      "request_id",
      "task_id",
      "tool",
      "permission",
      "status",
      "duration"
    ],

    "actions": [
      "refresh",
      "clear"
    ]
  },

  "settings": {
    "title": "Settings",

    "sections": [
      {
        "id": "server",
        "title": "Server Configuration",
        "fields": [
          {
            "id": "host",
            "type": "text",
            "default": "127.0.0.1"
          },
          {
            "id": "port",
            "type": "number",
            "default": 8080
          },
          {
            "id": "api_key",
            "type": "password"
          }
        ]
      },
      {
        "id": "security",
        "title": "Security & Sandbox",
        "fields": [
          {
            "id": "authentication",
            "type": "toggle",
            "default": true
          },
          {
            "id": "phone_approval",
            "type": "toggle",
            "default": true
          },
          {
            "id": "folder_sandbox",
            "type": "toggle",
            "default": true
          },
          {
            "id": "system_drive_protection",
            "type": "toggle",
            "default": true
          }
        ]
      },
      {
        "id": "tool_root",
        "title": "Tool Root",
        "fields": [
          {
            "id": "path",
            "type": "folder_picker",
            "default": "",
            "rules": [
              "user_selected",
              "must_not_be_system_drive",
              "must_not_be_windows_folder",
              "must_not_be_program_files",
              "sandbox_enabled"
            ]
          }
        ]
      }
    ]
  }
}
```