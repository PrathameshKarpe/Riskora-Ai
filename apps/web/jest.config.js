const nextJest = require("next/jest");

const createJestConfig = nextJest({ dir: "./" });

const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
    // recharts uses ESM — map to CJS stub in tests
    "^recharts$": "<rootDir>/__mocks__/recharts.tsx",
  },
  testMatch: ["**/__tests__/**/*.test.{ts,tsx}"],
  transform: {
    "^.+\\.(ts|tsx)$": ["ts-jest", {
      tsconfig: {
        jsx: "react-jsx",
        esModuleInterop: true,
      }
    }],
  },
  transformIgnorePatterns: [
    "/node_modules/(?!(recharts|d3-.*|@tanstack)/)",
  ],
};

module.exports = createJestConfig(customJestConfig);
