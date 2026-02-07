import React, { useState } from "react";
import { useGame } from "../contexts/GameContext";
import "./DiceRoller.css";

const DICE_TYPES = [4, 6, 8, 10, 12, 20, 100];

export default function DiceRoller() {
  const { rollDice, currentCharacter } = useGame();
  const [selectedDice, setSelectedDice] = useState(20);
  const [numDice, setNumDice] = useState(1);
  const [modifier, setModifier] = useState(0);
  const [rollingDice, setRollingDice] = useState(null);
  const [isCustomRolling, setIsCustomRolling] = useState(false);

  const handleRoll = () => {
    if (isCustomRolling) return;
    if (!currentCharacter) {
      alert("Please select a character first");
      return;
    }
    setIsCustomRolling(true);
    rollDice(selectedDice, numDice, modifier, "manual");
    setTimeout(() => setIsCustomRolling(false), 400);
  };

  const quickRoll = (diceType) => {
    if (rollingDice) return;
    if (!currentCharacter) {
      alert("Please select a character first");
      return;
    }
    setRollingDice(diceType);
    rollDice(diceType, 1, 0, "manual");
    setTimeout(() => setRollingDice(null), 400);
  };

  return (
    <div className="dice-roller">
      <h3>Dice Roller</h3>

      <div className="quick-roll-section">
        <div className="quick-roll-label">Quick Roll:</div>
        <div className="quick-roll-buttons">
          {DICE_TYPES.map((dice) => (
            <button
              key={dice}
              onClick={() => quickRoll(dice)}
              className={`dice-button dice-d${dice}${rollingDice === dice ? " rolling" : ""}`}
              title={`Roll 1d${dice}`}
            >
              <span className="dice-label">d{dice}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="custom-roll-section">
        <div className="custom-roll-label">Custom Roll:</div>

        <div className="roll-inputs">
          <div className="input-group">
            <label htmlFor="numDice">Number of Dice</label>
            <input
              id="numDice"
              type="number"
              min="1"
              max="100"
              value={numDice}
              onChange={(e) =>
                setNumDice(Math.max(1, parseInt(e.target.value) || 1))
              }
            />
          </div>

          <div className="input-group">
            <label htmlFor="diceType">Dice Type</label>
            <select
              id="diceType"
              value={selectedDice}
              onChange={(e) => setSelectedDice(parseInt(e.target.value))}
            >
              {DICE_TYPES.map((dice) => (
                <option key={dice} value={dice}>
                  d{dice}
                </option>
              ))}
            </select>
          </div>

          <div className="input-group">
            <label htmlFor="modifier">Modifier</label>
            <input
              id="modifier"
              type="number"
              value={modifier}
              onChange={(e) => setModifier(parseInt(e.target.value) || 0)}
            />
          </div>
        </div>

        <div className="roll-preview">
          Roll: {numDice}d{selectedDice}
          {modifier !== 0 && ` ${modifier >= 0 ? "+" : ""}${modifier}`}
        </div>

        <button
          onClick={handleRoll}
          className={`btn btn-primary roll-button${isCustomRolling ? " rolling" : ""}`}
        >
          Roll Dice
        </button>
      </div>
    </div>
  );
}
