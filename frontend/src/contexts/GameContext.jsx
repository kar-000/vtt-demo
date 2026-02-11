import React, { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";
import websocket from "../services/websocket";
import { useAuth } from "./AuthContext";

const GameContext = createContext(null);

export const GameProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [characters, setCharacters] = useState([]);
  const [allCharacters, setAllCharacters] = useState([]); // All characters (DM only)
  const [currentCharacter, setCurrentCharacter] = useState(null);
  const [rollLog, setRollLog] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initiative, setInitiative] = useState({
    active: false,
    round: 1,
    current_turn_index: 0,
    combatants: [],
  });

  // Auto-track action economy when attacks/spells are used
  const [autoTrackActions, setAutoTrackActions] = useState(() => {
    const saved = localStorage.getItem("autoTrackActions");
    return saved !== null ? JSON.parse(saved) : true;
  });

  // Persist auto-track setting
  useEffect(() => {
    localStorage.setItem("autoTrackActions", JSON.stringify(autoTrackActions));
  }, [autoTrackActions]);

  // Campaign ID for demo purposes (in Phase 3, this will be dynamic)
  const campaignId = 1;

  useEffect(() => {
    if (isAuthenticated) {
      loadCharacters();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated && user) {
      const token = localStorage.getItem("token");
      if (token) {
        connectWebSocket(token);
      }
    }

    return () => {
      websocket.disconnect();
    };
  }, [isAuthenticated, user]);

  const connectWebSocket = (token) => {
    websocket.connect(campaignId, token);

    websocket.on("connected", () => {
      setConnected(true);
    });

    websocket.on("disconnected", () => {
      setConnected(false);
    });

    websocket.on("dice_roll_result", (data) => {
      setRollLog((prev) => [data, ...prev].slice(0, 100)); // Keep last 100 rolls
    });

    websocket.on("user_connected", (data) => {
      console.log("User connected:", data);
    });

    websocket.on("user_disconnected", (data) => {
      console.log("User disconnected:", data);
    });

    websocket.on("initiative_state", (data) => {
      setInitiative(data);
    });

    websocket.on("chat_message", (data) => {
      // Add chat messages to roll log with a special type
      setRollLog((prev) => [{ ...data, type: "chat" }, ...prev].slice(0, 100));
    });
  };

  const postToChat = (message) => {
    websocket.sendChatMessage(message);
  };

  const loadCharacters = async () => {
    try {
      setLoading(true);
      const chars = await api.getCharacters();
      setCharacters(chars);
      if (chars.length > 0 && !currentCharacter) {
        setCurrentCharacter(chars[0]);
      }
    } catch (error) {
      console.error("Error loading characters:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadAllCharacters = async () => {
    try {
      const chars = await api.getAllCharacters();
      setAllCharacters(chars);
      return chars;
    } catch (error) {
      console.error("Error loading all characters:", error);
      throw error;
    }
  };

  const createCharacter = async (characterData) => {
    try {
      const newChar = await api.createCharacter(characterData);
      setCharacters((prev) => [...prev, newChar]);
      if (!currentCharacter) {
        setCurrentCharacter(newChar);
      }
      return newChar;
    } catch (error) {
      console.error("Error creating character:", error);
      throw error;
    }
  };

  const updateCharacter = async (id, characterData) => {
    try {
      const updated = await api.updateCharacter(id, characterData);
      setCharacters((prev) =>
        prev.map((char) => (char.id === id ? updated : char)),
      );
      // Also update allCharacters for DM view
      setAllCharacters((prev) =>
        prev.map((char) => (char.id === id ? updated : char)),
      );
      if (currentCharacter?.id === id) {
        setCurrentCharacter(updated);
      }
      return updated;
    } catch (error) {
      console.error("Error updating character:", error);
      throw error;
    }
  };

  const deleteCharacter = async (id) => {
    try {
      await api.deleteCharacter(id);
      setCharacters((prev) => prev.filter((char) => char.id !== id));
      if (currentCharacter?.id === id) {
        setCurrentCharacter(characters[0] || null);
      }
    } catch (error) {
      console.error("Error deleting character:", error);
      throw error;
    }
  };

  const updateHP = async (characterId, updateData) => {
    try {
      let updated;
      if (updateData.type === "damage" || updateData.type === "healing") {
        updated = await api.applyDamageOrHealing(
          characterId,
          updateData.type,
          updateData.amount,
        );
      } else if (updateData.type === "direct") {
        updated = await api.updateHP(characterId, updateData.data);
      }

      setCharacters((prev) =>
        prev.map((char) => (char.id === characterId ? updated : char)),
      );
      // Also update allCharacters for DM view
      setAllCharacters((prev) =>
        prev.map((char) => (char.id === characterId ? updated : char)),
      );
      if (currentCharacter?.id === characterId) {
        setCurrentCharacter(updated);
      }
      return updated;
    } catch (error) {
      console.error("Error updating HP:", error);
      throw error;
    }
  };

  const rollDice = (
    diceType,
    numDice = 1,
    modifier = 0,
    rollType = "manual",
    label = null,
  ) => {
    if (!currentCharacter) {
      console.error("No character selected");
      return;
    }

    // Convert dice type string (e.g., "d20") to integer (e.g., 20)
    let diceTypeInt = diceType;
    if (typeof diceType === "string") {
      const match = diceType.match(/d(\d+)/i);
      if (match) {
        diceTypeInt = parseInt(match[1], 10);
      }
    }

    websocket.rollDice({
      character_name: currentCharacter.name,
      dice_type: diceTypeInt,
      num_dice: numDice,
      modifier,
      roll_type: rollType,
      label,
    });
  };

  // Initiative tracker methods
  const sendInitiativeAction = (action, data = {}) => {
    websocket.send("initiative_update", { action, data });
  };

  const startCombat = (characterIds) => {
    sendInitiativeAction("start_combat", { character_ids: characterIds });
  };

  const addCombatant = (monsterData) => {
    // Accept either a string (simple name) or full monster object
    if (typeof monsterData === "string") {
      sendInitiativeAction("add_combatant", {
        name: monsterData,
        initiative: null,
      });
    } else {
      sendInitiativeAction("add_combatant", {
        name: monsterData.name,
        initiative: monsterData.initiative || null,
        max_hp: monsterData.max_hp || monsterData.hit_points || 10,
        armor_class: monsterData.armor_class || 10,
        speed: monsterData.speed || 30,
        attacks: monsterData.attacks || [],
        dex_mod: monsterData.dex_mod || 0,
      });
    }
  };

  const updateNPC = (combatantId, updates) => {
    sendInitiativeAction("update_npc", {
      combatant_id: combatantId,
      ...updates,
    });
  };

  const removeCombatant = (combatantId) => {
    sendInitiativeAction("remove_combatant", { combatant_id: combatantId });
  };

  const rollInitiativeFor = (combatantId) => {
    sendInitiativeAction("roll_initiative", { combatant_id: combatantId });
  };

  const rollAllInitiative = () => {
    sendInitiativeAction("roll_all", {});
  };

  const setInitiativeValue = (combatantId, value) => {
    sendInitiativeAction("set_initiative", {
      combatant_id: combatantId,
      value,
    });
  };

  const nextTurn = () => {
    sendInitiativeAction("next_turn", {});
  };

  const previousTurn = () => {
    sendInitiativeAction("previous_turn", {});
  };

  const endCombat = () => {
    sendInitiativeAction("end_combat", {});
  };

  // Action economy methods
  const useAction = (combatantId) => {
    sendInitiativeAction("use_action", { combatant_id: combatantId });
  };

  const useBonusAction = (combatantId) => {
    sendInitiativeAction("use_bonus_action", { combatant_id: combatantId });
  };

  const useReaction = (combatantId) => {
    sendInitiativeAction("use_reaction", { combatant_id: combatantId });
  };

  const useMovement = (combatantId, amount) => {
    sendInitiativeAction("use_movement", { combatant_id: combatantId, amount });
  };

  const resetActionEconomy = (combatantId) => {
    sendInitiativeAction("reset_action_economy", { combatant_id: combatantId });
  };

  // Get combatant ID for current character (if in combat)
  const getCurrentCombatantId = () => {
    if (!initiative.active || !currentCharacter) return null;
    const combatant = initiative.combatants.find(
      (c) => c.character_id === currentCharacter.id,
    );
    return combatant?.id || null;
  };

  // Auto-consume action economy when attacks/spells are used
  // actionType: "action" | "bonus_action" | "reaction"
  const consumeActionEconomy = (actionType) => {
    if (!autoTrackActions || !initiative.active) return;

    const combatantId = getCurrentCombatantId();
    if (!combatantId) return;

    // Only consume if it's the current character's turn (for action/bonus action)
    // Reactions can be used on any turn
    const currentTurnCombatant =
      initiative.combatants[initiative.current_turn_index];
    const isMyTurn = currentTurnCombatant?.id === combatantId;

    if (actionType === "action" && isMyTurn) {
      useAction(combatantId);
    } else if (actionType === "bonus_action" && isMyTurn) {
      useBonusAction(combatantId);
    } else if (actionType === "reaction") {
      // Reactions can be used on any turn
      useReaction(combatantId);
    }
  };

  const value = {
    characters,
    allCharacters,
    currentCharacter,
    setCurrentCharacter,
    rollLog,
    connected,
    loading,
    loadCharacters,
    loadAllCharacters,
    createCharacter,
    updateCharacter,
    deleteCharacter,
    updateHP,
    rollDice,
    postToChat,
    // Initiative tracker
    initiative,
    startCombat,
    addCombatant,
    updateNPC,
    removeCombatant,
    rollInitiativeFor,
    rollAllInitiative,
    setInitiativeValue,
    nextTurn,
    previousTurn,
    endCombat,
    // Action economy
    useAction,
    useBonusAction,
    useReaction,
    useMovement,
    resetActionEconomy,
    // Auto-track actions
    autoTrackActions,
    setAutoTrackActions,
    consumeActionEconomy,
  };

  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
};

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error("useGame must be used within a GameProvider");
  }
  return context;
};
