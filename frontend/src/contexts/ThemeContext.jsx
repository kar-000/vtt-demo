import React, { createContext, useContext, useState, useEffect } from "react";

const ThemeContext = createContext(null);

const THEME_STORAGE_KEY = "vtt-theme";
const VALID_THEMES = ["dark-medieval", "pink-pony-club", "boring"];
const DEFAULT_THEME = "dark-medieval";

export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState(() => {
    // Initialize from localStorage or default
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return VALID_THEMES.includes(stored) ? stored : DEFAULT_THEME;
  });

  // Apply theme to document body
  useEffect(() => {
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = (newTheme) => {
    if (VALID_THEMES.includes(newTheme)) {
      setThemeState(newTheme);
    } else {
      console.warn(
        `Invalid theme: ${newTheme}. Valid themes: ${VALID_THEMES.join(", ")}`,
      );
    }
  };

  const cycleTheme = () => {
    const currentIndex = VALID_THEMES.indexOf(theme);
    const nextIndex = (currentIndex + 1) % VALID_THEMES.length;
    setTheme(VALID_THEMES[nextIndex]);
  };

  const value = {
    theme,
    setTheme,
    cycleTheme,
    themes: VALID_THEMES,
    isTheme: (t) => theme === t,
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
