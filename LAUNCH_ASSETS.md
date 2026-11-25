# 🚀 MCPX v1.1.0 Viral Launch Kit (Show HN, Reddit & X)

Universal Model Context Protocol (MCP) Inspector, Interactive Web Studio & Stdio Sniffer
GitHub: https://github.com/BNTiyan/mcpx

---

## 1. Hacker News ("Show HN") Submission

**Title**:
> Show HN: mcpx – Zero-dependency Web Studio & Inspector for Model Context Protocol (MCP)

**URL**:
`https://github.com/BNTiyan/mcpx`

**Body**:
```text
Hey HN,

Over the last few months, Model Context Protocol (MCP) has exploded as the open standard connecting Claude Desktop, Cursor, and autonomous agents to local tools and APIs.

However, developing and debugging an MCP server has been notoriously frustrating:
1. To test changes, developers restart Claude Desktop dozens of times.
2. If a tool fails or throws an exception, Claude Desktop often shows a silent error or freezes without showing the raw JSON-RPC frame.
3. Existing inspectors require installing heavy Node.js runtimes, Docker containers, or browser extensions.

I built `mcpx` (https://github.com/BNTiyan/mcpx) to give developers an instant, zero-dependency diagnostic toolkit that works in 1 second directly from your shell:

- `mcpx web`: Spawns a local, dark-mode glassmorphic Bento Studio with auto-generated form inputs for all tools, real-time tool execution, and an active JSON-RPC traffic waterfall (zero npm/node dependencies, 100% Python standard library).
- `mcpx proxy`: A transparent bidirectional stdio sniffer you can put in your Claude Desktop config to log and inspect live communication in real time.
- `mcpx doctor`: Auto-scans your Claude Desktop and Cursor config files, tests server handshakes, and detects latency bottlenecks or crashed processes.
- `mcpx demo`: An instant sandbox server you can try right now with zero setup.

Quick test:
  curl -fsSL https://raw.githubusercontent.com/BNTiyan/mcpx/main/install.sh | bash
  mcpx demo

It’s open source (MIT), written in pure Python, and has zero heavy external dependencies. I’d love your feedback, bug reports, and feature requests!
```

---

## 2. Reddit Post (`r/LocalLLaMA`, `r/Anthropic`, `r/ClaudeAI`)

**Title**:
> I built mcpx: a lightweight Postman/Wireshark for MCP servers (with Claude Desktop Doctor & Web Studio)

**Post Body**:
```markdown
If you’ve been building or using Model Context Protocol (MCP) servers with Claude Desktop or Cursor, you know how painful debugging can be. If a tool crashes or has a schema mismatch, you're usually stuck digging through hidden Application Support logs.

I built **`mcpx`** (MIT open source): an instant terminal inspector and local Web Studio for MCP.

GitHub: https://github.com/BNTiyan/mcpx

### Key Features:
- ⚡ **`mcpx web`**: One-command browser studio with a dark-mode Bento Grid. It inspects your server, auto-generates form controls from your JSON Schema, lets you execute tools with Cmd+Enter, and displays live microsecond latency.
- 🩺 **`mcpx doctor`**: One command that checks your Claude Desktop (`claude_desktop_config.json`) and Cursor configs, runs stdio handshakes, and flags missing binaries or crashed processes.
- 🔍 **`mcpx proxy`**: Transparent stdio sniffer that sits between Claude Desktop and your server to log all live JSON-RPC request/response frames.
- 📊 **`mcpx test`**: Automated micro-benchmark suite measuring p50, p95, and p99 latency under simulated load.

### 1-Line Install:
```bash
curl -fsSL https://raw.githubusercontent.com/BNTiyan/mcpx/main/install.sh | bash
mcpx demo
```

Would love to hear what other diagnostic features you'd find useful for your agent toolchains!
```

---

## 3. X (Twitter) Viral Launch Thread

**Tweet 1 (Hook)**:
> Debugging Model Context Protocol (MCP) servers in Claude Desktop is painfully slow—silent crashes, opaque stdio framing, and endless restarts.
> 
> So I built **mcpx**: an instant, zero-dependency Web Studio & Inspector for MCP servers.
> 
> 100% open source. Here’s what it does 👇
> 
> 🔗 https://github.com/BNTiyan/mcpx

**Tweet 2 (Web Studio)**:
> 1/ `mcpx web`: A sleek, zero-dependency local Bento Studio.
> 
> Auto-generates UI forms from your tool schemas, lets you test tools with microsecond timing, and shows a live JSON-RPC traffic waterfall.
> 
> Works with any MCP server executable.

**Tweet 3 (Doctor & Proxy)**:
> 2/ `mcpx doctor` & `mcpx proxy`:
> 
> - `doctor` audits your Claude Desktop / Cursor configs and flags broken binaries or hanging processes.
> - `proxy` transparently sniffs live traffic between Claude Desktop and your server so you see every frame in real time.

**Tweet 4 (CTA)**:
> Install in 5 seconds via curl:
> `curl -fsSL https://raw.githubusercontent.com/BNTiyan/mcpx/main/install.sh | bash`
> 
> Check it out on GitHub and star if you find it helpful! ⭐
> https://github.com/BNTiyan/mcpx
