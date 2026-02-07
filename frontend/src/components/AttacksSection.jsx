import React, { useState } from "react";
import { useGame } from "../contexts/GameContext";
import "./AttacksSection.css";
import srdWeapons from "../data/srd-weapons.json";

export default function AttacksSection({
  character,
  onUpdateCharacter,
  onRollDice,
  canEdit,
}) {
  const { consumeActionEconomy } = useGame();
  const [isAdding, setIsAdding] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);
  const [showSRDBrowser, setShowSRDBrowser] = useState(false);
  const [srdFilterType, setSRDFilterType] = useState("all");
  const [formData, setFormData] = useState({
    name: "",
    attack_bonus: 0,
    damage_dice: "",
    damage_type: "",
  });

  const attacks = character.attacks || [];

  // Calculate ability modifier from score
  const getModifier = (score) => Math.floor((score - 10) / 2);

  // Calculate proficiency bonus from level
  const getProficiencyBonus = (level) => 2 + Math.floor((level - 1) / 4);

  // Calculate attack bonus based on weapon properties and character stats
  const calculateAttackBonus = (weapon) => {
    const strMod = getModifier(character.strength || 10);
    const dexMod = getModifier(character.dexterity || 10);
    const profBonus = getProficiencyBonus(character.level || 1);

    let abilityMod;

    // Check if ranged weapon
    if (weapon.weapon_type?.includes("Ranged")) {
      abilityMod = dexMod;
    }
    // Check if finesse weapon (can use STR or DEX, pick higher)
    else if (weapon.properties?.toLowerCase().includes("finesse")) {
      abilityMod = Math.max(strMod, dexMod);
    }
    // Default to STR for melee
    else {
      abilityMod = strMod;
    }

    return abilityMod + profBonus;
  };

  const handleStartAdd = () => {
    setFormData({
      name: "",
      attack_bonus: 0,
      damage_dice: "",
      damage_type: "",
    });
    setIsAdding(true);
    setEditingIndex(null);
  };

  const handleStartEdit = (index) => {
    setFormData({ ...attacks[index] });
    setEditingIndex(index);
    setIsAdding(false);
  };

  const handleCancelEdit = () => {
    setIsAdding(false);
    setEditingIndex(null);
    setFormData({
      name: "",
      attack_bonus: 0,
      damage_dice: "",
      damage_type: "",
    });
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert("Attack name is required");
      return;
    }

    let updatedAttacks;
    if (editingIndex !== null) {
      // Edit existing
      updatedAttacks = [...attacks];
      updatedAttacks[editingIndex] = formData;
    } else {
      // Add new
      updatedAttacks = [...attacks, formData];
    }

    try {
      await onUpdateCharacter(character.id, { attacks: updatedAttacks });
      handleCancelEdit();
    } catch (error) {
      console.error("Error saving attack:", error);
      alert("Failed to save attack");
    }
  };

  const handleDelete = async (index) => {
    if (!window.confirm("Are you sure you want to delete this attack?")) {
      return;
    }

    const updatedAttacks = attacks.filter((_, i) => i !== index);
    try {
      await onUpdateCharacter(character.id, { attacks: updatedAttacks });
    } catch (error) {
      console.error("Error deleting attack:", error);
      alert("Failed to delete attack");
    }
  };

  const handleRollAttack = (attack) => {
    const bonus = parseInt(attack.attack_bonus) || 0;
    const sign = bonus >= 0 ? "+" : "";
    onRollDice(
      "d20",
      1,
      bonus,
      "attack",
      `${character.name} attacks with ${attack.name} (1d20${sign}${bonus})`,
    );
    // Auto-consume action when attacking
    consumeActionEconomy("action");
  };

  const handleRollDamage = (attack) => {
    // Parse damage dice (e.g., "1d8", "2d6")
    const match = attack.damage_dice.match(/(\d+)d(\d+)/i);
    if (!match) {
      alert("Invalid damage dice format. Use format like '1d8' or '2d6'");
      return;
    }

    const [_, count, sides] = match;
    onRollDice(
      `d${sides}`,
      parseInt(count),
      0,
      "damage",
      `${character.name} rolls damage for ${attack.name} (${attack.damage_dice} ${attack.damage_type})`,
    );
  };

  const handleAddSRDWeapon = async (srdWeapon) => {
    // Check if weapon already exists
    const exists = attacks.some((a) => a.name === srdWeapon.name);
    if (exists) {
      alert(`${srdWeapon.name} is already in your attacks list!`);
      return;
    }

    // Calculate attack bonus based on character stats and weapon properties
    const attackBonus = calculateAttackBonus(srdWeapon);

    // Create attack from weapon with calculated bonus
    const newAttack = {
      name: srdWeapon.name,
      attack_bonus: attackBonus,
      damage_dice: srdWeapon.damage_dice,
      damage_type: srdWeapon.damage_type,
    };

    const updatedAttacks = [...attacks, newAttack];

    try {
      await onUpdateCharacter(character.id, { attacks: updatedAttacks });
    } catch (error) {
      console.error("Error adding SRD weapon:", error);
      alert("Failed to add weapon");
    }
  };

  // Filter SRD weapons by type
  const filteredSRDWeapons = srdWeapons.filter((weapon) => {
    if (srdFilterType === "all") return true;
    return weapon.weapon_type === srdFilterType;
  });

  return (
    <div className="attacks-section">
      <div className="section-header">
        <h3>Attacks</h3>
        {canEdit && !isAdding && editingIndex === null && (
          <div className="header-buttons">
            <button
              onClick={() => setShowSRDBrowser(true)}
              className="btn btn-secondary btn-sm"
            >
              ⚔️ Browse SRD Weapons
            </button>
            <button onClick={handleStartAdd} className="btn btn-primary btn-sm">
              + Add Custom Attack
            </button>
          </div>
        )}
      </div>

      {(isAdding || editingIndex !== null) && (
        <div className="attack-form">
          <div className="form-row">
            <div className="form-group">
              <label>Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="Longsword"
              />
            </div>
            <div className="form-group">
              <label>Attack Bonus</label>
              <input
                type="number"
                value={formData.attack_bonus}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    attack_bonus: parseInt(e.target.value) || 0,
                  })
                }
                placeholder="5"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Damage Dice</label>
              <input
                type="text"
                value={formData.damage_dice}
                onChange={(e) =>
                  setFormData({ ...formData, damage_dice: e.target.value })
                }
                placeholder="1d8"
              />
            </div>
            <div className="form-group">
              <label>Damage Type</label>
              <input
                type="text"
                value={formData.damage_type}
                onChange={(e) =>
                  setFormData({ ...formData, damage_type: e.target.value })
                }
                placeholder="slashing"
              />
            </div>
          </div>
          <div className="form-actions">
            <button onClick={handleSave} className="btn btn-primary">
              Save
            </button>
            <button onClick={handleCancelEdit} className="btn btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}

      {attacks.length === 0 && !isAdding && editingIndex === null ? (
        <div className="empty-state">
          <p>No attacks added yet.</p>
          {canEdit && <p>Add your first weapon or spell attack!</p>}
        </div>
      ) : (
        <div className="attacks-list">
          {attacks.map((attack, index) => (
            <div key={index} className="attack-card">
              <div className="attack-main">
                <div className="attack-header">
                  <h4>{attack.name}</h4>
                  {canEdit && (
                    <div className="attack-actions">
                      <button
                        onClick={() => handleStartEdit(index)}
                        className="btn-icon"
                        title="Edit attack"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDelete(index)}
                        className="btn-icon"
                        title="Delete attack"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
                <div className="attack-details">
                  <button
                    onClick={() => handleRollAttack(attack)}
                    className="roll-button attack-roll"
                    title="Roll attack"
                  >
                    <span className="roll-label">Attack</span>
                    <span className="roll-value">
                      {attack.attack_bonus >= 0 ? "+" : ""}
                      {attack.attack_bonus}
                    </span>
                  </button>
                  <button
                    onClick={() => handleRollDamage(attack)}
                    className="roll-button damage-roll"
                    title="Roll damage"
                  >
                    <span className="roll-label">Damage</span>
                    <span className="roll-value">
                      {attack.damage_dice} {attack.damage_type}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SRD Weapons Browser Modal */}
      {showSRDBrowser && (
        <div
          className="weapon-browser-modal"
          onClick={() => setShowSRDBrowser(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>SRD 5.1 Weapons Library</h3>
              <button
                onClick={() => setShowSRDBrowser(false)}
                className="close-btn"
              >
                ✕
              </button>
            </div>
            <div className="modal-filters">
              <div className="filter-row">
                <label>
                  Filter by Type:
                  <select
                    value={srdFilterType}
                    onChange={(e) => setSRDFilterType(e.target.value)}
                  >
                    <option value="all">All Weapons</option>
                    <option value="Simple Melee">Simple Melee</option>
                    <option value="Simple Ranged">Simple Ranged</option>
                    <option value="Martial Melee">Martial Melee</option>
                    <option value="Martial Ranged">Martial Ranged</option>
                  </select>
                </label>
              </div>
              <div className="filter-info">
                <span className="weapon-count">
                  {filteredSRDWeapons.length} weapons
                </span>
              </div>
            </div>
            <div className="modal-body">
              {filteredSRDWeapons.map((weapon, index) => (
                <div
                  key={`srd-${weapon.name}-${index}`}
                  className="srd-weapon-card"
                >
                  <div className="srd-weapon-header">
                    <div className="srd-weapon-title">
                      <h4>{weapon.name}</h4>
                      <span className="srd-weapon-type">
                        {weapon.weapon_type}
                      </span>
                    </div>
                    <button
                      onClick={() => handleAddSRDWeapon(weapon)}
                      className="btn btn-primary btn-sm"
                    >
                      + Add
                    </button>
                  </div>
                  <div className="srd-weapon-stats">
                    <span>
                      <strong>Attack:</strong> +{calculateAttackBonus(weapon)}
                    </span>
                    <span>
                      <strong>Damage:</strong> {weapon.damage_dice}{" "}
                      {weapon.damage_type}
                    </span>
                  </div>
                  {weapon.properties && (
                    <div className="srd-weapon-properties">
                      <strong>Properties:</strong> {weapon.properties}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
