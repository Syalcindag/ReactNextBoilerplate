module.exports = {
    preset: 'ts-jest',
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['./setupTests.ts'],
    testPathIgnorePatterns: ['/node_modules/', '/.next/'],
  };
  