# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]:
    - generic [ref=e5]: "[plugin:vite:import-analysis]"
    - generic [ref=e6]: Failed to resolve import "../../frontend/src/api/authClient" from "src/components/LoginForm.tsx". Does the file exist?
  - generic [ref=e7]:
    - text: "C:"
    - generic [ref=e8] [cursor=pointer]: /Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/src/components/LoginForm.tsx:2:33
  - generic [ref=e9]: "2 | var _s = $RefreshSig$(); 3 | import { useState } from \"react\"; 4 | import { createAuthClient } from \"../../frontend/src/api/authClient\"; | ^ 5 | const isValidEmail = (email) => { 6 | const trimmed = email.trim();"
  - generic [ref=e10]:
    - text: "at TransformPluginContext._formatError (file:"
    - generic [ref=e11] [cursor=pointer]: ///C:/Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/node_modules/vite/dist/node/chunks/dep-D_zLpgQd.js:49258:41
    - text: ") at TransformPluginContext.error (file:"
    - generic [ref=e12] [cursor=pointer]: ///C:/Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/node_modules/vite/dist/node/chunks/dep-D_zLpgQd.js:49253:16
    - text: ") at normalizeUrl (file:"
    - generic [ref=e13] [cursor=pointer]: ///C:/Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/node_modules/vite/dist/node/chunks/dep-D_zLpgQd.js:64306:23
    - text: ) at process.processTicksAndRejections (node:internal
    - generic [ref=e14] [cursor=pointer]: /process/task_queues:105:5
    - text: ") at async file:"
    - generic [ref=e15] [cursor=pointer]: ///C:/Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/node_modules/vite/dist/node/chunks/dep-D_zLpgQd.js:64438:39
    - text: "at async Promise.all (index 2) at async TransformPluginContext.transform (file:"
    - generic [ref=e16] [cursor=pointer]: ///C:/Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/node_modules/vite/dist/node/chunks/dep-D_zLpgQd.js:64365:7
    - text: ") at async PluginContainer.transform (file:"
    - generic [ref=e17] [cursor=pointer]: ///C:/Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/node_modules/vite/dist/node/chunks/dep-D_zLpgQd.js:49099:18
    - text: ") at async loadAndTransform (file:"
    - generic [ref=e18] [cursor=pointer]: ///C:/Users/admin/Downloads/fba/repos/fba-bench-enterprise/web/node_modules/vite/dist/node/chunks/dep-D_zLpgQd.js:51977:27
  - generic [ref=e19]:
    - text: Click outside, press
    - generic [ref=e20]: Esc
    - text: key, or fix the code to dismiss.
    - text: You can also disable this overlay by setting
    - code [ref=e21]: server.hmr.overlay
    - text: to
    - code [ref=e22]: "false"
    - text: in
    - code [ref=e23]: vite.config.ts
    - text: .
```