Here's the implementation of a searchable select component with accessibility support in React 18.x using TypeScript:

SearchableSelect.tsx:

```typescript
import React, { useState, useRef, useEffect } from 'react';

interface Option {
  value: string;
  label: string;
}

interface SearchableSelectProps {
  options: Option[];
  onChange: (selectedOption: Option | null) => void;
  placeholder?: string;
}

export const SearchableSelect: React.FC<SearchableSelectProps> = ({
  options,
  onChange,
  placeholder = 'Select an option',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<Option | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const selectRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const filteredOptions = options.filter((option) =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setSearchTerm('');
      setFocusedIndex(-1);
    }
  };

  const handleOptionClick = (option: Option) => {
    setSelectedOption(option);
    onChange(option);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'Enter':
        if (!isOpen) {
          setIsOpen(true);
        } else if (focusedIndex !== -1) {
          handleOptionClick(filteredOptions[focusedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex((prevIndex) =>
          Math.min(prevIndex + 1, filteredOptions.length - 1)
        );
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex((prevIndex) => Math.max(prevIndex - 1, -1));
        break;
    }
  };

  useEffect(() => {
    if (isOpen && listRef.current) {
      const focusedElement = listRef.current.children[focusedIndex] as HTMLElement;
      if (focusedElement) {
        focusedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [focusedIndex, isOpen]);

  return (
    <div
      ref={selectRef}
      className="searchable-select"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      <div className="select-header" onClick={handleToggle}>
        {selectedOption ? selectedOption.label : placeholder}
      </div>
      {isOpen && (
        <div className="select-dropdown">
          <input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search..."
            autoFocus
          />
          <ul ref={listRef}>
            {filteredOptions.map((option, index) => (
              <li
                key={option.value}
                onClick={() => handleOptionClick(option)}
                className={index === focusedIndex ? 'focused' : ''}
              >
                {option.label}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

index.css:

```css
.searchable-select {
  position: relative;
  width: 200px;
  font-family: Arial, sans-serif;
}

.select-header {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  background-color: #fff;
}

.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  border: 1px solid #ccc;
  border-top: none;
  border-radius: 0 0 4px 4px;
  background-color: #fff;
  max-height: 200px;
  overflow-y: auto;
}

.select-dropdown input {
  width: 100%;
  padding: 10px;
  border: none;
  border-bottom: 1px solid #ccc;
  outline: none;
}

.select-dropdown ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.select-dropdown li {
  padding: 10px;
  cursor: pointer;
}

.select-dropdown li:hover,
.select-dropdown li.focused {
  background-color: #f0f0f0;
}
```

This implementation provides a searchable select component with accessibility support, including keyboard navigation and focus management. The component can be used by importing it and passing the required props:

```typescript
import { SearchableSelect } from './SearchableSelect';

const options = [
  { value: '1', label: 'Option 1' },
  { value: '2', label: 'Option 2' },
  { value: '3', label: 'Option 3' },
];

const handleChange = (selectedOption: Option | null) => {
  console.log('Selected option:', selectedOption);
};

<SearchableSelect options={options} onChange={handleChange} placeholder="Select an option" />
```