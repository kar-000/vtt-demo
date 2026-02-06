import React from "react";
import { useGame } from "../contexts/GameContext";
import HPManager from "./HPManager";
import "./CharacterSheet.css";

const SKILLS = {
  acrobatics: { ability: "dexterity", label: "Acrobatics" },
  animal_handling: { ability: "wisdom", label: "Animal Handling" },
  arcana: { ability: "intelligence", label: "Arcana" },
  athletics: { ability: "strength", label: "Athletics" },
  deception: { ability: "charisma", label: "Deception" },
  history: { ability: "intelligence", label: "History" },
  insight: { ability: "wisdom", label: "Insight" },
  intimidation: { ability: "charisma", label: "Intimidation" },
  investigation: { ability: "intelligence", label: "Investigation" },
  medicine: { ability: "wisdom", label: "Medicine" },
  nature: { ability: "intelligence", label: "Nature" },
  perception: { ability: "wisdom", label: "Perception" },
  performance: { ability: "charisma", label: "Performance" },
  persuasion: { ability: "charisma", label: "Persuasion" },
  religion: { ability: "intelligence", label: "Religion" },
  sleight_of_hand: { ability: "dexterity", label: "Sleight of Hand" },
  stealth: { ability: "dexterity", label: "Stealth" },
  survival: { ability: "wisdom", label: "Survival" },
};

const SAVES = [
  "strength",
  "dexterity",
  "constitution",
  "intelligence",
  "wisdom",
  "charisma",
];

export default function CharacterSheet({ character }) {
  const { rollDice, updateHP, updateCharacter } = useGame();

  const getModifier = (score) => {
    return Math.floor((score - 10) / 2);
  };

  const formatModifier = (mod) => {
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  const handleAbilityCheck = (abilityName, modifier) => {
    rollDice(20, 1, modifier, "ability", `${abilityName.toUpperCase()} Check`);
  };

  const handleSavingThrow = (abilityName, modifier, proficient) => {
    const bonus = proficient
      ? modifier + character.proficiency_bonus
      : modifier;
    rollDice(20, 1, bonus, "save", `${abilityName.toUpperCase()} Save`);
  };

  const handleSkillCheck = (skillName, skillData) => {
    const abilityMod = character[`${skillData.ability}_modifier`];
    const proficiencyLevel = character.skills?.[skillName] || 0;
    const bonus = abilityMod + proficiencyLevel * character.proficiency_bonus;
    rollDice(20, 1, bonus, "skill", skillData.label);
  };

  const handleSkillProficiencyToggle = async (skillName, e) => {
    e.stopPropagation(); // Prevent skill check roll when clicking proficiency
    const currentLevel = character.skills?.[skillName] || 0;
    const newLevel = (currentLevel + 1) % 3; // Cycle: 0 -> 1 -> 2 -> 0

    const updatedSkills = {
      ...character.skills,
      [skillName]: newLevel,
    };

    try {
      await updateCharacter(character.id, { skills: updatedSkills });
    } catch (error) {
      console.error("Error updating skill proficiency:", error);
    }
  };

  const handleSaveProficiencyToggle = async (saveName, e) => {
    e.stopPropagation(); // Prevent save roll when clicking proficiency
    const currentProficiency =
      character.saving_throw_proficiencies?.[saveName] || false;

    const updatedSaves = {
      ...character.saving_throw_proficiencies,
      [saveName]: !currentProficiency,
    };

    try {
      await updateCharacter(character.id, {
        saving_throw_proficiencies: updatedSaves,
      });
    } catch (error) {
      console.error("Error updating save proficiency:", error);
    }
  };

  const handleUpdateHP = async (updateData) => {
    await updateHP(character.id, updateData);
  };

  return (
    <div className="character-sheet">
      {/* Header */}
      <div className="sheet-header">
        <div className="character-title">
          <h2>{character.name}</h2>
          <p>
            Level {character.level} {character.race} {character.character_class}
          </p>
        </div>
      </div>

      {/* Main Stats */}
      <div className="main-stats">
        <div className="stat-box">
          <div className="stat-label">AC</div>
          <div className="stat-value">{character.armor_class}</div>
        </div>
        <HPManager character={character} onUpdateHP={handleUpdateHP} />
        <div className="stat-box">
          <div className="stat-label">Speed</div>
          <div className="stat-value">{character.speed} ft</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Prof. Bonus</div>
          <div className="stat-value">+{character.proficiency_bonus}</div>
        </div>
      </div>

      {/* Ability Scores */}
      <div className="abilities-section">
        <h3>Ability Scores</h3>
        <div className="abilities-grid">
          {[
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
          ].map((ability) => {
            const score = character[ability];
            const modifier = character[`${ability}_modifier`];
            return (
              <div
                key={ability}
                className="ability-box clickable"
                onClick={() => handleAbilityCheck(ability, modifier)}
                title={`Click to roll ${ability} check`}
              >
                <div className="ability-name">
                  {ability.slice(0, 3).toUpperCase()}
                </div>
                <div className="ability-modifier">
                  {formatModifier(modifier)}
                </div>
                <div className="ability-score">{score}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Saving Throws */}
      <div className="saves-section">
        <h3>Saving Throws</h3>
        <div className="saves-list">
          {SAVES.map((save) => {
            const modifier = character[`${save}_modifier`];
            const proficient =
              character.saving_throw_proficiencies?.[save] || false;
            const bonus = proficient
              ? modifier + character.proficiency_bonus
              : modifier;
            return (
              <div
                key={save}
                className={`save-item clickable ${proficient ? "proficient" : ""}`}
                onClick={() => handleSavingThrow(save, modifier, proficient)}
                title={`Click to roll ${save} save`}
              >
                <span
                  className="save-prof save-prof-toggle"
                  onClick={(e) => handleSaveProficiencyToggle(save, e)}
                  title="Click to toggle proficiency"
                >
                  {proficient ? "●" : "○"}
                </span>
                <span className="save-bonus">{formatModifier(bonus)}</span>
                <span className="save-name">
                  {save.charAt(0).toUpperCase() + save.slice(1)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Skills */}
      <div className="skills-section">
        <h3>Skills</h3>
        <div className="skills-list">
          {Object.entries(SKILLS).map(([skillKey, skillData]) => {
            const abilityMod = character[`${skillData.ability}_modifier`];
            const proficiencyLevel = character.skills?.[skillKey] || 0;
            const bonus =
              abilityMod + proficiencyLevel * character.proficiency_bonus;
            return (
              <div
                key={skillKey}
                className={`skill-item clickable ${proficiencyLevel > 0 ? "proficient" : ""}`}
                onClick={() => handleSkillCheck(skillKey, skillData)}
                title={`Click to roll ${skillData.label}`}
              >
                <span
                  className="skill-prof skill-prof-toggle"
                  onClick={(e) => handleSkillProficiencyToggle(skillKey, e)}
                  title="Click to toggle proficiency (Not Proficient → Proficient → Expert)"
                >
                  {proficiencyLevel === 2
                    ? "◆"
                    : proficiencyLevel === 1
                      ? "●"
                      : "○"}
                </span>
                <span className="skill-bonus">{formatModifier(bonus)}</span>
                <span className="skill-name">{skillData.label}</span>
                <span className="skill-ability">
                  ({skillData.ability.slice(0, 3)})
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
