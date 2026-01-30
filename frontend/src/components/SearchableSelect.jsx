import React, { useState, useRef, useEffect } from 'react';

/**
 * Searchable dropdown. options: [{ id, label, endpoint? }], value: selected id,
 * onChange(value, fullOption).
 */
export default function SearchableSelect({ options, value, onChange, placeholder = 'Select...' }) {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState('');
  const containerRef = useRef(null);

  const selected = options.find((o) => o.id === value);
  const displayLabel = selected ? selected.label : placeholder;

  const filtered =
    filter.trim() === ''
      ? options
      : options.filter(
          (o) =>
            o.label.toLowerCase().includes(filter.toLowerCase()) ||
            o.id.toLowerCase().includes(filter.toLowerCase())
        );

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, [open]);

  const handleSelect = (option) => {
    onChange(option.id, option);
    setOpen(false);
    setFilter('');
  };

  return (
    <div className="searchable-select" ref={containerRef}>
      <button
        type="button"
        className="searchable-select-trigger"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className="searchable-select-value">{displayLabel}</span>
        <span className="searchable-select-arrow">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="searchable-select-dropdown" role="listbox">
          <input
            type="text"
            className="searchable-select-input"
            placeholder="Search models..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            autoFocus
            aria-label="Filter models"
          />
          <ul className="searchable-select-list">
            {filtered.length === 0 ? (
              <li className="searchable-select-empty">No matches</li>
            ) : (
              filtered.map((opt) => (
                <li
                  key={opt.id}
                  role="option"
                  aria-selected={opt.id === value}
                  className={`searchable-select-option ${opt.id === value ? 'selected' : ''}`}
                  onClick={() => handleSelect(opt)}
                >
                  <span className="searchable-select-option-label">{opt.label}</span>
                  <span className="searchable-select-option-id">{opt.id}</span>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
