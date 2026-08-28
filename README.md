# PC TOOL SERVER — GITHUB BUILD SPEC
# Version 1.0

> SOURCE OF TRUTH:
> - APP_SPEC_GITHUB.md
> - ui.json (ui.md)
>
> Mục tiêu:
> Build một Windows PC Tool Server hoàn chỉnh, có source code sạch,
> test đầy đủ, GitHub Actions build tự động và sẵn sàng upload GitHub.

---

# 1. PROJECT GOAL

PC Tool Server là một Windows desktop application cho phép AI bên ngoài
(ChatGPT / Random AI / AI Manager) gọi các Tool được User cấp quyền để
thực thi trên PC.

AI KHÔNG có quyền thực thi command hệ thống tùy ý.

AI chỉ có thể:

AI
→ Connector
→ API
→ Security Gateway
→ Tool Registry
→ Permission
→ Argument Validation
→ Approval nếu cần
→ Tool Executor
→ Tool đã đăng ký
→ Result

---

# 2. TECHNOLOGY

Required:

- Python 3.12+
- PySide6
- FastAPI
- Uvicorn
- SQLite
- Pydantic v2
- psutil
- httpx

Optional:

- pynvml
- pytest

Không sử dụng:

- Flask
- Electron
- Node.js backend

---

# 3. APPLICATION COMPONENTS

Application gồm:

1. PySide6 Desktop UI
2. FastAPI Server
3. Security Gateway
4. Tool Registry
5. Tool Discovery
6. Tool Executor
7. Permission Manager
8. Argument Validator
9. Sandbox Manager
10. Task Manager
11. Approval Manager
12. System Monitor
13. SQLite Database
14. Logging System
15. Connector API

---

# 4. CONNECTOR PROTOCOL

Connector là cầu nối giữa AI và PC Tool Server.

Transport mặc định:

HTTP/HTTPS

API base:

/api/v1

Tool execution:

POST /api/v1/tools/{tool_name}/execute

Example:

{
  "request_id": "req_001",
  "action": "execute",
  "arguments": {}
}

Response:

{
  "success": true,
  "request_id": "req_001",
  "tool": "check_system",
  "status": "COMPLETED",
  "result": {}
}

AI không được truyền:

- shell command
- CMD command
- PowerShell command
- arbitrary Python
- arbitrary executable path

AI chỉ truyền:

- tool name
- action
- arguments theo schema của Tool.

---

# 5. AUTHENTICATION

Default authentication:

Bearer API Key

Header:

Authorization: Bearer <API_KEY>

Không có hoặc sai API Key:

401 Unauthorized

API key:

- Không hiển thị plaintext trong UI
- Không ghi vào log
- Không commit Git
- Không hard-code source
- Có thể regenerate bởi User

---

# 6. DEFAULT NETWORK

Default:

127.0.0.1:8080

Không public Internet mặc định.

Không bind 0.0.0.0 trừ khi User chủ động cấu hình.

---

# 7. SECURITY GATEWAY

Tất cả tool request bắt buộc đi qua Security Gateway.

Flow:

Request
→ Authentication
→ Tool Lookup
→ Enabled Check
→ Permission Check
→ Argument Validation
→ Sandbox Validation
→ Approval Validation
→ Task Creation
→ Execute
→ Result
→ Log

Không Tool nào được bypass Gateway.

---

# 8. TOOL REGISTRY

Tool Registry là trung tâm quản lý Tool.

Mỗi Tool có:

- name
- description
- version
- type
- entry
- permission
- enabled
- requires_approval
- arguments_schema
- allowed_paths
- metadata

Example:

{
  "name": "check_system",
  "version": "1.0.0",
  "description": "Check CPU RAM GPU",
  "type": "BAT",
  "entry": "system/check_system.bat",
  "permission": "READ",
  "enabled": true,
  "requires_approval": false
}

---

# 9. TOOL DISCOVERY

Tool system MUST support automatic discovery.

Server scan Tool Root và các Tool Plugin Directory.

Mỗi Tool phải có manifest.

Example:

tool/
├── manifest.json
└── ...

Registry đọc manifest và validate.

Tool không hợp lệ:

- không đăng ký
- không enabled
- không được execute

---

# 10. EXTENSIBILITY

Tool system MUST be modular.

New tools MUST be addable after the core application is completed.

Không được yêu cầu sửa:

- Security Gateway
- API layer
- Task Manager
- Core server
- Permission engine

để thêm một Tool mới.

Quy trình:

User
→ đặt Tool vào Tool Root
→ Tool Discovery
→ Manifest validation
→ Registry
→ User Enable
→ Tool available to AI

AI không được tự cài Tool.

AI không được tự enable Tool.

AI không được tự sửa Tool Registry.

---

# 11. TOOL TYPES

Built-in Tool types:

- JSON
- SQLite
- Browser
- BAT

