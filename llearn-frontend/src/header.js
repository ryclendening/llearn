import React from 'react';

const styles = {
  Header: {
    position: 'relative',
    top: '0px',
    left: '0px',
    width: '100vw',
    height: '64px',
    backgroundColor: '#282828',
  },
  Brand: {
    position: 'absolute',
    margin: '10px',
    padding: '10px',
    color: 'white',
    fontFamily: 'Raleway'

  },
};

const Header = (props) => {
  return (
    <div style={styles.Header}>
    <h1 style={styles.Brand}>LLearn</h1>
    {props.children}
    </div>
  );
};

export default Header;