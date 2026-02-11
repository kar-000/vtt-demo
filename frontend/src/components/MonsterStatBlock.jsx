import { useState } from "react";
import { useGame } from "../contexts/GameContext";
import "./MonsterStatBlock.css";

export default function MonsterStatBlock({ combatant, onRollDice }) {
  const { updateNPC } = useGame();
  const [isExpanded, setIsExpanded] = useState(false);
  const [hpAdjust, setHpAdjust] = useState("");

  const hpPercent = combatant.max_hp
    ? Math.round((combatant.current_hp / combatant.max_hp) * 100)
    : 100;

  const getHpColor = () => {
    if (hpPercent <= 25) return "var(--color-danger)";
    if (hpPercent <= 50) return "var(--color-warning, #f0ad4e)";
    return "var(--color-success)";
  };

  const handleDamage = () => {
    const amount = parseInt(hpAdjust, 10);
    if (!isNaN(amount) && amount > 0) {
      updateNPC(combatant.id, {
        current_hp: Math.max(0, combatant.current_hp - amount),
      });
      setHpAdjust("");
    }
  };

  const handleHeal = () => {
    const amount = parseInt(hpAdjust, 10);
    if (!isNaN(amount) && amount > 0) {
      updateNPC(combatant.id, {
        current_hp: Math.min(combatant.max_hp, combatant.current_hp + amount),
      });
      setHpAdjust("");
    }
  };

  const handleRollAttack = (attack) => {
    // Parse attack bonus and roll d20
    const bonus = attack.attack_bonus || 0;
    onRollDice(20, 1, bonus, "attack", `${combatant.name}: ${attack.name}`);
  };

  const handleRollDamage = (attack) => {
    // Parse damage dice like "2d6+3" or "1d8"
    const match = attack.damage_dice?.match(/(\d+)d(\d+)([+-]\d+)?/i);
    if (match) {
      const count = parseInt(match[1], 10);
      const sides = parseInt(match[2], 10);
      const bonus = match[3] ? parseInt(match[3], 10) : 0;
      onRollDice(
        sides,
        count,
        bonus,
        "damage",
        `${combatant.name}: ${attack.name} damage`,
      );
    }
  };

  if (!combatant.max_hp) {
    // Simple NPC without stats
    return null;
  }

  return (
    <div className={`monster-stat-block ${isExpanded ? "expanded" : ""}`}>
      <div
        className="monster-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="monster-quick-stats">
          <span className="monster-ac" title="Armor Class">
            AC {combatant.armor_class || 10}
          </span>
          <div className="monster-hp-bar-container">
            <div
              className="monster-hp-bar"
              style={{
                width: `${hpPercent}%`,
                backgroundColor: getHpColor(),
              }}
            />
            <span className="monster-hp-text">
              {combatant.current_hp}/{combatant.max_hp}
            </span>
          </div>
        </div>
        <span className="monster-expand-icon">{isExpanded ? "▼" : "▶"}</span>
      </div>

      {isExpanded && (
        <div className="monster-details">
          {/* HP Controls */}
          <div className="monster-hp-controls">
            <input
              type="number"
              className="hp-adjust-input"
              value={hpAdjust}
              onChange={(e) => setHpAdjust(e.target.value)}
              placeholder="HP"
              min="1"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              className="btn-hp btn-damage"
              onClick={(e) => {
                e.stopPropagation();
                handleDamage();
              }}
              disabled={!hpAdjust}
              title="Deal damage"
            >
              -
            </button>
            <button
              className="btn-hp btn-heal"
              onClick={(e) => {
                e.stopPropagation();
                handleHeal();
              }}
              disabled={!hpAdjust}
              title="Heal"
            >
              +
            </button>
          </div>

          {/* Attacks */}
          {combatant.attacks && combatant.attacks.length > 0 && (
            <div className="monster-attacks">
              <div className="attacks-label">Attacks:</div>
              {combatant.attacks.map((attack, idx) => (
                <div key={idx} className="monster-attack-row">
                  <span className="attack-name">{attack.name}</span>
                  <button
                    className="btn-roll btn-attack-roll"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRollAttack(attack);
                    }}
                    title={`Roll attack: +${attack.attack_bonus || 0}`}
                  >
                    +{attack.attack_bonus || 0}
                  </button>
                  <button
                    className="btn-roll btn-damage-roll"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRollDamage(attack);
                    }}
                    title={`Roll damage: ${attack.damage_dice}`}
                  >
                    {attack.damage_dice}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
