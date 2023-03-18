import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router, Switch, Route, Link } from 'react-router-dom';
import './index.css';

function App() {
  const [percentage, setPercentage] = useState(0);
  const [bluePercentage, setBluePercentage] = useState(0);
  const [redPercentage, setRedPercentage] = useState(100);

  const handleInputChange = (event) => {
    setPercentage(parseInt(event.target.value));
  };

  const handleButtonClick = () => {
    const blueBar = document.getElementById('blueBar');
    blueBar.style.width = `${percentage}%`;

    setBluePercentage(percentage);
    setRedPercentage(100 - percentage);
  };

  return (
    <Router>
      <div className="container">
        <input type="text" onChange={handleInputChange} />
        <button onClick={handleButtonClick}>Update Bar</button>
        <div className="bar">
          <div className="blue" id="blueBar"></div>
          <div className="blue-percentage">{bluePercentage}%</div>
          <div className="red-percentage">{redPercentage}%</div>
        </div>
        <div className="footer">
          <Link to="/terms">Terms and Conditions</Link>
          <Link to="/contact">Contact</Link>
        </div>
      </div>
      <Switch>
        <Route path="/terms">
          <h1>Terms and Conditions Page</h1>
          <p>Placeholder text for terms and conditions.</p>
        </Route>
        <Route path="/contact">
          <h1>Contact Page</h1>
          <p>Placeholder text for contact information.</p>
        </Route>
      </Switch>
    </Router>
  );
}

ReactDOM.render(<App />, document.getElementById('root'));
