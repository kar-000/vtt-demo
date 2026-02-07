import { useState } from "react";
import { useGame } from "../contexts/GameContext";
import { useAuth } from "../contexts/AuthContext";
import HPManager from "./HPManager";
import AttacksSection from "./AttacksSection";
import SpellsSection from "./SpellsSection";
import LevelUpModal from "./LevelUpModal";
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

const ABILITY_INFO = {
  strength: {
    name: "Strength",
    abbr: "STR",
    description:
      "Physical power. Used for melee attacks, athletics, carrying capacity, and breaking things.",
    skills: ["Athletics"],
    commonUses: [
      "Melee attack/damage",
      "Grappling",
      "Shoving",
      "Lifting/carrying",
      "Climbing",
      "Swimming",
    ],
  },
  dexterity: {
    name: "Dexterity",
    abbr: "DEX",
    description:
      "Agility and reflexes. Used for ranged attacks, initiative, AC, and finesse weapons.",
    skills: ["Acrobatics", "Sleight of Hand", "Stealth"],
    commonUses: [
      "Ranged attacks",
      "Initiative",
      "AC bonus",
      "Finesse weapons",
      "Dodging effects",
    ],
  },
  constitution: {
    name: "Constitution",
    abbr: "CON",
    description:
      "Endurance and health. Determines hit points and concentration. No skills use Constitution.",
    skills: [],
    commonUses: [
      "Hit point bonus",
      "Concentration saves",
      "Enduring harsh conditions",
      "Resisting poison",
    ],
  },
  intelligence: {
    name: "Intelligence",
    abbr: "INT",
    description:
      "Memory, reasoning, and learning. Used by wizards and for knowledge checks.",
    skills: ["Arcana", "History", "Investigation", "Nature", "Religion"],
    commonUses: [
      "Wizard spellcasting",
      "Recalling lore",
      "Deduction",
      "Identifying spells/items",
    ],
  },
  wisdom: {
    name: "Wisdom",
    abbr: "WIS",
    description:
      "Awareness and intuition. Used by clerics, druids, and rangers for spellcasting.",
    skills: [
      "Animal Handling",
      "Insight",
      "Medicine",
      "Perception",
      "Survival",
    ],
    commonUses: [
      "Cleric/Druid spellcasting",
      "Spotting hidden things",
      "Sensing motives",
      "Resisting charms",
    ],
  },
  charisma: {
    name: "Charisma",
    abbr: "CHA",
    description:
      "Force of personality. Used by bards, paladins, sorcerers, and warlocks for spellcasting.",
    skills: ["Deception", "Intimidation", "Performance", "Persuasion"],
    commonUses: [
      "Bard/Sorcerer spellcasting",
      "Social interactions",
      "Leadership",
      "Banishing fiends",
    ],
  },
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
  const { rollDice, updateHP, updateCharacter, postToChat } = useGame();
  const { user } = useAuth();
  const [showLevelUpModal, setShowLevelUpModal] = useState(false);
  const [expandedAbility, setExpandedAbility] = useState(null);

  // Check if DM is viewing another player's character
  const isDMViewingPlayer = user?.is_dm && character.owner_id !== user.id;

  // Can level up if not at max level (20)
  const canLevelUp = character.level < 20;

  const getModifier = (score) => {
    return Math.floor((score - 10) / 2);
  };

  const formatModifier = (mod) => {
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  const handleAbilityCheck = (abilityName, modifier) => {
    rollDice(20, 1, modifier, "ability", `${abilityName.toUpperCase()} Check`);
  };

  const toggleAbilityExpand = (ability, e) => {
    e.stopPropagation();
    setExpandedAbility(expandedAbility === ability ? null : ability);
  };

  const handleShareAbility = (ability, e) => {
    e.stopPropagation();
    const info = ABILITY_INFO[ability];
    const score = character[ability];
    const modifier = character[`${ability}_modifier`];
    const modStr = modifier >= 0 ? `+${modifier}` : `${modifier}`;

    const message = `**${character.name}'s ${info.name}** | Score: ${score} (${modStr}) | ${info.description}`;
    postToChat(message);
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

  const handleExportCharacter = () => {
    const characterData = {
      ...character,
      exported_at: new Date().toISOString(),
      export_version: "1.0",
    };

    const dataStr = JSON.stringify(characterData, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `${character.name.replace(/[^a-z0-9]/gi, "_")}_character.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="character-sheet">
      {/* Header */}
      <div className="sheet-header">
        <div className="character-title">
          <h2>
            {character.name}
            {isDMViewingPlayer && (
              <span className="dm-viewing-badge">DM View</span>
            )}
          </h2>
          <p>
            Level {character.level} {character.race} {character.character_class}
          </p>
        </div>
        <div className="header-buttons">
          {canLevelUp && (
            <button
              onClick={() => setShowLevelUpModal(true)}
              className="btn btn-primary level-up-btn"
              title="Level up your character"
            >
              ⬆ Level Up
            </button>
          )}
          <button
            onClick={handleExportCharacter}
            className="btn btn-secondary export-btn"
            title="Download character as JSON backup"
          >
            📥 Export
          </button>
        </div>
      </div>

      {/* Main Stats */}
      <div className="main-stats">
        <div className="combat-stats-stack">
          <div className="stacked-stat">
            <span className="stacked-label">AC</span>
            <span className="stacked-value">{character.armor_class}</span>
          </div>
          <div className="stacked-stat">
            <span className="stacked-label">Speed</span>
            <span className="stacked-value">{character.speed} ft</span>
          </div>
          <div className="stacked-stat">
            <span className="stacked-label">Prof</span>
            <span className="stacked-value">
              +{character.proficiency_bonus}
            </span>
          </div>
        </div>
        <HPManager character={character} onUpdateHP={handleUpdateHP} />
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
            const info = ABILITY_INFO[ability];
            const isExpanded = expandedAbility === ability;
            return (
              <div key={ability} className="ability-container">
                <div
                  className={`ability-box clickable ${isExpanded ? "expanded" : ""}`}
                  onClick={() => handleAbilityCheck(ability, modifier)}
                  title={`Click to roll ${ability} check`}
                >
                  <button
                    className="ability-expand-btn"
                    onClick={(e) => toggleAbilityExpand(ability, e)}
                    title={isExpanded ? "Collapse" : "Expand for details"}
                  >
                    {isExpanded ? "▼" : "▶"}
                  </button>
                  <div className="ability-name">{info.abbr}</div>
                  <div className="ability-modifier">
                    {formatModifier(modifier)}
                  </div>
                  <div className="ability-score">{score}</div>
                </div>
                {isExpanded && (
                  <div className="ability-details">
                    <p className="ability-description">{info.description}</p>
                    {info.skills.length > 0 && (
                      <div className="ability-skills">
                        <strong>Skills:</strong> {info.skills.join(", ")}
                      </div>
                    )}
                    <div className="ability-uses">
                      <strong>Common Uses:</strong>
                      <ul>
                        {info.commonUses.map((use, i) => (
                          <li key={i}>{use}</li>
                        ))}
                      </ul>
                    </div>
                    <button
                      className="btn btn-secondary btn-sm share-ability-btn"
                      onClick={(e) => handleShareAbility(ability, e)}
                      title="Share ability info to chat"
                    >
                      📢 Share to Log
                    </button>
                  </div>
                )}
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

      {/* Attacks & Spells Side-by-Side */}
      <div className="combat-sections">
        <AttacksSection
          character={character}
          onUpdateCharacter={updateCharacter}
          onRollDice={rollDice}
          canEdit={true}
        />
        <SpellsSection
          character={character}
          onUpdateCharacter={updateCharacter}
          onRollDice={rollDice}
          onPostToChat={postToChat}
          canEdit={true}
        />
      </div>

      {/* Level Up Modal */}
      {showLevelUpModal && (
        <LevelUpModal
          character={character}
          onUpdateCharacter={updateCharacter}
          onClose={() => setShowLevelUpModal(false)}
        />
      )}
    </div>
  );
}
