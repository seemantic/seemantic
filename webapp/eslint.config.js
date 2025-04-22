//  @ts-check

import { tanstackConfig } from '@tanstack/eslint-config'

const disableImport = {
    rules: {
        "import/order": "off",
    },
}

export default [
    {
        ignores: ["src/shadcn/**"],
    },
    ...tanstackConfig,
    disableImport,
]
