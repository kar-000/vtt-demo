import { useState, useMemo } from "react";
import "./SpellsSection.css";
import srdSpells from "../data/srd-spells.json";
import classData from "../data/srd-class-data.json";

export default function SpellsSection({
  character,
  onUpdateCharacter,
  onRollDice,
  onPostToChat,
  canEdit,
}) {
  const [isAdding, setIsAdding] = useState(false);
  const [editingSpell, setEditingSpell] = useState(null);
  const [showSRDBrowser, setShowSRDBrowser] = useState(false);
  const [srdFilterLevel, setSRDFilterLevel] = useState("all");
  const [showAllClasses, setShowAllClasses] = useState(false);
  const [expandedSpells, setExpandedSpells] = useState({});
  const [formData, setFormData] = useState({
    name: "",
    level: 0,
    school: "",
    casting_time: "1 action",
    range: "",
    components: "",
    duration: "",
    description: "",
    damage_dice: "",
    damage_type: "",
    save_type: "",
    is_healing: false,
  });

  const spellData = character.spells || {};
  const spellSlots = spellData.spell_slots || {};
  const spellsKnown = spellData.spells_known || [];

  // Calculate spell save DC and attack bonus based on class
  const spellcastingCalcs = useMemo(() => {
    const charClass = classData[character.character_class];
    if (!charClass?.spellcaster) {
      return { ability: null, modifier: 0, saveDC: 0, attackBonus: 0 };
    }

    const abilityName = charClass.spellcasting_ability;
    const abilityScore = character[abilityName] || 10;
    const modifier = Math.floor((abilityScore - 10) / 2);
    const proficiency = character.proficiency_bonus || 2;

    return {
      ability: abilityName,
      modifier,
      saveDC: 8 + proficiency + modifier,
      attackBonus: proficiency + modifier,
    };
  }, [character]);

  // Use calculated values, falling back to stored values for manual override
  const spellSaveDC = spellData.spell_save_dc ?? spellcastingCalcs.saveDC;
  const spellAttackBonus =
    spellData.spell_attack_bonus ?? spellcastingCalcs.attackBonus;

  // Group spells by level
  const spellsByLevel = {};
  for (let i = 0; i <= 9; i++) {
    spellsByLevel[i] = spellsKnown.filter((spell) => spell.level === i);
  }

  const handleStartAdd = () => {
    setFormData({
      name: "",
      level: 0,
      school: "",
      casting_time: "1 action",
      range: "",
      components: "",
      duration: "",
      description: "",
      damage_dice: "",
      damage_type: "",
      save_type: "",
      is_healing: false,
    });
    setIsAdding(true);
    setEditingSpell(null);
  };

  const handleStartEdit = (spell) => {
    setFormData({ ...spell });
    setEditingSpell(spell);
    setIsAdding(false);
  };

  const toggleSpellExpanded = (spellKey) => {
    setExpandedSpells((prev) => ({
      ...prev,
      [spellKey]: !prev[spellKey],
    }));
  };

  const handleCancelEdit = () => {
    setIsAdding(false);
    setEditingSpell(null);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert("Spell name is required");
      return;
    }

    let updatedSpells;
    if (editingSpell) {
      // Edit existing
      updatedSpells = spellsKnown.map((s) =>
        s.name === editingSpell.name && s.level === editingSpell.level
          ? formData
          : s,
      );
    } else {
      // Add new
      updatedSpells = [...spellsKnown, formData];
    }

    const updatedSpellData = {
      ...spellData,
      spells_known: updatedSpells,
    };

    try {
      await onUpdateCharacter(character.id, { spells: updatedSpellData });
      handleCancelEdit();
    } catch (error) {
      console.error("Error saving spell:", error);
      alert("Failed to save spell");
    }
  };

  const handleDelete = async (spell) => {
    if (!window.confirm(`Are you sure you want to delete ${spell.name}?`)) {
      return;
    }

    const updatedSpells = spellsKnown.filter(
      (s) => !(s.name === spell.name && s.level === spell.level),
    );

    const updatedSpellData = {
      ...spellData,
      spells_known: updatedSpells,
    };

    try {
      await onUpdateCharacter(character.id, { spells: updatedSpellData });
    } catch (error) {
      console.error("Error deleting spell:", error);
      alert("Failed to delete spell");
    }
  };

  const handleCastSpell = (spell) => {
    if (spell.is_healing && spell.damage_dice) {
      // Healing spell
      const match = spell.damage_dice.match(/(\d+)d(\d+)/i);
      if (match) {
        const [_, count, sides] = match;
        onRollDice(
          `d${sides}`,
          parseInt(count),
          0,
          "healing",
          `${character.name} casts ${spell.name} (${spell.damage_dice} healing)`,
        );
      }
    } else if (spell.damage_dice) {
      // Damage spell
      const match = spell.damage_dice.match(/(\d+)d(\d+)/i);
      if (match) {
        const [_, count, sides] = match;
        const saveInfo = spell.save_type
          ? ` (DC ${spellSaveDC} ${spell.save_type} save)`
          : "";
        onRollDice(
          `d${sides}`,
          parseInt(count),
          0,
          "damage",
          `${character.name} casts ${spell.name} (${spell.damage_dice} ${spell.damage_type})${saveInfo}`,
        );
      }
    } else {
      // Non-damaging spell - post to chat instead
      handleShareSpell(spell);
    }
  };

  const handleShareSpell = (spell) => {
    if (!onPostToChat) return;

    const levelText = spell.level === 0 ? "Cantrip" : `Level ${spell.level}`;
    const parts = [
      `**${spell.name}** (${levelText}${spell.school ? ` ${spell.school}` : ""})`,
    ];

    if (spell.casting_time) parts.push(`Casting Time: ${spell.casting_time}`);
    if (spell.range) parts.push(`Range: ${spell.range}`);
    if (spell.duration) parts.push(`Duration: ${spell.duration}`);
    if (spell.components) parts.push(`Components: ${spell.components}`);
    if (spell.description) parts.push(spell.description);
    if (spell.damage_dice) {
      const dmgType = spell.is_healing ? "Healing" : "Damage";
      parts.push(`${dmgType}: ${spell.damage_dice} ${spell.damage_type || ""}`);
    }
    if (spell.save_type)
      parts.push(`Save: DC ${spellSaveDC} ${spell.save_type}`);

    onPostToChat(`${character.name} shares: ${parts.join(" | ")}`);
  };

  const handleSlotChange = async (level, current) => {
    const maxSlots = spellSlots[level]?.max || 0;
    const newCurrent = Math.max(0, Math.min(maxSlots, current));

    const updatedSlots = {
      ...spellSlots,
      [level]: { ...spellSlots[level], current: newCurrent },
    };

    const updatedSpellData = {
      ...spellData,
      spell_slots: updatedSlots,
    };

    try {
      await onUpdateCharacter(character.id, { spells: updatedSpellData });
    } catch (error) {
      console.error("Error updating spell slots:", error);
    }
  };

  const handleMaxSlotsChange = async (level, max) => {
    const newMax = Math.max(0, max);
    const current = Math.min(spellSlots[level]?.current || 0, newMax);

    const updatedSlots = {
      ...spellSlots,
      [level]: { current, max: newMax },
    };

    const updatedSpellData = {
      ...spellData,
      spell_slots: updatedSlots,
    };

    try {
      await onUpdateCharacter(character.id, { spells: updatedSpellData });
    } catch (error) {
      console.error("Error updating spell slots:", error);
    }
  };

  const handleAddSRDSpell = async (srdSpell) => {
    // Check if spell already exists
    const exists = spellsKnown.some(
      (s) => s.name === srdSpell.name && s.level === srdSpell.level,
    );
    if (exists) {
      alert(`${srdSpell.name} is already in your spell list!`);
      return;
    }

    const updatedSpells = [...spellsKnown, srdSpell];
    const updatedSpellData = {
      ...spellData,
      spells_known: updatedSpells,
    };

    try {
      await onUpdateCharacter(character.id, { spells: updatedSpellData });
    } catch (error) {
      console.error("Error adding SRD spell:", error);
      alert("Failed to add spell");
    }
  };

  // Filter SRD spells by level and class
  const filteredSRDSpells = srdSpells.filter((spell) => {
    // Filter by level
    const levelMatch =
      srdFilterLevel === "all" || spell.level === parseInt(srdFilterLevel);

    // Filter by class (unless showing all)
    const classMatch =
      showAllClasses ||
      !character.character_class ||
      spell.classes?.includes(character.character_class);

    return levelMatch && classMatch;
  });

  return (
    <div className="spells-section">
      <div className="section-header">
        <h3>Spellcasting</h3>
        {canEdit && !isAdding && !editingSpell && (
          <div className="header-buttons">
            <button
              onClick={() => setShowSRDBrowser(true)}
              className="btn btn-secondary btn-sm"
            >
              📖 Browse SRD Spells
            </button>
            <button onClick={handleStartAdd} className="btn btn-primary btn-sm">
              + Add Custom Spell
            </button>
          </div>
        )}
      </div>

      {/* Spell Stats */}
      <div className="spell-stats">
        <div className="stat-item">
          <label>
            Spell Save DC
            {spellcastingCalcs.ability && (
              <span className="stat-formula">
                (8 + Prof +{" "}
                {spellcastingCalcs.ability.slice(0, 3).toUpperCase()})
              </span>
            )}
          </label>
          <div className="stat-value">{spellSaveDC}</div>
        </div>
        <div className="stat-item">
          <label>
            Spell Attack
            {spellcastingCalcs.ability && (
              <span className="stat-formula">
                (Prof + {spellcastingCalcs.ability.slice(0, 3).toUpperCase()})
              </span>
            )}
          </label>
          <div className="stat-value">
            {spellAttackBonus >= 0 ? "+" : ""}
            {spellAttackBonus}
          </div>
        </div>
        {spellcastingCalcs.ability && (
          <div className="stat-item ability-info">
            <label>Spellcasting Ability</label>
            <div className="stat-value">
              {spellcastingCalcs.ability.charAt(0).toUpperCase() +
                spellcastingCalcs.ability.slice(1)}
              <span className="modifier">
                ({spellcastingCalcs.modifier >= 0 ? "+" : ""}
                {spellcastingCalcs.modifier})
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Spell Slots */}
      <div className="spell-slots">
        <h4>Spell Slots</h4>
        <div className="slots-grid">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((level) => {
            const slot = spellSlots[level] || { current: 0, max: 0 };
            if (slot.max === 0 && !canEdit) return null;

            return (
              <div key={level} className="slot-item">
                <span className="slot-level">Level {level}</span>
                <div className="slot-controls">
                  {canEdit ? (
                    <>
                      <input
                        type="number"
                        value={slot.current}
                        onChange={(e) =>
                          handleSlotChange(level, parseInt(e.target.value))
                        }
                        className="slot-input"
                        min="0"
                        max={slot.max}
                      />
                      <span className="slot-divider">/</span>
                      <input
                        type="number"
                        value={slot.max}
                        onChange={(e) =>
                          handleMaxSlotsChange(level, parseInt(e.target.value))
                        }
                        className="slot-input"
                        min="0"
                      />
                    </>
                  ) : (
                    <span className="slot-display">
                      {slot.current} / {slot.max}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Add/Edit Form */}
      {(isAdding || editingSpell) && (
        <div className="spell-form">
          <h4>{editingSpell ? "Edit Spell" : "Add Spell"}</h4>
          <div className="form-row">
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="Fireball"
              />
            </div>
            <div className="form-group">
              <label>Level *</label>
              <select
                value={formData.level}
                onChange={(e) =>
                  setFormData({ ...formData, level: parseInt(e.target.value) })
                }
              >
                <option value={0}>Cantrip</option>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((lvl) => (
                  <option key={lvl} value={lvl}>
                    {lvl}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>School</label>
              <input
                type="text"
                value={formData.school}
                onChange={(e) =>
                  setFormData({ ...formData, school: e.target.value })
                }
                placeholder="Evocation"
              />
            </div>
            <div className="form-group">
              <label>Casting Time</label>
              <input
                type="text"
                value={formData.casting_time}
                onChange={(e) =>
                  setFormData({ ...formData, casting_time: e.target.value })
                }
                placeholder="1 action"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Range</label>
              <input
                type="text"
                value={formData.range}
                onChange={(e) =>
                  setFormData({ ...formData, range: e.target.value })
                }
                placeholder="150 feet"
              />
            </div>
            <div className="form-group">
              <label>Duration</label>
              <input
                type="text"
                value={formData.duration}
                onChange={(e) =>
                  setFormData({ ...formData, duration: e.target.value })
                }
                placeholder="Instantaneous"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group full-width">
              <label>Components</label>
              <input
                type="text"
                value={formData.components}
                onChange={(e) =>
                  setFormData({ ...formData, components: e.target.value })
                }
                placeholder="V, S, M (a tiny ball of bat guano and sulfur)"
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group full-width">
              <label>Description</label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="A bright streak flashes from your pointing finger..."
                rows={3}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={formData.is_healing}
                  onChange={(e) =>
                    setFormData({ ...formData, is_healing: e.target.checked })
                  }
                />
                Healing Spell
              </label>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Damage/Healing Dice</label>
              <input
                type="text"
                value={formData.damage_dice}
                onChange={(e) =>
                  setFormData({ ...formData, damage_dice: e.target.value })
                }
                placeholder="8d6"
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
                placeholder="fire"
              />
            </div>
            <div className="form-group">
              <label>Save Type</label>
              <input
                type="text"
                value={formData.save_type}
                onChange={(e) =>
                  setFormData({ ...formData, save_type: e.target.value })
                }
                placeholder="dexterity"
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

      {/* Spells List */}
      <div className="spells-list">
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((level) => {
          const spells = spellsByLevel[level];
          if (spells.length === 0) return null;

          return (
            <div key={level} className="spell-level-group">
              <h4 className="spell-level-header">
                {level === 0 ? "Cantrips" : `Level ${level} Spells`}
              </h4>
              <div className="spell-cards">
                {spells.map((spell, index) => {
                  const spellKey = `${spell.name}-${spell.level}-${index}`;
                  const isExpanded = expandedSpells[spellKey];

                  return (
                    <div
                      key={spellKey}
                      className={`spell-card ${isExpanded ? "expanded" : "collapsed"}`}
                    >
                      <div
                        className="spell-header clickable"
                        onClick={() => toggleSpellExpanded(spellKey)}
                      >
                        <div className="spell-title">
                          <span className="expand-icon">
                            {isExpanded ? "▼" : "▶"}
                          </span>
                          <h5>{spell.name}</h5>
                          <span className="spell-meta">
                            {spell.school && (
                              <span className="spell-school">
                                {spell.school}
                              </span>
                            )}
                            {!isExpanded && spell.damage_dice && (
                              <span className="spell-dice-preview">
                                {spell.damage_dice}
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="spell-header-actions">
                          {!isExpanded && spell.damage_dice && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCastSpell(spell);
                              }}
                              className={`cast-button-mini ${spell.is_healing ? "healing" : "damage"}`}
                              title={`Cast: ${spell.damage_dice}`}
                            >
                              🎲
                            </button>
                          )}
                          {canEdit && (
                            <div className="spell-actions">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStartEdit(spell);
                                }}
                                className="btn-icon"
                                title="Edit spell"
                              >
                                ✏️
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDelete(spell);
                                }}
                                className="btn-icon"
                                title="Delete spell"
                              >
                                🗑️
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                      {isExpanded && (
                        <>
                          <div className="spell-details">
                            {spell.casting_time && (
                              <span>Casting Time: {spell.casting_time}</span>
                            )}
                            {spell.range && <span>Range: {spell.range}</span>}
                            {spell.duration && (
                              <span>Duration: {spell.duration}</span>
                            )}
                            {spell.components && (
                              <span>Components: {spell.components}</span>
                            )}
                          </div>
                          {spell.description && (
                            <p className="spell-description">
                              {spell.description}
                            </p>
                          )}
                          <div className="spell-buttons">
                            {spell.damage_dice && (
                              <button
                                onClick={() => handleCastSpell(spell)}
                                className={`cast-button ${spell.is_healing ? "healing" : "damage"}`}
                              >
                                <span className="cast-label">Cast</span>
                                <span className="cast-value">
                                  {spell.damage_dice} {spell.damage_type}
                                </span>
                              </button>
                            )}
                            <button
                              onClick={() => handleShareSpell(spell)}
                              className="share-button"
                              title="Share spell info to chat"
                            >
                              📜 Share
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
        {spellsKnown.length === 0 && !isAdding && !editingSpell && (
          <div className="empty-state">
            <p>No spells added yet.</p>
            {canEdit && <p>Add your first spell to get started!</p>}
          </div>
        )}
      </div>

      {/* SRD Spell Browser Modal */}
      {showSRDBrowser && (
        <div
          className="spell-browser-modal"
          onClick={() => setShowSRDBrowser(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>SRD 5.1 Spell Library</h3>
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
                  Filter by Level:
                  <select
                    value={srdFilterLevel}
                    onChange={(e) => setSRDFilterLevel(e.target.value)}
                  >
                    <option value="all">All Levels</option>
                    <option value="0">Cantrips</option>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((lvl) => (
                      <option key={lvl} value={lvl}>
                        Level {lvl}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={showAllClasses}
                    onChange={(e) => setShowAllClasses(e.target.checked)}
                  />
                  Show all classes
                </label>
              </div>
              <div className="filter-info">
                {!showAllClasses && character.character_class && (
                  <span className="class-filter">
                    Showing {character.character_class} spells
                  </span>
                )}
                <span className="spell-count">
                  {filteredSRDSpells.length} spells
                </span>
              </div>
            </div>
            <div className="modal-body">
              {filteredSRDSpells.map((spell, index) => (
                <div
                  key={`srd-${spell.name}-${index}`}
                  className="srd-spell-card"
                >
                  <div className="srd-spell-header">
                    <div className="srd-spell-title">
                      <h4>{spell.name}</h4>
                      <span className="srd-spell-level">
                        {spell.level === 0 ? "Cantrip" : `Level ${spell.level}`}
                      </span>
                      {spell.school && (
                        <span className="srd-spell-school">{spell.school}</span>
                      )}
                    </div>
                    <button
                      onClick={() => handleAddSRDSpell(spell)}
                      className="btn btn-primary btn-sm"
                    >
                      + Add
                    </button>
                  </div>
                  <div className="srd-spell-meta">
                    {spell.casting_time && <span>⏱️ {spell.casting_time}</span>}
                    {spell.range && <span>📏 {spell.range}</span>}
                    {spell.duration && <span>⏳ {spell.duration}</span>}
                  </div>
                  {spell.components && (
                    <div className="srd-spell-components">
                      <strong>Components:</strong> {spell.components}
                    </div>
                  )}
                  <p className="srd-spell-description">{spell.description}</p>
                  {spell.damage_dice && (
                    <div className="srd-spell-damage">
                      <strong>
                        {spell.is_healing ? "Healing:" : "Damage:"}
                      </strong>{" "}
                      {spell.damage_dice} {spell.damage_type}
                      {spell.save_type && ` (${spell.save_type} save)`}
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
