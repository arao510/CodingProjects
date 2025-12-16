import React, { useState } from "react";

export default function ThresholdPanel() {
  const [sshValue, setSshValue] = useState("");
  const [icmpValue, setIcmpValue] = useState("");
  const [arpValue, setArpValue] = useState("");
  const [portscanValue, setPortscanValue] = useState("");

  async function updateThreshold(detector, value) {
    if (!value) return alert("Please enter a value.");

    const res = await fetch("http://127.0.0.1:8080/set_threshold", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        detector_name: detector,
        new_value: parseInt(value),
      }),
    });

    const data = await res.json();
    if (data.status === "ok") {
      alert(`Updated ${detector.toUpperCase()} threshold successfully!`);
    } else {
      alert("Error updating threshold.");
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">Detection Thresholds</div>
      </div>

      <div className="settings-group">
        <label className="settings-label">SSH Threshold (attempts/sec)</label>
        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="number"
            value={sshValue}
            onChange={(e) => setSshValue(e.target.value)}
            className="settings-input"
            placeholder="e.g., 5"
            min="1"
          />
          <button
            onClick={() => updateThreshold("ssh", sshValue)}
            className="btn"
            style={{ width: "auto", padding: "10px 20px" }}
          >
            Update
          </button>
        </div>
      </div>

      <div className="settings-group">
        <label className="settings-label">ICMP Threshold (packets/sec)</label>
        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="number"
            value={icmpValue}
            onChange={(e) => setIcmpValue(e.target.value)}
            className="settings-input"
            placeholder="e.g., 50"
            min="1"
          />
          <button
            onClick={() => updateThreshold("icmp", icmpValue)}
            className="btn"
            style={{ width: "auto", padding: "10px 20px" }}
          >
            Update
          </button>
        </div>
      </div>

      <div className="settings-group">
        <label className="settings-label">ARP Threshold (attempts/sec)</label>
        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="number"
            value={arpValue}
            onChange={(e) => setArpValue(e.target.value)}
            className="settings-input"
            placeholder="e.g., 10"
            min="1"
          />
          <button
            onClick={() => updateThreshold("arp", arpValue)}
            className="btn"
            style={{ width: "auto", padding: "10px 20px" }}
          >
            Update
          </button>
        </div>
      </div>

      <div className="settings-group">
        <label className="settings-label">Port Scan Threshold (scans/sec)</label>
        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="number"
            value={portscanValue}
            onChange={(e) => setPortscanValue(e.target.value)}
            className="settings-input"
            placeholder="e.g., 10"
            min="1"
          />
          <button
            onClick={() => updateThreshold("portscan", portscanValue)}
            className="btn"
            style={{ width: "auto", padding: "10px 20px" }}
          >
            Update
          </button>
        </div>
      </div>
    </div>
  );
}