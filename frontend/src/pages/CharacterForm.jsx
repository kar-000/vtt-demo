import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGame } from "../contexts/GameContext";
import "./CharacterForm.css";

const RACES = [
  "Human",
  "Elf",
  "Dwarf",
  "Halfling",
  "Dragonborn",
  "Gnome",
  "Half-Elf",
  "Half-Orc",
  "Tiefling",
];
const CLASSES = [
  "Barbarian",
  "Bard",
  "Cleric",
  "Druid",
  "Fighter",
  "Monk",
  "Paladin",
  "Ranger",
  "Rogue",
  "Sorcerer",
  "Warlock",
  "Wizard",
];

export default function CharacterForm() {
  const navigate = useNavigate();
  const { createCharacter } = useGame();

  const [formData, setFormData] = useState({
    name: "",
    race: "Human",
    character_class: "Fighter",
    level: 1,
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10,
    armor_class: 10,
    max_hp: 10,
    current_hp: 10,
    speed: 30,
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === "name" || name === "race" || name === "character_class"
          ? value
          : Number(value),
    }));
  };

  const calculateModifier = (score) => {
    return Math.floor((score - 10) / 2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await createCharacter(formData);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Failed to create character");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="character-form-page">
      <div className="character-form-container">
        <div className="form-header">
          <h1>Create New Character</h1>
          <button
            onClick={() => navigate("/dashboard")}
            className="btn btn-secondary"
          >
            Cancel
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="character-form">
          <section className="form-section">
            <h2>Basic Information</h2>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">Character Name *</label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="race">Race *</label>
                <select
                  id="race"
                  name="race"
                  value={formData.race}
                  onChange={handleChange}
                  required
                >
                  {RACES.map((race) => (
                    <option key={race} value={race}>
                      {race}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="character_class">Class *</label>
                <select
                  id="character_class"
                  name="character_class"
                  value={formData.character_class}
                  onChange={handleChange}
                  required
                >
                  {CLASSES.map((cls) => (
                    <option key={cls} value={cls}>
                      {cls}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="level">Level *</label>
                <input
                  id="level"
                  name="level"
                  type="number"
                  min="1"
                  max="20"
                  value={formData.level}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </section>

          <section className="form-section">
            <h2>Ability Scores</h2>
            <div className="ability-scores-grid">
              {[
                "strength",
                "dexterity",
                "constitution",
                "intelligence",
                "wisdom",
                "charisma",
              ].map((ability) => (
                <div key={ability} className="ability-score-group">
                  <label htmlFor={ability}>
                    {ability.charAt(0).toUpperCase() + ability.slice(1)}
                  </label>
                  <div className="ability-score-input">
                    <input
                      id={ability}
                      name={ability}
                      type="number"
                      min="1"
                      max="30"
                      value={formData[ability]}
                      onChange={handleChange}
                      required
                    />
                    <span className="modifier">
                      {calculateModifier(formData[ability]) >= 0 ? "+" : ""}
                      {calculateModifier(formData[ability])}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="form-section">
            <h2>Combat Stats</h2>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="armor_class">Armor Class *</label>
                <input
                  id="armor_class"
                  name="armor_class"
                  type="number"
                  min="1"
                  value={formData.armor_class}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="max_hp">Max HP *</label>
                <input
                  id="max_hp"
                  name="max_hp"
                  type="number"
                  min="1"
                  value={formData.max_hp}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="current_hp">Current HP *</label>
                <input
                  id="current_hp"
                  name="current_hp"
                  type="number"
                  min="0"
                  value={formData.current_hp}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="speed">Speed *</label>
                <input
                  id="speed"
                  name="speed"
                  type="number"
                  min="0"
                  value={formData.speed}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
          </section>

          <div className="form-actions">
            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? "Creating..." : "Create Character"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
