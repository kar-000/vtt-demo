import React, { useState } from "react";
import "./AttacksSection.css";

export default function AttacksSection({
  character,
  onUpdateCharacter,
  onRollDice,
  canEdit,
}) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    attack_bonus: 0,
    damage_dice: "",
    damage_type: "",
  });

  const attacks = character.attacks || [];

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

  return (
    <div className="attacks-section">
      <div className="section-header">
        <h3>Attacks & Spells</h3>
        {canEdit && !isAdding && editingIndex === null && (
          <button onClick={handleStartAdd} className="btn btn-primary btn-sm">
            + Add Attack
          </button>
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
    </div>
  );
}
