import React from 'react';
const styles = {
  Screen: {
    backgroundColor: '#5a72a0',
    width: '100vw', // viewport width
    height: '100vh', // viewport height
    position: 'absolute',
  },
};

const Screen = (props) => {
  return (
    <div style={styles.Screen}>
      {props.children}
    </div>
  );
};

export default Screen;