import React, { useState } from "react";

export default function EmailSettingsPanel() {
    const [email, setEmail] = useState("");

    const saveEmail = async () => {
        const res = await fetch("http://127.0.0.1:8080/api/set_email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });

        if (res.ok) {
            alert("Email saved!");
        } else {
            alert("Error saving email");
        }
    };

    return (
        <div className="panel">
            <h3>Email Alerts</h3>
            <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />
            <button onClick={saveEmail}>Save Email</button>
        </div>
    );
}

