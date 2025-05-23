//  @ts-check

import js from "@eslint/js"; // Add this line to import js
import { tanstackConfig } from '@tanstack/eslint-config';
// It's good practice to include base JS rules if not already handled by tanstackConfig

const disableImportRules = { // Renamed for clarity
    "import/order": "off",
};

export default [
    // 1. Ignore specific files globally first
    {
        ignores: [
            "src/shadcn/**",        // Ignore shadcn generated code
            "eslint.config.js",     // Ignore this ESLint config file
            "prettier.config.js",   // Ignore Prettier config
            "vite.config.js",       // Ignore Vite config
            "vitest.workspace.js", // Ignore Vitest workspace config
            ".storybook/**",      // Ignore Storybook config
            // Add other root config files like tailwind.config.js, postcss.config.js if they exist
        ],
    },

    // 2. Apply base JavaScript rules
    js.configs.recommended,

    // 3. Apply Tanstack config (likely includes TS rules with parserOptions.project)
    ...tanstackConfig,

    // 4. Apply custom rule overrides AFTER tanstackConfig
    {
        rules: {
            ...disableImportRules,
            "import/no-extraneous-dependencies": [
                "error",
                {
                    devDependencies: ["**/*.stories.tsx", "**/*.stories.ts"],
                    peerDependencies: true,
                },
            ],
            "eqeqeq": "error", // Enforce strict equality
            "no-console": "warn", // Warn about console.log statements
            // Add other project-specific rule overrides here if needed
        }
    }
];
