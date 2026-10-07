// Control Surface thin shell. Everything on screen comes from the service answer for this request,
// never from a client-side guess: a submit shows RUNNING, and only an ACCEPTED result with a receipt and
// a readback is worded as done. A NOT_IMPLEMENTED operation is listed with its reason and cannot be sent,
// because the backend already refuses it — and the refusal reason is the useful part.
"use strict"

const state = { descriptor: null, idempotencyKey: "" }

const el = (id) => document.getElementById(id)

function newIdempotencyKey(taskId) {
  const random = (() => {
    const buffer = new Uint8Array(8)
    if (globalThis.crypto && crypto.getRandomValues) {
      crypto.getRandomValues(buffer)
    } else {
      for (let index = 0; index < buffer.length; index += 1) buffer[index] = Math.floor(Math.random() * 256)
    }
    return Array.from(buffer, (byte) => byte.toString(16).padStart(2, "0")).join("")
  })()
  return `ctl-${(taskId || "unit").replace(/[^A-Za-z0-9._-]/g, "-").slice(0, 40)}-${random}`
}

function renderTransport() {
  const line = el("transport")
  if (!state.descriptor) {
    line.textContent = "状态 UNKNOWN（尚未读到 descriptor）"
    line.className = "tag warn"
    return
  }
  const ceiling = state.descriptor.evidence_ceiling || "UNKNOWN"
  line.textContent = `已连接 · loopback-only · 证据上限 ${ceiling}（本地写不会自称 REAL）`
  line.className = "tag ok"
}

function renderOperations() {
  const list = el("operations")
  list.textContent = ""
  const operations = (state.descriptor && state.descriptor.operations) || []
  if (!operations.length) {
    const empty = document.createElement("li")
    empty.textContent = "操作清单 UNKNOWN（descriptor 未到达）"
    list.appendChild(empty)
    return
  }
  for (const operation of operations) {
    const item = document.createElement("li")
    item.className = operation.support === "IMPLEMENTED" ? "op supported" : "op unsupported"

    const name = document.createElement("span")
    name.className = "mono"
    name.textContent = operation.operation
    item.appendChild(name)

    const badge = document.createElement("span")
    badge.className = operation.support === "IMPLEMENTED" ? "tag ok" : "tag muted"
    badge.textContent = operation.support === "IMPLEMENTED" ? "可提交" : "不可用（后端未实现）"
    item.appendChild(badge)

    const reason = document.createElement("p")
    reason.textContent = `${operation.reason_code} · ${operation.reason}`
    item.appendChild(reason)

    if (operation.next_action) {
      const next = document.createElement("p")
      next.className = "next"
      next.textContent = `下一步：${operation.next_action}`
      item.appendChild(next)
    }
    list.appendChild(item)
  }
}

async function loadDescriptor() {
  try {
    const response = await fetch("/api/control/descriptor", { headers: { Accept: "application/json" } })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    state.descriptor = await response.json()
  } catch (error) {
    state.descriptor = null
    el("transport").textContent = `后端不可达：${error.message}（保持 UNKNOWN，不假装可写）`
    el("transport").className = "tag error"
  }
  renderTransport()
  renderOperations()
}

function statusLine(result) {
  const receipt = result.receipt
    ? `回执 ${result.receipt.receipt_id} · ${result.receipt.kind} · digest ${String(result.receipt.digest).slice(0, 12)}`
    : "无回执（计划或未执行）"
  const verdict = {
    ACCEPTED: "已写入并读回",
    PLANNED: "只是计划，未写入",
    REFUSED: "被拒绝",
    NEEDS_HUMAN: "等待人工门",
    NOT_IMPLEMENTED: "后端未实现",
    READBACK_MISMATCH: "写入未能读回",
    FAILED: "失败",
  }[result.status] || result.status
  return [
    `状态 ${result.status} · ${verdict}`,
    `原因 ${result.reason_code} · ${result.reason}`,
    `证据等级 ${result.evidence_level}`,
    receipt,
    result.next_action ? `下一步 ${result.next_action}` : "下一步 UNKNOWN",
  ].join("\n")
}

function renderReadback(result) {
  const line = el("readback")
  if (!result || !result.readback) {
    line.hidden = true
    line.textContent = ""
    return
  }
  const record = result.readback
  const where = `?view=work&taskId=${encodeURIComponent(record.taskId || "")}`
  line.textContent = record.replayed
    ? `重放到已存在的记录 ${record.taskId}（状态 ${record.status}）。在 Observer 的 Work 泳道用 ${where} 读回。`
    : `读回记录 ${record.taskId}：项目 ${record.projectId} · 状态 ${record.status} · checkpoint ${record.checkpointPresent ? `键 ${record.checkpointKeys.join("/")}` : "无"}。在 Observer 的 Work 泳道用 ${where} 读回。`
  line.hidden = false
}

function buildRequest(form) {
  const taskId = el("task-id").value.trim()
  return {
    schema_version: "worklab/control-operation/v1",
    operation: "work-unit.create",
    project_id: el("project-id").value.trim(),
    task_id: taskId,
    revision: null,
    attempt: null,
    scope: {
      boundaries: [el("boundary").value.trim()].filter(Boolean),
      granted_by: el("granted-by").value.trim(),
    },
    expected_version: null,
    idempotency_key: state.idempotencyKey || newIdempotencyKey(taskId),
    actor: "control-shell",
    // The contract demands an RFC3339 instant; a clock that is unavailable is not a licence to send "".
    requested_at: new Date().toISOString(),
    payload: { goal: el("goal").value.trim() },
  }
}

async function submit(request) {
  el("pending").hidden = false
  el("submit").disabled = true
  el("result").textContent = "提交中 · RUNNING（完成与否由后端回执与读回决定）"
  try {
    const response = await fetch("/api/control/operations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    })
    const result = await response.json().catch(() => ({ status: "FAILED", reason_code: "UNPARSEABLE_ANSWER",
      reason: `HTTP ${response.status} 的响应不是 JSON`, evidence_level: "NO_EVIDENCE" }))
    el("result").textContent = statusLine(result)
    renderReadback(result)
    if (result.status === "ACCEPTED" && !result.readback.replayed) {
      // one record keeps one identity: after a verified create, the same click must not silently replay
      state.idempotencyKey = newIdempotencyKey(request.task_id)
      el("idem").textContent = `idempotency ${state.idempotencyKey}`
    }
  } catch (error) {
    el("result").textContent = `状态 FAILED · 传输失败\n原因 ${error.message}\n证据等级 NO_EVIDENCE\n下一步 确认控制服务仍在运行（本页由它提供服务）`
    el("readback").hidden = true
  } finally {
    el("pending").hidden = true
    el("submit").disabled = false
  }
}

function main() {
  state.idempotencyKey = newIdempotencyKey(el("task-id").value.trim())
  el("idem").textContent = `idempotency ${state.idempotencyKey}`
  el("regen").addEventListener("click", () => {
    state.idempotencyKey = newIdempotencyKey(el("task-id").value.trim())
    el("idem").textContent = `idempotency ${state.idempotencyKey}`
  })
  el("task-id").addEventListener("input", () => {
    state.idempotencyKey = newIdempotencyKey(el("task-id").value.trim())
    el("idem").textContent = `idempotency ${state.idempotencyKey}`
  })
  el("create-form").addEventListener("submit", (event) => {
    event.preventDefault()
    void submit(buildRequest(event.target))
  })
  void loadDescriptor()
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", main)
} else {
  main()
}
