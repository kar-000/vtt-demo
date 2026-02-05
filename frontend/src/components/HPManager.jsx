import React, { useState } from "react";
import "./HPManager.css";

export default function HPManager({ character, onUpdateHP }) {
  const [damageAmount, setDamageAmount] = useState("");
  const [healAmount, setHealAmount] = useState("");
  const [tempHP, setTempHP] = useState(character.temp_hp || 0);
  const [showDeathSaves, setShowDeathSaves] = useState(
    character.current_hp === 0,
  );

  const handleDamage = async () => {
    const amount = parseInt(damageAmount);
    if (isNaN(amount) || amount <= 0) return;

    await onUpdateHP({
      type: "damage",
      amount: amount,
    });
    setDamageAmount("");
  };

  const handleHeal = async () => {
    const amount = parseInt(healAmount);
    if (isNaN(amount) || amount <= 0) return;

    await onUpdateHP({
      type: "healing",
      amount: amount,
    });
    setHealAmount("");
  };

  const handleTempHPChange = async () => {
    await onUpdateHP({
      type: "direct",
      data: { temp_hp: tempHP },
    });
  };

  const handleDeathSave = async (type) => {
    const newDeathSaves = { ...character.death_saves };
    if (type === "success") {
      newDeathSaves.successes = Math.min(3, newDeathSaves.successes + 1);
    } else {
      newDeathSaves.failures = Math.min(3, newDeathSaves.failures + 1);
    }

    await onUpdateHP({
      type: "direct",
      data: { death_saves: newDeathSaves },
    });

    // Check if stabilized or dead
    if (newDeathSaves.successes >= 3) {
      alert("Character stabilized!");
    } else if (newDeathSaves.failures >= 3) {
      alert("Character has died!");
    }
  };

  const resetDeathSaves = async () => {
    await onUpdateHP({
      type: "direct",
      data: { death_saves: { successes: 0, failures: 0 } },
    });
  };

  const hpPercentage = (character.current_hp / character.max_hp) * 100;

  return (
    <div className="hp-manager">
      {/* HP Bar */}
      <div className="hp-bar-container">
        <div className="hp-bar-bg">
          <div
            className="hp-bar-fill"
            style={{
              width: `${Math.max(0, Math.min(100, hpPercentage))}%`,
              backgroundColor:
                hpPercentage > 50
                  ? "#4caf50"
                  : hpPercentage > 25
                    ? "#ff9800"
                    : "#f44336",
            }}
          />
        </div>
        <div className="hp-display">
          <span className="hp-current">{character.current_hp}</span>
          <span className="hp-separator">/</span>
          <span className="hp-max">{character.max_hp}</span>
          {character.temp_hp > 0 && (
            <span className="hp-temp"> (+{character.temp_hp} temp)</span>
          )}
        </div>
      </div>

      {/* Damage/Healing Controls */}
      <div className="hp-controls">
        <div className="hp-control-group">
          <label>Damage</label>
          <input
            type="number"
            min="0"
            value={damageAmount}
            onChange={(e) => setDamageAmount(e.target.value)}
            placeholder="0"
          />
          <button onClick={handleDamage} disabled={!damageAmount}>
            Apply
          </button>
        </div>

        <div className="hp-control-group">
          <label>Healing</label>
          <input
            type="number"
            min="0"
            value={healAmount}
            onChange={(e) => setHealAmount(e.target.value)}
            placeholder="0"
          />
          <button onClick={handleHeal} disabled={!healAmount}>
            Apply
          </button>
        </div>

        <div className="hp-control-group">
          <label>Temp HP</label>
          <input
            type="number"
            min="0"
            value={tempHP}
            onChange={(e) => setTempHP(parseInt(e.target.value) || 0)}
          />
          <button onClick={handleTempHPChange}>Set</button>
        </div>
      </div>

      {/* Death Saves */}
      {character.current_hp === 0 && (
        <div className="death-saves">
          <h4>Death Saves</h4>
          <div className="death-saves-tracker">
            <div className="death-save-row">
              <span className="death-save-label">Successes:</span>
              <div className="death-save-boxes">
                {[1, 2, 3].map((i) => (
                  <div
                    key={`success-${i}`}
                    className={`death-save-box ${character.death_saves?.successes >= i ? "filled success" : ""}`}
                    onClick={() =>
                      character.death_saves?.successes < i &&
                      handleDeathSave("success")
                    }
                  >
                    {character.death_saves?.successes >= i ? "✓" : ""}
                  </div>
                ))}
              </div>
            </div>
            <div className="death-save-row">
              <span className="death-save-label">Failures:</span>
              <div className="death-save-boxes">
                {[1, 2, 3].map((i) => (
                  <div
                    key={`failure-${i}`}
                    className={`death-save-box ${character.death_saves?.failures >= i ? "filled failure" : ""}`}
                    onClick={() =>
                      character.death_saves?.failures < i &&
                      handleDeathSave("failure")
                    }
                  >
                    {character.death_saves?.failures >= i ? "✗" : ""}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <button onClick={resetDeathSaves} className="reset-death-saves">
            Reset Death Saves
          </button>
        </div>
      )}
    </div>
  );
}
