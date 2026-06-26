# Virtual Workspace

Pass a VS Code-style `.code-workspace` JSON file as a positional argument.

## Flattened View (Default)

By default, folder paths are symlinked into `~/workspace/` inside the sandbox:

```shell
bubble-agent ~/projects/my.code-workspace
```

Example workspace file:

```jsonc
// ~/projects/my.code-workspace
{
  "folders": [
    { "path": "/home/user/frontend-app", "name": "frontend" },
    { "path": "/home/user/backend-api", "name": "backend" },
    { "path": "../libs/shared-utils", "name": "shared" }
  ]
}
```

Inside the sandbox:

```
~/workspace/
  frontend/  -> /home/user/frontend-app
  backend/   -> /home/user/backend-api
  shared/    -> /home/user/libs/shared-utils
```

## Preserving Original Tree

For projects like Ansible collections that depend on a specific directory layout, pass `-S` to skip symlink creation and chdir to the deepest common ancestor of all workspace folders instead:

```shell
bubble-agent -S ~/ansible.code-workspace
```

This bind-mounts only the real paths, so the original `ansible/collections/ansible_collections/...` hierarchy is visible as-is. Relative paths are resolved relative to the `.code-workspace` file's location. Duplicate folder names get a `_N` suffix appended.
