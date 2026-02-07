import React from "react";
import { useGame } from "../contexts/GameContext";
import "./RollLog.css";

export default function RollLog() {
  const { rollLog } = useGame();

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const getRollTypeColor = (rollType) => {
    switch (rollType) {
      case "ability":
        return "#667eea";
      case "skill":
        return "#4caf50";
      case "save":
        return "#ff9800";
      case "attack":
        return "#f44336";
      case "manual":
        return "#9c27b0";
      default:
        return "#666";
    }
  };

  const formatRollDetails = (roll) => {
    const rollsStr = roll.rolls.join(" + ");
    const modStr =
      roll.modifier !== 0
        ? ` ${roll.modifier >= 0 ? "+" : ""}${roll.modifier}`
        : "";
    return `${roll.num_dice}d${roll.dice_type} (${rollsStr})${modStr}`;
  };

  return (
    <div className="roll-log">
      <h3>Roll Log</h3>

      {rollLog.length === 0 ? (
        <div className="empty-log">
          <p>No rolls yet. Start rolling!</p>
        </div>
      ) : (
        <div className="log-entries">
          {rollLog.map((entry, index) => (
            <div
              key={index}
              className={`log-entry ${entry.type === "chat" ? "chat-entry" : ""}`}
            >
              <div className="log-header">
                <span className="character-name">
                  {entry.character_name || entry.username}
                </span>
                <span className="roll-time">{formatTime(entry.timestamp)}</span>
              </div>
              {entry.type === "chat" ? (
                <div className="chat-message">{entry.message}</div>
              ) : (
                <>
                  {entry.label && (
                    <div
                      className="roll-label"
                      style={{ color: getRollTypeColor(entry.roll_type) }}
                    >
                      {entry.label}
                    </div>
                  )}
                  <div className="roll-details">{formatRollDetails(entry)}</div>
                  <div className="roll-total">
                    Total: <span className="total-value">{entry.total}</span>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
