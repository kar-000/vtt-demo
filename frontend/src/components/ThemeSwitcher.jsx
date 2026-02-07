import React, { useState, useRef, useEffect } from "react";
import { useTheme } from "../contexts/ThemeContext";
import "./ThemeSwitcher.css";

const THEME_INFO = {
  "dark-medieval": {
    label: "Dark Medieval",
    icon: "\u{1F3F0}",
    description: "Classic dark fantasy with gold accents",
  },
  "pink-pony-club": {
    label: "Pink Pony Club",
    icon: "\u{1F984}",
    description: "Sparkly pink and playful",
  },
  boring: {
    label: "Boring",
    icon: "\u{1F4C4}",
    description: "Minimal and no-frills",
  },
};

export const ThemeSwitcher = ({ compact = false }) => {
  const { theme, setTheme, themes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (newTheme) => {
    setTheme(newTheme);
    setIsOpen(false);
  };

  const currentTheme = THEME_INFO[theme];

  if (compact) {
    // Simple icon button that cycles through themes
    return (
      <button
        className="theme-switcher-compact"
        onClick={() => {
          const currentIndex = themes.indexOf(theme);
          const nextIndex = (currentIndex + 1) % themes.length;
          setTheme(themes[nextIndex]);
        }}
        title={`Theme: ${currentTheme.label} (click to change)`}
      >
        {currentTheme.icon}
      </button>
    );
  }

  return (
    <div className="theme-switcher" ref={dropdownRef}>
      <button
        className="theme-switcher-trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span className="theme-icon">{currentTheme.icon}</span>
        <span className="theme-label">{currentTheme.label}</span>
        <span className="theme-arrow">{isOpen ? "\u25B2" : "\u25BC"}</span>
      </button>

      {isOpen && (
        <ul className="theme-dropdown" role="listbox">
          {themes.map((t) => (
            <li
              key={t}
              className={`theme-option ${t === theme ? "active" : ""}`}
              onClick={() => handleSelect(t)}
              role="option"
              aria-selected={t === theme}
            >
              <span className="theme-icon">{THEME_INFO[t].icon}</span>
              <div className="theme-details">
                <span className="theme-name">{THEME_INFO[t].label}</span>
                <span className="theme-desc">{THEME_INFO[t].description}</span>
              </div>
              {t === theme && <span className="theme-check">{"\u2713"}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ThemeSwitcher;
