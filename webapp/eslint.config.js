//  @ts-check

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
            // Add other root config files like tailwind.config.js, postcss.config.js if they exist
        ],
    },

    // 2. Apply base JavaScript rules (optional, check if tanstackConfig includes this)
    // js.configs.recommended, // Uncomment if needed

    // 3. Apply Tanstack config (likely includes TS rules with parserOptions.project)
    ...tanstackConfig,

    // 4. Apply custom rule overrides AFTER tanstackConfig
    {
        rules: {
            ...disableImportRules,
            // Add other project-specific rule overrides here if needed
        }
    }
];
