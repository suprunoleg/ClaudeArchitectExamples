---
name: deploy-staging
description: Compiles the codebase and pushes the artifact to the staging server. Use this when the user asks to "deploy to staging".
---

# Deploy to Staging Skill

You have been invoked to deploy the current project to the staging server.

## Instructions
1. Run `pytest` to ensure all tests pass before deploying.
2. If tests fail, STOP. Tell the user the deployment failed due to tests.
3. If tests pass, run `docker build -t app:staging .`
4. Run `docker push myregistry.com/app:staging`
5. Report the final deployment status to the user.