Có thể mở rộng Custom Tool Plugin sau này.

Mỗi loại Tool phải sử dụng interface thống nhất.

Example:

Tool.execute(arguments)

Tool.validate(arguments)

Tool.describe()

---

# 12. BAT TOOL

BAT Tool chỉ được chạy nếu:

1. BAT nằm trong Tool Root.
2. BAT đã được đăng ký.
3. Manifest hợp lệ.
4. Tool enabled.
5. Permission hợp lệ.
6. Arguments hợp lệ.

Không có API generic:

- /cmd
- /powershell
- /shell
- /exec
- /python

AI không được truyền BAT path tùy ý.

AI chỉ gọi:

{
  "tool": "check_system",
  "arguments": {}
}

Server tự map Tool → file BAT đã đăng ký.

Không expose arbitrary shell execution.

---

# 13. PERMISSION LEVELS

READ

WRITE

DANGEROUS

Examples:

check_system → READ

read_json → READ

update_json → WRITE

delete_file → DANGEROUS

DANGEROUS mặc định yêu cầu Phone Approval.

---

# 14. ARGUMENT VALIDATION

Pydantic v2 được sử dụng để validate arguments.

Validate:

- required fields
- field types
- allowed values
- string length
- numeric range
- path
- unknown fields

Reject các payload nguy hiểm.

Không cho argument biến thành shell command.

---

# 15. TOOL ROOT

User chọn Tool Root bằng UI.

Tool Root:

- User selected
- Có thể thay đổi
- Không hard-code
- Phải tồn tại
- Phải là directory
- Không được nằm trong Windows/System folder
- Không được nằm trong Program Files
- Không được nằm trong system directory
- Không được là System Drive chứa Windows

Ví dụ hợp lệ:

D:\\AI_TOOLS
D:\\PROJECTS\\TOOLS
E:\\MY_TOOLS

Ví dụ không hợp lệ:

C:\\
C:\\Windows
C:\\Program Files
C:\\Program Files (x86)
C:\\ProgramData

---

# 16. SANDBOX

Mọi filesystem operation phải nằm trong Tool Root.

Path phải được canonicalize trước khi check.

Block:

- ..
- ../
- ..\\
- absolute path outside root
- symlink escape
- junction escape

Tool không được tự ý truy cập bên ngoài Tool Root.

---

# 17. TASK MANAGER

Mỗi Tool execution tạo một Task.

States:

QUEUED
WAITING_APPROVAL
RUNNING
COMPLETED
FAILED
REJECTED
CANCELLED

Task fields:

- task_id
- request_id
- tool
- action
- arguments
- status
- created_at
- started_at
- finished_at
- duration
- result
- error

API:

GET /api/v1/tasks
GET /api/v1/tasks/{task_id}
POST /api/v1/tasks/{task_id}/cancel

---

# 18. PHONE APPROVAL

Approval là một security layer.

Flow:

AI
→ Connector
→ Server
→ Approval Required
→ Phone
→ Approve / Reject
→ Server
→ Execute / Reject

Approval object:

- request_id
- tool
- action
- arguments
- permission
- risk_level
- created_at
- expires_at
- status

Approval phải bind với request_id + tool + arguments.

Nếu arguments thay đổi:

Approval invalid.

Expired approval:

Không execute.

---

# 19. SYSTEM MONITOR

Dashboard realtime:

- CPU
- RAM
- GPU
- VRAM
- Storage
- Server status
- Uptime
- Request count
- Active tasks

CPU/RAM/Storage dùng psutil.

GPU có thể dùng pynvml nếu khả dụng.

GPU monitoring lỗi không được làm server crash.

---

# 20. SQLITE

SQLite lưu:

- tools
- tasks
- approvals
- logs
- settings

Production database không commit Git.

---

# 21. LOGGING

Log:

- timestamp
- request_id
- task_id
- tool
- permission
- status
- duration
- error

Không log:

- API keys
- passwords
- secrets
- credentials
- seed phrases

---

# 22. DESKTOP UI

PySide6.

Pages:

- Dashboard
- Tools
- Tasks
- Approvals
- Logs
- Settings

UI phải tuân thủ ui.json.

---

# 23. DASHBOARD

Phải hiển thị:

CPU
RAM
GPU
Storage

Server:
- Status
- Host
- Port
- Uptime
- Requests

Tools:
- Total
- Enabled
- Disabled

Active Tasks:
- Tool
- Status
- Detail
- Duration

Tool Root:
- Current Path
- Sandbox status

---

# 24. TOOLS PAGE

Actions:

- Add Tool
- View Tool
- Edit Tool Metadata
- Test Tool
- Enable
- Disable
- Refresh

Không cho UI tạo arbitrary executable command.

---

# 25. TASKS PAGE

Filters:

