import React, { useState } from "react";
import { useGame } from "../contexts/GameContext";
import { useAuth } from "../contexts/AuthContext";
import "./InitiativeTracker.css";

export default function InitiativeTracker() {
  const { user } = useAuth();
  const {
    characters,
    initiative,
    startCombat,
    addCombatant,
    removeCombatant,
    rollInitiativeFor,
    rollAllInitiative,
    nextTurn,
    previousTurn,
    endCombat,
  } = useGame();

  const [showAddNPC, setShowAddNPC] = useState(false);
  const [npcName, setNpcName] = useState("");
  const [npcInitiative, setNpcInitiative] = useState("");

  const isDM = user?.is_dm;

  const handleStartCombat = () => {
    const characterIds = characters.map((c) => c.id);
    startCombat(characterIds);
  };

  const handleAddNPC = () => {
    if (!npcName.trim()) return;
    const initValue = npcInitiative ? parseInt(npcInitiative, 10) : null;
    addCombatant(npcName.trim(), initValue);
    setNpcName("");
    setNpcInitiative("");
    setShowAddNPC(false);
  };

  const getCurrentCombatant = () => {
    if (initiative.combatants.length === 0) return null;
    return initiative.combatants[initiative.current_turn_index];
  };

  const currentCombatant = getCurrentCombatant();

  // Collapsed state when no combat
  if (!initiative.active) {
    return (
      <div className="initiative-tracker initiative-collapsed">
        <div className="initiative-header">
          <h3>Initiative</h3>
          {isDM && (
            <button
              onClick={handleStartCombat}
              className="btn btn-primary btn-sm"
            >
              Start Combat
            </button>
          )}
        </div>
        {!isDM && <p className="no-combat-msg">No active combat</p>}
      </div>
    );
  }

  return (
    <div className="initiative-tracker">
      <div className="initiative-header">
        <h3>Initiative</h3>
        <div className="round-display">Round {initiative.round}</div>
      </div>

      {/* Turn Controls */}
      {isDM && (
        <div className="turn-controls">
          <button
            onClick={previousTurn}
            className="btn btn-secondary btn-sm"
            title="Previous Turn"
          >
            &lt;
          </button>
          <span className="turn-label">
            {currentCombatant ? currentCombatant.name : "—"}
          </span>
          <button
            onClick={nextTurn}
            className="btn btn-secondary btn-sm"
            title="Next Turn"
          >
            &gt;
          </button>
        </div>
      )}

      {/* Combatants List */}
      <div className="combatants-list">
        {initiative.combatants.map((combatant, index) => (
          <div
            key={combatant.id}
            className={`combatant-item ${index === initiative.current_turn_index ? "active-turn" : ""} ${combatant.type}`}
          >
            <div className="combatant-initiative">
              {combatant.initiative !== null ? combatant.initiative : "—"}
            </div>
            <div className="combatant-info">
              <span className="combatant-name">{combatant.name}</span>
              {combatant.type === "npc" && (
                <span className="combatant-type">NPC</span>
              )}
            </div>
            <div className="combatant-actions">
              {isDM && combatant.initiative === null && (
                <button
                  onClick={() => rollInitiativeFor(combatant.id)}
                  className="btn-icon"
                  title="Roll Initiative"
                >
                  🎲
                </button>
              )}
              {isDM && (
                <button
                  onClick={() => removeCombatant(combatant.id)}
                  className="btn-icon btn-danger"
                  title="Remove"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* DM Actions */}
      {isDM && (
        <div className="initiative-actions">
          {initiative.combatants.some((c) => c.initiative === null) && (
            <button
              onClick={rollAllInitiative}
              className="btn btn-secondary btn-sm"
            >
              Roll All
            </button>
          )}
          <button
            onClick={() => setShowAddNPC(!showAddNPC)}
            className="btn btn-secondary btn-sm"
          >
            + NPC
          </button>
          <button onClick={endCombat} className="btn btn-danger btn-sm">
            End Combat
          </button>
        </div>
      )}

      {/* Add NPC Form */}
      {showAddNPC && isDM && (
        <div className="add-npc-form">
          <input
            type="text"
            placeholder="NPC Name"
            value={npcName}
            onChange={(e) => setNpcName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddNPC()}
          />
          <input
            type="number"
            placeholder="Init (optional)"
            value={npcInitiative}
            onChange={(e) => setNpcInitiative(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddNPC()}
          />
          <button onClick={handleAddNPC} className="btn btn-primary btn-sm">
            Add
          </button>
        </div>
      )}
    </div>
  );
}
