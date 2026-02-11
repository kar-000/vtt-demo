import React, { useState, useRef, useEffect } from "react";
import { useGame } from "../contexts/GameContext";
import { useAuth } from "../contexts/AuthContext";
import CharacterPortrait from "./CharacterPortrait";
import MonsterStatBlock from "./MonsterStatBlock";
import srdMonsters from "../data/srd-monsters.json";
import "./InitiativeTracker.css";

export default function InitiativeTracker() {
  const { user } = useAuth();
  const {
    characters,
    currentCharacter,
    initiative,
    startCombat,
    addCombatant,
    removeCombatant,
    rollInitiativeFor,
    rollAllInitiative,
    nextTurn,
    previousTurn,
    endCombat,
    useAction,
    useBonusAction,
    useReaction,
    useMovement,
    resetActionEconomy,
    autoTrackActions,
    setAutoTrackActions,
    rollDice,
  } = useGame();

  const [showAddNPC, setShowAddNPC] = useState(false);
  const [selectedMonster, setSelectedMonster] = useState("");
  const [customName, setCustomName] = useState("");
  const combatantRefs = useRef({});

  // Auto-scroll to current combatant when turn changes
  useEffect(() => {
    if (initiative.active && initiative.combatants.length > 0) {
      const currentCombatant =
        initiative.combatants[initiative.current_turn_index];
      if (currentCombatant && combatantRefs.current[currentCombatant.id]) {
        combatantRefs.current[currentCombatant.id].scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }
  }, [initiative.current_turn_index, initiative.active, initiative.combatants]);

  const isDM = user?.is_dm;

  const handleStartCombat = () => {
    const characterIds = characters.map((c) => c.id);
    startCombat(characterIds);
  };

  const handleAddNPC = () => {
    if (selectedMonster) {
      // Add from SRD monster list
      const monster = srdMonsters.monsters.find(
        (m) => m.name === selectedMonster,
      );
      if (monster) {
        const dexMod = monster.abilities
          ? Math.floor((monster.abilities.dex - 10) / 2)
          : 0;
        addCombatant({
          name: customName.trim() || monster.name,
          max_hp: monster.hit_points,
          armor_class: monster.armor_class,
          speed: monster.speed,
          attacks: monster.attacks || [],
          dex_mod: dexMod,
        });
      }
    } else if (customName.trim()) {
      // Add custom NPC with just a name
      addCombatant({ name: customName.trim() });
    }
    setSelectedMonster("");
    setCustomName("");
    setShowAddNPC(false);
  };

  const getCurrentCombatant = () => {
    if (initiative.combatants.length === 0) return null;
    return initiative.combatants[initiative.current_turn_index];
  };

  const currentCombatant = getCurrentCombatant();

  // Check if current user can control the current combatant's action economy
  const canControlActionEconomy = () => {
    if (!currentCombatant) return false;
    if (isDM) return true;
    // Player can control their own character's turn
    if (
      currentCombatant.character_id &&
      currentCharacter?.id === currentCombatant.character_id
    ) {
      return true;
    }
    return false;
  };

  const handleUseMovement = (amount) => {
    if (currentCombatant) {
      useMovement(currentCombatant.id, amount);
    }
  };

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
        {initiative.combatants.map((combatant, index) => {
          const character =
            combatant.character_id &&
            characters.find((c) => c.id === combatant.character_id);
          return (
            <div
              key={combatant.id}
              ref={(el) => (combatantRefs.current[combatant.id] = el)}
              className={`combatant-item-wrapper ${index === initiative.current_turn_index ? "active-turn" : ""}`}
            >
              <div className={`combatant-item ${combatant.type}`}>
                {character ? (
                  <CharacterPortrait
                    character={character}
                    size="tiny"
                    editable={false}
                  />
                ) : (
                  <div className="combatant-npc-icon">👹</div>
                )}
                <div className="combatant-initiative">
                  {combatant.initiative !== null ? combatant.initiative : "—"}
                </div>
                <div className="combatant-info">
                  <span className="combatant-name">{combatant.name}</span>
                  {combatant.type === "npc" && (
                    <span className="combatant-type">NPC</span>
                  )}
                </div>
                {/* PC Stats - visible to all */}
                {character && (
                  <div className="combatant-pc-stats">
                    <span className="pc-ac" title="Armor Class">
                      {character.armor_class}
                    </span>
                    <div className="pc-hp-bar-container">
                      <div
                        className="pc-hp-bar"
                        style={{
                          width: `${Math.max(0, Math.min(100, (character.current_hp / character.max_hp) * 100))}%`,
                          backgroundColor:
                            character.current_hp <= character.max_hp * 0.25
                              ? "var(--color-danger)"
                              : character.current_hp <= character.max_hp * 0.5
                                ? "var(--color-warning)"
                                : "var(--color-success)",
                        }}
                      />
                      <span className="pc-hp-text">
                        {character.current_hp}/{character.max_hp}
                      </span>
                    </div>
                  </div>
                )}
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
              {/* Monster Stat Block for NPCs */}
              {isDM && combatant.type === "npc" && combatant.max_hp && (
                <MonsterStatBlock combatant={combatant} onRollDice={rollDice} />
              )}
            </div>
          );
        })}
      </div>

      {/* Action Economy for Current Turn */}
      {currentCombatant && currentCombatant.action_economy && (
        <div className="action-economy-section">
          <div className="action-economy-header">
            <span className="action-economy-title">
              {currentCombatant.name}'s Turn
            </span>
            <div className="action-economy-controls">
              <label
                className="auto-track-toggle"
                title="Auto-track actions when attacking or casting spells"
              >
                <input
                  type="checkbox"
                  checked={autoTrackActions}
                  onChange={(e) => setAutoTrackActions(e.target.checked)}
                />
                <span className="toggle-slider"></span>
                <span className="toggle-label">Auto</span>
              </label>
              {isDM && (
                <button
                  onClick={() => resetActionEconomy(currentCombatant.id)}
                  className="btn-icon btn-reset"
                  title="Reset all"
                >
                  ↻
                </button>
              )}
            </div>
          </div>
          <div className="action-economy-grid">
            <button
              className={`action-token ${currentCombatant.action_economy.action ? "available" : "used"}`}
              onClick={() =>
                canControlActionEconomy() && useAction(currentCombatant.id)
              }
              disabled={
                !canControlActionEconomy() ||
                !currentCombatant.action_economy.action
              }
              title={
                currentCombatant.action_economy.action
                  ? "Use Action"
                  : "Action Used"
              }
            >
              <span className="token-icon">⚔</span>
              <span className="token-label">Action</span>
            </button>
            <button
              className={`action-token ${currentCombatant.action_economy.bonus_action ? "available" : "used"}`}
              onClick={() =>
                canControlActionEconomy() && useBonusAction(currentCombatant.id)
              }
              disabled={
                !canControlActionEconomy() ||
                !currentCombatant.action_economy.bonus_action
              }
              title={
                currentCombatant.action_economy.bonus_action
                  ? "Use Bonus Action"
                  : "Bonus Action Used"
              }
            >
              <span className="token-icon">⚡</span>
              <span className="token-label">Bonus</span>
            </button>
            <button
              className={`action-token ${currentCombatant.action_economy.reaction ? "available" : "used"}`}
              onClick={() =>
                canControlActionEconomy() && useReaction(currentCombatant.id)
              }
              disabled={
                !canControlActionEconomy() ||
                !currentCombatant.action_economy.reaction
              }
              title={
                currentCombatant.action_economy.reaction
                  ? "Use Reaction"
                  : "Reaction Used"
              }
            >
              <span className="token-icon">🛡</span>
              <span className="token-label">Reaction</span>
            </button>
          </div>
          <div className="movement-tracker">
            <span className="movement-label">Movement:</span>
            <div className="movement-controls">
              <button
                className="btn-movement"
                onClick={() => handleUseMovement(5)}
                disabled={
                  !canControlActionEconomy() ||
                  currentCombatant.action_economy.movement < 5
                }
                title="Use 5 ft movement"
              >
                -5
              </button>
              <span className="movement-value">
                {currentCombatant.action_economy.movement}/
                {currentCombatant.action_economy.max_movement} ft
              </span>
              <button
                className="btn-movement"
                onClick={() => handleUseMovement(10)}
                disabled={
                  !canControlActionEconomy() ||
                  currentCombatant.action_economy.movement < 10
                }
                title="Use 10 ft movement"
              >
                -10
              </button>
            </div>
          </div>
        </div>
      )}

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
          <select
            className="monster-select"
            value={selectedMonster}
            onChange={(e) => setSelectedMonster(e.target.value)}
          >
            <option value="">-- Select Monster --</option>
            {srdMonsters.monsters.map((monster) => (
              <option key={monster.name} value={monster.name}>
                {monster.name} (CR {monster.challenge_rating})
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Custom name (optional)"
            value={customName}
            onChange={(e) => setCustomName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddNPC()}
          />
          <button
            onClick={handleAddNPC}
            className="btn btn-primary btn-sm"
            disabled={!selectedMonster && !customName.trim()}
          >
            Add
          </button>
        </div>
      )}
    </div>
  );
}
