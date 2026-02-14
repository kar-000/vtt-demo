import React, { useState, useRef, useEffect } from "react";
import conditions from "../data/srd-conditions.json";
import "./ConditionManager.css";

export default function ConditionManager({
  combatant,
  onAddCondition,
  onRemoveCondition,
  isDM,
}) {
  const [showPicker, setShowPicker] = useState(false);
  const [durationInput, setDurationInput] = useState("");
  const [durationType, setDurationType] = useState("indefinite");
  const [pickerPos, setPickerPos] = useState({ top: 0, left: 0 });
  const addBtnRef = useRef(null);
  const pickerRef = useRef(null);

  // Close picker on outside click
  useEffect(() => {
    if (!showPicker) return;
    const handleClick = (e) => {
      if (
        pickerRef.current &&
        !pickerRef.current.contains(e.target) &&
        addBtnRef.current &&
        !addBtnRef.current.contains(e.target)
      ) {
        setShowPicker(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showPicker]);

  const activeConditions = combatant.conditions || [];

  const handleAdd = (condition) => {
    const duration =
      durationType === "rounds" && durationInput
        ? parseInt(durationInput)
        : null;

    onAddCondition(combatant.id, {
      name: condition.name,
      duration,
      duration_type: durationType,
    });

    setShowPicker(false);
    setDurationInput("");
    setDurationType("indefinite");
  };

  const availableConditions = conditions.filter(
    (c) => !activeConditions.some((ac) => ac.name === c.name),
  );

  return (
    <div className="condition-manager">
      {/* Active condition badges */}
      <div className="condition-badges">
        {activeConditions.map((cond) => {
          const condData = conditions.find((c) => c.name === cond.name);
          return (
            <span
              key={cond.name}
              className="condition-badge"
              style={{ backgroundColor: condData?.color || "#666" }}
              title={`${cond.name}${cond.duration ? ` (${cond.duration} rounds)` : ""}${cond.source ? ` - ${cond.source}` : ""}\n${condData?.description || ""}`}
            >
              <span className="condition-icon">{condData?.icon || "?"}</span>
              <span className="condition-name">{cond.name}</span>
              {cond.duration_type === "rounds" && cond.duration != null && (
                <span className="condition-duration">{cond.duration}</span>
              )}
              {isDM && (
                <button
                  className="condition-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveCondition(combatant.id, cond.name);
                  }}
                  title="Remove condition"
                >
                  ×
                </button>
              )}
            </span>
          );
        })}

        {isDM && (
          <button
            ref={addBtnRef}
            className="condition-add-btn"
            onClick={() => {
              if (!showPicker && addBtnRef.current) {
                const rect = addBtnRef.current.getBoundingClientRect();
                setPickerPos({ top: rect.bottom + 4, left: rect.left });
              }
              setShowPicker(!showPicker);
            }}
            title="Add condition"
          >
            +
          </button>
        )}
      </div>

      {/* Condition picker dropdown - fixed position to escape overflow containers */}
      {showPicker && isDM && (
        <div
          ref={pickerRef}
          className="condition-picker"
          style={{
            position: "fixed",
            top: pickerPos.top,
            left: pickerPos.left,
          }}
        >
          <div className="condition-picker-header">
            <span>Add Condition</span>
            <div className="duration-controls">
              <select
                value={durationType}
                onChange={(e) => setDurationType(e.target.value)}
              >
                <option value="indefinite">Indefinite</option>
                <option value="rounds">Rounds</option>
                <option value="concentration">Concentration</option>
              </select>
              {durationType === "rounds" && (
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={durationInput}
                  onChange={(e) => setDurationInput(e.target.value)}
                  placeholder="#"
                  className="duration-input"
                />
              )}
            </div>
          </div>
          <div className="condition-list">
            {availableConditions.map((cond) => (
              <button
                key={cond.name}
                className="condition-option"
                onClick={() => handleAdd(cond)}
                title={cond.description}
              >
                <span
                  className="condition-option-icon"
                  style={{ backgroundColor: cond.color }}
                >
                  {cond.icon}
                </span>
                <span className="condition-option-name">{cond.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
