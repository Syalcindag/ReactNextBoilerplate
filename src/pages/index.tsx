import React, { useMemo } from 'react';
import styles from '../styles/Home.module.scss';

const Home: React.FC = () => {
  const mockData = useMemo(() => ({
    title: "Welcome to Next.js!",
    description: "This is a boilerplate for your Next.js project."
  }), []);

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>{mockData.title}</h1>
      <p className={styles.description}>{mockData.description}</p>
    </div>
  );
};

export default Home;
