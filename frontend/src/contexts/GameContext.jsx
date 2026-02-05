import React, { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";
import websocket from "../services/websocket";
import { useAuth } from "./AuthContext";

const GameContext = createContext(null);

export const GameProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [characters, setCharacters] = useState([]);
  const [currentCharacter, setCurrentCharacter] = useState(null);
  const [rollLog, setRollLog] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);

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

    websocket.rollDice({
      character_name: currentCharacter.name,
      dice_type: diceType,
      num_dice: numDice,
      modifier,
      roll_type: rollType,
      label,
    });
  };

  const value = {
    characters,
    currentCharacter,
    setCurrentCharacter,
    rollLog,
    connected,
    loading,
    loadCharacters,
    createCharacter,
    updateCharacter,
    deleteCharacter,
    rollDice,
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
