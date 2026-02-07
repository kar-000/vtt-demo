import { useState, useMemo } from "react";
import classData from "../data/srd-class-data.json";
import "./LevelUpModal.css";

const ABILITY_NAMES = [
  "strength",
  "dexterity",
  "constitution",
  "intelligence",
  "wisdom",
  "charisma",
];

export default function LevelUpModal({
  character,
  onUpdateCharacter,
  onClose,
}) {
  const [step, setStep] = useState(1);
  const [selectedClass, setSelectedClass] = useState(character.character_class);
  const [isMulticlass, setIsMulticlass] = useState(false);
  const [hpChoice, setHpChoice] = useState(null); // 'roll' or 'average'
  const [hpRollResult, setHpRollResult] = useState(null);
  const [asiChoice, setAsiChoice] = useState(null); // '+2-one' or '+1-two'
  const [asiAbility1, setAsiAbility1] = useState("");
  const [asiAbility2, setAsiAbility2] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const newLevel = character.level + 1;
  const currentClassData = classData[selectedClass];

  // Calculate CON modifier
  const conModifier = Math.floor((character.constitution - 10) / 2);

  // Check if this level gets an ASI for the selected class
  const getsASI = useMemo(() => {
    if (!currentClassData) return false;
    return currentClassData.asi_levels.includes(newLevel);
  }, [currentClassData, newLevel]);

  // Calculate HP gain
  const averageHp = useMemo(() => {
    if (!currentClassData) return 0;
    return Math.floor(currentClassData.hit_die / 2) + 1 + conModifier;
  }, [currentClassData, conModifier]);

  const rolledHp = useMemo(() => {
    if (hpRollResult === null) return null;
    return Math.max(1, hpRollResult + conModifier);
  }, [hpRollResult, conModifier]);

  const hpGain = hpChoice === "average" ? averageHp : rolledHp;

  // Roll the hit die
  const handleRollHitDie = () => {
    const result = Math.floor(Math.random() * currentClassData.hit_die) + 1;
    setHpRollResult(result);
    setHpChoice("roll");
  };

  // Get new spell slots for casters
  const getNewSpellSlots = () => {
    if (!currentClassData?.spellcaster) return null;

    if (currentClassData.pact_magic) {
      // Warlock pact magic
      const pactInfo = currentClassData.pact_slots[newLevel.toString()];
      return { pact_magic: true, ...pactInfo };
    }

    const slots = currentClassData.spell_slots[newLevel.toString()];
    if (!slots) return null;

    // Convert array to spell_slots object format
    const slotObj = {};
    slots.forEach((count, index) => {
      if (count > 0) {
        slotObj[index + 1] = { current: count, max: count };
      }
    });
    return slotObj;
  };

  // Validate ASI selections
  const asiValid = useMemo(() => {
    if (!getsASI) return true;
    if (!asiChoice) return false;

    if (asiChoice === "+2-one") {
      if (!asiAbility1) return false;
      if (character[asiAbility1] >= 19) return false; // Can't go above 20
      return true;
    }

    if (asiChoice === "+1-two") {
      if (!asiAbility1 || !asiAbility2) return false;
      if (asiAbility1 === asiAbility2) return false;
      if (character[asiAbility1] >= 20) return false;
      if (character[asiAbility2] >= 20) return false;
      return true;
    }

    return false;
  }, [getsASI, asiChoice, asiAbility1, asiAbility2, character]);

  // Build the update payload
  const buildUpdatePayload = () => {
    const updates = {
      level: newLevel,
      max_hp: character.max_hp + hpGain,
      current_hp: character.current_hp + hpGain,
    };

    // Handle multiclass
    if (isMulticlass && selectedClass !== character.character_class) {
      // Store multiclass info - append to existing or create new
      const existingClasses = character.multiclass || {};
      updates.multiclass = {
        ...existingClasses,
        [selectedClass]: (existingClasses[selectedClass] || 0) + 1,
      };
      // Update the class display to show primary class
      // The character_class stays as the original class
    }

    // ASI updates
    if (getsASI && asiChoice) {
      if (asiChoice === "+2-one") {
        updates[asiAbility1] = character[asiAbility1] + 2;
      } else if (asiChoice === "+1-two") {
        updates[asiAbility1] = character[asiAbility1] + 1;
        updates[asiAbility2] = character[asiAbility2] + 1;
      }
    }

    // Spell slot updates for casters
    const newSlots = getNewSpellSlots();
    if (newSlots && !newSlots.pact_magic) {
      const existingSpells = character.spells || {};
      updates.spells = {
        ...existingSpells,
        spell_slots: Object.fromEntries(
          Object.entries(newSlots).map(([level, data]) => [
            level,
            {
              current:
                existingSpells.spell_slots?.[level]?.current ?? data.current,
              max: data.max,
            },
          ]),
        ),
      };
    }

    return updates;
  };

  const handleConfirm = async () => {
    if (!hpGain || (getsASI && !asiValid)) return;

    setIsSubmitting(true);
    try {
      const updates = buildUpdatePayload();
      await onUpdateCharacter(character.id, updates);
      onClose();
    } catch (error) {
      console.error("Error leveling up:", error);
      setIsSubmitting(false);
    }
  };

  const renderStep1 = () => (
    <div className="level-up-step">
      <h3>Choose Class for Level {newLevel}</h3>
      <p className="step-description">
        Level up in your current class or multiclass into a new one.
      </p>

      <div className="class-choice-section">
        <div
          className={`class-option ${!isMulticlass ? "selected" : ""}`}
          onClick={() => {
            setIsMulticlass(false);
            setSelectedClass(character.character_class);
          }}
        >
          <div className="class-option-header">
            <span className="class-name">{character.character_class}</span>
            <span className="class-tag">Current Class</span>
          </div>
          <div className="class-details">
            <span>
              Hit Die: d{classData[character.character_class]?.hit_die}
            </span>
          </div>
        </div>

        <div className="multiclass-divider">
          <span>or</span>
        </div>

        <div
          className={`class-option multiclass-option ${isMulticlass ? "selected" : ""}`}
          onClick={() => {
            setIsMulticlass(true);
            // Set default multiclass to first available class
            const availableClasses = Object.keys(classData).filter(
              (c) => c !== character.character_class,
            );
            if (
              availableClasses.length > 0 &&
              selectedClass === character.character_class
            ) {
              setSelectedClass(availableClasses[0]);
            }
          }}
        >
          <div className="class-option-header">
            <span className="class-name">Multiclass</span>
            <span className="class-tag">New Class</span>
          </div>
          {isMulticlass && (
            <div className="multiclass-select">
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                {Object.keys(classData)
                  .filter((c) => c !== character.character_class)
                  .map((className) => (
                    <option key={className} value={className}>
                      {className} (d{classData[className].hit_die})
                    </option>
                  ))}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="step-actions">
        <button className="btn btn-secondary" onClick={onClose}>
          Cancel
        </button>
        <button className="btn btn-primary" onClick={() => setStep(2)}>
          Continue
        </button>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="level-up-step">
      <h3>Increase Hit Points</h3>
      <p className="step-description">
        Choose how to calculate your HP increase for {selectedClass} (d
        {currentClassData?.hit_die}).
      </p>

      <div className="hp-choice-section">
        <div
          className={`hp-option ${hpChoice === "roll" ? "selected" : ""}`}
          onClick={handleRollHitDie}
        >
          <div className="hp-option-header">
            <span className="hp-method">Roll Hit Die</span>
            {hpRollResult !== null && (
              <span className="hp-result">
                Rolled: {hpRollResult} + {conModifier} CON = {rolledHp} HP
              </span>
            )}
          </div>
          <button className="roll-hit-die-btn" onClick={handleRollHitDie}>
            🎲 Roll d{currentClassData?.hit_die}
          </button>
        </div>

        <div className="hp-divider">
          <span>or</span>
        </div>

        <div
          className={`hp-option ${hpChoice === "average" ? "selected" : ""}`}
          onClick={() => setHpChoice("average")}
        >
          <div className="hp-option-header">
            <span className="hp-method">Take Average</span>
            <span className="hp-result">
              {Math.floor(currentClassData?.hit_die / 2) + 1} + {conModifier}{" "}
              CON = {averageHp} HP
            </span>
          </div>
          <div className="average-explanation">
            Fixed value: ({currentClassData?.hit_die}/2 + 1) + CON modifier
          </div>
        </div>
      </div>

      <div className="step-actions">
        <button className="btn btn-secondary" onClick={() => setStep(1)}>
          Back
        </button>
        <button
          className="btn btn-primary"
          disabled={!hpChoice}
          onClick={() => setStep(getsASI ? 3 : 4)}
        >
          Continue
        </button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="level-up-step">
      <h3>Ability Score Improvement</h3>
      <p className="step-description">
        At level {newLevel}, you gain an Ability Score Improvement.
      </p>

      <div className="asi-choice-section">
        <div
          className={`asi-option ${asiChoice === "+2-one" ? "selected" : ""}`}
          onClick={() => setAsiChoice("+2-one")}
        >
          <div className="asi-option-header">
            <span className="asi-method">+2 to One Ability</span>
          </div>
          {asiChoice === "+2-one" && (
            <div className="asi-select">
              <select
                value={asiAbility1}
                onChange={(e) => setAsiAbility1(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                <option value="">Select ability...</option>
                {ABILITY_NAMES.map((ability) => {
                  const current = character[ability];
                  const canIncrease = current <= 18;
                  return (
                    <option
                      key={ability}
                      value={ability}
                      disabled={!canIncrease}
                    >
                      {ability.charAt(0).toUpperCase() + ability.slice(1)} (
                      {current}
                      {canIncrease ? ` → ${current + 2}` : " - MAX"})
                    </option>
                  );
                })}
              </select>
            </div>
          )}
        </div>

        <div className="asi-divider">
          <span>or</span>
        </div>

        <div
          className={`asi-option ${asiChoice === "+1-two" ? "selected" : ""}`}
          onClick={() => setAsiChoice("+1-two")}
        >
          <div className="asi-option-header">
            <span className="asi-method">+1 to Two Abilities</span>
          </div>
          {asiChoice === "+1-two" && (
            <div className="asi-select-two">
              <select
                value={asiAbility1}
                onChange={(e) => setAsiAbility1(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                <option value="">First ability...</option>
                {ABILITY_NAMES.map((ability) => {
                  const current = character[ability];
                  const canIncrease = current < 20;
                  return (
                    <option
                      key={ability}
                      value={ability}
                      disabled={!canIncrease || ability === asiAbility2}
                    >
                      {ability.charAt(0).toUpperCase() + ability.slice(1)} (
                      {current}
                      {canIncrease ? ` → ${current + 1}` : " - MAX"})
                    </option>
                  );
                })}
              </select>
              <select
                value={asiAbility2}
                onChange={(e) => setAsiAbility2(e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                <option value="">Second ability...</option>
                {ABILITY_NAMES.map((ability) => {
                  const current = character[ability];
                  const canIncrease = current < 20;
                  return (
                    <option
                      key={ability}
                      value={ability}
                      disabled={!canIncrease || ability === asiAbility1}
                    >
                      {ability.charAt(0).toUpperCase() + ability.slice(1)} (
                      {current}
                      {canIncrease ? ` → ${current + 1}` : " - MAX"})
                    </option>
                  );
                })}
              </select>
            </div>
          )}
        </div>
      </div>

      <div className="step-actions">
        <button className="btn btn-secondary" onClick={() => setStep(2)}>
          Back
        </button>
        <button
          className="btn btn-primary"
          disabled={!asiValid}
          onClick={() => setStep(4)}
        >
          Continue
        </button>
      </div>
    </div>
  );

  const renderStep4 = () => {
    const newSlots = getNewSpellSlots();

    return (
      <div className="level-up-step">
        <h3>Confirm Level Up</h3>
        <p className="step-description">Review your changes before applying.</p>

        <div className="summary-section">
          <div className="summary-item">
            <span className="summary-label">Level</span>
            <span className="summary-value">
              {character.level} → {newLevel}
            </span>
          </div>

          {isMulticlass && selectedClass !== character.character_class && (
            <div className="summary-item multiclass-summary">
              <span className="summary-label">Multiclass</span>
              <span className="summary-value">+1 {selectedClass}</span>
            </div>
          )}

          <div className="summary-item">
            <span className="summary-label">Hit Points</span>
            <span className="summary-value">
              {character.max_hp} → {character.max_hp + hpGain}{" "}
              <span className="hp-gain">(+{hpGain})</span>
            </span>
          </div>

          {getsASI && asiChoice === "+2-one" && (
            <div className="summary-item">
              <span className="summary-label">Ability Score</span>
              <span className="summary-value">
                {asiAbility1.charAt(0).toUpperCase() + asiAbility1.slice(1)}:{" "}
                {character[asiAbility1]} → {character[asiAbility1] + 2}
              </span>
            </div>
          )}

          {getsASI && asiChoice === "+1-two" && (
            <>
              <div className="summary-item">
                <span className="summary-label">Ability Scores</span>
                <span className="summary-value">
                  {asiAbility1.charAt(0).toUpperCase() + asiAbility1.slice(1)}:{" "}
                  {character[asiAbility1]} → {character[asiAbility1] + 1}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label"></span>
                <span className="summary-value">
                  {asiAbility2.charAt(0).toUpperCase() + asiAbility2.slice(1)}:{" "}
                  {character[asiAbility2]} → {character[asiAbility2] + 1}
                </span>
              </div>
            </>
          )}

          {newSlots && !newSlots.pact_magic && (
            <div className="summary-item">
              <span className="summary-label">Spell Slots</span>
              <span className="summary-value spell-slots-summary">
                {Object.entries(newSlots).map(([level, data]) => (
                  <span key={level} className="slot-info">
                    Lvl {level}: {data.max}
                  </span>
                ))}
              </span>
            </div>
          )}

          {newSlots?.pact_magic && (
            <div className="summary-item">
              <span className="summary-label">Pact Slots</span>
              <span className="summary-value">
                {newSlots.slots} slot{newSlots.slots > 1 ? "s" : ""} at level{" "}
                {newSlots.level}
              </span>
            </div>
          )}
        </div>

        <div className="step-actions">
          <button
            className="btn btn-secondary"
            onClick={() => setStep(getsASI ? 3 : 2)}
          >
            Back
          </button>
          <button
            className="btn btn-primary confirm-btn"
            onClick={handleConfirm}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Leveling Up..." : "Confirm Level Up"}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="level-up-modal-overlay" onClick={onClose}>
      <div className="level-up-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Level Up: {character.name}</h2>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="step-indicator">
          <div className={`step-dot ${step >= 1 ? "active" : ""}`}>1</div>
          <div className="step-line" />
          <div className={`step-dot ${step >= 2 ? "active" : ""}`}>2</div>
          <div className="step-line" />
          <div
            className={`step-dot ${step >= 3 ? "active" : ""} ${!getsASI ? "skipped" : ""}`}
          >
            3
          </div>
          <div className="step-line" />
          <div className={`step-dot ${step >= 4 ? "active" : ""}`}>4</div>
        </div>

        <div className="modal-content">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}
        </div>
      </div>
    </div>
  );
}
