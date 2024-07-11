import React from 'react';
import styles from '../styles/Home.module.scss';

const Home: React.FC = () => {
  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Welcome to Next.js!</h1>
    </div>
  );
};

export default Home;
