Here's the implementation of the requested application:

First, let's create a new React project with TypeScript:

```bash
npx create-react-app swapi-characters --template typescript
cd swapi-characters
npm install axios
```

Now, let's update the necessary files:

src/App.tsx:

```tsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

interface Character {
  name: string;
  url: string;
}

const App: React.FC = () => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        const response = await axios.get('https://swapi.dev/api/people');
        setCharacters(response.data.results);
      } catch (error) {
        console.error('Error fetching characters:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCharacters();
  }, []);

  if (isLoading) {
    return <div className="loader">Loading...</div>;
  }

  return (
    <div className="App">
      <h1>Star Wars Characters</h1>
      <ul className="character-list">
        {characters.map((character) => (
          <li key={character.url} className="character-item">
            {character.name}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default App;
```

src/App.css:

```css
.App {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
}

.loader {
  text-align: center;
  font-size: 24px;
  margin-top: 50px;
}

.character-list {
  list-style-type: none;
  padding: 0;
}

.character-item {
  background-color: #f0f0f0;
  margin: 10px 0;
  padding: 15px;
  border-radius: 5px;
  font-size: 18px;
}
```

This implementation creates a simple React application that fetches Star Wars characters from the SWAPI API and displays them in a list. It uses TypeScript for type safety and axios for making API requests. The application shows a loading message while fetching data and handles potential errors by logging them to the console.

To run the application, use the following command in the project directory:

```bash
npm start
```

The application will be available at http://localhost:3000 in your web browser.