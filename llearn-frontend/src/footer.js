import React from 'react';


const styles = {
    Footer: {
    backgroundColor: '#fdffe2',
    position: 'fixed', 
    bottom: 0, 
    left: 0,
     width: '100%' }}


const Footer = (props) =>  {
  return (
    <div style={styles.Footer}>
    {props.children}
    </div>
  );
}

export default Footer;