- ALL
- QUEUED
- WAITING_APPROVAL
- RUNNING
- COMPLETED
- FAILED
- REJECTED
- CANCELLED

Actions:

- View
- Cancel

---

# 26. APPROVAL PAGE

Hiển thị:

- Request ID
- Tool
- Action
- Arguments
- Permission
- Risk
- Timestamp
- Status

Actions:

- View
- Approve
- Reject

---

# 27. LOGS PAGE

Filters:

- ALL
- SUCCESS
- FAILED
- REJECTED

Actions:

- Refresh
- Clear

---

# 28. SETTINGS

Server:

- host
- port
- API key

Security:

- authentication
- phone approval
- sandbox
- system drive protection

Tool Root:

- current path
- change folder

Security defaults:

authentication = ON
phone_approval = ON
sandbox = ON
system_drive_protection = ON

---

# 29. PROJECT STRUCTURE

pc-tool-server/
│
├── APP_SPEC_GITHUB.md
├── ui.json
├── README.md
├── requirements.txt
├── .gitignore
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── api/
│   │   ├── health.py
│   │   ├── tools.py
│   │   ├── tasks.py
│   │   ├── approvals.py
│   │   ├── system.py
│   │   └── logs.py
│   │
│   ├── security/
│   │   ├── gateway.py
│   │   ├── auth.py
│   │   ├── permissions.py
│   │   ├── validator.py
│   │   └── sandbox.py
│   │
│   ├── tools/
│   │   ├── registry.py
│   │   ├── discovery.py
│   │   ├── executor.py
│   │   ├── base.py
│   │   ├── json_tool.py
│   │   ├── sqlite_tool.py
│   │   ├── browser_tool.py
│   │   └── bat_tool.py
│   │
│   ├── tasks/
│   │   └── manager.py
│   │
│   ├── approvals/
│   │   └── manager.py
│   │
│   ├── monitoring/
│   │   └── system_monitor.py
│   │
│   └── gui/
│       ├── main_window.py
│       ├── dashboard.py
│       ├── tools_page.py
│       ├── tasks_page.py
│       ├── approvals_page.py
│       ├── logs_page.py
│       └── settings_page.py
│
├── tests/
│
├── plugins/
│
└── .github/
    └── workflows/
        └── build.yml

---

# 30. TESTING

Required tests:

- Authentication
- Permission
- Tool allowlist
- Tool discovery
- Manifest validation
- Argument validation
- Sandbox
- Path traversal
- System folder protection
- Disabled Tool
- Unknown Tool
- Approval expiration
- Approval argument mismatch
- Unauthorized BAT
- CMD injection
- PowerShell injection
- Arbitrary executable injection
- Task cancellation
- API errors

---

# 31. GITHUB ACTIONS

Pipeline:

Checkout
→ Python setup
→ Install dependencies
→ Run tests
→ Build Windows application
→ Package ZIP
→ Upload artifact

Artifact:

PC-Tool-Server-Windows.zip

Never commit:

- .env
- API keys
- credentials
- production database
- logs
- .venv
- build output

---

# 32. WINDOWS BUILD

Provide:

scripts/build_windows.bat

Build output:

dist/PC Tool Server/

Application phải chạy được trên Windows mà không cần IDE.

---

# 33. README

README phải có:

- Overview
- Architecture
- Installation
- Run
- Configuration
- Tool Root
- Tool System
- Add Tool
- API
- Security
- Testing
- Build
- GitHub Actions
- Troubleshooting

---

# 34. ACCEPTANCE CRITERIA

[ ] Windows app chạy
[ ] PySide6 UI hoạt động
[ ] FastAPI hoạt động
[ ] Connector API hoạt động
[ ] Authentication hoạt động
[ ] Tool Registry hoạt động
[ ] Tool Discovery hoạt động
[ ] Plugin Tool system hoạt động
[ ] Permission hoạt động
[ ] Argument Validation hoạt động
[ ] Sandbox hoạt động
[ ] Phone Approval framework hoạt động
[ ] Task Manager hoạt động
[ ] JSON Tool hoạt động
[ ] SQLite Tool hoạt động
[ ] Browser Tool architecture hoạt động
[ ] BAT Tool whitelist hoạt động
[ ] CMD generic execution bị block
[ ] PowerShell generic execution bị block
[ ] Arbitrary Python bị block
[ ] Arbitrary executable bị block
[ ] Security tests pass
[ ] GitHub Actions build pass
[ ] Windows artifact build thành công

---

# 35. CORE RULE

AI không được điều khiển OS trực tiếp.

AI chỉ được gọi Tool.

Tool phải tồn tại trong Registry.

Security Gateway quyết định request có hợp lệ.

Tool Executor chỉ chạy Tool đã được User cho phép.

New Tool có thể được thêm sau khi app hoàn thành.

Core Server không cần sửa để thêm Tool mới.
