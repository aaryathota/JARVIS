from workflow_manager import workflow_manager

print('Loaded Workflows:')
print('=' * 60)
for name, workflow in workflow_manager.workflows.items():
    print(f'\n{name}')
    print(f'  Commands: {len(workflow["commands"])}')
    for i, cmd in enumerate(workflow['commands'], 1):
        print(f'    {i}. {cmd}')

print('\n' + '=' * 60)
print(f'Total: {len(workflow_manager.workflows)} workflows loaded')
